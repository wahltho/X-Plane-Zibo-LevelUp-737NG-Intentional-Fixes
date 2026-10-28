"""Full FMS chunk/lifecycle with real XLua glue and bounded native bindings.

Not a simulator test. X-Plane datarefs, commands and timers are supplied by the
fixture; navigation files are absent and aircraft writes are prohibited.
INTENTIONAL_STARTUP_FIXTURES may name additional composed FMS scripts (pathsep).
INTENTIONAL_STARTUP_HELPERS contains the released companion Lua modules.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=Path(os.environ.get('ZIBO_40535_LUA',
    '/Users/wahltho/dev/Zibo Mod/Original/Zibo Mod Original/B738X_XP12_4_05_35/plugins/xlua/scripts/B738.a_fms/B738.a_fms.lua'))


class LoadStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lua=os.environ.get('LUAJIT') or shutil.which('luajit')
        cls.init=Path(os.environ.get('XLUA_STARTUP_INIT', ORIGINAL.parents[2]/'init.lua'))
        if not cls.lua or not ORIGINAL.is_file() or not cls.init.is_file():
            raise unittest.SkipTest('LuaJIT and original .35 FMS/init.lua required')
        import sys
        sys.path.insert(0,str(ROOT))
        import z_Install
        cls.temporary=tempfile.TemporaryDirectory(prefix='ifix-startup-')
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.folder=Path(cls.temporary.name)
        cls.standalone=cls.folder/'standalone.lua'
        manifest=json.loads((ROOT/'standalone-manifest.json').read_text())
        cls.standalone.write_bytes(z_Install.compose(ORIGINAL.read_bytes(),manifest))

    def probe(self,fixture,mode,api='xlua-lookup'):
        run=subprocess.run([self.lua,str(ROOT/'tests/fixtures/xlua_load_startup.lua'),
            str(self.init),str(fixture),mode,os.environ.get('INTENTIONAL_STARTUP_HELPERS',''),api],
            cwd=self.folder,capture_output=True,text=True,timeout=30)
        self.assertEqual(0,run.returncode,run.stdout+run.stderr)
        self.assertIn('frames=6 status=44',run.stdout)

    def test_standalone_command_availability(self):
        for api in ('xlua-lookup','xplm-lookup'):
            for mode in ('present','flight-start','late','never'):
                with self.subTest(api=api,mode=mode): self.probe(self.standalone,mode,api)

    def test_early_registration_negative_control(self):
        # Restore just the released early-registration defect. The candidate
        # must fail in the same harness which accepts the corrected lifecycle.
        helper=(ROOT/'src/ground_lnav.lua').read_text()
        ensure=helper[helper.index('function B738_ifix_vi.ensure_lnav_wrapper()'):].rstrip()
        early='''wrap_command("laminar/B738/autopilot/lnav_press",
    function(phase, duration) if phase == 0 then lnav_prior() end end,
    function(phase, duration) end)'''
        source=self.standalone.read_text()
        self.assertEqual(1,source.count(ensure))
        fixture=self.folder/'early-negative.lua'
        fixture.write_text(source.replace(ensure,early))
        run=subprocess.run([self.lua,str(ROOT/'tests/fixtures/xlua_load_startup.lua'),
            str(self.init),str(fixture),'never','','xlua-lookup','expect-early-failure'],
            cwd=self.folder,capture_output=True,text=True,timeout=30)
        self.assertEqual(0,run.returncode,run.stdout+run.stderr)
        self.assertIn('early wrapper aborts FMS load',run.stdout)

    def test_composed_products_command_availability(self):
        fixtures=os.environ.get('INTENTIONAL_STARTUP_FIXTURES','')
        if not fixtures: self.skipTest('Set INTENTIONAL_STARTUP_FIXTURES for composed Zibo/LevelUp scripts')
        for name in fixtures.split(os.pathsep):
            for api in ('xlua-lookup','xplm-lookup'):
                for mode in ('present','flight-start','late','never'):
                    with self.subTest(fixture=name,api=api,mode=mode): self.probe(Path(name),mode,api)
