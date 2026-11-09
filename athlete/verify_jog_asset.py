"""Compare the two actual GLBs to guard the scope of a locomotion rebake.

By default only Jog may change. `--changed` names the clips that may change
and `--added` the clips that may be new (the gait rebuild: --changed Jog
--added Run). Every other animation and every mesh attribute must be equal.
"""
import argparse
import hashlib
import json
from pathlib import Path
from verify_asset import read_glb,values

parser=argparse.ArgumentParser()
parser.add_argument('--before',type=Path,required=True)
parser.add_argument('--after',type=Path,required=True)
parser.add_argument('--report',type=Path,required=True)
parser.add_argument('--changed',action='append',default=None)
parser.add_argument('--added',action='append',default=[])
parser.add_argument('--reskinned',action='append',default=[],help='a mesh whose JOINTS_0/WEIGHTS_0 may change; every other attribute must not')
args=parser.parse_args()
changed=args.changed or ['Jog']
def read(path):
    doc,binary=read_glb(path)
    clips={}
    for action in doc['animations']:
        channels={}
        for channel in action['channels']:
            sampler=action['samplers'][channel['sampler']]
            key=(doc['nodes'][channel['target']['node']]['name'],channel['target']['path'])
            channels[key]=(sampler.get('interpolation','LINEAR'),values(doc,binary,sampler['input']),values(doc,binary,sampler['output']))
        clips[action['name']]=channels
    meshes={mesh['name']:[{name:values(doc,binary,index) for name,index in primitive['attributes'].items()} for primitive in mesh['primitives']] for mesh in doc['meshes']}
    return clips,meshes
before,mesh_before=read(args.before)
after,mesh_after=read(args.after)
assert set(after)-set(before)==set(args.added),('added',sorted(set(after)-set(before)))
assert set(before)<=set(after),('removed',sorted(set(before)-set(after)))
unchanged=[]
for name in before:
    if name in changed:continue
    assert before[name]==after[name],name+' changed outside the rebake'
    unchanged.append(name)
skin=('JOINTS_0','WEIGHTS_0')
assert mesh_before.keys()==mesh_after.keys(),'meshes added or removed'
reskinned=[]
for name in mesh_before:
    if name in args.reskinned:
        strip=lambda prims:[{k:v for k,v in p.items() if k not in skin} for p in prims]
        assert strip(mesh_before[name])==strip(mesh_after[name]),name+': geometry changed, not only its skin'
        assert mesh_before[name]!=mesh_after[name],name+': named as reskinned but unchanged'
        reskinned.append(name)
    else:
        assert mesh_before[name]==mesh_after[name],name+': vertex geometry or skin weights changed'
for name in changed:assert before[name]!=after[name],name+' did not change'
report={'before':hashlib.sha256(args.before.read_bytes()).hexdigest(),'after':hashlib.sha256(args.after.read_bytes()).hexdigest(),
        'unchangedAnimations':unchanged,'allMeshAttributesUnchanged':not reskinned,'reskinnedMeshes':reskinned,'geometryUnchanged':True,'changedAnimations':changed,'addedAnimations':args.added}
args.report.write_text(json.dumps(report,indent=2))
print(json.dumps(report))
