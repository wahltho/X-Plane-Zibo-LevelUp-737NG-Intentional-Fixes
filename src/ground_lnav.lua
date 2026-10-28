function lnav_prior()
    -- FIX: evaluate the first committed leg, independent of selected MOD work.
    B738DR_lnav_prior_arm = 0
    if not (simDR_on_ground[0] == 1 or simDR_on_ground[1] == 1 or simDR_on_ground[2] == 1) then return end
    if legs_num <= 2 or offset <= 0 or offset >= 4 or (rte12_act ~= 0 and rte12_act ~= 1) then return end
    if not legs_data[1] or not legs_data[2] or not legs_data[3] or not is_rw_wpt(legs_data[2][1]) then return end
    local airport = rte12_act == 0 and ref_icao or ref_icao7
    local runway = rte12_act == 0 and ref_rwy or ref_rwy7
    if type(airport) ~= "string" or type(runway) ~= "string" or legs_data[1][1] ~= airport then return end
    runway = runway:match("^%s*(.-)%s*$")
    find_ref_rnw_data(0, rte12_act)
    if not B738_ifix_course.finite(ref_runway_lenght) or ref_runway_lenght <= 0
        or not B738_ifix_course.finite(ref_runway_crs) then return end
    if legs_data[2][1] ~= "RW"..runway and legs_data[2][1] ~= "RW"..ref_runway_old_name then return end
    local start_lat, start_lon
    -- The existing finder supplies TRUE runway direction; require its actual record.
    local letter = string.byte(airport, 1)
    local bucket = letter and idx_rnw[letter]
    if bucket then
        for k = 1, bucket[99999] or 0 do
            local r = rnw_data[bucket[k]]
            if r and r[1] == airport and r[2] == runway then
                if not B738_ifix_course.finite(r[3]) or not B738_ifix_course.finite(r[4])
                    or not B738_ifix_course.finite(r[5]) or not B738_ifix_course.finite(r[6])
                    or (r[3] == r[5] and r[4] == r[6]) then return end
                start_lat, start_lon = r[3], r[4]
                break
            end
        end
    end
    if start_lat == nil then return end
    local row = legs_data[3]
    local direction
    if row[31] == "VA" or row[31] == "VD" or row[31] == "VI" or row[31] == "VM" or row[31] == "VR" then
        direction = B738_ifix_course.true_at(row, start_lat, start_lon)
    elseif B738_ifix_course.finite(row[2]) then
        direction = math.deg(row[2])
    end
    if not B738_ifix_course.finite(direction) then return end
    local delta = math.abs((direction - ref_runway_crs + 180) % 360 - 180)
    if delta <= 5 then B738DR_lnav_prior_arm = 1 end
end

-- Native commands may not exist while XLua first loads this script.
-- Retry from lifecycle callbacks, and stop looking once the wrapper is installed.
function B738_ifix_vi.ensure_lnav_wrapper()
    if B738_ifix_vi.lnav_wrapped then return end
    local lookup = XLuaFindCommand or XPLMFindCommand
    if type(lookup) ~= "function" or not lookup("laminar/B738/autopilot/lnav_press") then return end
    wrap_command("laminar/B738/autopilot/lnav_press",
        function(phase, duration) if phase == 0 then lnav_prior() end end,
        function(phase, duration) end)
    B738_ifix_vi.lnav_wrapped = true
end
