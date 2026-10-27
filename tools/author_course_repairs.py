#!/usr/bin/env python3
"""Author bounded I02/I04/I40 exact replacements from the pinned .35 reference.

This does not write an aircraft or a release. Lua authoring assets are injected
into the existing FMS script; they are not extra XLua modules at installation.
"""
from __future__ import annotations
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE = Path('/Users/wahltho/dev/Zibo Mod/Original/Zibo Mod Original/B738X_XP12_4_05_35/plugins/xlua/scripts/B738.a_fms/B738.a_fms.lua')
PIN = 'ff313b0e88c62845ad1c4a2b1f4bd599f57d8799e8d6707bfc10a3369fd63a8e'
PUBLISHED = '5555ba6ef8c35be6e6bef549316521a9d19efaeb'
C = 'B738_ifix_course'
V = 'B738_ifix_vi'

def published(name):
    return json.loads(subprocess.check_output(['git','show',PUBLISHED+':src/fixes/'+name],cwd=ROOT))

def apply(text, document):
    lines=text.split('\n')
    for item in document['replacements']:
        old,new=item['oldLines'],item['newLines']
        matches=[i for i in range(len(lines)-len(old)+1) if lines[i:i+len(old)]==old]
        if len(matches)!=1: raise ValueError(item['name']+' old matches '+str(len(matches)))
        i=matches[0]; lines[i:i+len(old)]=new
    return '\n'.join(lines)

def surface(text, name):
    a = text.index('function '+name+'(')
    match = re.search(r'\nfunction ',text[a+1:])
    b = a+1+match.start() if match else len(text)
    return a,b,text[a:b]

def edit_function(text,name,edit):
    a,b,old = surface(text,name)
    return text[:a]+edit(old)+text[b:]

def once(text,old,new):
    if text.count(old)!=1: raise ValueError('Expected one anchor: '+repr(old[:100])+' got '+str(text.count(old)))
    return text.replace(old,new,1)

def payload(old,new,family):
    with tempfile.TemporaryDirectory(prefix='ifix-author-') as scratch:
        a,b=Path(scratch)/'old',Path(scratch)/'new'
        a.write_text(old); b.write_text(new)
        diff=subprocess.run(['git','diff','--no-index','--patience','--no-color','--unified=0',str(a),str(b)],capture_output=True,text=True)
        if diff.returncode not in (0,1): raise ValueError(diff.stderr)
        groups=[]
        for line in diff.stdout.splitlines():
            m=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',line)
            if not m: continue
            i,n,j,k=[int(x) if x is not None else 1 for x in m.groups()]
            i=i-1 if n else i; j=j-1 if k else j
            groups.append([i,i+n,j,j+k,3])
        left,right=old.split('\n'),new.split('\n')
        def bounds(g):
            i,j,k,l,r=g
            # W&B annotates flight_start's declaration and both W&B/27K add
            # private entry resets. Retire before the first original writes.
            if i==j and left[i:i+2]==['\tsimDR_latitude = simDR_latitude0','\tsimDR_longitude = simDR_longitude0']:
                return i,j+2,k,l+2
            # Entry hooks are anchored to the function declaration alone.
            # Earlier modules may legitimately insert their own entry code.
            if i==j and i>0 and left[i-1].startswith('function '):
                return i-1,j,k-1,l
            before=min(r,i,k); after=min(r,len(left)-j,len(right)-l)
            return i-before,j+after,k-before,l+after
        # Widen only an ambiguous hunk. A single repeated assignment must not
        # pull hundreds of unrelated companion-patch lines into every anchor.
        for attempt in range(32):
            merged=[]
            for g in groups:
                if merged:
                    p=merged[-1]; x=bounds(p); y=bounds(g)
                    if x[1]>=y[0] or x[3]>=y[2]:
                        merged[-1]=[p[0],g[1],p[2],g[3],max(p[4],g[4])]
                        continue
                merged.append(g)
            if len(merged)!=len(groups): groups=merged; continue
            result=[]; ambiguous=False
            for g in groups:
                i,j,k,l=bounds(g); before=left[i:j]; after=right[k:l]
                unique=before and after and ('\n'+old+'\n').count('\n'+'\n'.join(before)+'\n')==1 and ('\n'+new+'\n').count('\n'+'\n'.join(after)+'\n')==1
                if not unique:
                    g[4]*=2; ambiguous=True
                result.append({'name':family+' '+str(len(result)+1),'oldLines':before,'newLines':after})
            if ambiguous: continue
            doc={'format':'exact-text-replacements-v1','replacements':result}
            if apply(old,doc)!=new: raise ValueError('Diff did not reconstruct '+family)
            sys.path.insert(0,str(ROOT))
            import z_Install
            if z_Install.apply_exact_replacements(old.encode(),doc).decode()!=new:
                raise ValueError('Exact handler did not reconstruct '+family)
            return doc
    raise ValueError('No unique bounded diff for '+family)

