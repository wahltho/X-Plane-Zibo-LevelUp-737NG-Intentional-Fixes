#!/usr/bin/env python3
"""Assemble the remaining fix-only structural payloads.

This authoring tool reads the two verified clean baselines plus the preserved
last-active Lua and a pre-diagnostics historical Lua snapshot.  It emits only
bounded exact-text replacements; it never emits a complete upstream Lua file.
"""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").split("\n")


def block(text: str) -> list[str]:
    return text.strip("\n").split("\n")


def occurrences(source: list[str], candidate: list[str]) -> int:
    return ("\0".join(source) + "\0").count("\0".join(candidate) + "\0")


def function_surface(source: list[str], name: str) -> list[str]:
    prefix = f"function {name}("
    start = next(i for i, line in enumerate(source) if line.startswith(prefix))
    end = next(i for i in range(start + 1, len(source)) if source[i].startswith("function "))
    return source[start:end + 1]


def changed_groups(old: list[str], new: list[str], context: int = 3) -> list[tuple[int, int, int, int]]:
    changes = [op for op in difflib.SequenceMatcher(a=old, b=new, autojunk=False).get_opcodes() if op[0] != "equal"]
    groups: list[list[tuple[str, int, int, int, int]]] = []
    for change in changes:
        if not groups or change[1] - groups[-1][-1][2] > context * 2 or change[3] - groups[-1][-1][4] > context * 2:
            groups.append([change])
        else:
            groups[-1].append(change)
    return [
        (max(0, group[0][1] - context), min(len(old), group[-1][2] + context),
         max(0, group[0][3] - context), min(len(new), group[-1][4] + context))
        for group in groups
    ]


def unique_bounds(
    old_surface: list[str], new_surface: list[str], bounds: tuple[int, int, int, int],
    zibo: list[str], levelup: list[str], reference: list[str],
) -> tuple[int, int, int, int]:
    old_start, old_end, new_start, new_end = bounds
    left = right = 0
    while True:
        os = max(0, old_start - left)
        oe = min(len(old_surface), old_end + right)
        ns = max(0, new_start - left)
        ne = min(len(new_surface), new_end + right)
        old_block = old_surface[os:oe]
        new_block = new_surface[ns:ne]
        if (occurrences(zibo, old_block) == 1 and occurrences(levelup, old_block) == 1
                and occurrences(reference, new_block) == 1 and occurrences(new_block, old_block) == 0):
            return os, oe, ns, ne
        if os == 0 and oe == len(old_surface):
            raise ValueError("Could not derive a unique shared structural block")
        if os > 0:
            left += 1
        if oe < len(old_surface):
            right += 1


def selected_function_groups(
    family: str, function: str, zibo: list[str], levelup: list[str], reference: list[str],
    *, group_numbers: set[int] | None = None, required_token: str | None = None,
) -> list[dict[str, object]]:
    old_surface = function_surface(zibo, function)
    levelup_surface = function_surface(levelup, function)
    if old_surface != levelup_surface:
        raise ValueError(f"{function}: clean Zibo and LevelUp owner surfaces differ")
    new_surface = function_surface(reference, function)
    result = []
    for number, candidate in enumerate(changed_groups(old_surface, new_surface), 1):
        if group_numbers is not None and number not in group_numbers:
            continue
        if required_token is not None and not any(required_token in line for line in new_surface[candidate[2]:candidate[3]]):
            continue
        os, oe, ns, ne = unique_bounds(old_surface, new_surface, candidate, zibo, levelup, reference)
        result.append({
            "name": f"{family} {function} block {number}",
            "oldLines": old_surface[os:oe],
            "newLines": new_surface[ns:ne],
        })
    return result


