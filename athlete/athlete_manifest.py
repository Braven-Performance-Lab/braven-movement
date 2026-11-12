"""The athlete manifest, version 1: convert a build folder to it, and refuse a mismatched set.

The format and every refusal code are defined in docs/ATHLETE_MANIFEST.md. Standard library
only, so Braven Studio, the host tests and a consumer's own checks can all run it.

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
# Text that names a place on one machine: a drive letter with a separator, a UNC share, a home
# folder (~/), or any root path of two or more parts (/opt/, /srv/, /Users/...). A relative path
# such as mpfb/hair/x.mhclo, or a name such as Blender/MPFB, does not start a word with / or ~.
LOCAL_PATH = re.compile(r'''(^|[\s"'(=])([A-Za-z]:[\\/]|\\\\|~[\\/]|/[^/\s"']+/)''')


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
    try:
        magic, _version, _length = struct.unpack_from('<4sII', data, 0)
        size, kind = struct.unpack_from('<II', data, 12)
    except struct.error:
        raise ManifestRefusal('file', f'{path.name} is too short to be a GLB') from None
    if magic != b'glTF' or kind != 0x4E4F534A:
        raise ManifestRefusal('file', f'{path.name} is not a GLB with a JSON chunk')
    try:
        doc = json.loads(data[20:20 + size])
        # A chunk whose top level is not an object fails on doc.get with AttributeError, caught below.
        names =[a['name'] for a in doc.get('animations', [])]
        durations = [max(doc['accessors'][s['input']]['max'][0] for s in a['samplers'])
                     for a in doc.get('animations', [])]
        skins = doc.get('skins', [])
        joints = [doc['nodes'][j].get('name', '') for j in skins[0]['joints']] if skins else []
    except (ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
        raise ManifestRefusal('file', f'{path.name} has an unreadable JSON chunk: {exc!r}') from None
    if len(set(names)) != len(names):
        raise ManifestRefusal('clip-set', f'{path.name} has two animations with one name')
    return {'animations': dict(zip(names, durations)), 'joints': joints}


def _external_asset(source: dict) -> dict:
    """A legacy source keeps its name, licence and hash; its path on one machine is dropped.

    An MPFB asset is named by its path under MPFB's own data folder, the first `data` after an
    `mpfb` part, so a user folder that is also called `data` cannot leak into the name. Any
    other asset is named by its file name alone.
    """
    parts = re.split(r'[\\/]', source['path'])
    lowered = [p.lower() for p in parts]
    name = parts[-1]
    if 'mpfb' in lowered:
        after = lowered.index('mpfb')
        if 'data' in lowered[after:]:
            name = '/'.join(['mpfb', *parts[lowered.index('data', after) + 1:]])
    return {'name': name, 'licence': source.get('licence'), 'sha256': source['sha256']}


def _review(technique: dict) -> str:
    if technique.get('coachApproved'):
        return 'coach-approved'
    return 'passes-source-checks' if technique.get('sourceChecksPassed') else 'needs-review'


def _history(legacy: dict) -> list:
    """The revisions the legacy manifest still records. A step it no longer records is absent."""
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


def _check_paths(manifest: dict) -> None:
    for text in _strings(manifest):
        if LOCAL_PATH.search(text):
            raise ManifestRefusal('path', f'a local path is in the manifest: {text[:60]!r}')
    # A relative path with / and no .. stays in the folder. Each test below is one way out of
    # it that the local-path text check cannot see, such as /opt/x.glb (one root part) or D:x.glb.
    # A symbolic link inside the folder is not followed: the pipeline writes none, and the file
    # check hashes what it reads.
    for name in manifest.get('files', {}):
        if '\\' in name:
            raise ManifestRefusal('path', f'file path uses \\: {name!r}')
        if PurePosixPath(name).is_absolute() or re.match(r'^[A-Za-z]:', name):
            raise ManifestRefusal('path', f'file path is absolute: {name!r}')
        if '..' in PurePosixPath(name).parts:
            raise ManifestRefusal('path', f'file path climbs out of the folder: {name!r}')


def write(folder: Path, manifest: dict) -> Path:
    """Write the manifest, refusing a local path before anything reaches the disk."""
    _check_paths(manifest)
    path = Path(folder) / MANIFEST_NAME
    path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return path


def _json(path: Path, code: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except ValueError as exc:
        raise ManifestRefusal(code, f'{path.name} is not JSON: {exc}') from None
    if not isinstance(value, dict):
        raise ManifestRefusal(code, f'{path.name} is JSON but not an object')
    return value


def _seconds(value) -> float:
    """A number of seconds, or NaN, which no tolerance accepts, for a value that is missing or not a number."""
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else float('nan')


def validate(folder: Path, supported_families=frozenset({RIG_FAMILY})) -> dict:
    """Return the manifest if the folder matches it; raise ManifestRefusal with its code if not.

    The rig family is always checked: a consumer names the families it supports, and the
    default is the one family this format knows.
    """
    folder = Path(folder)
    if not (folder / MANIFEST_NAME).is_file():
        raise ManifestRefusal('format', f'no {MANIFEST_NAME}: write it with athlete_manifest.py write <folder>')
    manifest = _json(folder / MANIFEST_NAME, 'format')
    if manifest.get('format') != FORMAT or manifest.get('formatVersion') != FORMAT_VERSION:
        raise ManifestRefusal('format', f"{manifest.get('format')!r} version {manifest.get('formatVersion')!r}")
    _check_paths(manifest)

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
    ids = [c['id'] for c in clips]
    if len(set(ids)) != len(ids):
        raise ManifestRefusal('clip-set', 'the manifest lists one clip twice')
    if set(model['animations']) != set(ids):
        raise ManifestRefusal('clip-set', f"the model and the manifest disagree on clips: "
                                          f"{sorted(set(model['animations']) ^ set(ids))}")
    for clip in clips:
        if clip.get('review') not in REVIEW_STATES:
            raise ManifestRefusal('format', f"{clip['id']} has review state {clip.get('review')!r}")
        if not isinstance(clip.get('fps'), int) or clip['fps'] <= 0:
            raise ManifestRefusal('format', f"{clip['id']} has frame rate {clip.get('fps')!r}")
        if abs(model['animations'][clip['id']] - clip['seconds']) > 0.5 / clip['fps']:
            raise ManifestRefusal('clip-timing', f"{clip['id']} lasts {model['animations'][clip['id']]:.4f} s "
                                                 f"in the model and {clip['seconds']:.4f} s in the manifest")

    if techniques:
        library = _json(folder / by_role['library'][0], 'library')
        if (library.get('assetSha256') or '').lower() != files[model_name]['sha256'].lower():
            raise ManifestRefusal('library', 'the library was made for another model')
        clips_in_library = [t['clip'] for t in library['techniques']]
        if len(set(clips_in_library)) != len(clips_in_library):
            raise ManifestRefusal('library', 'the library lists one technique twice')
        rows = {t['clip']: t for t in library['techniques']}
        if set(rows) != set(techniques):
            raise ManifestRefusal('library', f'technique sets differ: {sorted(set(rows) ^ set(techniques))}')
        for name, clip in techniques.items():
            row = rows[name]
            pairs = (('fps', int(row['fps']), clip['fps']), ('frameCount', row['frameCount'], clip['frameCount']),
                     ('contactFrame', row.get('contactFrame'), clip['contactFrame']),
                     ('releaseFrame', row.get('releaseFrame'), clip['releaseFrame']))
            for field, theirs, ours in pairs:
                if theirs != ours:
                    raise ManifestRefusal('library', f'{name} {field} is {theirs} in the library and {ours} here')
            # The library's own timing must agree with the model's clip, not only with the manifest.
            # Written as "not inside": a missing or non-numeric value is NaN, and NaN is refused.
            seconds_by_frames = (row['frameCount'] - 1) / row['fps']
            for label, theirs in (('seconds', _seconds(row.get('seconds'))), ('frame count', seconds_by_frames)):
                if not abs(theirs - model['animations'][name]) <= 0.5 / clip['fps']:
                    raise ManifestRefusal('clip-timing', f"{name}: the library's {label} gives {theirs:.4f} s "
                                                         f"and the model's clip lasts {model['animations'][name]:.4f} s")

    rig = manifest['rig']
    joints = model['joints']
    if len(joints) != rig['jointCount']:
        raise ManifestRefusal('rig', f"the model has {len(joints)} joints and the manifest {rig['jointCount']}")
    if joint_set_sha256(joints) != rig['jointSetSha256']:
        raise ManifestRefusal('rig', "the model's joint names are not the manifest's")
    if list(rig['contractBones']) != list(CONTRACT_BONES):
        raise ManifestRefusal('rig', 'the manifest does not list the contract bones this validator knows')
    missing = [b for b in CONTRACT_BONES if b not in joints]
    if missing:
        raise ManifestRefusal('rig', f'contract bones missing or renamed in the model: {missing}')

    if rig['family'] not in supported_families:
        raise ManifestRefusal('family', f"{rig['family']} is not one of {sorted(supported_families)}")
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('action', choices=('write', 'check'))
    parser.add_argument('folder', type=Path)
    parser.add_argument('--kit', default='braven-netball-fitted-v1')
    parser.add_argument('--family', action='append', help=f'a supported rig family (default {RIG_FAMILY})')
    args = parser.parse_args(argv)
    families = frozenset(args.family or [RIG_FAMILY])
    target = args.folder / MANIFEST_NAME
    # The manifest that was there before this run, so that a refused or failed run puts it back.
    before = target.read_bytes() if args.action == 'write' and target.is_file() else None
    written = None
    try:
        if args.action == 'write':
            written = write(args.folder, convert_legacy(args.folder, kit_id=args.kit))
        manifest = validate(args.folder, families)
    except BaseException as failure:
        # A manifest this run wrote is never left beside a build that did not pass, whatever
        # stopped the check: a coded refusal, or any other error.
        if written is not None:
            if before is None:
                written.unlink(missing_ok=True)
            else:
                written.write_bytes(before)
        if isinstance(failure, ManifestRefusal):
            print(f'REFUSED {failure}', file=sys.stderr)
            return 1
        raise
    if written is not None:
        print(written)
    model = next(e['sha256'] for e in manifest['files'].values() if e['role'] == 'model')
    print(json.dumps({'accepted': MANIFEST_NAME, 'revision': manifest['asset']['revision'],
                      'clips': len(manifest['clips']), 'model': model}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
