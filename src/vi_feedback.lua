function B738_read_calc_data()
    -- FIX: completion callback ACKs command; only a completed positive count is ready.
    if not B738_ifix_vi.admissible() or not B738_ifix_vi.matches then
        B738_ifix_vi.clear_packet()
        return
    end
    if legs_num <= 0 then B738_ifix_vi.clear_packet(); return end
    for ii = 1, legs_num + 1 do
        legs_data[ii][50] = B738DR_fms_legs_dist_dest_t[ii-1]
        legs_data[ii][51] = B738DR_fms_legs_dist_t[ii-1]
    end
    if B738DR_fms_add_data_num <= 0 then return end
    if not B738_ifix_vi.packet_valid() then B738_ifix_vi.clear_packet(); return end
    for k = 0, B738DR_fms_add_data_num-1 do
        local row = legs_data[B738DR_fms_add_data_1[k]]
        row[7], row[8] = B738DR_fms_add_data_2[k], B738DR_fms_add_data_3[k]
        row[2], row[3] = B738DR_fms_add_data_4[k], B738DR_fms_add_data_5[k]
        if row[31] ~= "VI" then row[18] = B738DR_fms_add_data_6[k] end
        row[37] = B738DR_fms_add_data_4[k]
    end
    -- Project dependent VI rows after the whole geometry image, not packet order.
    B738_ifix_course.refresh_vi(legs_data, legs_num)
    B738_ifix_vi.clear_packet()
    if rte12_act == 0 then
        if calc_rte_enable2 == 0 and legs_delete == 0 and legs_intdir == 0 and hold_exec == 0 and rte_exec == 0 then
            copy_to_legsdata2(rte12_act)
        end
    elseif rte12_act == 1 then
        if calc_rte_enable8 == 0 and legs_delete == 0 and legs_intdir == 0 and hold_exec2 == 0 and rte_exec2 == 0 then
            copy_to_legsdata2(rte12_act)
        end
    end
end
