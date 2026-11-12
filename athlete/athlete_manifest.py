"""The athlete manifest, version 1: convert a build folder to it, and refuse a mismatched set.

The format and every refusal code are defined in docs/ATHLETE_MANIFEST.md. Standard library
only, so Braven Studio, the Tactics importer's checks and the host tests can all run it.

    python athlete/athlete_manifest.py write <build folder> [--kit braven-netball-fitted-v1]
    python athlete/athlete_manifest.py check <build folder> [--family braven-athlete-v6]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
from pathlib import Path, PurePosixPath

FORMAT = 'braven-athlete-manifest'
FORMAT_VERSION = 1
MANIFEST_NAME = 'athlete-manifest.json'
LEGACY_NAME = 'manifest.json'
RIG_FAMILY = 'braven-athlete-v6'
# Braven Tactics' BONES (src/engine/skinned.ts), spelled and cased as it spells them.
CONTRACT_BONES = ('root', 'pelvis', 'spine_01', 'spine_02', 'spine_03', 'neck_01', 'Head',
                  'clavicle_l', 'clavicle_r', 'upperarm_l', 'lowerarm_l', 'hand_l',
                  'upperarm_r', 'lowerarm_r', 'hand_r', 'thigh_l', 'calf_l', 'foot_l',
                  'thigh_r', 'calf_r', 'foot_r')
FILE_ROLES = {'netball-athlete.glb': 'model', 'netball-athlete.blend': 'master',
              'athlete-source.blend': 'body-source', 'movement-library.json': 'library'}
# build.py authors the general clips at 30 fps; techniques and the gait rebuild carry their own.
GENERAL_FPS = 30
REVIEW_STATES = ('passes-source-checks', 'needs-review', 'coach-approved', 'not-graded')
# A string that names a place on one machine: a drive letter, a UNC share, or a home or root path.
LOCAL_PATH = re.compile(r'(^|[\s"(])([A-Za-z]:[\\/]|\\\\|/(?:home|Users|mnt|tmp|var)/)')


class ManifestRefusal(Exception):
    def __init__(self, code: str, detail: str):
        super().__init__(f'{code}: {detail}')
        self.code, self.detail = code, detail


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def joint_set_sha256(names) -> str:
    return sha256_bytes('\n'.join(sorted(names)).encode('utf-8'))


def read_glb(path: Path) -> dict:
    """Animation durations and skin joint names, read from the GLB's JSON chunk."""
    data = path.read_bytes()
    magic, _version, _length = struct.unpack_from('<4sII', data, 0)
    size, kind = struct.unpack_from('<II', data, 12)
    if magic != b'glTF' or kind != 0x4E4F534A:
        raise ManifestRefusal('file', f'{path.name} is not a GLB with a JSON chunk')
    doc = json.loads(data[20:20 + size])
    animations = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers'])
                  for a in doc.get('animations', [])}
    skins = doc.get('skins', [])
    joints = [doc['nodes'][j].get('name', '') for j in skins[0]['joints']] if skins else []
    return {'animations': animations, 'joints': joints}


def _external_asset(source: dict) -> dict:
    """A legacy source keeps its name, licence and hash; its path on one machine is dropped."""
    parts = re.split(r'[\\/]', source['path'])
    name = '/'.join(['mpfb', *parts[parts.index('data') + 1:]]) if 'data' in parts else parts[-1]
    return {'name': name, 'licence': source.get('licence'), 'sha256': source['sha256']}


def _review(technique: dict) -> str:
    if technique.get('coachApproved'):
        return 'coach-approved'
    return 'passes-source-checks' if technique.get('sourceChecksPassed') else 'needs-review'


def _history(legacy: dict) -> list:
    entries = []
    if legacy.get('gravityCorrections'):
        entries.append({'revision': 6, 'change': 'Gravity-correct jump flight', 'recipeSha256': None})
    if legacy.get('realismRecipeSha256'):
        entries.append({'revision': 7, 'change': 'Ball flight, bounce and catch absorption',
                        'recipeSha256': legacy['realismRecipeSha256']})
    if legacy.get('jogCorrection'):
        entries.append({'revision': 8, 'change': 'Rebake Jog from stable leg frames', 'recipeSha256': None})
    if legacy.get('gaitRebuild'):
        entries.append({'revision': 9, 'change': 'Rebuild Jog and add Run from a gait model',
                        'recipeSha256': None})
    return entries


