#!/usr/bin/env python3
"""Generate the MTK schema-5 contract and its deterministic release archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.1"
PACKAGE_ID = "wahltho.zibo-40535.intentional-fixes"
REPOSITORY_URL = "https://github.com/wahltho/X-Plane-Zibo-LevelUp-737NG-Intentional-Fixes"
TARGET = "plugins/xlua/scripts/B738.a_fms/B738.a_fms.lua"
MODULES = (
    ("intentional-fixes-zibo", False, 70),
    ("intentional-fixes-levelup", True, 71),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def package_files() -> dict[str, bytes]:
    plan = json.loads((ROOT / "package-plan.json").read_text(encoding="utf-8"))
    files: dict[str, bytes] = {}
    modules = []
    for module_id, include_weight_balance, order in MODULES:
        payloads = []
        targets = []
        for family in plan["families"]:
            if "path" not in family or (family["ids"] == ["I33"] and not include_weight_balance):
                continue
            source = ROOT / family["path"]
            data = source.read_bytes()
            payload_name = source.name
            files[f"modules/{module_id}/{payload_name}"] = data
            payloads.append({"path": payload_name, "size": len(data), "sha256": sha256(data)})
            target = {
                "operation": "exact-text-replacements-v1",
                "payload": payload_name,
                "relativePath": TARGET,
                "sourceSha256": [],
            }
            if family["ids"] == ["I06"]:
                target["whenModulesSelected"] = ["cpdlc"]
            elif family["ids"] == ["I33"]:
                target["whenModulesSelected"] = ["weight-and-balance"]
            targets.append(target)
        modules.append({
            "moduleId": module_id,
            "displayName": "Intentional Fixes",
            "description": (
                "Optional unofficial corrections to existing FMS behavior. "
                "CPDLC and Weight & Balance corrections apply only when those patches are selected."
            ),
            "policy": "optional",
            "defaultEnabled": False,
            "installationOrder": order,
            "requires": [],
            "conflictsWith": [],
            "payloads": payloads,
            "targets": targets,
        })
    files["package-manifest.json"] = json_bytes({
        "schemaVersion": 5,
        "packageType": "compatibilityPackage",
        "packageId": PACKAGE_ID,
        "packageVersion": VERSION,
        "repositoryUrl": REPOSITORY_URL,
        "aircraftFamily": "Zibo Mod / LevelUp 737NG for X-Plane 12",
        "supportedProducts": ["zibo-737ng", "levelup-737ng"],
        "restartRequired": True,
        "supportedUpstreamReleases": [],
        "modules": modules,
    })
    return files


def build_archive(destination: Path, files: dict[str, bytes]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in sorted(files):
            info = zipfile.ZipInfo(relative, date_time=(2026, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, files[relative], compresslevel=9)
    checksum = sha256(destination.read_bytes())
    destination.with_suffix(destination.suffix + ".sha256").write_text(
        f"{checksum}  {destination.name}\n", encoding="utf-8"
    )
    print(f"Wrote {destination} (sha256={checksum})")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="update the tracked MTK manifest")
    parser.add_argument("--check", action="store_true", help="verify the tracked MTK manifest")
    parser.add_argument("--archive", type=Path, help="build a deterministic MTK-only release archive")
    args = parser.parse_args()
    if not (args.write or args.check or args.archive):
        parser.error("select --write, --check or --archive")
    files = package_files()
    manifest_path = ROOT / "package-manifest.json"
    if args.write:
        manifest_path.write_bytes(files["package-manifest.json"])
        print(f"Wrote {manifest_path}")
    if args.check or args.archive:
        if not manifest_path.is_file() or manifest_path.read_bytes() != files["package-manifest.json"]:
            print("STALE: package-manifest.json", file=sys.stderr)
            return 1
        print("PASS: MTK package manifest matches patch sources")
    if args.archive:
        build_archive(args.archive.expanduser().resolve(), files)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
