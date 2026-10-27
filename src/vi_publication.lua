-- BEGIN CUSTOM I40 VI source publication lifetime
local B738_ifix_vi = {published=nil, staging=nil, matches=false, publishing=false}
function B738_ifix_vi.clear_packet()
    B738DR_fms_add_cmd = 0
    B738DR_fms_add_data_num = 0
end
function B738_ifix_vi.retire()
    B738_ifix_vi.matches = false
    B738_ifix_vi.clear_packet()
    B738DR_lnav_prior_arm = 0
end
function B738_ifix_vi.begin()
    B738_ifix_vi.retire()
    B738_ifix_vi.publishing = true
    B738_ifix_vi.staging = {count=0, rows={}}
end
function B738_ifix_vi.stage(index, row)
    local image = B738_ifix_vi.staging
    if not image then return end
    image.count = math.max(image.count, index)
    if row[31] == "VI" then
        local h, t = B738_ifix_course.read(row[29], "VI")
        image.rows[index] = {h=h, t=t, path="VI"}
    end
end
function B738_ifix_vi.commit()
    if not B738_ifix_vi.publishing then return end
    B738_ifix_vi.published = B738_ifix_vi.staging
    B738_ifix_vi.staging = nil
    B738_ifix_vi.publishing = false
    B738_ifix_vi.matches = true
    lnav_prior() -- FIX: publication retirement must not leave a coherent ground gate cleared.
end
function B738_ifix_vi.admissible()
    return ffirst_time2 ~= 0 and calc_rte_enable == 0 and
        not ((calc_rte_enable2 ~= 0 and rte12_act == 0) or (calc_rte_enable8 ~= 0 and rte12_act == 1))
end
function B738_ifix_vi.packet_valid()
    local n = B738DR_fms_add_data_num
    if not B738_ifix_course.finite(n) or n < 1 or n > 128 or n ~= math.floor(n) then return false end
    for k = 0, n-1 do
        local index = B738DR_fms_add_data_1[k]
        if not B738_ifix_course.finite(index) or index ~= math.floor(index) or index < 1
            or index > legs_num or index >= FMC_MAX_WPT then return false end
        for _, values in ipairs({B738DR_fms_add_data_2, B738DR_fms_add_data_3,
            B738DR_fms_add_data_4, B738DR_fms_add_data_5, B738DR_fms_add_data_6}) do
            if not B738_ifix_course.finite(values[k]) then return false end
        end
    end
    return true
end
function B738_ifix_vi.complete()
    if B738DR_fms_add_cmd ~= 1 then return end
    local image = B738_ifix_vi.published
    if B738_ifix_vi.publishing or not image then B738_ifix_vi.clear_packet(); return end
    -- FIX: old native publication remains the source even after private ACT replacement.
    for index, intent in pairs(image.rows) do
        local lat, lon = B738DR_fms_legs_lat[index-1], B738DR_fms_legs_lon[index-1]
        local mag = B738_ifix_course.project(intent.h, intent.t, false, lat, lon)
        if mag then
            B738DR_fms_legs_crs_mag[index-1] = mag
            B738DR_fms_legs_brg_mag[index-1] = math.rad(mag)
        end
    end
    if not B738_ifix_vi.matches or not B738_ifix_vi.admissible() or not B738_ifix_vi.packet_valid() then
        B738_ifix_vi.clear_packet()
    else
        -- Scalar ACK is required for original XLua's changed-value notification.
        B738DR_fms_add_cmd = 0
    end
end
-- END CUSTOM I40 VI source publication lifetime
