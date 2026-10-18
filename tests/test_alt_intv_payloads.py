"""Execute the complete I30 command handler, including its enclosing scopes."""

import importlib.util
import json
import subprocess
import unittest

import test_cruise_fix_payloads as cruise


class AltInterventionPayloadTests(unittest.TestCase):
    lua_result = cruise.CruiseFixPayloadTests.lua_result
    assert_corrected_and_original_red = cruise.CruiseFixPayloadTests.assert_corrected_and_original_red

    @classmethod
    def setUpClass(cls):
        cruise.CruiseFixPayloadTests.setUpClass.__func__(cls)
        spec = importlib.util.spec_from_file_location("i30_installer", cruise.ROOT / "z_Install.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        # Exact published defect, not a synthetic misplaced-end approximation.
        published = json.loads(subprocess.check_output(
            ["git", "show", "fcd9db42f6b1d5301266319a3b801c5802df48e7:src/fixes/i30-alt-intervention-constraint-release.json"],
            cwd=cruise.ROOT, text=True,
        ))
        cls.legacy = installer.apply_exact_replacements(cls.original.encode(), published).decode()

    @staticmethod
    def handler(source):
        name = "B738_autopilot_alt_interv_CMDhandler"
        start = source.index("local function B738_alt_intv_release_next_constraint(")
        end = source.index("\nfunction ", source.index("function " + name + "(") + 1)
        return source[start:end] + "\n"

    PRELUDE = r'''
function B738_calc_vnav_spd() end
function reset_fmc_pages() end
function reset_fmc_pages_fo() end
function add_fmc_msg() end
local function reset(phase)
    B738DR_flight_phase = phase or 1
    B738DR_alt_intv_but = 1; B738DR_autopilot_vnav_status = 1
    B738DR_vnav_alt_mode = 0; B738DR_mcp_alt_dial = 12000
    B738DR_preselected_alt = 12000; simDR_altitude_pilot = 8000
    crz_alt_num = 10000; B738DR_trans_alt_mod = 18000
    B738DR_descent_mode = 0; B738DR_climb_mode = 0; B738DR_cruise_mode = 0
    B738DR_fms_descent_now = 0; elevation_ft = 0
    B738DR_altitude_mode = 0; B738DR_ap_on = 0; B738DR_vnav_altitude_mode = 0
    B738DR_vnav_td_dist = 0; first_desc_rest = 0
    offset = 2; tc_idx = 5; ed_found = 0; first_app_idx = 0
    legs_num = 6; legs_num2 = 6; legs_delete = 0
    fms_recalc = 0; vnav_update = 0
    legs_data = {}; legs_data2 = {}; legs_restr_alt = {}; legs_restr_alt_n = 0
    for i = 1, 6 do
        legs_data[i] = {[5]=0, [6]=0, [41]=0}
        legs_data2[i] = {[5]=0, [6]=0, [41]=0}
    end
end
local function restriction(index, altitude, kind, altitude2)
    legs_restr_alt_n = legs_restr_alt_n + 1
    legs_restr_alt[legs_restr_alt_n] = {"WPT", index, altitude, kind or 0, altitude2 or 0}
    legs_data[index][5] = altitude; legs_data[index][6] = altitude2 or 0
    legs_data[index][41] = kind or 0
    legs_data2[index][5] = altitude; legs_data2[index][6] = altitude2 or 0
    legs_data2[index][41] = kind or 0
end
local function press()
    B738_autopilot_alt_interv_CMDhandler(0, 0)
    assert(B738DR_autopilot_alt_interv_pos == 1, "press position lost")
    B738_autopilot_alt_interv_CMDhandler(2, 0)
    assert(B738DR_autopilot_alt_interv_pos == 0, "release position lost")
end
'''

    def test_full_handler_first_intervention_and_repeat(self):
        cases = r'''
for _, phase in ipairs({1, 8}) do
    reset(phase)
    restriction(2, 9000); restriction(3, 10000)
    press()
    assert(legs_data[2][5] == 0, "first intervention skipped constraint deletion")
    assert(legs_data[3][5] == 10000, "one press deleted multiple constraints")
    assert(legs_data2[2][5] == 0 and crz_alt_num == 12000, "mirror or cruise update lost")
    -- Normal restriction-table refresh between presses, not a repeated stale row.
    legs_restr_alt = {{"NEXT", 3, 10000, 0, 0}}; legs_restr_alt_n = 1
    press()
    assert(legs_data[3][5] == 0 and fms_recalc == 1 and vnav_update == 1,
        "repeat did not release next refreshed constraint")
end
'''
        self.assert_corrected_and_original_red(
            self.handler(self.source) + self.PRELUDE + cases,
            self.handler(self.legacy) + self.PRELUDE + cases,
            "first intervention skipped constraint deletion",
        )

    def test_full_handler_preserves_stock_fallback(self):
        cases = r'''
reset(1); B738DR_autopilot_vnav_status = 0
press()
assert(crz_alt_num == 12000 and B738DR_fmc_cruise_alt == 12000,
    "stock fallback cruise altitude lost")
assert(crz_alt_num2 == 0 and crz_alt_changed == 1, "fallback lifecycle lost")
'''
        self.assert_corrected_and_original_red(
            self.handler(self.source) + self.PRELUDE + cases,
            self.handler(self.legacy) + self.PRELUDE + cases,
            "stock fallback cruise altitude lost",
        )

    def test_full_handler_boundaries_mod_and_descent(self):
        cases = r'''
-- MCP equality is not a conflict; T/C is outside the climb deletion window.
reset(1); crz_alt_num = 12000
restriction(2, 12000); restriction(5, 9000)
press()
assert(legs_data[2][5] == 12000 and legs_data[5][5] == 9000, "climb boundary lost")
-- An explicit same-row pending MOD constraint must survive the ACTIVE release.
reset(1); crz_alt_num = 12000; legs_delete = 1
restriction(2, 9000); legs_data2[2][5] = 9500
press()
assert(legs_data[2][5] == 0 and legs_data2[2][5] == 9500, "edited MOD overwritten")
-- Existing VNAV ALT branch: less than 300 ft lower MCP must still admit descent.
reset(5); crz_alt_num = 35000; B738DR_vnav_alt_mode = 1
B738DR_preselected_alt = 10000; B738DR_mcp_alt_dial = 9900; simDR_altitude_pilot = 10000
restriction(2, 10000); restriction(3, 11000)
press()
assert(B738DR_vnav_alt_mode == 0 and B738DR_fms_descent_now == 2,
    "small lower-MCP descent not released")
assert(legs_data[2][5] == 0 and legs_data[3][5] == 11000, "descent did not release one")
-- First approach leg stays outside an established end-of-descent window.
reset(5); crz_alt_num = 35000; B738DR_autopilot_vnav_status = 0
B738DR_mcp_alt_dial = 5000; B738DR_preselected_alt = 10000
ed_found = 6; first_app_idx = 3; restriction(3, 7000)
press()
assert(legs_data[3][5] == 7000, "approach boundary deleted")
-- Disabled option must preserve constraints and cruise altitude.
reset(1); B738DR_alt_intv_but = 0; restriction(2, 9000)
press()
assert(legs_data[2][5] == 9000 and crz_alt_num == 10000, "disabled option changed state")
'''
        result = self.lua_result(self.handler(self.source) + self.PRELUDE + cases)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
