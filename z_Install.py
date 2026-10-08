#!/usr/bin/env python3
"""Install the fix-only package on an untouched original Zibo 4.05.35 Lua."""

from __future__ import annotations

from standalone_guard import native_operation, owned_write, owned_replace, owned_unlink, owned_copy, owned_rmtree, owned_mkdir

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = PACKAGE_ROOT / "standalone-manifest.json"
STATE_DIRECTORY = ".zibo-intentional-fixes-clean35"
STATE_FILENAME = "state.json"


class InstallerError(RuntimeError):
    """Raised when a standalone-install precondition is not satisfied."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise InstallerError(f"Expected a JSON object in {path}")
    return value


def safe_relative_path(value: str) -> Path:
    posix = PurePosixPath(value)
    if posix.is_absolute() or not posix.parts or ".." in posix.parts:
        raise InstallerError(f"Unsafe relative path: {value!r}")
    return Path(*posix.parts)


def load_manifest() -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH)
    if manifest.get("schemaVersion") != 1:
        raise InstallerError("Unsupported standalone manifest schema")
    if manifest.get("packageId") != "wahltho.zibo-40535.intentional-fixes.clean-only":
        raise InstallerError("Unexpected package identity")
    target = manifest.get("target")
    if not isinstance(target, dict):
        raise InstallerError("Manifest target is missing")
    safe_relative_path(target["relativePath"])
    for field in ("sourceSha256", "resultSha256"):
        if not isinstance(target.get(field), str) or len(target[field]) != 64:
            raise InstallerError(f"Invalid target {field}")
    payloads = manifest.get("payloads")
    if not isinstance(payloads, list) or len(payloads) != 13:
        raise InstallerError("Standalone manifest must contain exactly 13 clean-only payloads")
    return manifest


def validate_payloads(manifest: dict[str, Any]) -> None:
    seen: set[str] = set()
    for item in manifest["payloads"]:
        relative = item["path"]
        if relative in seen:
            raise InstallerError(f"Duplicate payload: {relative}")
        seen.add(relative)
        path = PACKAGE_ROOT / safe_relative_path(relative)
        if not path.is_file():
            raise InstallerError(f"Missing payload: {relative}")
        if path.stat().st_size != item["size"] or sha256_path(path) != item["sha256"]:
            raise InstallerError(f"Payload integrity check failed: {relative}")
        spec = load_json(path)
        if spec.get("format") != "exact-text-replacements-v1" or spec.get("condition") is not None:
            raise InstallerError(f"Standalone payload is conditional or unsupported: {relative}")


def split_text_bytes(data: bytes) -> tuple[list[str], str, bool]:
    crlf_count = data.count(b"\r\n")
    lf_only_count = data.count(b"\n") - crlf_count
    eol = "\r\n" if crlf_count > lf_only_count else "\n"
    has_final_eol = data.endswith((b"\n", b"\r"))
    text = data.decode("utf-8", errors="strict")
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if has_final_eol and lines and lines[-1] == "":
        lines.pop()
    return lines, eol, has_final_eol


def join_text_bytes(lines: list[str], eol: str, has_final_eol: bool) -> bytes:
    text = eol.join(lines)
    if has_final_eol:
        text += eol
    return text.encode("utf-8")


def find_sequence(lines: list[str], sequence: list[str]) -> list[int]:
    if not sequence:
        raise InstallerError("Empty replacement sequence")
    width = len(sequence)
    return [index for index in range(len(lines) - width + 1) if lines[index:index + width] == sequence]


def matches_inside(inner: list[int], inner_width: int, outer_start: int, outer_width: int) -> bool:
    outer_end = outer_start + outer_width
    return all(outer_start <= start and start + inner_width <= outer_end for start in inner)


def apply_exact_replacements(data: bytes, spec: dict[str, Any]) -> bytes:
    if spec.get("format") != "exact-text-replacements-v1":
        raise InstallerError("Unsupported payload format")
    replacements = spec.get("replacements")
    if not isinstance(replacements, list) or not replacements:
        raise InstallerError("Payload contains no replacements")
    lines, eol, final_eol = split_text_bytes(data)
    for replacement in replacements:
        old = replacement["oldLines"]
        new = replacement["newLines"]
        old_matches = find_sequence(lines, old)
        new_matches = find_sequence(lines, new)
        name = replacement.get("name", "unnamed replacement")
        if len(new_matches) == 1 and matches_inside(old_matches, len(old), new_matches[0], len(new)):
            continue
        if len(old_matches) == 1 and not new_matches:
            start = old_matches[0]
            lines[start:start + len(old)] = new
            continue
        raise InstallerError(
            f"{name}: expected one clean block or one installed block; "
            f"found clean={len(old_matches)}, installed={len(new_matches)}"
        )
    return join_text_bytes(lines, eol, final_eol)


def compose(source: bytes, manifest: dict[str, Any]) -> bytes:
    result = source
    for item in manifest["payloads"]:
        result = apply_exact_replacements(
            result, load_json(PACKAGE_ROOT / safe_relative_path(item["path"]))
        )
    expected = manifest["target"]["resultSha256"]
    actual = sha256_bytes(result)
    if actual != expected:
        raise InstallerError(f"Generated result hash mismatch: {actual} != {expected}")
    return result


def state_path(aircraft_root: Path) -> Path:
    return aircraft_root / STATE_DIRECTORY / STATE_FILENAME


def load_state(aircraft_root: Path) -> dict[str, Any] | None:
    path = state_path(aircraft_root)
    return load_json(path) if path.exists() else None


def target_path(aircraft_root: Path, manifest: dict[str, Any]) -> Path:
    return aircraft_root / safe_relative_path(manifest["target"]["relativePath"])


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    owned_mkdir(path.parent, parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    owned_write(temporary, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    owned_replace(temporary, path)


def require_clean_source(path: Path, manifest: dict[str, Any]) -> bytes:
    if not path.is_file():
        raise InstallerError(f"Required aircraft file is missing: {manifest['target']['relativePath']}")
    source = path.read_bytes()
    actual = sha256_bytes(source)
    expected = manifest["target"]["sourceSha256"]
    if actual != expected:
        raise InstallerError(
            "Standalone installation requires the untouched original shared Zibo 4.05.35 Lua.\n"
            f"  actual:   {actual}\n"
            f"  expected: {expected}\n"
            "Use the Maintenance Toolkit for aircraft with other Lua patches."
        )
    return source


def verify_installed(aircraft_root: Path, manifest: dict[str, Any], state: dict[str, Any]) -> None:
    if state.get("packageId") != manifest["packageId"]:
        raise InstallerError("Installed state belongs to another package")
    if state.get("packageVersion") != manifest["packageVersion"]:
        raise InstallerError("Installed standalone version differs from this package")
    path = target_path(aircraft_root, manifest)
    if not path.is_file() or sha256_path(path) != manifest["target"]["resultSha256"]:
        raise InstallerError("Installed Lua was changed or the installation is incomplete")


@native_operation
def command_check(aircraft_root: Path, manifest: dict[str, Any]) -> int:
    validate_payloads(manifest)
    state = load_state(aircraft_root)
    if state is not None:
        verify_installed(aircraft_root, manifest, state)
        print(f"Installed and verified: {manifest['displayName']} {manifest['packageVersion']}")
        return 0
    source = require_clean_source(target_path(aircraft_root, manifest), manifest)
    compose(source, manifest)
    print(f"Ready to install: {manifest['displayName']} {manifest['packageVersion']}")
    print("Detected untouched shared Zibo/LevelUp 4.05.35 Lua; no files were changed.")
    return 0


@native_operation
def command_install(aircraft_root: Path, manifest: dict[str, Any]) -> int:
    validate_payloads(manifest)
    existing_state = load_state(aircraft_root)
    if existing_state is not None:
        verify_installed(aircraft_root, manifest, existing_state)
        print(f"Already installed and verified: {manifest['displayName']} {manifest['packageVersion']}")
        return 0
    destination = target_path(aircraft_root, manifest)
    source = require_clean_source(destination, manifest)
    result = compose(source, manifest)
    state_root = aircraft_root / STATE_DIRECTORY
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = state_root / "backups" / timestamp / safe_relative_path(manifest["target"]["relativePath"])
    owned_mkdir(backup.parent, parents=True, exist_ok=False)
    owned_copy(destination, backup)
    state = {
        "schemaVersion": 1,
        "packageId": manifest["packageId"],
        "packageVersion": manifest["packageVersion"],
        "installedAtUtc": datetime.now(timezone.utc).isoformat(),
        "manifestSha256": sha256_path(MANIFEST_PATH),
        "targetRelativePath": manifest["target"]["relativePath"],
        "originalSha256": manifest["target"]["sourceSha256"],
        "installedSha256": manifest["target"]["resultSha256"],
        "backupRelativePath": backup.relative_to(aircraft_root).as_posix(),
    }
    try:
        with tempfile.TemporaryDirectory(prefix="intentional-fixes-stage-", dir=state_root) as name:
            staged = Path(name) / destination.name
            owned_write(staged, result)
            os.chmod(staged, stat.S_IMODE(destination.stat().st_mode))
            owned_replace(staged, destination)
        write_json_atomic(state_path(aircraft_root), state)
    except Exception:
        if backup.exists():
            owned_copy(backup, destination)
        raise
    print(f"Installed {manifest['displayName']} {manifest['packageVersion']}.")
    print(f"Backup: {backup}")
    print("Restart X-Plane before testing the aircraft.")
    return 0


@native_operation
def command_verify(aircraft_root: Path, manifest: dict[str, Any]) -> int:
    validate_payloads(manifest)
    state = load_state(aircraft_root)
    if state is None:
        raise InstallerError("The standalone Intentional Fixes package is not installed")
    verify_installed(aircraft_root, manifest, state)
    print(f"Verified {manifest['displayName']} {manifest['packageVersion']}.")
    return 0


@native_operation
def command_uninstall(aircraft_root: Path, manifest: dict[str, Any]) -> int:
    validate_payloads(manifest)
    state = load_state(aircraft_root)
    if state is None:
        raise InstallerError("The standalone Intentional Fixes package is not installed")
    verify_installed(aircraft_root, manifest, state)
    backup = aircraft_root / safe_relative_path(state["backupRelativePath"])
    if not backup.is_file() or sha256_path(backup) != manifest["target"]["sourceSha256"]:
        raise InstallerError("The original clean backup is missing or changed")
    destination = target_path(aircraft_root, manifest)
    state_root = aircraft_root / STATE_DIRECTORY
    with tempfile.TemporaryDirectory(prefix="intentional-fixes-restore-", dir=state_root) as name:
        staged = Path(name) / destination.name
        owned_copy(backup, staged)
        os.chmod(staged, stat.S_IMODE(destination.stat().st_mode))
        owned_replace(staged, destination)
    if sha256_path(destination) != manifest["target"]["sourceSha256"]:
        raise InstallerError("Restored Lua hash does not match the clean .35 original")
    owned_rmtree(state_root)
    print(f"Uninstalled {manifest['displayName']} and restored the exact clean .35 Lua.")
    return 0


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "install", "verify", "uninstall"))
    parser.add_argument("--aircraft-root", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    aircraft_root = arguments.aircraft_root.expanduser().resolve()
    if not aircraft_root.is_dir():
        raise InstallerError(f"Aircraft root is not a directory: {aircraft_root}")
    manifest = load_manifest()
    actions = {
        "check": command_check,
        "install": command_install,
        "verify": command_verify,
        "uninstall": command_uninstall,
    }
    return actions[arguments.action](aircraft_root, manifest)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (InstallerError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
