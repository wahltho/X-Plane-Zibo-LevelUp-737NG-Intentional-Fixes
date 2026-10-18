"""Focused source-component cases; not a simulator or complete MTK replay.

Run only after explicit dry-test approval. Handlers are extracted whole from
the composed Lua. Restriction and fuel cases run the existing bounded producer
or renderer branch, not a Python reimplementation of the corrected arithmetic.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE = Path(
    "/Users/wahltho/dev/Zibo Mod/Original/Zibo Mod Original/"
    "B738X_XP12_4_05_35/plugins/xlua/scripts/B738.a_fms/B738.a_fms.lua"
)


def function_text(source: str, name: str) -> str:
    start = source.index(f"function {name}(")
    end = source.index("\nfunction ", start + 1)
    return source[start:end]


class CruiseFixPayloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lua = shutil.which("luajit") or shutil.which("lua")
        if cls.lua is None:
            raise unittest.SkipTest("A Lua interpreter is required")
        path = Path(os.environ.get("ZIBO_40535_LUA", BASELINE))
        if not path.is_file():
            raise unittest.SkipTest("Original .35 Lua is unavailable")
        # The established installer imports its sibling ownership helper.
        import sys

        sys.path.insert(0, str(ROOT))
        spec = importlib.util.spec_from_file_location("intentional_clean_installer", ROOT / "z_Install.py")
        assert spec is not None and spec.loader is not None
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        manifest = json.loads((ROOT / "standalone-manifest.json").read_text())
        original = path.read_bytes()
        if installer.sha256_bytes(original) != manifest["target"]["sourceSha256"]:
            raise unittest.SkipTest("Verified original .35 Lua is required")
        cls.original = original.decode("utf-8-sig").replace("\r\n", "\n")
        composed = installer.compose(original, manifest)
        # Optional output from the released MTK handler matrix, never an aircraft.
        fixture = os.environ.get("INTENTIONAL_COMPOSED_LUA")
        cls.source = (Path(fixture).read_bytes() if fixture else composed).decode("utf-8-sig").replace("\r\n", "\n")

    def lua_result(self, code: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([self.lua, "-"], input=code, text=True, capture_output=True)

    def assert_corrected_and_original_red(self, corrected: str, original: str, witness: str) -> None:
        result = self.lua_result(corrected)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        control = self.lua_result(original)
        self.assertNotEqual(0, control.returncode, "Original unexpectedly satisfies the same oracle")
        self.assertIn(witness, control.stderr, control.stdout + control.stderr)

    def test_cruise_selector_passed_current_future_and_short_lead(self) -> None:
        def selection(source: str) -> str:
            surface = function_text(source, "B738_restrict_data")
            begin = "\t\t\telseif B738DR_flight_phase >= 2 and B738DR_flight_phase <= 4 then\t-- cruise before T/D"
            end = "\t\t\telseif B738DR_flight_phase > 4 and B738DR_flight_phase < 8 then\t\t-- descent"
            branch = surface[surface.index(begin):surface.index(end)]
            return "function select_cruise()\nlocal td_idx_temp = 0\nlocal first_ma_idx = 0\n" + branch.replace("elseif", "if", 1) + "end\nend\n"

        cases = r'''
local function reset(phase, active, idx, leg_distance, remaining)
    B738DR_flight_phase = phase
    offset = active; tc_idx = 0; last_sid_idx = 1
    td_idx = 8; first_star_idx = 0; first_app_idx = 0
    rnav_idx_last = 0; legs_num = 8
    B738DR_fmc_cruise_speed = 300; B738DR_fmc_dist = remaining
    B738DR_rest_wpt_spd = 0; B738DR_rest_wpt_spd_idx = 0
    B738DR_rest_wpt_spd_tgt = 0; B738DR_rest_wpt_spd_id = ""
    legs_restr_spd = {{"RESTRICT", idx, 210, 1}}; legs_restr_spd_n = 1
    legs_data = {}
    for i = 1, 9 do legs_data[i] = {[3]=10, [4]=0, [19]=0} end
    legs_data[idx][3] = leg_distance
end
for phase = 2, 4 do
    reset(phase, 5, 3, 10, 1)
    select_cruise()
    assert(B738DR_rest_wpt_spd_idx == 0, "passed restriction revived")
    reset(phase, 5, 5, 10, 1)
    select_cruise()
    assert(B738DR_rest_wpt_spd_idx == 5, "current restriction lost")
    reset(phase, 5, 5, 10, 8)
    select_cruise()
    assert(B738DR_rest_wpt_spd_idx == 0, "current restriction applied too early")
    reset(phase, 5, 7, 10, 1)
    select_cruise()
    assert(B738DR_rest_wpt_spd_idx == 0, "future long-leg restriction applied too early")
    reset(phase, 6, 7, 0.1, 1)
    select_cruise()
    assert(B738DR_rest_wpt_spd_idx == 7, "valid short-leg deceleration lost")
    reset(phase, 7, 7, 0.1, 1)
    select_cruise()
    assert(B738DR_rest_wpt_spd_idx == 7, "lead behind active row incorrectly excludes current endpoint")
    reset(phase, 5, 3, 10, 1)
    legs_restr_spd = {{"FUTURE", 6, 220, 1}, {"PASSED", 3, 210, 1}}
    legs_restr_spd_n = 2
    legs_data[6][3] = 0.1
    select_cruise()
    assert(B738DR_rest_wpt_spd_idx == 6, "passed candidate prevented continuing reverse search")
    reset(phase, 2, 3, 0.1, 1)
    select_cruise()
    assert(B738DR_rest_wpt_spd_idx == 3, "restriction remained blacklisted after active-index change")
end
'''
        self.assert_corrected_and_original_red(
            selection(self.source) + cases, selection(self.original) + cases, "passed restriction revived"
        )

    def test_both_complete_lsk2_handlers_mcp_lock_and_pending_edit(self) -> None:
        for fmc in (1, 2):
            with self.subTest(fmc=fmc):
                name = f"B738_fmc{fmc}_2L_CMDhandler"
                entry = "entry" if fmc == 1 else "entry2"
                page = "page_cruise" if fmc == 1 else "page_cruise2"
                lag = f"fmc{fmc}_input_lag"
                cases = f'''
INVALID_INPUT = 100; INVALID_DELETE = 200
function cpdlc_patch_lsk() return false end -- Test only: CPDLC yields the key.
local messages = {{}}
function add_fmc_msg(code, priority, side) messages[#messages + 1] = {{code, side}} end
local function reset(text)
    {page} = 1; {lag} = 1; {entry} = text
    perf_exec = 2; B738DR_flight_phase = 2
    crz_exec = 0; crz_spd_exec = 0; B738DR_ap_spd_interv_status = 1
    fmc_cruise_speed_mod = 190; fmc_cruise_speed_mach_mod = 0.71
    fmc_cruise_mode_mod = 1; messages = {{}}
end
for _, text in ipairs({{"280", ".780", ">DELETE"}}) do
    reset(text)
    {name}(0, 0)
    assert(crz_spd_exec == 0 and fmc_cruise_speed_mod == 190 and
        fmc_cruise_speed_mach_mod == 0.71 and fmc_cruise_mode_mod == 1,
        "edited MCP target")
    local expected = text == ">DELETE" and INVALID_DELETE or INVALID_INPUT
    assert(#messages == 1 and messages[1][1] == expected and messages[1][2] == {fmc - 1}, "wrong FMC error")
    assert({entry} == text and {lag} == 0, "scratchpad or input lifecycle changed")
    {name}(2, 0)
    assert(B738DR_fms_key == 0, "key release lost")
end
for _, control in ipairs({{"managed", "pending", "precruise", "goaround", "uninitialized"}}) do
    reset("280")
    if control == "managed" then B738DR_ap_spd_interv_status = 0 end
    if control == "pending" then crz_spd_exec = 1 end
    if control == "precruise" then B738DR_flight_phase = 1 end
    if control == "goaround" then B738DR_flight_phase = 8 end
    if control == "uninitialized" then perf_exec = 0 end
    {name}(0, 0)
    assert(crz_spd_exec == 1 and fmc_cruise_speed_mod == 280 and #messages == 0,
        "non-MCP or pending target was locked")
end
reset("")
{name}(0, 0)
assert(crz_spd_exec == 0 and #messages == 1 and messages[1][1] == INVALID_INPUT,
    "stock empty-entry behavior changed")
'''
                self.assert_corrected_and_original_red(
                    function_text(self.source, name) + cases,
                    function_text(self.original, name) + cases,
                    "edited MCP target",
                )

    def test_actual_step_renderer_sign_and_both_units(self) -> None:
        def renderer(source: str) -> str:
            surface = function_text(source, "B738_fmc_cruise")
            start = surface.index('line4_l = " W/STEP  "')
            end = surface.index("\n\t\t\t\t\t\t\telse", start)
            constant = re.search(r"^KGS_LBS = [0-9.]+", source, re.MULTILINE)
            assert constant is not None
            return constant.group() + "\nfunction render_step()\n" + surface[start:end] + "\nend\n"

        cases = r'''
legs_data = {{[40]=10000}}; prev_idx = 1
local expected = {
    [0] = {[2000]=" W/STEP  17.6", [0]=" W/STEP  22.0", [-2000]=" W/STEP  26.5"},
    [1] = {[2000]=" W/STEP   8.0", [0]=" W/STEP  10.0", [-2000]=" W/STEP  12.0"}
}
for unit = 0, 1 do
    for _, delta in ipairs({2000, 0, -2000}) do
        units = unit; sc_fuel_delta = delta
        render_step()
        assert(line4_l == expected[unit][delta], "wrong step arrival fuel: " .. line4_l)
    end
end
'''
        self.assert_corrected_and_original_red(
            renderer(self.source) + cases, renderer(self.original) + cases, "wrong step arrival fuel"
        )


if __name__ == "__main__":
    unittest.main()
