"""Compare the two actual GLBs to guard the scope of a locomotion rebake.

By default only Jog may change. `--changed` names the clips that may change
and `--added` the clips that may be new (the gait rebuild: --changed Jog
--added Run). `--reskinned` names a mesh whose skin (JOINTS_0, WEIGHTS_0)
may change; its other attributes, positions included, must not. Every other
animation and every other mesh attribute must be equal.

`compare()` holds the rules; tests/test_verify_jog_asset.py checks them on
synthetic data, so each relaxation is shown to refuse what it must refuse.
"""
import argparse
import hashlib
import json
from pathlib import Path

SKIN = ('JOINTS_0', 'WEIGHTS_0')


class ScopeError(AssertionError):
    pass


def compare(before, after, mesh_before, mesh_after, changed=('Jog',), added=(), reskinned=()):
    """Return (unchanged clips, reskinned meshes) or raise ScopeError."""
    changed, added, reskinned = list(changed), list(added), list(reskinned)
    if set(changed) & set(added):
        raise ScopeError(f'a clip cannot be both changed and added: {sorted(set(changed) & set(added))}')
    unknown_clips = [name for name in changed if name not in before]
    if unknown_clips:
        raise ScopeError(f'--changed names clips that are not in the before asset: {unknown_clips}')
    unknown_meshes = [name for name in reskinned if name not in mesh_before]
    if unknown_meshes:
        raise ScopeError(f'--reskinned names meshes that are not in the before asset: {unknown_meshes}')
    if set(after) - set(before) != set(added):
        raise ScopeError(f'added clips {sorted(set(after) - set(before))} differ from --added {sorted(added)}')
    if not set(before) <= set(after):
        raise ScopeError(f'removed clips: {sorted(set(before) - set(after))}')
    unchanged = []
    for name in before:
        if name in changed:
            continue
        if before[name] != after[name]:
            raise ScopeError(name + ' changed outside the rebake')
        unchanged.append(name)
    for name in changed:
        if before[name] == after[name]:
            raise ScopeError(name + ' did not change')
    if mesh_before.keys() != mesh_after.keys():
        raise ScopeError('meshes added or removed')
    strip = lambda prims: [{k: v for k, v in p.items() if k not in SKIN} for p in prims]
    for name in mesh_before:
        if name in reskinned:
            if strip(mesh_before[name]) != strip(mesh_after[name]):
                raise ScopeError(name + ': geometry changed, not only its skin')
            if mesh_before[name] == mesh_after[name]:
                raise ScopeError(name + ': named as reskinned but unchanged')
        elif mesh_before[name] != mesh_after[name]:
            raise ScopeError(name + ': vertex geometry or skin weights changed')
    return unchanged, reskinned


def read(path):
    from verify_asset import read_glb, values
    doc, binary = read_glb(path)
    clips = {}
    for action in doc['animations']:
        channels = {}
        for channel in action['channels']:
            sampler = action['samplers'][channel['sampler']]
            key = (doc['nodes'][channel['target']['node']]['name'], channel['target']['path'])
            channels[key] = (sampler.get('interpolation', 'LINEAR'), values(doc, binary, sampler['input']), values(doc, binary, sampler['output']))
        clips[action['name']] = channels
    meshes = {mesh['name']: [{name: values(doc, binary, index) for name, index in primitive['attributes'].items()}
                             for primitive in mesh['primitives']] for mesh in doc['meshes']}
    return clips, meshes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--changed', action='append', default=None)
    parser.add_argument('--added', action='append', default=[])
    parser.add_argument('--reskinned', action='append', default=[],
                        help='a mesh whose JOINTS_0/WEIGHTS_0 may change; every other attribute must not')
    args = parser.parse_args()
    changed = args.changed or ['Jog']
    before, mesh_before = read(args.before)
    after, mesh_after = read(args.after)
    unchanged, reskinned = compare(before, after, mesh_before, mesh_after, changed, args.added, args.reskinned)
    report = {'before': hashlib.sha256(args.before.read_bytes()).hexdigest(), 'after': hashlib.sha256(args.after.read_bytes()).hexdigest(),
              'unchangedAnimations': unchanged, 'allMeshAttributesUnchanged': not reskinned, 'reskinnedMeshes': reskinned,
              'geometryUnchanged': True, 'changedAnimations': changed, 'addedAnimations': args.added}
    args.report.write_text(json.dumps(report, indent=2))
    print(json.dumps(report))


if __name__ == '__main__':
    main()