def convert_legacy(folder: Path, *, kit_id: str, sport: str = 'netball') -> dict:
    """Build a v1 manifest from a folder in the legacy layout. Hashes are read off the files."""
    folder = Path(folder)
    legacy = json.loads((folder / LEGACY_NAME).read_text(encoding='utf-8'))
    model = read_glb(folder / 'netball-athlete.glb')
    library_path = folder / 'movement-library.json'
    library = json.loads(library_path.read_text(encoding='utf-8')) if library_path.exists() else {'techniques': []}
    techniques = {t['clip']: t for t in library['techniques']}
    gaits = (legacy.get('gaitRebuild') or {}).get('gaits', {})
    clips = []
    for name in sorted(model['animations'], key=str.lower):
        entry = {'id': name, 'seconds': round(model['animations'][name], 6)}
        if name in techniques:
            t = techniques[name]
            entry.update(kind='technique', fps=int(t['fps']), frameCount=t['frameCount'],
                         movementId=t['movementId'], jobSha256=t.get('jobSha256'),
                         contactFrame=t.get('contactFrame'), releaseFrame=t.get('releaseFrame'),
                         review=_review(t))
        else:
            entry.update(kind='general', fps=int(gaits.get(name, {}).get('fps', GENERAL_FPS)), review='not-graded')
        clips.append(entry)
    roles = legacy.get('roles', {})
    files = {}
    for name, role in FILE_ROLES.items():
        path = folder / name
        if path.exists():
            data = path.read_bytes()
            files[name] = {'role': role, 'bytes': len(data), 'sha256': sha256_bytes(data)}
    return {
        'format': FORMAT, 'formatVersion': FORMAT_VERSION,
        'asset': {'name': legacy['name'], 'revision': legacy['revision'],
                  'parentSha256': legacy.get('parentAssetSha256')},
        'sport': sport,
        'rig': {'family': RIG_FAMILY, 'contractBones': list(CONTRACT_BONES),
                'jointCount': len(model['joints']), 'jointSetSha256': joint_set_sha256(model['joints'])},
        'kit': {'id': kit_id,
                'garments': {k: v for k, v in roles.items() if k.startswith('Kit_')},
                'lettering': {k: k.split('_', 1)[1] for k, v in roles.items() if v == 'lettering'}},
        'source': {'movementCommit': legacy.get('movementSourceCommit') or library.get('sourceCommit'),
                   'generator': legacy.get('generator'), 'blender': legacy.get('blender'),
                   'externalAssets': [_external_asset(s) for s in legacy.get('sources', [])]},
        'files': files,
        'clips': clips,
        'history': _history(legacy),
    }


def _strings(value):
    if isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)
    elif isinstance(value, str):
        yield value


def _check_paths(folder: Path, manifest: dict) -> None:
    for text in _strings(manifest):
        if LOCAL_PATH.search(text):
            raise ManifestRefusal('path', f'a local path is in the manifest: {text[:60]!r}')
    # A relative path with / and no .. stays in the folder. A symbolic link inside the folder
    # is not followed here: the pipeline writes none, and the file check hashes what it reads.
    for name in manifest.get('files', {}):
        if '\\' in name or PurePosixPath(name).is_absolute() or re.match(r'^[A-Za-z]:', name) \
                or '..' in PurePosixPath(name).parts:
            raise ManifestRefusal('path', f'file path must be relative, with / and no ..: {name!r}')


def write(folder: Path, manifest: dict) -> Path:
    """Write the manifest, refusing a local path before anything reaches the disk."""
    _check_paths(folder, manifest)
    path = Path(folder) / MANIFEST_NAME
    path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return path