def combined_function_groups(
    family: str, function: str, zibo: list[str], levelup: list[str], reference: list[str],
    group_sets: tuple[set[int], ...],
) -> list[dict[str, object]]:
    old_surface = function_surface(zibo, function)
    if old_surface != function_surface(levelup, function):
        raise ValueError(f"{function}: clean Zibo and LevelUp owner surfaces differ")
    new_surface = function_surface(reference, function)
    groups = changed_groups(old_surface, new_surface)
    result = []
    for sequence, selected in enumerate(group_sets, 1):
        candidates = [groups[number - 1] for number in sorted(selected)]
        bounds = (
            min(item[0] for item in candidates), max(item[1] for item in candidates),
            min(item[2] for item in candidates), max(item[3] for item in candidates),
        )
        os, oe, ns, ne = unique_bounds(old_surface, new_surface, bounds, zibo, levelup, reference)
        result.append({
            "name": f"{family} {function} combined block {sequence}",
            "oldLines": old_surface[os:oe],
            "newLines": new_surface[ns:ne],
        })
    return result


def line_substitution_replacements(
    family: str, function: str, zibo: list[str], levelup: list[str], substitutions: tuple[tuple[str, str], ...],
) -> list[dict[str, object]]:
    old_surface = function_surface(zibo, function)
    if old_surface != function_surface(levelup, function):
        raise ValueError(f"{function}: clean Zibo and LevelUp owner surfaces differ")
    new_surface = list(old_surface)
    changed = []
    for index, line in enumerate(new_surface):
        replacement_line = line
        for old, new in substitutions:
            if old.startswith("atc_msg_rsp[") and "==" not in replacement_line and "~=" not in replacement_line:
                continue
            replacement_line = replacement_line.replace(old, new)
        if replacement_line != line:
            new_surface[index] = replacement_line
            changed.append(index)
    if not changed:
        return []
    windows = [[index, index + 1] for index in changed]
    while True:
        expanded = []
        for start, end in windows:
            left = right = 0
            while True:
                old_block = old_surface[max(0, start-left):min(len(old_surface), end+right)]
                new_block = new_surface[max(0, start-left):min(len(new_surface), end+right)]
                if (occurrences(zibo, old_block) == 1 and occurrences(levelup, old_block) == 1
                        and occurrences(zibo, new_block) == 0 and occurrences(levelup, new_block) == 0):
                    break
                if start - left > 0:
                    left += 1
                if end + right < len(old_surface):
                    right += 1
                if start - left == 0 and end + right == len(old_surface):
                    raise ValueError(f"{family}/{function}: substitution anchor is not unique")
            expanded.append([max(0, start-left), min(len(old_surface), end+right)])
        expanded.sort()
        merged = []
        for start, end in expanded:
            if merged and start < merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        if merged == windows:
            break
        windows = merged
    return [
        {"name": f"{family} {function} response block {number}", "oldLines": old_surface[start:end], "newLines": new_surface[start:end]}
        for number, (start, end) in enumerate(windows, 1)
    ]


def comparison_owner_functions(source: list[str], tokens: tuple[str, ...]) -> list[str]:
    result: list[str] = []
    current: str | None = None
    for line in source:
        if line.startswith("function "):
            current = line.removeprefix("function ").split("(", 1)[0]
        if current is not None and ("==" in line or "~=" in line) and any(token in line for token in tokens):
            if current not in result:
                result.append(current)
    return result


def contextualize_repeated_replacement(
    item: dict[str, object], zibo: list[str], levelup: list[str], name_prefix: str,
) -> list[dict[str, object]]:
    old = item["oldLines"]
    new = item["newLines"]
    starts = [i for i in range(len(zibo) - len(old) + 1) if zibo[i:i + len(old)] == old]
    levelup_starts = [i for i in range(len(levelup) - len(old) + 1) if levelup[i:i + len(old)] == old]
    if len(starts) != len(levelup_starts) or not starts:
        raise ValueError(f"{name_prefix}: repeated clean anchors differ")
    result = []
    for sequence, (start, levelup_start) in enumerate(zip(starts, levelup_starts), 1):
        left = right = 0
        while True:
            old_context = zibo[start-left:start + len(old) + right]
            levelup_context = levelup[levelup_start-left:levelup_start + len(old) + right]
            if old_context == levelup_context and occurrences(zibo, old_context) == 1 and occurrences(levelup, old_context) == 1:
                break
            left += 1
            right += 1
        new_context = old_context[:left] + new + old_context[left + len(old):]
        result.append({"name": f"{name_prefix} {sequence}", "oldLines": old_context, "newLines": new_context})
    return result