def save(name,doc):
    (ROOT/'src/fixes'/name).write_text(json.dumps(doc,indent=2,ensure_ascii=False)+'\n')

def refinements(before, after, documents):
    """Keep earlier installed-block signatures valid after co-owned I40 edits.

    A later exact replacement must not cut up an earlier payload's installed
    block: otherwise managed reapplication would fail. Transfer those specific
    refinements to the existing owner; I40 retains all other additions.
    """
    old,new=before.split('\n'),after.split('\n')
    # Only changed owning functions enter SequenceMatcher; unchanged spans are anchors.
    names=re.compile(r'^function ([\w.]+)\(',re.M)
    anchors=[(m.start(),m.group(1)) for m in names.finditer(before)]
    ops=[]
    # Git's small hunks avoid a quadratic match over the complete original script.
    with tempfile.TemporaryDirectory(prefix='ifix-owner-') as folder:
        a,b=Path(folder)/'old',Path(folder)/'new'; a.write_text(before); b.write_text(after)
        diff=subprocess.run(['git','diff','--no-index','--no-color','--unified=0',str(a),str(b)],capture_output=True,text=True)
        for line in diff.stdout.splitlines():
            m=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',line)
            if not m:continue
            i,n,j,k=[int(x) if x is not None else 1 for x in m.groups()]
            i=i-1 if n else i; j=j-1 if k else j
            for tag,x,y,p,q in difflib.SequenceMatcher(None,old[i:i+n],new[j:j+k],autojunk=False).get_opcodes():
                if tag!='equal':ops.append((i+x,i+y,j+p,j+q))
    def boundary(x):
        delta=0
        for a,b,c,d in ops:
            if a==b:
                if a<x:delta+=d-c
            elif b<=x:delta+=(d-c)-(b-a)
            elif a<x<b:raise ValueError('Owner boundary bisects changed source at '+str(x))
        return x+delta
    for name,doc in documents:
        for r in doc['replacements']:
            block=r['newLines']; n=len(block)
            hits=[i for i in range(len(old)-n+1) if old[i:i+n]==block]
            if len(hits)!=1: raise ValueError('Existing owner is not unique: '+r['name'])
            a=hits[0]; b=a+n
            updated=new[boundary(a):boundary(b)]
            if updated!=block:
                r['newLines']=updated
                r['name']+='; I40 co-owned lifetime boundary'
        save(name,doc)