def validate(folder: Path, supported_families=None) -> dict:
    """Return the manifest if the folder matches it; raise ManifestRefusal with its code if not."""
    folder = Path(folder)
    if not (folder / MANIFEST_NAME).is_file():
        raise ManifestRefusal('format', f'no {MANIFEST_NAME}: write it with athlete_manifest.py write <folder>')
    manifest = json.loads((folder / MANIFEST_NAME).read_text(encoding='utf-8'))
    if manifest.get('format') != FORMAT or manifest.get('formatVersion') != FORMAT_VERSION:
        raise ManifestRefusal('format', f"{manifest.get('format')!r} version {manifest.get('formatVersion')!r}")
    _check_paths(folder, manifest)

    files = manifest['files']
    for name, entry in files.items():
        path = folder / name
        if not path.is_file():
            raise ManifestRefusal('file', f'{name} is missing')
        data = path.read_bytes()
        if len(data) != entry['bytes'] or sha256_bytes(data) != entry['sha256'].lower():
            raise ManifestRefusal('file', f'{name} differs from its manifest entry')

    by_role = {}
    for name, entry in files.items():
        by_role.setdefault(entry['role'], []).append(name)
    if len(by_role.get('model', [])) != 1:
        raise ManifestRefusal('role', f"exactly one model is required, found {by_role.get('model', [])}")
    clips = manifest['clips']
    techniques = {c['id']: c for c in clips if c['kind'] == 'technique'}
    if techniques and len(by_role.get('library', [])) != 1:
        raise ManifestRefusal('role', 'technique clips need exactly one library file')

    model_name = by_role['model'][0]
    model = read_glb(folder / model_name)
    if set(model['animations']) != {c['id'] for c in clips} or len(clips) != len(model['animations']):
        extra = sorted(set(model['animations']) ^ {c['id'] for c in clips})
        raise ManifestRefusal('clip-set', f'the model and the manifest disagree on clips: {extra}')
    for clip in clips:
        if clip.get('review') not in REVIEW_STATES:
            raise ManifestRefusal('format', f"{clip['id']} has review state {clip.get('review')!r}")
        if abs(model['animations'][clip['id']] - clip['seconds']) > 0.5 / clip['fps']:
            raise ManifestRefusal('clip-timing', f"{clip['id']} lasts {model['animations'][clip['id']]:.4f} s "
                                                 f"in the model and {clip['seconds']:.4f} s in the manifest")

    if techniques:
        library = json.loads((folder / by_role['library'][0]).read_text(encoding='utf-8'))
        if library.get('assetSha256', '').lower() != files[model_name]['sha256'].lower():
            raise ManifestRefusal('library', 'the library was made for another model')
        rows = {t['clip']: t for t in library['techniques']}
        if set(rows) != set(techniques) or len(rows) != len(library['techniques']):
            raise ManifestRefusal('library', f'technique sets differ: {sorted(set(rows) ^ set(techniques))}')
        for name, clip in techniques.items():
            row = rows[name]
            pairs = (('fps', int(row['fps']), clip['fps']), ('frameCount', row['frameCount'], clip['frameCount']),
                     ('contactFrame', row.get('contactFrame'), clip['contactFrame']),
                     ('releaseFrame', row.get('releaseFrame'), clip['releaseFrame']))
            for field, theirs, ours in pairs:
                if theirs != ours:
                    raise ManifestRefusal('library', f'{name} {field} is {theirs} in the library and {ours} here')

    rig = manifest['rig']
    joints = model['joints']
    if len(joints) != rig['jointCount'] or joint_set_sha256(joints) != rig['jointSetSha256']:
        raise ManifestRefusal('rig', f"the model's {len(joints)} joints are not the manifest's {rig['jointCount']}")
    missing = [b for b in rig['contractBones'] if b not in joints]
    if missing or list(rig['contractBones']) != list(CONTRACT_BONES):
        raise ManifestRefusal('rig', f'contract bones missing or renamed: {missing}')

    if supported_families is not None and rig['family'] not in supported_families:
        raise ManifestRefusal('family', f"{rig['family']} is not one of {sorted(supported_families)}")
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('action', choices=('write', 'check'))
    parser.add_argument('folder', type=Path)
    parser.add_argument('--kit', default='braven-netball-fitted-v1')
    parser.add_argument('--family', action='append')
    args = parser.parse_args(argv)
    try:
        if args.action == 'write':
            print(write(args.folder, convert_legacy(args.folder, kit_id=args.kit)))
        manifest = validate(args.folder, set(args.family) if args.family else None)
    except ManifestRefusal as refusal:
        print(f'REFUSED {refusal}', file=sys.stderr)
        return 1
    model = next(e['sha256'] for e in manifest['files'].values() if e['role'] == 'model')
    print(json.dumps({'accepted': MANIFEST_NAME, 'revision': manifest['asset']['revision'],
                      'clips': len(manifest['clips']), 'model': model}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
