from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "tools/build_mtk_package.py"
TARGET = "plugins/xlua/scripts/B738.a_fms/B738.a_fms.lua"


class MtkPackageTests(unittest.TestCase):
    def test_schema5_contract_and_payloads(self) -> None:
        manifest = json.loads((ROOT / "package-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(5, manifest["schemaVersion"])
        self.assertEqual("0.1.1", manifest["packageVersion"])
        self.assertEqual(["zibo-737ng", "levelup-737ng"], manifest["supportedProducts"])
        self.assertEqual(
            ["intentional-fixes-zibo", "intentional-fixes-levelup"],
            [module["moduleId"] for module in manifest["modules"]],
        )
        for module, expected_count in zip(manifest["modules"], (14, 15), strict=True):
            self.assertEqual("optional", module["policy"])
            self.assertFalse(module["defaultEnabled"])
            self.assertEqual(expected_count, len(module["targets"]))
            self.assertEqual(expected_count, len(module["payloads"]))
            self.assertEqual({TARGET}, {target["relativePath"] for target in module["targets"]})
            self.assertEqual(
                ["cpdlc"],
                next(target["whenModulesSelected"] for target in module["targets"]
                     if target["payload"].startswith("i06-")),
            )
            for payload in module["payloads"]:
                data = (ROOT / "src/fixes" / payload["path"]).read_bytes()
                self.assertEqual(len(data), payload["size"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), payload["sha256"])
        zibo, levelup = manifest["modules"]
        self.assertFalse(any(target["payload"].startswith("i33-") for target in zibo["targets"]))
        self.assertEqual(
            ["weight-and-balance"],
            next(target["whenModulesSelected"] for target in levelup["targets"]
                 if target["payload"].startswith("i33-")),
        )

    def test_archive_is_deterministic_and_complete(self) -> None:
        with tempfile.TemporaryDirectory(prefix="intentional-mtk-package-") as folder:
            archive = Path(folder) / "X-Plane-Zibo-LevelUp-737NG-Intentional-Fixes-MTK-v0.1.1.zip"
            command = [sys.executable, str(BUILDER), "--check", "--archive", str(archive)]
            subprocess.run(command, cwd=ROOT, check=True, capture_output=True)
            first = archive.read_bytes()
            subprocess.run(command, cwd=ROOT, check=True, capture_output=True)
            self.assertEqual(first, archive.read_bytes())
            with zipfile.ZipFile(archive) as package:
                manifest = json.loads(package.read("package-manifest.json"))
                for module in manifest["modules"]:
                    for payload in module["payloads"]:
                        name = f"modules/{module['moduleId']}/{payload['path']}"
                        self.assertEqual(
                            payload["sha256"], hashlib.sha256(package.read(name)).hexdigest()
                        )
                self.assertEqual(30, len(package.namelist()))


if __name__ == "__main__":
    unittest.main()
