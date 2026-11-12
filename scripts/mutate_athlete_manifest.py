"""Prove that every guard in athlete/athlete_manifest.py can fail its tests.

Each mutation turns one guard's condition off in a copy of the module, in a temporary
tree, and runs tests/test_athlete_manifest.py against that copy. A mutation is KILLED when
the run's summary line says FAILED. The working tree is never edited.

The denominator is the guard list below, read against the module: the run refuses if any
mutation's text is not found exactly once, so a guard that moved is not silently skipped.

    python -B scripts/mutate_athlete_manifest.py
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MODULE = REPO / 'athlete' / 'athlete_manifest.py'
TEST = REPO / 'tests' / 'test_athlete_manifest.py'

# (refusal it guards, exact text, replacement). Every `raise ManifestRefusal` in the module has
# exactly one row here; WRITE_MUTATIONS removes a call rather than a refusal and is counted apart.
MUTATIONS = [
    ('file not a GLB', "if magic != b'glTF' or kind != 0x4E4F534A:", 'if False:'),
    ('format', "if manifest.get('format') != FORMAT or manifest.get('formatVersion') != FORMAT_VERSION:", 'if False:'),
    ('format review', "if clip.get('review') not in REVIEW_STATES:", 'if False:'),
    ('path local text', 'if LOCAL_PATH.search(text):', 'if False:'),
    ('path relative', "if '\\\\' in name or PurePosixPath(name).is_absolute() or re.match(r'^[A-Za-z]:', name) \\\n"
                      "                or '..' in PurePosixPath(name).parts:", 'if False:'),
    ('file missing', 'if not path.is_file():', 'if False:'),
    ('file hash', "if len(data) != entry['bytes'] or sha256_bytes(data) != entry['sha256'].lower():", 'if False:'),
    ('role model', "if len(by_role.get('model', [])) != 1:", 'if False:'),
    ('role library', "if techniques and len(by_role.get('library', [])) != 1:", 'if False:'),
    ('clip-set', "if set(model['animations']) != {c['id'] for c in clips} or len(clips) != len(model['animations']):",
                 'if False:'),
    ('clip-timing', "if abs(model['animations'][clip['id']] - clip['seconds']) > 0.5 / clip['fps']:", 'if False:'),
    ('library model', "if library.get('assetSha256', '').lower() != files[model_name]['sha256'].lower():", 'if False:'),
    ('library set', "if set(rows) != set(techniques) or len(rows) != len(library['techniques']):", 'if False:'),
    ('library field', 'if theirs != ours:', 'if False:'),
    ('rig joints', "if len(joints) != rig['jointCount'] or joint_set_sha256(joints) != rig['jointSetSha256']:",
                   'if False:'),
    ('rig contract', "if missing or list(rig['contractBones']) != list(CONTRACT_BONES):", 'if False:'),
    ('family', "if supported_families is not None and rig['family'] not in supported_families:", 'if False:'),
]
WRITE_MUTATIONS = [
    ('path in write', '    _check_paths(folder, manifest)\n    path = Path(folder) / MANIFEST_NAME',
                      '    path = Path(folder) / MANIFEST_NAME'),
]


def run(module_text: str) -> tuple[str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / 'athlete').mkdir()
        (root / 'tests').mkdir()
        (root / 'athlete' / MODULE.name).write_text(module_text, encoding='utf-8')
        shutil.copy(TEST, root / 'tests' / TEST.name)
        proc = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(root / 'tests'),
                               '-p', TEST.name], capture_output=True, text=True, cwd=root)
    out = proc.stderr.strip().splitlines()
    ran = next((line for line in out if line.startswith('Ran ')), 'Ran ? (no summary line: a failed read)')
    return ran, (out[-1] if out else '')


def main() -> int:
    source = MODULE.read_text(encoding='utf-8')
    raises = len(re.findall(r'raise ManifestRefusal\(', source))
    if raises != len(MUTATIONS):
        print(f'REFUSED: the module has {raises} refusals and this list mutates {len(MUTATIONS)}')
        return 2
    ran, last = run(source)
    print(f'unmutated: {ran}; {last}')
    if last != 'OK':
        print('REFUSED: the unmutated module does not pass, so no mutation can be read')
        return 2
    survivors = []
    for name, text, replacement in MUTATIONS + WRITE_MUTATIONS:
        found = source.count(text)
        if found != 1:
            print(f'REFUSED: {name!r} text found {found} times')
            return 2
        ran, last = run(source.replace(text, replacement))
        killed = last.startswith('FAILED')
        print(f"{'KILLED  ' if killed else 'SURVIVED'} {name:16} {ran}; {last}")
        if not killed:
            survivors.append(name)
    total = len(MUTATIONS) + len(WRITE_MUTATIONS)
    print(f'{total - len(survivors)} of {total} mutations killed: {len(MUTATIONS)} for the module\'s '
          f'{raises} refusals, {len(WRITE_MUTATIONS)} for the write path')
    return 1 if survivors else 0


if __name__ == '__main__':
    sys.exit(main())
