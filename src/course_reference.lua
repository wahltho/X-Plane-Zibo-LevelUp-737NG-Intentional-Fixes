-- BEGIN CUSTOM I02 typed prescribed courses
local B738_ifix_course = {}
function B738_ifix_course.finite(x)
    return type(x) == "number" and x == x and x ~= math.huge and x ~= -math.huge
end
function B738_ifix_course.read(raw, path)
    if type(raw) ~= "string" then return nil end
    raw = raw:match("^%s*(.-)%s*$")
    local digits = raw:match("^(%d%d%d)T$")
    if digits then
        local h = tonumber(digits)
        if h <= 360 then return h % 360, true end
        return nil
    end
    local numeric = raw:match("^%d%d%d%d$")
    if not numeric and type(path) == "string" and path:sub(1,1) == "H" then
        numeric = #raw >= 1 and #raw <= 4 and raw:match("^%d+$")
    end
    if numeric then
        local h = tonumber(raw)
        if h <= 3600 then return (h / 10) % 360, false end
    end
    return nil
end
function B738_ifix_course.project(h, is_true, want_true, lat, lon)
    if not B738_ifix_course.finite(h) then return nil end
    if is_true == want_true then return h end
    if not B738_ifix_course.finite(lat) or not B738_ifix_course.finite(lon) then return nil end
    local v = mag_variation_deg(lat, lon)
    if not B738_ifix_course.finite(v) then return nil end
    return (h + (want_true and -v or v)) % 360
end
function B738_ifix_course.command(path)
    return type(path) == "string" and
        (path:sub(1,1) == "C" or path:sub(1,1) == "V" or path:sub(1,1) == "H"
        or path == "FA" or path == "FC" or path == "FD" or path == "FM" or path == "PI")
end
-- This scope borrows existing lookup inputs only until the synchronous query returns.
-- It retains no datum and does not change the finder, its I01 correction, or a cache.
function B738_ifix_course.start(rows, count, index, rte, active)
    local row, prev = rows[index], rows[index-1]
    if not row or not prev then return nil end
    local lat, lon = prev[7], prev[8]
    local path = row[31]
    if path:sub(1,1) == "H" or path == "PI" then
        return row[7], row[8]
    end
    if path ~= "FD" and path ~= "FC" and path ~= "FM" then return lat, lon end
    if is_rw_wpt(prev[1]) then return lat, lon, 0, 0, 1 end
    local ndb = row[32] > 9 and 2 or 1
    local mode = 0
    if row[19] == 1 or row[19] == 3 then mode = 11
    elseif row[19] == 2 or row[19] == 4 or row[19] == 7 or row[19] == 8 or row[19] == 9 then mode = 12
    elseif lat ~= 0 and lon ~= 0 then mode = 3 end
    local names = {"navaid_list", "navaid_list_n", "temp_nav_sort", "find_lat", "find_lon",
        "legs_data", "legs_num", "offset", "ref_icao_lat_x", "ref_icao_lon_x",
        "des_icao_lat_x", "des_icao_lon_x", "ref_icao_lat7_x", "ref_icao_lon7_x",
        "des_icao_lat7_x", "des_icao_lon7_x"}
    -- XLua script globals live in the function namespace, not its parent _G.
    local env = getfenv and getfenv(1) or _ENV
    local saved = {}
    for i, key in ipairs(names) do saved[i] = env[key] end
    local suffix = rte == 1 and "7" or ""
    local source_suffix = suffix .. (active and "" or "_x")
    local dep_lat, dep_lon = env["ref_icao_lat"..source_suffix], env["ref_icao_lon"..source_suffix]
    local dst_lat, dst_lon = env["des_icao_lat"..source_suffix], env["des_icao_lon"..source_suffix]
    local source_offset = active and offset or (rte == 1 and offset_mod2 or offset_mod)
    local result_type = 0
    local ok, err = pcall(function()
        find_lat, find_lon = lat, lon
        legs_data, legs_num, offset = rows, count, source_offset
        env["ref_icao_lat"..suffix.."_x"], env["ref_icao_lon"..suffix.."_x"] = dep_lat, dep_lon
        env["des_icao_lat"..suffix.."_x"], env["des_icao_lon"..suffix.."_x"] = dst_lat, dst_lon
        find_navaid2(row[34], "", mode, row[16], ndb, rte)
        if navaid_list_n > 0 then
            lat, lon, result_type = navaid_list[1][2], navaid_list[1][3], navaid_list[1][1]
        end
    end)
    for i, key in ipairs(names) do env[key] = saved[i] end
    if not ok then error(err, 0) end
    return lat, lon, result_type, mode, ndb
end
function B738_ifix_course.mag(rows, count, index, rte, active)
    local row = rows[index]
    if not row then return nil end
    if not B738_ifix_course.command(row[31]) then return math.deg(row[18]) end
    local h, t = B738_ifix_course.read(row[29], row[31])
    if not t then return h end
    local lat, lon = B738_ifix_course.start(rows, count, index, rte, active)
    return B738_ifix_course.project(h, t, false, lat, lon)
end
function B738_ifix_course.true_at(row, lat, lon)
    local h, t = B738_ifix_course.read(row[29], row[31])
    return B738_ifix_course.project(h, t, true, lat, lon)
end
function B738_ifix_course.format(value, pattern)
    return value and string.format(pattern, value) or "   "
end
function B738_ifix_course.true_air(row)
    local h, t = B738_ifix_course.read(row[29], row[31])
    if not h then return nil end
    if t then return h end
    if not B738_ifix_course.finite(simDR_mag_variation) then return nil end
    return (h - simDR_mag_variation) % 360
end
function B738_ifix_course.native(row)
    local h, t = B738_ifix_course.read(row[29], row[31])
    return B738_ifix_course.project(h, t, false, row[7], row[8])
end
function B738_ifix_course.borrow(row, lat, lon, declination)
    local h, t = B738_ifix_course.read(row[29], row[31])
    if not h then return nil end
    if t then return h end
    if row[31] == "VI" or declination == nil then
        return B738_ifix_course.project(h, t, true, lat, lon)
    end
    -- FIX: retain the original non-VI magnetic navaid/radial expression.
    local v = mag_variation_deg(lat, lon)
    if not B738_ifix_course.finite(v) then return nil end
    return (h - declination + v) % 360
end
function B738_ifix_course.refresh_vi(rows, count, only_index)
    for index = only_index or 2, only_index or (count + 1) do
        local row, prev = rows[index], rows[index-1]
        if row and prev and row[31] == "VI" then
            local h, t = B738_ifix_course.read(row[29], "VI")
            local mag = B738_ifix_course.project(h, t, false, prev[7], prev[8])
            if mag then row[18] = math.rad(mag) end
        end
    end
end
function B738_ifix_course.hold_default(row)
    local raw, name = row[30], row[1] or ""
    local missing = raw == "" or (type(raw) == "string" and raw:match("^%d+$") and tonumber(raw) == 0)
    if missing and (name == "" or name:find("PROC",1,true)) then row[30] = "0050" end
end
-- END CUSTOM I02 typed prescribed courses