def decoder(original,legacy):
    # Retain I03's structural interceptor; replace all I02 unit/reference logic.
    start='\t-- (INTC) Course to Intercept -> CI/VI'
    end='\t-- (1000) -> CA/VA/FA'
    aa=original.index(start); bb=original.index(end,aa)
    x=legacy.index(start); y=legacy.index(end,x)
    branch=legacy[x:y]
    branch=re.sub(r'\blegs_num2\b','legs_num2_buf',branch)
    own_start=branch.index('\t\tif idx1 > 0 then\n\t\t\tcrs1 = tonumber(dec_brg)')
    own_end=branch.index('\t\t\tlocal crs3 = 0',own_start)
    oa=original.index('\t\tif idx1 > 0 then\n\t\t\tcrs1 = tonumber(dec_brg)',aa)
    ob=original.index('\t\t\tlocal crs3 = 0',oa)
    branch=branch[:own_start]+original[oa:ob]+branch[own_end:]
    # All borrowed sources retain explicit validity; unavailable is not north.
    for idx in ('idx_next1','idx_next2'):
        pattern=r'(?m)^(\t+)crs2, crs2_is_true = parse_course_value\(legs_data2_buf\['+idx+r'\]\[29\]\).*?\n(?=\t+else\n|\t+elseif )'
        # The precise course-to-TRUE block ends at dec_next_brg, not a nested else.
        pattern=r'(?m)^(\t+)crs2, crs2_is_true = parse_course_value\(legs_data2_buf\['+idx+r'\]\[29\]\)[^\n]*\n[\s\S]*?^\1dec_next_brg = [^\n]+\n'
        def borrowed(m):
            t=m[1]
            return (t+f'crs2 = {C}.borrow(legs_data2_buf[{idx}], lat1, lon1, vor_declination) -- FIX: typed successor\n'+
                t+'if crs2 ~= nil then\n'+t+'\tif dec_path == "VI" then idx1 = 2 else idx1 = 3 end\n'+
                t+'\tdec_next_brg = (crs2 + 180) % 360\n'+t+'end\n')
        branch,n=re.subn(pattern,borrowed,branch)
        if n!=1: raise ValueError('borrow '+idx+' '+str(n))
    branch=branch.replace('if dist > 360 then dist = dist / 10 end\t-- FIX: only scale if stored in 1/10 units','dist = dist / 10 -- FIX: AF radius/distance is always tenths NM')
    branch=branch.replace('if crs1 ~= 0 then','if crs1 ~= nil then')
    branch=branch.replace('parse_course_value(',C+'.read(')
    # No arithmetic on missing borrowed operands. Preserve geometry admission.
    branch=branch.replace('if crs1_is_true then','if crs1 == nil then\n\t\t\t\t\tidx1 = 0\n\t\t\t\telseif crs1_is_true then')
    branch=branch.replace('if not crs1_is_true then','if crs1 ~= nil and not crs1_is_true then')
    # AF tangent branch cannot construct a point without its source angle.
    branch=branch.replace('calc_brg_dist(lat3, lon3, math.rad(crs1), dist)\n\t\t\t\t\tlat2',
        'if crs1 == nil then return end\n\t\t\t\t\tcalc_brg_dist(lat3, lon3, math.rad(crs1), dist)\n\t\t\t\t\tlat2')
    original=original[:aa]+branch+original[bb:]
    original=original.replace('local ndb_navaid = 1','local ndb_navaid = 0',1)
    original=once(original,'\tdec_brg = legs_data2_buf[dec_idx][29]',
        '\tdec_brg = legs_data2_buf[dec_idx][29]\n'+
        f'\tlocal own_h, own_t = {C}.read(dec_brg, legs_data2_buf[dec_idx][31])\n'+
        f'\tif {C}.command(legs_data2_buf[dec_idx][31]) and own_h == nil then return end -- FIX: missing is not north')
    # Restore all eleven own course parsing groups, with exactly one unit decode.
    pattern=r'(?m)^(\t+)crs1 = tonumber\(dec_brg\)\n\1if crs1 == nil then\n\1\tcrs1 = 0\n\1else\n\1\tcrs1 = crs1 / 10\n\1end'
    original,n=re.subn(pattern,lambda m:m[1]+'crs1 = own_h -- FIX: declared raw units, no magnitude heuristic',original)
    if n!=11: raise ValueError('own groups '+str(n))
    original=original.replace('dec_calc_brg = crs1',f'dec_calc_brg = {C}.project(own_h, own_t, false, dec_prev_lat, dec_prev_lon)')
    original=original.replace('(crs1 - mag_variation_deg(dec_prev_lat, dec_prev_lon) + 360) % 360',f'{C}.project(own_h, own_t, true, dec_prev_lat, dec_prev_lon)')
    # Same scoped source-datum resolver in decoder and later consumers.
    for path, marker in [('FD','\t\tlocal tmp_lat'),('FC','\t\t-- if string.sub'),('FM','\t\t-- if string.sub')]:
        p=original.index('elseif dec_path == "'+path+'" then')
        a=original.index(marker,p); b=original.index('\t\tcrs1 = own_h',a)
        prefix='\t\tlocal tmp_lat = dec_prev_lat\n\t\tlocal tmp_lon = dec_prev_lon\n' if path=='FD' else ''
        replacement=prefix+f'\t\tdec_prev_lat, dec_prev_lon, dec_find_type, find_from, ndb_navaid = {C}.start(legs_data2_buf, legs_num2_buf, dec_idx, in_rte, false)\n\t\t\n'
        original=original[:a]+replacement+original[b:]
    # PI keeps its original MAG comparison policy; TRUE never gains variation.
    original=original.replace('crs1 = (crs1 + mag_variation_deg(dec_calc_lat, dec_calc_lon) + 360) % 360',
        'if not own_t then crs1 = (crs1 + mag_variation_deg(dec_calc_lat, dec_calc_lon) + 360) % 360 end')
    # HOLD's valid course is not canonicalized destructively; preserve time length.
    a=original.index('\telseif dec_path == "HA" or dec_path == "HF" or dec_path == "HM" then')
    b=original.index('\n\t-- save decoded data',a)
    original=original[:a]+'''\telseif dec_path == "HA" or dec_path == "HF" or dec_path == "HM" then
\t\tdec_calc_brg = B738_ifix_course.project(own_h, own_t, false, dec_calc_lat, dec_calc_lon)
\t\tB738_ifix_course.hold_default(legs_data2_buf[dec_idx])
\t\tdec_find_type = 4
\tend
\t''' + original[b:]
    # Reacquire PI projection after resolution; the geometry comparison remains separate.
    original=original.replace('\t-- save decoded data',
        '\tif dec_path == "PI" then\n\t\tdec_calc_brg = B738_ifix_course.project(own_h, own_t, false, dec_calc_lat, dec_calc_lon)\n\tend\n\t-- save decoded data')
    original=original.replace('legs_data2_buf[dec_idx][18] = math.rad(dec_calc_brg)',
        'if dec_calc_brg ~= nil then legs_data2_buf[dec_idx][18] = math.rad(dec_calc_brg) end -- FIX: no unavailable-to-north write')
    # Predecessor source reads are separate from its MAG-radian private cache.
    pattern=r'(?m)^(\t+)crs3, crs3_is_true = B738_ifix_course.read\(legs_data2_buf\[dec_idx-1\]\[29\]\)[^\n]*\n[\s\S]*?^\1end'
    original,n=re.subn(pattern,lambda m:m[1]+f'crs3 = {C}.borrow(legs_data2_buf[dec_idx-1], dec_prev_lat, dec_prev_lon)\n'+m[1]+'if crs3 ~= nil then dec_prev_crs = math.rad(crs3) end',original)
    if n!=2: raise ValueError('predecessor '+str(n))
    # Missing borrowed FM/FA course cannot retain the unconditional idx1=5.
    original=original.replace('idx1 = 5\n', 'if crs1 ~= nil then idx1 = 5 end\n')
    original=original.replace('local crs1 = 0', 'local crs1 = 0\n\tlocal crs1_is_true = false\n\tlocal crs2_is_true = false',1)
    # Every repaired arithmetic projection has explicit unavailable admission.
    original=re.sub(r'(?m)^(\t+)(dec_calc_brg|crs1) = (B738_ifix_course.project\([^\n]+\))$',
        lambda m:m[0]+'\n'+m[1]+'if '+m[2]+' == nil then return end',original)
    a=original.index('\telseif dec_path == "PI" then'); b=original.index('\t-- HOLD',a)
    pi=original[a:b].replace('\t\tdec_calc_brg = B738_ifix_course.project(own_h, own_t, false, dec_prev_lat, dec_prev_lon)\n\t\tif dec_calc_brg == nil then return end',
        '\t\t-- FIX: own PI projection follows resolved fix, never the predecessor datum.')
    original=original[:a]+pi+original[b:]
    original=once(original, '\t-- actual wpt', '\tdec_find_type = 0 -- FIX: no stale result on unavailable course\n\t-- actual wpt')
    original=once(original,'\tcopy_to_legs_data2_buf(in_rte)',
        '\tif dec_idx < 2 then dec_find_type = 0; return end -- FIX: I03 first-leg boundary\n\tcopy_to_legs_data2_buf(in_rte)')
    # FD's following DME lookup intentionally uses the pre-resolution predecessor.
    a=original.index('\telseif dec_path == "FD" then'); b=original.index('\telseif dec_path == "CD"',a)
    fd=original[a:b]
    anchor='\t\tfind_navaid2(dec_rnavaid, "", find_from, dec_rnavaid_rc, ndb_navaid, in_rte)'
    fd=once(fd,anchor,'\t\tif find_from == 3 then find_lat, find_lon = tmp_lat, tmp_lon end -- FIX: second-query datum\n'+anchor)
    original=original[:a]+fd+original[b:]
    original=original.replace('if dec_calc_brg == nil then return end','if dec_calc_brg == nil then dec_find_type = 0; return end')
    original=original.replace('if crs1 == nil then return end','if crs1 == nil then dec_find_type = 0; return end')
    return original