def replacement(name: str, old: str, new: str, zibo: list[str], levelup: list[str]) -> dict[str, object]:
    old_lines = block(old)
    if occurrences(zibo, old_lines) != 1 or occurrences(levelup, old_lines) != 1:
        raise ValueError(f"{name}: old block is not unique on both clean baselines")
    return {"name": name, "oldLines": old_lines, "newLines": block(new)}


def write_payload(path: Path, replacements: list[dict[str, object]], condition: str | None = None) -> None:
    if not replacements:
        raise ValueError(f"{path.name}: empty payload")
    document: dict[str, object] = {"format": "exact-text-replacements-v1"}
    if condition is not None:
        document["condition"] = condition
    document["replacements"] = replacements
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def repair_i05_i06(output_dir: Path) -> None:
    i05_path = output_dir / "i05-app-normalization-and-if-merge.json"
    i06_path = output_dir / "i06-cpdlc-response-origin-fallback.json"
    i05 = json.loads(i05_path.read_text(encoding="utf-8"))
    i06 = json.loads(i06_path.read_text(encoding="utf-8"))
    if not any(item["name"].startswith("I05 APP canonicalization") for item in i05["replacements"]):
        return
    cpdlc_from_i05 = i05["replacements"][:5]
    app_from_i06 = [item for item in i06["replacements"] if item["name"].split()[-1] in {"14", "15", "16", "17", "18", "19"}]
    i05["replacements"] = app_from_i06 + i05["replacements"][5:]
    for number, item in enumerate(i05["replacements"], 1):
        item["name"] = f"I05 APP/IF/Ref-ICAO correction {number}"
    i06["replacements"] = [item for item in i06["replacements"] if item not in app_from_i06]
    # The first five blocks belong to the CPDLC response owner, not I05.
    for item in cpdlc_from_i05:
        item["name"] = item["name"].replace("I05 APP canonicalization", "I06 effective response")
    i06["replacements"] = cpdlc_from_i05 + i06["replacements"]
    # Remove duplicate old blocks while preserving the widest, first occurrence.
    deduped = []
    seen = set()
    for item in i06["replacements"]:
        key = json.dumps(item["oldLines"])
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    i06["replacements"] = deduped
    i05_path.write_text(json.dumps(i05, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    i06_path.write_text(json.dumps(i06, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def normalize_existing_payloads(output_dir: Path, zibo: list[str], levelup: list[str]) -> None:
    i05_path = output_dir / "i05-app-normalization-and-if-merge.json"
    i05 = json.loads(i05_path.read_text(encoding="utf-8"))
    if len(i05["replacements"]) >= 6 and i05["replacements"][4]["name"].startswith("I05 APP/IF"):
        merged = replacement(
            "I05 APP display canonicalization both render branches",
            "\t\t\tif des_app_exec == 1 then\n\t\t\t\ttemp_str = string.sub(use_des_app, 1, 1)\n\t\t\t\t\n\t\t\t\ttemp_str2 = use_des_app\n\t\t\t\ttemp_str_rnw = string.sub(temp_str2, 2, 3)\n\t\t\t\tif tonumber(temp_str_rnw) == nil then",
            "\t\t\tif des_app_exec == 1 then\n\t\t\t\ttemp_str = string.sub(use_des_app_disp, 1, 1)\n\t\t\t\t\n\t\t\t\ttemp_str2 = use_des_app_disp\n\t\t\t\ttemp_str_rnw = string.sub(temp_str2, 2, 3)\n\t\t\t\tif tonumber(temp_str_rnw) == nil then",
            zibo, levelup,
        )
        i05["replacements"] = i05["replacements"][:4] + [merged] + i05["replacements"][6:]
    for item in i05["replacements"]:
        if item["oldLines"][:1] == ["\tend"] and "\tend" not in item["newLines"][:2] and "end" in item["newLines"][:3]:
            item["newLines"].insert(0, "\tend")
    i05_path.write_text(json.dumps(i05, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for filename, repeated_name in (
        ("i24-n1-owner-and-oat-guard.json", "I24 initialize manual N1 retirement owner"),
    ):
        path = output_dir / filename
        document = json.loads(path.read_text(encoding="utf-8"))
        updated = []
        for item in document["replacements"]:
            if item["name"] == repeated_name:
                updated.extend(contextualize_repeated_replacement(item, zibo, levelup, repeated_name))
            else:
                updated.append(item)
        document["replacements"] = updated
        path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    i27_path = output_dir / "i27-manual-go-around-evidence.json"
    i27 = json.loads(i27_path.read_text(encoding="utf-8"))
    i27_initializers = []
    for sequence, altitude_owner in enumerate(("tai_off_alt_num_mod", "tai_off_alt_num"), 1):
        blank_lines = "\n" if altitude_owner.endswith("_mod") else "\n\n"
        old = (
            f"{altitude_owner} = 0\n{blank_lines}eng_out_prompt = 0\n\n"
            "was_on_air = 0\n"
            "takeoff_enable = 0\n"
            "climb_enable = 1\n"
            "descent_enable = 0\n"
            "goaround_enable = 0\n"
            "fmc_climb_mode = 0"
        )
        new = old.replace(
            "goaround_enable = 0\nfmc_climb_mode = 0",
            "goaround_enable = 0\n"
            "-- FIX: INTENTIONAL FIX I27 - observed same-arrival landing-flap retraction owns manual FMC go-around inference.\n"
            "manual_ga_flap_last = -1\n"
            "manual_ga_retracted = 0\n"
            'manual_ga_arrival_key = ""\n'
            "fmc_climb_mode = 0",
        )
        i27_initializers.append(replacement(
            f"I27 initialize manual go-around evidence owner {sequence}", old, new, zibo, levelup,
        ))
    i27["replacements"] = i27_initializers + [
        item for item in i27["replacements"]
        if not item["name"].startswith("I27 initialize manual go-around evidence owner")
    ]
    i27_path.write_text(json.dumps(i27, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    i33_path = output_dir / "i33-levelup-wb-zfw-gate.json"
    i33 = json.loads(i33_path.read_text(encoding="utf-8"))
    i33["condition"] = "levelup-wb-surface-present"
    i33_path.write_text(json.dumps(i33, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def i09_helpers() -> list[str]:
    return block(r'''
-- FIX: preserve manual/procedure hold identity when stock route mutations temporarily
-- rewrite a same-fix hold row to DF.
function B738_is_hold_context_leg(legs_tbl, leg_idx, in_rte)
	if legs_tbl == nil or leg_idx == nil or leg_idx < 1 then return false end
	local leg = legs_tbl[leg_idx]
	if leg == nil then return false end
	local path_txt = tostring(leg[31] or "")
	if path_txt == "HA" or path_txt == "HF" or path_txt == "HM" then return true end
	if path_txt ~= "DF" then return false end
	local leg_id = tostring(leg[1] or "")
	local prev_leg = legs_tbl[leg_idx - 1]
	if leg_id == "" or prev_leg == nil then return false end
	if tostring(prev_leg[1] or "") ~= leg_id then return false end
	if tostring(prev_leg[16] or "") ~= tostring(leg[16] or "") then return false end
	local prev_path = tostring(prev_leg[31] or "")
	if prev_path == "HA" or prev_path == "HF" or prev_path == "HM" then return false end
	local hold_td = tostring(leg[30] or "")
	local hold_turn = tonumber(leg[21]) or -1
	if hold_td == "" and hold_turn ~= 0 and hold_turn ~= 1 then return false end
	local leg_lat = tonumber(leg[7]) or 0
	local leg_lon = tonumber(leg[8]) or 0
	local prev_lat = tonumber(prev_leg[7]) or 0
	local prev_lon = tonumber(prev_leg[8]) or 0
	if math.abs(leg_lat - prev_lat) > 0.00001 or math.abs(leg_lon - prev_lon) > 0.00001 then return false end
	if in_rte == rte12_act then
		local active_idx = tonumber(offset_seq) or 0
		local offset_idx = tonumber(offset) or 0
		if leg_idx == active_idx or leg_idx == offset_idx then return true end
	end
	local prev_prev_leg = legs_tbl[leg_idx - 2]
	local prev_prev_path = prev_prev_leg ~= nil and tostring(prev_prev_leg[31] or "") or ""
	return prev_prev_path == "AF" or prev_prev_path == "RF" or prev_prev_path == "CI" or prev_prev_path == "VI"
end

function B738_rebuild_hold_data_from_legs(legs_tbl, legs_cnt, in_rte)
	local hold_tbl = {}
	local hold_num = 0
	for ii = 1, legs_cnt do
		if B738_is_hold_context_leg(legs_tbl, ii, in_rte) then
			hold_num = hold_num + 1
			hold_tbl[hold_num] = ii
		end
	end
	return hold_tbl, hold_num
end

function B738_should_preserve_hold_offset_sync(legs_tbl, offset_mod_idx, in_rte)
	if legs_tbl == nil or offset_mod_idx == nil or offset_mod_idx < 1 then return false end
	if B738_is_hold_context_leg(legs_tbl, offset_mod_idx, in_rte) then return true end
	local next_idx = offset_mod_idx + 1
	if B738_is_hold_context_leg(legs_tbl, next_idx, in_rte) then return true end
	local next_leg = legs_tbl[next_idx]
	if next_leg == nil or (tonumber(next_leg[25]) or 0) ~= 0 then return false end
	local scan_idx = next_idx + 1
	while legs_tbl[scan_idx] ~= nil do
		if B738_is_hold_context_leg(legs_tbl, scan_idx, in_rte) then return true end
		if (tonumber(legs_tbl[scan_idx][25]) or 0) ~= 0 then break end
		scan_idx = scan_idx + 1
	end
	return false
end
''')


def strip_diag_guard(lines: list[str]) -> list[str]:
    result: list[str] = []
    index = 0
    while index < len(lines):
        if "if B738_dup_diag_enabled()" in lines[index] and "then" in lines[index]:
            indent = len(lines[index]) - len(lines[index].lstrip("\t"))
            index += 1
            while index < len(lines):
                current_indent = len(lines[index]) - len(lines[index].lstrip("\t"))
                if lines[index].strip() == "end" and current_indent == indent:
                    index += 1
                    break
                index += 1
            continue
        result.append(lines[index])
        index += 1
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zibo-clean", type=Path, required=True)
    parser.add_argument("--levelup-clean", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--pre-diagnostics-reference", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    zibo = read_lines(args.zibo_clean)
    levelup = read_lines(args.levelup_clean)
    reference = read_lines(args.reference)
    pre_diag = read_lines(args.pre_diagnostics_reference)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    combined = selected_function_groups(
        "I02/I03", "dec_lat_lon2", zibo, levelup, pre_diag,
        group_numbers={1, 2, 3, 4, 10, 11, 12, 13, 14, 29, 30},
    )
    write_payload(args.output_dir / "i02-i03-course-and-intercept.json", combined)

    i04: list[dict[str, object]] = []
    i04 += combined_function_groups("I04", "rte_add_hold", zibo, levelup, reference, ({1, 2}, {4, 5}))
    for function in ("B738_fmc1_2L_CMDhandler", "B738_fmc1_3L_CMDhandler", "B738_fmc2_2L_CMDhandler", "B738_fmc2_3L_CMDhandler"):
        i04 += selected_function_groups("I04", function, zibo, levelup, reference, required_token="store entered MAG course directly")
    i04 += selected_function_groups("I04", "B738_fmc_hold", zibo, levelup, reference, required_token="hold_has_true_flag")
    write_payload(args.output_dir / "i04-hold-course-defaults.json", i04)

    i09: list[dict[str, object]] = []
    i09.append(replacement(
        "I09 hold identity helpers", "function create_fpln(in_rte)\n\n\tlocal ii = 0",
        "\n".join(i09_helpers() + ["", "function create_fpln(in_rte)", "", "\tlocal ii = 0"]), zibo, levelup,
    ))
    arm_helper = r'''
-- FIX: arm an active manual hold intercept without rewriting the new HA/HF/HM row to DF.
function B738_arm_manual_hold_intercept(in_item, in_rte, on_ground)
	if rte12_act ~= in_rte then return end
	local nd_lat2 = 0
	local nd_lon2 = 0
	if in_rte == 0 then nd_lat2, nd_lon2 = lat_lon_legs2(in_item) else nd_lat2, nd_lon2 = lat_lon_legs8(in_item) end
	if on_ground == false then
		legs_intdir = 1
		legs_intdir_rte = in_rte
		legs_intdir_idx_mod = in_item
		local nd_lat = math.rad(simDR_latitude)
		local nd_lon = math.rad(simDR_longitude)
		nd_lat2 = math.rad(nd_lat2)
		nd_lon2 = math.rad(nd_lon2)
		local nd_y = math.sin(nd_lon2 - nd_lon) * math.cos(nd_lat2)
		local nd_x = math.cos(nd_lat) * math.sin(nd_lat2) - math.sin(nd_lat) * math.cos(nd_lat2) * math.cos(nd_lon2 - nd_lon)
		local nd_hdg = (math.deg(math.atan2(nd_y, nd_x)) + 360) % 360
		legs_intdir_crs_mod = (nd_hdg + simDR_mag_variation + 360) % 360
	end
end

function rte_add_wpt(aaa, entry_in, mode_in, in_rte)
'''
    i09.append(replacement("I09 manual-hold intercept helper", "function rte_add_wpt(aaa, entry_in, mode_in, in_rte)", arm_helper, zibo, levelup))
    for function, token in (
        ("B738_activate", "activating a modified route"),
        ("rte_add_hold", "B738_rebuild_hold_data_from_legs"),
        ("legs_1_lsk", "B738_arm_manual_hold_intercept"),
        ("legs_x_lsk", "B738_arm_manual_hold_intercept"),
        ("B738_mod_change2", "B738_should_preserve_hold_offset_sync"),
    ):
        generated = selected_function_groups("I09", function, zibo, levelup, reference, required_token=token)
        for item in generated:
            item["newLines"] = strip_diag_guard(item["newLines"])
        i09 += generated
    write_payload(args.output_dir / "i09-hold-identity-route-mutations.json", i09)

    i16_helper = r'''
-- FIX: bound climb-restriction scans to climb/neutral route roles and fail closed
-- before arrival, approach or discontinuity rows. Active missed approach keeps its
-- own complete climb domain.
local function B738_climb_restriction_end_idx()
	if B738DR_missed_app_act > 0 then return legs_num end
	local end_idx = legs_num
	if tc_idx ~= nil and tc_idx > 1 then end_idx = math.min(end_idx, tc_idx - 1) end
	for ii = math.max(offset or 1, 1), end_idx do
		local leg = legs_data[ii]
		if leg == nil then return ii - 1 end
		local role = tonumber(leg[19]) or 0
		if leg[1] == "DISCONTINUITY" or role == 2 or role == 3 or role == 4 or role == 7 or role == 8 or role == 9 then
			return ii - 1
		end
	end
	return end_idx
end

function B738_restrict_data()
'''
    i16 = [replacement("I16 climb-domain helper", "function B738_restrict_data()", i16_helper, zibo, levelup)]
    i16.append(replacement(
        "I16 speed restriction climb bound",
        "\t\t\tif B738DR_flight_phase < 2 or B738DR_flight_phase > 7 then\t\t-- climb and go-around\n\t\t\t\t\n\t\t\t\ttd_idx_temp = math.max(last_sid_idx, tc_idx - 1)",
        "\t\t\tif B738DR_flight_phase < 2 or B738DR_flight_phase > 7 then\t\t-- climb and go-around\n\t\t\t\t\n\t\t\t\ttd_idx_temp = B738_climb_restriction_end_idx()",
        zibo, levelup,
    ))
    i16.append(replacement(
        "I16 altitude restriction climb bound",
        "\t\t\t\t\tif B738DR_missed_app_act > 0 then\n\t\t\t\t\t\ttd_idx_temp = legs_num\n\t\t\t\t\telse\n\t\t\t\t\t\ttd_idx_temp = math.max(last_sid_idx, tc_idx - 1)\n\t\t\t\t\tend",
        "\t\t\t\t\ttd_idx_temp = B738_climb_restriction_end_idx()",
        zibo, levelup,
    ))
    write_payload(args.output_dir / "i16-climb-restriction-domain.json", i16)

    i30_helper = r'''
-- FIX: ALT INTV releases exactly the next committed altitude constraint that
-- conflicts with the selected MCP altitude. MOD ownership is preserved.
local function B738_alt_intv_release_next_constraint(climb_mode)
	local end_idx = legs_num
	if climb_mode then
		end_idx = tc_idx - 1
	elseif ed_found ~= 0 then
		end_idx = first_app_idx ~= 0 and (first_app_idx - 1) or (ed_found - 1)
	end
	if end_idx < offset then return false end
	for nn = 1, legs_restr_alt_n do
		local n = legs_restr_alt[nn][2]
		if n > end_idx then break end
		if n >= offset and n <= legs_num then
			local rest_type = legs_restr_alt[nn][4]
			local alt1 = legs_restr_alt[nn][3]
			local alt2 = legs_restr_alt[nn][5]
			local release = false
			if climb_mode then
				release = (rest_type == 41 and alt2 < B738DR_mcp_alt_dial) or alt1 < B738DR_mcp_alt_dial
			else
				release = (rest_type == 41 and (alt1 > B738DR_mcp_alt_dial or alt2 > B738DR_mcp_alt_dial)) or alt1 > B738DR_mcp_alt_dial
			end
			if release then
				local old5 = legs_data[n][5]
				local old6 = legs_data[n][6]
				local old41 = legs_data[n][41]
				legs_data[n][5] = 0
				legs_data[n][6] = 0
				legs_data[n][41] = 0
				if n <= legs_num2 and (legs_delete == 0 or (legs_data2[n][5] == old5 and legs_data2[n][6] == old6 and legs_data2[n][41] == old41)) then
					legs_data2[n][5] = 0
					legs_data2[n][6] = 0
					legs_data2[n][41] = 0
				end
				fms_recalc = 1
				vnav_update = 1
				msg_unavaible_crz_alt = 0
				return true
			end
		end
	end
	return false
end

function B738_autopilot_alt_interv_CMDhandler(phase, duration)
'''
    i30 = [replacement("I30 committed-constraint release helper", "function B738_autopilot_alt_interv_CMDhandler(phase, duration)", i30_helper, zibo, levelup)]
    i30.append(replacement(
        "I30 descent lower-MCP no-deadband",
        "\t\t\t\t\telseif B738DR_flight_phase > 4 and B738DR_flight_phase < 8 and B738DR_mcp_alt_dial < (simDR_altitude_pilot - 300) then",
        "\t\t\t\t\telseif B738DR_flight_phase > 4 and B738DR_flight_phase < 8 and B738DR_mcp_alt_dial < B738DR_preselected_alt then",
        zibo, levelup,
    ))
    i30.append(replacement(
        "I30 cruise DES NOW no-deadband",
        "\t\t\t\t\telseif B738DR_flight_phase == 2 and B738DR_mcp_alt_dial < (simDR_altitude_pilot - 300) then",
        "\t\t\t\t\telseif B738DR_flight_phase == 2 and B738DR_mcp_alt_dial < crz_alt_num then",
        zibo, levelup,
    ))
    start = next(i for i, line in enumerate(zibo) if line == "\t\t\t\tif B738DR_flight_phase < 2 or B738DR_flight_phase == 8 then" and i > 83000)
    end = next(i for i in range(start, len(zibo)) if zibo[i] == "\t\t\t-- end") + 1
    old_tail = zibo[start:end]
    if occurrences(levelup, old_tail) != 1:
        raise ValueError("I30 deletion tail differs on LevelUp clean baseline")
    new_tail = block(r'''
				if B738DR_flight_phase < 2 or B738DR_flight_phase == 8 then
					B738_alt_intv_release_next_constraint(true)
				elseif B738DR_flight_phase > 4 and B738DR_flight_phase < 8 then
					B738_alt_intv_release_next_constraint(false)
					if B738DR_mcp_alt_dial < B738DR_preselected_alt and B738DR_flight_phase == 5 then
						B738DR_fms_descent_now = 2
						B738DR_ignore_td_idx2 = 1
						td_alt2_old = td_alt2
					end
				end
			end
			-- end
''')
    i30.append({"name": "I30 phase-independent next-constraint deletion", "oldLines": old_tail, "newLines": new_tail})
    write_payload(args.output_dir / "i30-alt-intervention-constraint-release.json", i30)

    repair_i05_i06(args.output_dir)
    normalize_existing_payloads(args.output_dir, zibo, levelup)

    i06_path = args.output_dir / "i06-cpdlc-response-origin-fallback.json"
    existing_i06 = json.loads(i06_path.read_text(encoding="utf-8"))
    retained_i06 = [
        item for item in existing_i06["replacements"]
        if item["name"] in {
            "I06 direct-send current-origin fallback",
            "I06 nil-safe secondary PREDEP route context",
        }
    ]
    if len(retained_i06) != 2:
        raise ValueError("I06: the two independently authored origin/context corrections are required")

    i06_helper = r'''
-- FIX: infer WILCO only for existing PDC/CLD messages whose response code is absent.
function cpdlc_effective_rsp(in_msg)
	local rsp = atc_msg_rsp[in_msg]
	if rsp == nil then rsp = 0 end
	if rsp ~= 0 then return rsp end
	local txt = atc_msg_txt[in_msg]
	if txt == nil or txt == "" then return rsp end
	local up = string.upper(txt)
	local is_pdc = string.find(up, " PDC ", 1, true) ~= nil or string.find(up, " PREDEP CLEARANCE", 1, true) ~= nil
	local is_cld = string.sub(up, 1, 4) == "CLD "
	if is_pdc or is_cld then return 2 end
	return rsp
end

function dl_cpdlc_message(in_msg)
	max_page_buf = 1
'''
    i06 = [replacement(
        "I06 effective CPDLC response helper",
        "function dl_cpdlc_message(in_msg)\n\tmax_page_buf = 1",
        i06_helper,
        zibo, levelup,
    )]
    response_tokens = ("atc_msg_rsp[atc_msg_log_cur]", "atc_msg_rsp[in_msg]")
    substitutions = (
        ("atc_msg_rsp[atc_msg_log_cur]", "cpdlc_effective_rsp(atc_msg_log_cur)"),
        ("atc_msg_rsp[in_msg]", "cpdlc_effective_rsp(in_msg)"),
        ('answer_msg = answer_msg " DUE TO WEATHER"', 'answer_msg = answer_msg .. " DUE TO WEATHER"'),
    )
    for function in comparison_owner_functions(zibo, response_tokens):
        i06 += line_substitution_replacements("I06", function, zibo, levelup, substitutions)
    if not any('answer_msg = answer_msg .. " DUE TO WEATHER"' in line for item in i06 for line in item["newLines"]):
        raise ValueError("I06: weather-response concatenation correction was not captured")
    i06 += retained_i06
    write_payload(i06_path, i06, "cpdlc-surface-present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
