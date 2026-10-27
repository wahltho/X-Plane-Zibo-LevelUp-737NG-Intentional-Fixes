"""Refresh candidate metadata from exact payload bytes; no release or aircraft write."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('installer',ROOT/'z_Install.py')
installer=importlib.util.module_from_spec(spec); spec.loader.exec_module(installer)
plan=json.loads((ROOT/'package-plan.json').read_text())
if not any(f['ids']==['I40'] for f in plan['families']):
    plan['families'].append({'ids':['I40'],'mode':'payload','path':'src/fixes/i40-vi-heading-and-ground-lnav.json'})
plan['summary'].update(fixFamilies=22,familiesWithLuaDelta=20,payloadDocuments=19)
(ROOT/'package-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
manifest=json.loads((ROOT/'standalone-manifest.json').read_text())
manifest['packageVersion']='0.1.3'
if 'I40' not in manifest['includedFamilies']: manifest['includedFamilies'].append('I40')
manifest['payloads']=[]
source=Path('/Users/wahltho/dev/Zibo Mod/Original/Zibo Mod Original/B738X_XP12_4_05_35')/manifest['target']['relativePath']
result=source.read_bytes()
for f in plan['families']:
    if 'path' not in f or f['mode']=='conditional-payload':continue
    data=(ROOT/f['path']).read_bytes()
    manifest['payloads'].append({'path':f['path'],'size':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    result=installer.apply_exact_replacements(result,json.loads(data))
manifest['target']['resultSha256']=hashlib.sha256(result).hexdigest()
(ROOT/'standalone-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
builder=ROOT/'tools/build_mtk_package.py'
builder.write_text(builder.read_text().replace('VERSION = "0.1.2"','VERSION = "0.1.3"'))
spec=importlib.util.spec_from_file_location('mtk_builder',builder)
mtk=importlib.util.module_from_spec(spec); spec.loader.exec_module(mtk)
(ROOT/'package-manifest.json').write_bytes(mtk.package_files()['package-manifest.json'])
policy_path=ROOT/'standalone-ownership.json'; policy=json.loads(policy_path.read_text())
for marker in ('-- BEGIN CUSTOM I02 typed prescribed courses','-- BEGIN CUSTOM I40 VI source publication lifetime'):
    signature={'relativePath':manifest['target']['relativePath'],'text':marker}
    if signature not in policy['policy']['signatures']: policy['policy']['signatures'].append(signature)
policy_path.write_text(json.dumps(policy,indent=2)+'\n')
print('Candidate 0.1.3 composed SHA256:',manifest['target']['resultSha256'])
if len(sys.argv)>1:
    Path(sys.argv[1]).write_bytes(result)
