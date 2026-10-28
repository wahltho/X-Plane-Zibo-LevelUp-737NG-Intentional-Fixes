"""Actual composed Lua components; no simulated aircraft or complete flight replay."""
import json
import os
import re
import subprocess
import unittest

import test_cruise_fix_payloads as base


def asset(source, name):
    markers={"course":("-- BEGIN CUSTOM I02 typed prescribed courses","-- END CUSTOM I02 typed prescribed courses"),
             "vi":("-- BEGIN CUSTOM I40 VI source publication lifetime","-- END CUSTOM I40 VI source publication lifetime")}
    a,b=markers[name]; start=source.index(a)
    return source[start:source.index(b,start)+len(b)]+"\n"


class CourseFixPayloadTests(base.CruiseFixPayloadTests):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import sys
        sys.path.insert(0,str(base.ROOT))
        import z_Install
        old=json.loads(subprocess.check_output(['git','show','5555ba6:src/fixes/i02-i03-course-and-intercept.json'],cwd=base.ROOT))
        cls.legacy=z_Install.apply_exact_replacements(cls.original.encode(),old).decode()

    def run_lua(self, code):
        result=self.lua_result(code)
        self.assertEqual(0,result.returncode,result.stdout+result.stderr)

    PRELUDE=r'''
function near(a,b) assert(type(a)=="number" and math.abs(a-b)<1e-8,tostring(a).." ~= "..tostring(b)) end
function mag_variation_deg(lat,lon) return lat end
function mag_variation_rad(lat,lon) return lat end
simDR_mag_variation=7
function is_rw_wpt(s) return s:sub(1,2)=="RW" end
function lnav_prior() end
function row(path,raw,lat,lon)
 local r={}; for i=1,57 do r[i]=0 end
 r[1]="FIX"; r[16]="LG"; r[29]=raw; r[30]="0050"; r[31]=path; r[34]="START"; r[35]="";
 r[7]=lat or 10; r[8]=lon or 20; r[19]=1; r[21]=-1
 return r
end
function reset_route(path,raw)
 legs_data2={row("TF","",10,20),row(path,raw,11,21),row("TF","",12,22)}
 legs_num2=2; legs_num8=1; legs_data8={row("TF","",30,40),row("TF","",31,41)}
 legs_data=legs_data2; legs_num=legs_num2; offset=2; rte12_act=0
 ref_icao_alt_x=0; des_icao_alt_x=0; ref_icao_alt7_x=0; des_icao_alt7_x=0
 ref_icao_lat_x=10; ref_icao_lon_x=20; des_icao_lat_x=12; des_icao_lon_x=22
 ref_icao_lat7_x=30; ref_icao_lon7_x=40; des_icao_lat7_x=31; des_icao_lon7_x=41
end
function copy_to_legs_data2_buf(rte)
 legs_data2_buf=rte==0 and legs_data2 or legs_data8; legs_num2_buf=rte==0 and legs_num2 or legs_num8
end
function copy_from_legs_data2_buf(rte) end
function lat_lon_legs2(i) return legs_data2[i][7],legs_data2[i][8] end
function lat_lon_legs8(i) return legs_data8[i][7],legs_data8[i][8] end
function find_navaid2(...)
 navaid_list_n=1; navaid_list={{}}; for i=1,57 do navaid_list[1][i]=0 end
 navaid_list[1][1]=2; navaid_list[1][2]=30; navaid_list[1][3]=40; navaid_list[1][4]="START"
end
-- Unavailable AF centre and no DME intersection in these course-only fixtures.
function find_navaid(...) navaid_list_n=0; navaid_list={} end
function inter(...) return 0 end
function wpt_distance2(...) return 0 end
function nd_calc_dist2(...) return 1 end
function nd_calc_brg(...) return 0 end
function nd_calc_brg_rad(...) return 0 end
function calc_brg_dist(lat,lon,brg,dist) calc_lat=lat+0.1; calc_lon=lon+0.1; last_solver_brg=brg end
function calc_brg_brg(...) calc_lat=10.1; calc_lon=20.1 end
function calc_brg_dist2(...) calc_lat=10.1; calc_lon=20.1 end
function calc_brg_dist3(...) calc_lat=10.1; calc_lon=20.1 end
function B738_rescale(a,b,c,d,x) return c end
'''

    def test_declared_schema_north_and_reference(self):
        self.run_lua(self.PRELUDE+asset(self.source,'course')+r'''
for _,p in ipairs({{"0360",36,false},{"2760",276,false},{"0231",23.1,false},{"0000",0,false},
 {"036T",36,true},{"228T",228,true},{"360T",0,true}}) do
 local h,t=B738_ifix_course.read(p[1],"VI"); near(h,p[2]); assert(t==p[3])
end
for _,s in ipairs({"","035","0360T","361T","3601","T036","3 60","-010","036.0"}) do
 assert(B738_ifix_course.read(s,"VI")==nil,"invalid accepted: "..s)
end
near(B738_ifix_course.read("000","HM"),0); near(B738_ifix_course.read("50","HF"),5)
near(B738_ifix_course.project(36,true,false,10,20),46)
near(B738_ifix_course.project(36,false,true,10,20),26)
near(B738_ifix_course.project(0,true,false,0,20),0)
assert(B738_ifix_course.project(36,true,false,0/0,20)==nil)
''')

    def test_whole_decoder_lgsk_mag_units_and_true_source(self):
        cases=r'''
-- Actual course tokens from local LGSK/01 EVIK1E and EVIK1B CIFP.
for _,p in ipairs({{"VA","0140",14},{"FA","0130",13},{"CF","0140",14},{"VM","2760",276}}) do
 reset_route(p[1],p[2]); dec_lat_lon2(2,0)
 near(math.deg(legs_data2[2][18]),p[3]); assert(legs_data2[2][29]==p[2],"source destroyed")
end
for _,path in ipairs({"VM","CF","VA","FA"}) do
 reset_route(path,"036T"); dec_lat_lon2(2,0)
 near(math.deg(legs_data2[2][18]),46); assert(legs_data2[2][29]=="036T")
 dec_lat_lon2(2,0); near(math.deg(legs_data2[2][18]),46)
end
for _,path in ipairs({"FD","FC","FM","PI"}) do
 reset_route(path,"036T"); dec_lat_lon2(2,0)
 near(math.deg(legs_data2[2][18]),66); assert(legs_data2[2][29]=="036T")
end
reset_route("FD","036T"); legs_data2[2][19]=0; legs_data2[2][32]=10; legs_data2[2][27]="DME"
local queries=0
find_navaid2=function(id,empty,mode,region,ndb,rte)
 queries=queries+1; assert(mode==3); near(find_lat,10); near(find_lon,20)
 if id=="DME" and ndb==2 then navaid_list_n=0; navaid_list={}; return end
 assert((id=="START" and ndb==2) or (id=="DME" and ndb==3))
 navaid_list_n=1; navaid_list={{2,30,40}}
 if id=="START" then find_lat=-999; find_lon=-999 end
end
dec_lat_lon2(2,0); assert(queries==3); near(math.deg(legs_data2[2][18]),66)
'''
        corrected=self.PRELUDE+asset(self.source,'course')+base.function_text(self.source,'dec_lat_lon2')+cases
        self.run_lua(corrected)
        control=self.lua_result(self.PRELUDE+base.function_text(self.legacy,'dec_lat_lon2')+cases)
        self.assertNotEqual(0,control.returncode,"Published I02 unexpectedly satisfies LGSK oracle")
        self.assertIn('~=',control.stderr)

    def test_vi_without_successor_geometry_and_hold_time(self):
        self.run_lua(self.PRELUDE+asset(self.source,'course')+base.function_text(self.source,'dec_lat_lon2')+r'''
for _,raw in ipairs({"0360","036T"}) do
 reset_route("VI",raw); legs_num2=2; legs_data2[2][7]=0; legs_data2[2][8]=0
 dec_lat_lon2(2,0); near(math.deg(legs_data2[2][18]),raw=="0360" and 36 or 46)
 assert(legs_data2[2][29]==raw)
end
reset_route("VI","0360"); legs_data2[3][31]="AF"; legs_data2[3][29]=""; legs_num2=3
legs_data2[4]=row("TF","",13,23); dec_lat_lon2(2,0)
near(math.deg(legs_data2[2][18]),36) -- unavailable successor geometry cannot suppress own source.
for _,raw in ipairs({"000","036T","2760"}) do
 reset_route("HM",raw); legs_data2[2][30]="T010"; legs_data2[2][1]="PROC HOLD"
 dec_lat_lon2(2,0); assert(legs_data2[2][29]==raw and legs_data2[2][30]=="T010")
end
reset_route("VM",""); dec_find_type=7; dec_lat_lon2(2,0); assert(dec_find_type==0)
''')

    def test_xlua_namespace_lookup_restoration_and_actual_start(self):
        # XLua uses an empty environment with values behind __index/__newindex.
        body=asset(self.source,'course')+'\nreturn B738_ifix_course\n'
        code=self.PRELUDE+'\nlocal helper_source='+json.dumps(body)+'\n'+r'''
local values={}; local env=setmetatable({}, {__index=function(_,k) if values[k]~=nil then return values[k] end return _G[k] end,
 __newindex=function(_,k,v) values[k]=v end})
local fn
if setfenv then fn=assert(loadstring(helper_source)); setfenv(fn,env)
else fn=assert(load(helper_source,"course","t",env)) end
local c=fn(); local rows={row("TF","",0,20),row("FD","036T",90,91)}
values.legs_data={original=true}; values.legs_num=99; values.offset=9
values.navaid_list={original=true}; values.navaid_list_n=5; values.temp_nav_sort={old=true}
values.find_lat=44; values.find_lon=55; values.offset_mod=2; values.offset_mod2=3
values.ref_icao_lat=11; values.ref_icao_lon=12; values.des_icao_lat=13; values.des_icao_lon=14
values.ref_icao_lat_x=21; values.ref_icao_lon_x=22; values.des_icao_lat_x=23; values.des_icao_lon_x=24
values.ref_icao_lat7=31; values.ref_icao_lon7=32; values.des_icao_lat7=33; values.des_icao_lon7=34
values.ref_icao_lat7_x=41; values.ref_icao_lon7_x=42; values.des_icao_lat7_x=43; values.des_icao_lon7_x=44
local old={}; for k,v in pairs(values) do old[k]=v end
values.find_navaid2=function(id,empty,mode,region,ndb,rte)
 assert(env.legs_data==rows and env.legs_num==1 and env.offset==9)
 assert(mode==11 and ndb==1 and rte==0 and env.ref_icao_lat_x==11)
 env.navaid_list={{2,30,40}}; env.navaid_list_n=1; env.temp_nav_sort={}; env.find_lat=-100
end
near(c.mag(rows,1,2,0,true),66) -- 36 TRUE + variation30 at resolved start, not endpoint90.
for k,v in pairs(old) do assert(values[k]==v,"namespace leak: "..k) end
values.find_navaid2=function() env.legs_data={bad=true}; env.navaid_list={}; error("lookup failure") end
local ok,err=pcall(c.mag,rows,1,2,0,true); assert(not ok and tostring(err):find("lookup failure"))
for k,v in pairs(old) do assert(values[k]==v,"error-path leak: "..k) end
'''
        self.run_lua(code)

    TRANSPORT=r'''
function reset_packet()
 reset_route("VI","036T"); FMC_MAX_WPT=512
 ffirst_time2=1; calc_rte_enable=0; calc_rte_enable2=0; calc_rte_enable8=0
 legs_delete=0; legs_intdir=0; hold_exec=0; rte_exec=0; hold_exec2=0; rte_exec2=0
 B738DR_fms_legs_lat={[0]=10,[1]=20,[2]=30}; B738DR_fms_legs_lon={[0]=20,[1]=21,[2]=22}
 B738DR_fms_legs_crs_mag={}; B738DR_fms_legs_brg_mag={}
 B738DR_fms_legs_dist_dest_t={}; B738DR_fms_legs_dist_t={}
 B738DR_fms_add_data_num=0; B738DR_fms_add_cmd=0
 B738DR_fms_add_data_1={}; B738DR_fms_add_data_2={}; B738DR_fms_add_data_3={}
 B738DR_fms_add_data_4={}; B738DR_fms_add_data_5={}; B738DR_fms_add_data_6={}
 B738_ifix_vi.begin(); for i=1,3 do B738_ifix_vi.stage(i,legs_data[i]) end; B738_ifix_vi.commit()
end
function packet(index,lat)
 B738DR_fms_add_data_num=1
 B738DR_fms_add_data_1[0]=index; B738DR_fms_add_data_2[0]=lat; B738DR_fms_add_data_3[0]=25
 B738DR_fms_add_data_4[0]=0.5; B738DR_fms_add_data_5[0]=4; B738DR_fms_add_data_6[0]=9
 B738DR_fms_add_cmd=1; fms_add_cmd_handler()
end
function copy_to_legsdata2(rte) copied=(copied or 0)+1 end
'''

    def transport_code(self):
        return self.PRELUDE+asset(self.source,'course')+asset(self.source,'vi')+base.function_text(self.source,'fms_add_cmd_handler')+'\n'+base.function_text(self.source,'fms_add_count_handler')+'\n'+base.function_text(self.source,'B738_read_calc_data')+'\n'+self.TRANSPORT

    def test_native_ack_old_intent_and_busy_geometry_rejection(self):
        self.run_lua(self.transport_code()+r'''
reset_packet(); packet(2,40)
near(B738DR_fms_legs_crs_mag[1],56); near(B738DR_fms_legs_brg_mag[1],math.rad(56))
assert(B738DR_fms_add_cmd==0 and B738DR_fms_add_data_num==1)
B738_read_calc_data(); near(legs_data[2][7],40); near(math.deg(legs_data[2][18]),46)
assert(B738DR_fms_add_data_num==0); local n=copied; B738_read_calc_data(); assert(copied==n)
reset_packet(); B738_ifix_vi.retire(); legs_data[2][29]="0900"; B738DR_fms_legs_lat[1]=30
packet(2,40); near(B738DR_fms_legs_crs_mag[1],66)
assert(B738DR_fms_add_data_num==0); near(legs_data[2][7],11)
reset_packet(); calc_rte_enable2=1; packet(2,40)
near(B738DR_fms_legs_crs_mag[1],56); assert(B738DR_fms_add_data_num==0)
reset_packet(); B738DR_fms_add_data_num=1; fms_add_count_handler()
assert(B738DR_fms_add_data_num==1 and B738DR_fms_legs_crs_mag[1]==nil,"count notified before arrays")
''')

    def test_feedback_predecessor_only_order_and_nonvi_adoption(self):
        self.run_lua(self.transport_code()+r'''
reset_packet(); packet(1,30); B738_read_calc_data()
near(math.deg(legs_data[2][18]),66) -- VI absent from packet, predecessor moved.
reset_packet(); packet(2,40); B738DR_fms_add_data_num=2
B738DR_fms_add_data_1[1]=1; B738DR_fms_add_data_2[1]=30; B738DR_fms_add_data_3[1]=25
B738DR_fms_add_data_4[1]=0.5; B738DR_fms_add_data_5[1]=4; B738DR_fms_add_data_6[1]=9
B738_read_calc_data(); near(math.deg(legs_data[2][18]),66) -- successor before predecessor.
for _,bad in ipairs({0,1.5,512,0/0,math.huge}) do
 reset_packet(); packet(bad,40); assert(B738DR_fms_add_data_num==0); near(legs_data[2][7],11)
end
for _,bad in ipairs({129,1.5,0/0,math.huge}) do
 reset_packet(); B738DR_fms_add_data_num=bad; B738DR_fms_add_cmd=1; fms_add_cmd_handler()
 assert(B738DR_fms_add_data_num==0)
end
reset_packet(); packet(2,40); B738DR_fms_add_data_2[0]=0/0; B738_read_calc_data()
near(legs_data[2][7],11); assert(B738DR_fms_add_data_num==0)
reset_packet(); legs_data[2][31]="CF"; B738_ifix_vi.begin()
for i=1,3 do B738_ifix_vi.stage(i,legs_data[i]) end; B738_ifix_vi.commit()
packet(2,40); B738_read_calc_data(); near(legs_data[2][18],9); near(legs_data[2][37],0.5)
''')

    def test_ground_first_leg_boundary_and_phase_zero_refresh(self):
        ground=base.function_text(self.source,'lnav_prior')+'\n'+base.function_text(self.source,'B738_ifix_vi.ensure_lnav_wrapper')
        self.run_lua(self.PRELUDE+asset(self.source,'course')+asset(self.source,'vi')+r'''
function wrap_command(name,before,after) assert(name=="laminar/B738/autopilot/lnav_press"); before_lnav=before end
function XLuaFindCommand(name) return name end
function find_ref_rnw_data(mode,rte) assert(mode==0 and rte==0); ref_runway_lenght=1000; ref_runway_crs=0; ref_runway_old_name="01" end
'''+ground+r'''
B738_ifix_vi.ensure_lnav_wrapper()
reset_route("VI","0360"); legs_num=3; offset=2; ref_icao="LGSK"; ref_rwy="01 "
legs_data={row("TF","",0,20),row("TF","",0,20),row("VI","0000",0,0),row("TF","",0,0)}
legs_data[1][1]="LGSK"; legs_data[2][1]="RW01"
simDR_on_ground={[0]=1,[1]=0,[2]=0}; idx_rnw={[76]={[99999]=1,[1]=1}}
rnw_data={{"LGSK","01",0,20,0.01,20,1000,0}}
calc_rte_enable2=1
for _,path in ipairs({"VA","VD","VI","VM","VR"}) do
 legs_data[3][31]=path
 for _,p in ipairs({{"0050",1},{"3550",1},{"0051",0},{"3549",0},{"0000",1},{"005T",1}}) do
  legs_data[3][29]=p[1]; legs_data[3][2]=math.rad(180); lnav_prior(); assert(B738DR_lnav_prior_arm==p[2])
 end
end
rnw_data[1][3]=10; rnw_data[1][5]=10.01; legs_data[3][31]="VI"
for _,p in ipairs({{"0100",1},{"0150",1},{"0151",0},{"0000",0},{"000T",1},{"005T",1},{"006T",0}}) do
 legs_data[3][29]=p[1]; lnav_prior(); assert(B738DR_lnav_prior_arm==p[2],"ground reference: "..p[1])
end
rnw_data[1][3]=0; rnw_data[1][5]=0.01
legs_data[3][31]="VI"; legs_data[3][29]="0000"; B738DR_lnav_prior_arm=0
before_lnav(0,0); assert(B738DR_lnav_prior_arm==1)
legs_data[3][29]=""; lnav_prior(); assert(B738DR_lnav_prior_arm==0)
legs_data[3][31]="TF"; legs_data[3][2]=math.rad(8); legs_data[4][31]="VI"; legs_data[4][29]="0000"
lnav_prior(); assert(B738DR_lnav_prior_arm==0,"skipped literal first leg")
legs_data[3][31]="VI"; legs_data[3][29]="0000"; rnw_data[1][5]=0
lnav_prior(); assert(B738DR_lnav_prior_arm==0,"invented runway geometry")
''')

    def test_command_registration_waits_and_runs_once(self):
        ensure=base.function_text(self.source,'B738_ifix_vi.ensure_lnav_wrapper')
        self.run_lua(asset(self.source,'course')+asset(self.source,'vi')+r'''
local available=false
local wraps, queries, refreshes=0,0,0
function XLuaFindCommand(name) queries=queries+1; return available and name or nil end
function lnav_prior() refreshes=refreshes+1 end
function wrap_command(name,before,after)
 assert(available); wraps=wraps+1; before_lnav=before; after_lnav=after
end
'''+ensure+r'''
for i=1,5 do B738_ifix_vi.ensure_lnav_wrapper() end
assert(wraps==0 and queries==5)
available=true; B738_ifix_vi.ensure_lnav_wrapper()
assert(wraps==1 and queries==6)
for i=1,10 do B738_ifix_vi.ensure_lnav_wrapper() end
assert(wraps==1 and queries==6)
before_lnav(1,0); before_lnav(2,0); after_lnav(0,0); assert(refreshes==0)
before_lnav(0,0); assert(refreshes==1)
-- Alternate lookup API, and genuine registration errors are not swallowed/latching success.
B738_ifix_vi.lnav_wrapped=false
XPLMFindCommand=XLuaFindCommand; XLuaFindCommand=nil
function wrap_command(...) error("registration failed") end
local ok,err=pcall(B738_ifix_vi.ensure_lnav_wrapper)
assert(not ok and err:find("registration failed",1,true)); assert(not B738_ifix_vi.lnav_wrapped)
''')

    def test_exact_payload_reapplication_and_wiring(self):
        import z_Install
        manifest=json.loads((base.ROOT/'standalone-manifest.json').read_text())
        output=z_Install.compose(base.BASELINE.read_bytes(),manifest)
        again=output
        for p in manifest['payloads']:
            again=z_Install.apply_exact_replacements(again,json.loads((base.ROOT/p['path']).read_bytes()))
        self.assertEqual(output,again)
        self.assertEqual(5,len(re.findall(r'radius_num = B738_ifix_course.native\(',self.source)))
        for f in ('B738_fmc1_exec_CMDhandler','B738_fmc2_exec_CMDhandler','vnav_baro_comp_calc','vnav_baro_comp_rst','B738_calc_rte','copy_to_legsdata2'):
            self.assertIn('B738_ifix_vi.retire()',base.function_text(self.source,f))
        callback=base.function_text(self.source,'after_physics')
        self.assertLess(callback.index('B738_ifix_vi.commit()'),callback.index('B738DR_fms_test1 = 103'))


if __name__=='__main__':unittest.main()