def course_surfaces(text):
    # Five publisher pairs: native MAG datum differs from private decoder datum.
    for name,rows,count,rte,suffix in [('legs_fill','legs_data','legs_num','rte12_act',''),
        ('legs_fill2','legs_data2','legs_num2','0','_2'),('legs_fill2','legs_data8','legs_num8','1','_2'),
        ('legs_fill3','legs_data2','legs_num2','0','_3'),('legs_fill3','legs_data8','legs_num8','1','_3')]:
        def pub(s):
            pattern=r'(?m)^(\t+)radius_num = tonumber\('+rows+r'\[ii\]\[29\]\)\n[\s\S]*?^\1B738DR_fms_legs_crs_mag'+suffix+r'\[ii-1\] = radius_num'
            def repl(m):
                t=m[1]
                return t+f'radius_num = {C}.native({rows}[ii])\n'+t+f'if radius_num ~= nil then\n'+t+f'\tB738DR_fms_legs_crs_mag{suffix}[ii-1] = radius_num\n'+t+f'\tif {C}.command({rows}[ii][31]) then B738DR_fms_legs_brg_mag{suffix}[ii-1] = math.rad(radius_num) end\n'+t+'else\n'+t+f'\tB738DR_fms_legs_crs_mag{suffix}[ii-1] = 0 -- original ABI placeholder; not valid source\n'+t+'end'
            s,n=re.subn(pattern,repl,s)
            if n!=1: raise ValueError('publisher '+name+' '+rows+' '+str(n))
            return s
        text=edit_function(text,name,pub)
    # Legacy MAG views and TRUE readers explicitly consume the raw reference.
    for name,rte in [('B738_fmc_legs99','use_rte12_sel'),('B738_fmc_progress','use_rte12_act')]:
        def display(s):
            s=re.sub(r'math.deg\(legs_data2_buf\[([^\]]+)\]\[18\]\)',lambda m:f'{C}.mag(legs_data2_buf, legs_num2_buf, {m[1]}, {rte}, false)',s)
            s=s.replace('fms_trk_act = displ_crs(fms_trk_act)','fms_trk_act = fms_trk_act and displ_crs(fms_trk_act)')
            s=s.replace('string.format("%3d", fms_trk_act)','(fms_trk_act and string.format("%3d", fms_trk_act) or "   ")')
            s=s.replace('fms_trk_act = (fms_trk_act + 360) % 360','fms_trk_act = fms_trk_act and (fms_trk_act + 360) % 360')
            s=s.replace('sid_len = displ_crs(sid_len)', 'sid_len = sid_len and displ_crs(sid_len)')
            s=s.replace('string.format("%3d",sid_len)', f'{C}.format(sid_len, "%3d")')
            s=s.replace('string.format("%03d", fms_trk_act)', f'{C}.format(fms_trk_act, "%03d")')
            s=s.replace('string.format("%03d", displ_crs(fms_trk_act))','(fms_trk_act and string.format("%03d", displ_crs(fms_trk_act)) or "   ")')
            # Other numeric output uses of the next/course MAG view.
            s=re.sub(r'string.format\("(%0?3d)", displ_crs\((?:math.deg\()?legs_data2_buf\[([^\]]+)\]\[18\]\)?\)\)',lambda m:f'string.format("{m[1]}", displ_crs({C}.mag(legs_data2_buf, legs_num2_buf, {m[2]}, {rte}, false)))',s)
            return s
        text=edit_function(text,name,display)
    # Per-row command TRUE operands with the original aircraft MAG variation datum.
    for name in ['rte_add_wpt3','B738_fmc_calc']:
        def consumer(s):
            s=re.sub(r'(?m)^(\t+)(id_brg2|B738DR_fmc_trk) = \(\(?math.deg\((legs_data[28]?\[[^\]]+\])\[18\]\) - simDR_mag_variation\)? \+ 360\) % 360',
                lambda m: (m[1]+f'local course_true = {C}.true_air({m[3]})\n'+m[1]+'if course_true == nil then return end\n'+m[1]+'id_brg2 = course_true') if m[2]=='id_brg2' else
                    m[1]+f'local course_true = {C}.true_air({m[3]})\n'+m[1]+'if course_true ~= nil then B738DR_fmc_trk = course_true end',s)
            pattern=r'(?m)^(\t+)local radius_num = tonumber\(legs_data\[offset_seq\]\[29\]\)\n[\s\S]*?^\1B738DR_fmc_trk = [^\n]+'
            s=re.sub(pattern,lambda m:m[1]+f'local course_true = {C}.true_air(legs_data[offset_seq])\n'+m[1]+'if course_true ~= nil then B738DR_fmc_trk = course_true end -- FIX: preserve reference',s)
            return s
        text=edit_function(text,name,consumer)
    # VM/FM/HOLD track derivation keeps TRUE source independent of MAG private18.
    for name,rows in [('B738_calc_rte2','legs_data2'),('B738_calc_rte8','legs_data8')]:
        def route(s):
            pattern=r'(?m)^(\t+)('+rows+r'\[calc_rte_act[28]\])\[2\] = '+rows+r'\[calc_rte_act[28]\]\[18\] - mag_variation_rad\(math.rad\(lat_tmp\), math.rad\(lon_tmp\)\)'
            s,n=re.subn(pattern,lambda m:m[1]+f'local course_true = {C}.true_at({m[2]}, lat_tmp, lon_tmp)\n'+m[1]+f'if course_true ~= nil then {m[2]}[2] = math.rad(course_true) end -- FIX: preserve TRUE source',s)
            if n!=2: raise ValueError('route track '+name+' '+str(n))
            return s
        text=edit_function(text,name,route)
    def progress(s):
        s=s.replace('(math.deg(legs_data[prev_idx][18]) + 360) % 360', f'{C}.mag(legs_data, legs_num, prev_idx, rte12_act, true)')
        s=s.replace('if tmp_wpt_eta2 < 0 then','if tmp_wpt_eta2 and tmp_wpt_eta2 < 0 then')
        s=s.replace('string.format("%03d", tmp_wpt_eta2)',f'{C}.format(tmp_wpt_eta2, "%03d")')
        return s
    text=edit_function(text,'B738_fmc_progress',progress)
    return text

