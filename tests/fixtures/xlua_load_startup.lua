-- Offline lifecycle probe: real XLua-1 init.lua, bounded XPLM bindings.
-- No simulator, plugin binary, navigation replay, or aircraft file writes.
local refs, types, arrays = {}, {
    ['sim/aircraft/view/acf_relative_path']='string',
    ['zibomod/Aircraft_Path']='string', ['zibomod/Xplane_Path']='string'
}, {}
local f=assert(io.open(arg[2], 'rb')); local source=f:read('*a'); f:close()
for variable in source:gmatch('([%w_]+)%s*%[') do arrays[variable]=true end
for variable,name in source:gmatch('([%w_]+)%s*=%s*find_dataref%s*%(%s*"([^"]+)"') do
    if arrays[variable] then types[name]='array[1024]' end
end
local frame, lookup_count, wrappers = 0, 0, 0
local command='laminar/B738/autopilot/lnav_press'
local available = arg[3]=='present'
local function lookup(name)
    if name==command then lookup_count=lookup_count+1; return available and name or nil end
    return name
end
function XLuaFindCommand(name) return lookup(name) end
function XLuaFindDataRef(name)
    if not refs[name] then refs[name]={name=name, value=0, kind=types[name] or 'number', a={}} end
    return refs[name]
end
function XLuaCreateDataRef(name,kind,writable,callback)
    local d=XLuaFindDataRef(name); d.kind=kind; d.callback=callback; return d
end
function XLuaGetDataRefType(d) return d.kind end
function XLuaGetNumber(d) return d.value end
-- XLua's own-dataref Lua writes update storage without firing the external notifier.
function XLuaSetNumber(d,v) d.value=v end
function XLuaGetString(d) return type(d.value)=='string' and d.value or '' end
function XLuaSetString(d,v) d.value=v end
function XLuaGetArray(d,k) return d.a[k] or 0 end
function XLuaSetArray(d,k,v) d.a[k]=v end
function XLuaCreateCommand(name,desc) return name end
function XLuaReplaceCommand(...) end
function XLuaWrapCommand(cmd,pre,post)
    assert(cmd~=nil,'expected command')
    if cmd==command then
        assert(available, 'registered unavailable native command')
        wrappers=wrappers+1
        assert(wrappers==1,'duplicate LNAV wrapper')
    end
end
function XLuaFilterCommand(...) end
function XLuaFindTimer(fn) return nil end
function XLuaCreateTimer(fn) return fn end
function XLuaRunTimer(...) end
function XLuaIsTimerScheduled(...) return false end
function XLuaGetCode(name)
    assert(arg[4]~='', 'Companion directory required')
    return loadfile(arg[4]..'/'..assert(name:match('[^/]+$')))
end
function XLuaGetAircraftPath() return '/nonexistent/' end
XLuaMajorVersion=1
assert(loadfile(arg[1]))()
local chunk=assert(loadfile(arg[2]))
-- XLua-2 uses a native namespace; this case tests only the alternate lookup API.
-- Keep the real XLua-1 namespace and bridge internally; do not call this an XLua-2 runtime test.
local saved_open=io.open
io.open=function(path,mode)
    if mode and mode:match('[wa+]') then
        -- A sink for unrelated cache/settings writes, never a real file handle.
        return {write=function(self,...) return self end, close=function() return true end}
    end
    return nil, 'No aircraft filesystem in lifecycle probe'
end
if arg[6]=='expect-early-failure' then
    local ok,err=pcall(run_module_in_namespace,chunk)
    assert(not ok and tostring(err):find('expected command',1,true), tostring(err))
    assert(n.flight_start==nil, 'failed script unexpectedly registered flight_start')
    print('PASS negative control: early wrapper aborts FMS load')
    return
end
run_module_in_namespace(chunk)
assert(wrappers==0,'registered wrapper during script load')
if arg[5]=='xplm-lookup' then
    -- Hide only the script-facing API. Original init.lua still uses its native
    -- XLuaFindCommand internally, as required by its own XLua-1 implementation.
    n.XLuaFindCommand=false
    n.XPLMFindCommand=lookup
end
-- Navigation cache generation needs real airport/scenery data and is outside
-- this startup-order check. Leave flight_start/after_physics themselves intact.
n.detect_apt_dat=function() end
n.SIM_PERIOD=1/60; n.IN_REPLAY=0
if arg[3]=='flight-start' then available=true end
do_callout('flight_start')
local frozen_lookups
for i=1,6 do
    frame=i
    if arg[3]=='late' and i==3 then available=true end
    do_callout('after_physics')
    assert(n.B738DR_fms_test1==44, 'FMS did not complete frame '..i)
    assert(wrappers==(available and 1 or 0),'wrong registration state at frame '..i)
    if wrappers==1 then
        if frozen_lookups then assert(lookup_count==frozen_lookups,'lookup continued after registration') end
        frozen_lookups=lookup_count
    end
end
-- Re-entering flight_start must not install the same wrapper twice.
do_callout('flight_start')
assert(wrappers==(available and 1 or 0),'duplicate wrapper after flight restart')
io.open=saved_open
print('PASS startup mode='..arg[3]..' wrappers='..wrappers..' frames=6 status=44')
