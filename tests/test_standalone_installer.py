from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = PACKAGE_ROOT / "z_Install.py"
DEFAULT_BASELINE = Path(
    "/Users/wahltho/dev/Zibo Mod/Original/Zibo Mod Original/"
    "B738X_XP12_4_05_35/plugins/xlua/scripts/B738.a_fms/B738.a_fms.lua"
)
SOURCE_HASH = "ff313b0e88c62845ad1c4a2b1f4bd599f57d8799e8d6707bfc10a3369fd63a8e"
RESULT_HASH = "49a6ab1f077bca893123f476873ec5e7c9af1d18e31570996a697403ae2c3f70"
RELATIVE_TARGET = Path("plugins/xlua/scripts/B738.a_fms/B738.a_fms.lua")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class StandaloneInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = Path(os.environ.get("ZIBO_40535_LUA", DEFAULT_BASELINE))
        if not cls.baseline.is_file() or digest(cls.baseline) != SOURCE_HASH:
            raise unittest.SkipTest("Verified original Zibo 4.05.35 Lua is unavailable")

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="intentional-fixes-test-")
        self.aircraft = Path(self.temporary.name) / "aircraft"
        self.target = self.aircraft / RELATIVE_TARGET
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(self.baseline.read_bytes())

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_installer(self, action: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            [sys.executable, str(INSTALLER), action, "--aircraft-root", str(self.aircraft)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(completed.returncode, expected, completed.stdout + completed.stderr)
        return completed

    def test_check_install_verify_repeat_and_uninstall(self) -> None:
        original = self.target.read_bytes()
        self.run_installer("check")
        self.assertEqual(self.target.read_bytes(), original)
        self.run_installer("install")
        self.assertEqual(digest(self.target), RESULT_HASH)
        luac = shutil.which("luac")
        if luac is not None:
            subprocess.run([luac, "-p", str(self.target)], check=True)
        state = self.aircraft / ".zibo-intentional-fixes-clean35/state.json"
        state_before = state.read_bytes()
        installed_before = self.target.read_bytes()
        self.run_installer("install")
        self.assertEqual(state.read_bytes(), state_before)
        self.assertEqual(self.target.read_bytes(), installed_before)
        self.run_installer("verify")
        self.run_installer("uninstall")
        self.assertEqual(self.target.read_bytes(), original)
        self.assertFalse(state.parent.exists())

    def test_modified_clean_source_is_rejected_without_state(self) -> None:
        self.target.write_bytes(self.target.read_bytes() + b"\n-- foreign edit\n")
        result = self.run_installer("install", expected=1)
        self.assertIn("requires the untouched original", result.stderr)
        self.assertFalse((self.aircraft / ".zibo-intentional-fixes-clean35").exists())

    def test_modified_install_is_not_uninstalled_over(self) -> None:
        self.run_installer("install")
        self.target.write_bytes(self.target.read_bytes() + b"\n-- foreign edit\n")
        result = self.run_installer("uninstall", expected=1)
        self.assertIn("Installed Lua was changed", result.stderr)
        self.assertTrue((self.aircraft / ".zibo-intentional-fixes-clean35/state.json").is_file())


if __name__ == "__main__":
    unittest.main()