def mutation_hooks(text):
    # Instrument concrete LHS owners, retaining exactly-once RHS evaluation.
    # Reader-owned adoption and private scratch binding are deliberately exempt.
    names = r'(?:legs_num|rte12_act|ref_icao7?|ref_rwy7?|ref_icao_(?:lat|lon)(?:7)?)'
    lhs = r'(?:legs_data(?:\[[^\]\n]+\]){0,2}|'+names+r')'
    pattern = re.compile(r'^([ \t]*)('+lhs+r') = (.+)$')
    lines=[]; owner='chunk'; counts={}
    for line in text.splitlines():
        if line.startswith('function ') or line.startswith('local function '):
            owner=line.split('function ',1)[1].split('(',1)[0]
        m=pattern.match(line)
        if not m or owner=='chunk' or owner.startswith('B738_ifix_') or owner=='B738_read_calc_data':
            lines.append(line); continue
        t,target,value=m.groups()
        # Comment is retained; every matched assignment is a single complete expression.
        quote=None; escaped=False; split=None
        for pos,ch in enumerate(value):
            if quote:
                if escaped: escaped=False
                elif ch=='\\': escaped=True
                elif ch==quote: quote=None
            elif ch in ('"',"'"):quote=ch
            elif value[pos:pos+2]=='--':split=pos;break
        comment=value[split+2:] if split is not None else ''
        sep=split is not None
        value=value[:split] if sep else value
        value=value.rstrip()
        if not value or value.endswith(('and','or',',','+','-','*','/','..')):
            raise ValueError('Multiline ACT mutation needs explicit boundary: '+line)
        condition=target+' ~= ifix_value'
        if re.match(r'ref_(icao|rwy)',target):
            route=1 if target.endswith('7') else 0
            condition='rte12_act == '+str(route)+' and '+condition
        lines.extend([t+'do -- FIX: retire native packet before actual ACT mutation',
            t+'\tlocal ifix_value = '+value,
            t+'\tif '+condition+' then '+V+'.retire() end',
            t+'\t'+target+' = ifix_value'+(' --'+comment if sep else ''),t+'end'])
        counts[owner]=counts.get(owner,0)+1
    (ROOT/'src/vi-mutation-owners.json').write_text(json.dumps(counts,indent=2)+'\n')
    return '\n'.join(lines)+ ('\n' if text.endswith('\n') else '')

