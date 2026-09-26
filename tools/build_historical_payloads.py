#!/usr/bin/env python3
"""Build structural payloads from the verified clean and reconciled Lua sources.

The generated payloads contain only changed blocks with stable surrounding
context. They never contain or emit a complete upstream Lua file.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


ZIBO_40535_SHA256 = "ff313b0e88c62845ad1c4a2b1f4bd599f57d8799e8d6707bfc10a3369fd63a8e"
LEVELUP_SHARED_40535_SHA256 = ZIBO_40535_SHA256


@dataclass(frozen=True)
class Surface:
    family: str
    start_function: str
    end_function: str
    required_new_token: str | None = None
    include_groups: tuple[int, ...] | None = None


REFERENCE_DATA_SURFACES = (
    Surface("I01", "spaces_after", "wind_alt_order"),
    Surface("I01", "read_navdata2", "dump_ils_table", include_groups=(1, 3, 4)),
    Surface("I08", "find_des_rnw_data", "find_id_app_data"),
    Surface("I08", "find_id_app_data", "find_hold_data", include_groups=(1, 2, 3, 4, 5)),
    Surface("I01", "find_id_app_data", "find_hold_data", include_groups=(6,)),
    Surface("I01", "B738_fmc_nav_status", "B738_fmc_hold"),
    # This owner also contains a historical runway-end geometry change which
    # is not part of I01/I08. Select only the explicitly classified LP blocks.
    Surface("I01", "B738_gls", "mmr_active_mode", "FIX: LP service level"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").split("\n")


def function_line(source: list[str], name: str) -> int:
    prefix = f"function {name}("
    matches = [index for index, line in enumerate(source) if line.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"Expected one top-level {name} function, found {len(matches)}")
    return matches[0]


def surface(source: list[str], spec: Surface) -> list[str]:
    start = function_line(source, spec.start_function)
    end = function_line(source, spec.end_function)
    if end <= start:
        raise ValueError(f"Invalid function order: {spec.start_function} -> {spec.end_function}")
    # Include the next function declaration as a right-hand structural anchor.
    # Several fixes insert a private helper between two existing functions; an
    # exclusive end would leave the clean block intact inside the replacement
    # and make repeated application ambiguous.
    return source[start:end + 1]


def occurrences(haystack: list[str], needle: list[str]) -> int:
    if not needle:
        raise ValueError("A structural replacement may not have an empty old block")
    # Lua source lines cannot contain NUL.  Joining with that sentinel keeps
    # line boundaries exact while avoiding an O(source * block) list-slice
    # comparison for every context-expansion attempt.
    return ("\0".join(haystack) + "\0").count("\0".join(needle) + "\0")


def changed_groups(old: list[str], new: list[str], context: int = 3) -> list[tuple[int, int, int, int]]:
    changes = [opcode for opcode in difflib.SequenceMatcher(a=old, b=new, autojunk=False).get_opcodes()
               if opcode[0] != "equal"]
    if not changes:
        return []
    groups: list[list[tuple[str, int, int, int, int]]] = []
    for change in changes:
        if not groups:
            groups.append([change])
            continue
        previous = groups[-1][-1]
        old_gap = change[1] - previous[2]
        new_gap = change[3] - previous[4]
        if old_gap <= context * 2 or new_gap <= context * 2:
            groups[-1].append(change)
        else:
            groups.append([change])
    result = []
    for group in groups:
        first, last = group[0], group[-1]
        result.append((
            max(0, first[1] - context),
            min(len(old), last[2] + context),
            max(0, first[3] - context),
            min(len(new), last[4] + context),
        ))
    return result


def unique_replacement_bounds(
    old_surface: list[str],
    new_surface: list[str],
    old_start: int,
    old_end: int,
    new_start: int,
    new_end: int,
    zibo: list[str],
    levelup: list[str],
    reference: list[str],
) -> tuple[int, int, int, int]:
    """Expand a changed block until both supported clean baselines identify it once.

    Short Lua fragments such as ``end`` or repeated table assignments are not safe
    structural anchors.  Expansion is deliberately confined to the owning surface;
    failure to reach a unique block aborts generation instead of guessing.
    """
    left = 0
    right = 0
    while True:
        bounded_old_start = max(0, old_start - left)
        bounded_old_end = min(len(old_surface), old_end + right)
        bounded_new_start = max(0, new_start - left)
        bounded_new_end = min(len(new_surface), new_end + right)
        old_block = old_surface[bounded_old_start:bounded_old_end]
        new_block = new_surface[bounded_new_start:bounded_new_end]
        if (
            occurrences(zibo, old_block) == 1
            and occurrences(levelup, old_block) == 1
            and occurrences(reference, new_block) == 1
            and not occurrences(new_block, old_block)
        ):
            return bounded_old_start, bounded_old_end, bounded_new_start, bounded_new_end
        if bounded_old_start == 0 and bounded_old_end == len(old_surface):
            raise ValueError("Owning surface is not a unique shared structural anchor")
        if bounded_old_start > 0:
            left += 1
        if bounded_old_end < len(old_surface):
            right += 1


def replacements_for_surface(
    spec: Surface,
    zibo: list[str],
    levelup: list[str],
    reference: list[str],
) -> list[dict[str, object]]:
    zibo_surface = surface(zibo, spec)
    levelup_surface = surface(levelup, spec)
    reference_surface = surface(reference, spec)
    replacements = []
    for sequence, (old_start, old_end, new_start, new_end) in enumerate(
        changed_groups(zibo_surface, reference_surface), start=1
    ):
        if spec.include_groups is not None and sequence not in spec.include_groups:
            continue
        candidate_new_block = reference_surface[new_start:new_end]
        if spec.required_new_token is not None and not any(
            spec.required_new_token in line for line in candidate_new_block
        ):
            continue
        try:
            old_start, old_end, new_start, new_end = unique_replacement_bounds(
                zibo_surface,
                reference_surface,
                old_start,
                old_end,
                new_start,
                new_end,
                zibo,
                levelup,
                reference,
            )
        except ValueError as error:
            raise ValueError(f"{spec.family}/{spec.start_function}/{sequence}: {error}") from error
        old_block = zibo_surface[old_start:old_end]
        new_block = reference_surface[new_start:new_end]
        replacements.append({
            "name": f"{spec.family} {spec.start_function} block {sequence}",
            "oldLines": old_block,
            "newLines": new_block,
        })
    return replacements


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zibo-clean", type=Path, required=True)
    parser.add_argument("--levelup-clean", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument("--output", type=Path)
    output_group.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    actual_zibo_hash = sha256(args.zibo_clean)
    actual_levelup_hash = sha256(args.levelup_clean)
    if actual_zibo_hash != ZIBO_40535_SHA256:
        raise ValueError(f"Unsupported Zibo clean source: {actual_zibo_hash}")
    if actual_levelup_hash != LEVELUP_SHARED_40535_SHA256:
        raise ValueError(f"Unsupported LevelUp clean source: {actual_levelup_hash}")

    zibo = lines(args.zibo_clean)
    levelup = lines(args.levelup_clean)
    reference = lines(args.reference)
    replacements_by_family: dict[str, list[dict[str, object]]] = {}
    for spec in REFERENCE_DATA_SURFACES:
        replacements_by_family.setdefault(spec.family, []).extend(
            replacements_for_surface(spec, zibo, levelup, reference)
        )
    replacements = [
        replacement
        for family_replacements in replacements_by_family.values()
        for replacement in family_replacements
    ]
    if not replacements:
        raise ValueError("No intentional-fix differences were found")

    if args.output is not None:
        document = {"format": "exact-text-replacements-v1", "replacements": replacements}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    else:
        output_names = {
            "I01": "i01-gls-lp-record-resolution.json",
            "I08": "i08-app-ref-resolution.json",
        }
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for family, family_replacements in replacements_by_family.items():
            if not family_replacements:
                raise ValueError(f"No intentional-fix differences were found for {family}")
            document = {
                "format": "exact-text-replacements-v1",
                "replacements": family_replacements,
            }
            output_path = args.output_dir / output_names[family]
            output_path.write_text(
                json.dumps(document, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
