#!/usr/bin/env python3
"""Build the deterministic Intentional Fixes release archive."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DIST_ROOT = REPOSITORY_ROOT / "dist"
MANIFEST = json.loads((REPOSITORY_ROOT / "standalone-manifest.json").read_text(encoding="utf-8"))
PACKAGE_PLAN = json.loads((REPOSITORY_ROOT / "package-plan.json").read_text(encoding="utf-8"))
PAYLOADS = tuple(row["path"] for row in PACKAGE_PLAN["families"] if "path" in row)
PACKAGE_FILES = (
    "CHANGELOG.md",
    "DRY_TEST_RESULTS.md",
    "FIX_CATALOG.md",
    "INSTALLATION.md",
    "LICENSE",
    "PATCH_MATRIX.md",
    "README.md",
    f"RELEASE_NOTES_{MANIFEST['packageVersion']}.md",
    "SOURCE.md",
    "package-plan.json",
    "standalone-manifest.json",
    "z_Install.py",
) + PAYLOADS


def main() -> int:
    version = MANIFEST["packageVersion"]
    root_name = f"X-Plane-Zibo-LevelUp-737NG-Intentional-Fixes-v{version}"
    archive = DIST_ROOT / f"{root_name}.zip"
    checksum = archive.with_suffix(archive.suffix + ".sha256")
    DIST_ROOT.mkdir(exist_ok=True)
    timestamp = (2026, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for relative in PACKAGE_FILES:
            source = REPOSITORY_ROOT / relative
            if not source.is_file():
                raise FileNotFoundError(relative)
            info = zipfile.ZipInfo(f"{root_name}/{relative}", timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100755 if relative == "z_Install.py" else 0o100644) << 16
            bundle.writestr(info, source.read_bytes())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(archive)
    print(checksum)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