def vi_surfaces(text):
    text=once(text,'function fms_add_cmd_handler() end',
        (ROOT/'src/vi_publication.lua').read_text()+'\nfunction fms_add_cmd_handler() B738_ifix_vi.complete() end\nfunction fms_add_count_handler() end')
    text=once(text,'create_dataref("laminar/B738/fms/fms_add_data_num", "number", fms_add_cmd_handler)',
        'create_dataref("laminar/B738/fms/fms_add_data_num", "number", fms_add_count_handler)')
    def dec(s):
        a='\tdec_path = legs_data2_buf[dec_idx][31]'
        s=once(s,a,a+'\n\t-- FIX: VI command ownership does not require successor geometry.\n'+
            '\tif dec_path == "VI" then\n\t\tdec_calc_brg = B738_ifix_course.project(own_h, own_t, false, dec_prev_lat, dec_prev_lon)\n'+
            '\t\tif dec_calc_brg == nil then return end\n'+
            '\t\tlegs_data2_buf[dec_idx][18] = math.rad(dec_calc_brg)\n'+
            '\t\tif in_rte == 0 then legs_data2[dec_idx][18] = math.rad(dec_calc_brg)\n'+
            '\t\telse legs_data8[dec_idx][18] = math.rad(dec_calc_brg) end -- FIX: source-only save survives geometry exits\n\tend')
        return s
    text=edit_function(text,'dec_lat_lon2',dec)
    for name,rows,count,index in [('B738_calc_rte2','legs_data2','legs_num2','calc_rte_act2'),
        ('B738_calc_rte8','legs_data8','legs_num8','calc_rte_act8')]:
        def route(s):
            match=re.search(r'(?m)^\t+if \(?'+re.escape(rows+'['+index+'][7] == 0 and '+rows+'['+index+'][8] == 0'),s)
            if not match: raise ValueError('Route coordinate admission '+name)
            pos=match.start()
            s=s[:pos]+f'\t\t\t\t\t{C}.refresh_vi({rows}, {count}, {index}) -- FIX: before cached-coordinate admission\n'+s[pos:]
            if rows=='legs_data8':
                anchor='\t\t\t\t\t\t\t\t'+rows+'['+index+'][18] = 0\n\t\t\t\t\t\t\t\t'+rows+'['+index+'][3] = 0\t\t-- distance'
                s=once(s,anchor,'\t\t\t\t\t\t\t\tif '+rows+'['+index+'][31] ~= "VI" then '+rows+'['+index+'][18] = 0 end -- FIX: preserve VI command\n\t\t\t\t\t\t\t\t'+rows+'['+index+'][3] = 0\t\t-- distance')
            return s
        text=edit_function(text,name,route)
    text=edit_function(text,'B738_read_calc_data',lambda _:(ROOT/'src/vi_feedback.lua').read_text().rstrip()+'\n')
    # Refresh after coherent copies; never alter source29 or point validity.
    for name in ['copy_to_legsdata','copy_from_legs_data2_buf','load_fmc']:
        def copied(s):
            pos=s.rfind('\nend')
            refresh=f'\n\t{C}.refresh_vi(legs_data, legs_num)\n\t{C}.refresh_vi(legs_data2, legs_num2)\n\t{C}.refresh_vi(legs_data8, legs_num8)\n'
            if name=='load_fmc':return once(s,'\treturn error_loading',refresh+'\treturn error_loading')
            return s[:pos]+refresh+s[pos:]
        text=edit_function(text,name,copied)
    def publisher(s):
        s=s.replace('function legs_fill()','function legs_fill()\n\tB738_ifix_vi.begin()')
        a='\t\t\t\tnum_of_wpts = num_of_wpts + 1'
        return once(s,a,a+'\n\t\t\t\tB738_ifix_vi.stage(ii, legs_data[ii])')
    text=edit_function(text,'legs_fill',publisher)
    text=edit_function(text,'lnav_prior',lambda _:(ROOT/'src/ground_lnav.lua').read_text()+'\n')
    # Function-entry ordinary refresh is read-only: it never clears a geometry packet.
    def callback(s):
        s=once(s,'function after_physics()', 'function after_physics()\n\tlnav_prior() -- FIX: coherent ACT even while MOD is busy')
        s=s.replace('\t\tlnav_prior()','\t\t-- FIX: refreshed at callback entry and before LNAV press')
        return once(s,'\t\tB738DR_fms_test1 = 103', '\t\tB738_ifix_vi.commit() -- FIX: only an actual completed ACTIVE export\n\t\tB738DR_fms_test1 = 103')
    text=edit_function(text,'after_physics',callback)
    text=edit_function(text,'flight_start',lambda s:once(s,'\tsimDR_latitude = simDR_latitude0',
        '\tB738_ifix_vi.retire() -- FIX: private lifecycle retirement\n\tsimDR_latitude = simDR_latitude0'))
    for name in ['B738_init2','B738_init3','B738_init4','aircraft_unload']:
        text=edit_function(text,name,lambda s:s.replace(s.split('\n',1)[0],s.split('\n',1)[0]+'\n\tB738_ifix_vi.retire() -- FIX: private lifecycle retirement',1))
    return mutation_hooks(text)

def main():
    raw=BASE.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PIN: raise ValueError('Unknown .35 input')
    original=raw.decode('utf-8-sig').replace('\r\n','\n')
    legacy=apply(original,published('i02-i03-course-and-intercept.json'))
    dec=decoder(surface(original,'dec_lat_lon2')[2],surface(legacy,'dec_lat_lon2')[2])
    repaired=edit_function(original,'dec_lat_lon2',lambda _:dec)
    repaired=once(repaired,'function fms_add_cmd_handler() end',(ROOT/'src/course_reference.lua').read_text()+'\nfunction fms_add_cmd_handler() end')
    repaired=course_surfaces(repaired)
    save('i02-i03-course-and-intercept.json',payload(original,repaired,'I02/I03 typed course repair'))
    # Update only the existing I04 reader, preserving its other fourteen replacements.
    i04=published('i04-hold-course-defaults.json')
    for r in i04['replacements']:
        if r['name']=='I04 B738_fmc_hold block 1':
            lines='\n'.join(r['newLines'])
            a=lines.index('\t\t\tlocal hold_magvar')
            b=lines.index('\t\t\t\thold_radial_num =',a)
            lines=lines[:a]+'''\t\t\tlocal hold_row = legs_data2_buf[hold_offset_idx_act]
\t\t\tlocal hold_h, hold_t = B738_ifix_course.read(hold_row[29], hold_row[31])
\t\t\tlocal hold_magvar = mag_variation_deg(hold_row[7], hold_row[8])
\t\t\tlocal hold_show_true = hold_t or (B738_ifix_course.finite(hold_magvar) and math.abs(hold_magvar) > 20)
\t\t\tx_temp = hold_h
\t\t\tif x_temp ~= nil then
\t\t\t\tlocal disp_brg = x_temp
\t\t\t\tif hold_show_true then disp_brg = B738_ifix_course.true_at(hold_row, hold_row[7], hold_row[8]) end
\t\t\t\thold_inbd = string.format("%03d", displ_crs(disp_brg))
\t\t\t\tif hold_show_true then hold_inbd = hold_inbd .. "T" end
''' + lines[b:]
            r['newLines']=lines.split('\n')
    save('i04-hold-course-defaults.json',i04)
    composed=original; documents=[]
    plan=json.loads((ROOT/'package-plan.json').read_text())
    for family in plan['families']:
        if 'path' in family and family['mode']!='conditional-payload' and family['ids']!=['I40']:
            name=Path(family['path']).name
            document=json.loads((ROOT/family['path']).read_text()) if name.startswith(('i02-','i04-')) else published(name)
            documents.append((name,document))
            composed=apply(composed,document)
    vi=vi_surfaces(composed)
    refinements(composed,vi,documents)
    revised=original
    for name,doc in documents: revised=apply(revised,doc)
    save('i40-vi-heading-and-ground-lnav.json',payload(revised,vi,'I40 VI source and publication'))
    print('Authored separate I02/I04 repair and I40 VI owner payload')

if __name__=='__main__': main()
