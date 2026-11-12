"""Prove that every refusal in athlete/athlete_manifest.py, and every clause inside one, can fail its tests.

Each mutation turns one guard or one clause off in a copy of the module, in a temporary tree,
and runs tests/test_athlete_manifest.py against that copy. A mutation is KILLED when the run's
summary line says FAILED. The working tree is never edited.

Three lists, counted apart, because a count only means something against its own population:
  REFUSALS  one row for every `raise ManifestRefusal(` in the module. The run refuses if the
            module's count differs, so a refusal added without a row is not silently uncounted.
            A refusal raised from an `except` is mutated to a bare `raise`, which lets the
            original error out where a ManifestRefusal is expected.
  CLAUSES   one row for each clause of a guard that has more than one, so that a clause no
            test can fail is not hidden by a sibling clause that some test does fail.
  WRITES    the write path's own check.
Every row's text must be found exactly once, so a guard that moved is not silently skipped.

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
OFF = 'if False:'

REFUSALS = [
    ('file GLB too short', "raise ManifestRefusal('file', f'{path.name} is too short to be a GLB') from None", 'raise'),
    ('file not a GLB', "if magic != b'glTF' or kind != 0x4E4F534A:", OFF),
    ('file JSON chunk', "raise ManifestRefusal('file', f'{path.name} has an unreadable JSON chunk: {exc!r}') from None", 'raise'),
    ('clip-set GLB names', 'if len(set(names)) != len(names):', OFF),
    ('format absent', 'if not (folder / MANIFEST_NAME).is_file():', OFF),
    ('not JSON', "raise ManifestRefusal(code, f'{path.name} is not JSON: {exc}') from None", 'raise'),
    ('not an object', 'if not isinstance(value, dict):', OFF),
    ('format', "if manifest.get('format') != FORMAT or manifest.get('formatVersion') != FORMAT_VERSION:", OFF),
    ('path local text', 'if LOCAL_PATH.search(text):', OFF),
    ('path backslash', "if '\\\\' in name:", OFF),
    ('path absolute', "if PurePosixPath(name).is_absolute() or re.match(r'^[A-Za-z]:', name):", OFF),
    ('path ..', "if '..' in PurePosixPath(name).parts:", OFF),
    ('file missing', 'if not path.is_file():', OFF),
    ('file hash', "if len(data) != entry['bytes'] or sha256_bytes(data) != entry['sha256'].lower():", OFF),
    ('role model', "if len(by_role.get('model', [])) != 1:", OFF),
    ('role library', "if techniques and len(by_role.get('library', [])) != 1:", OFF),
    ('clip-set twice', 'if len(set(ids)) != len(ids):', OFF),
    ('clip-set', "if set(model['animations']) != set(ids):", OFF),
    ('format review', "if clip.get('review') not in REVIEW_STATES:", OFF),
    ('format fps', "if not isinstance(clip.get('fps'), int) or clip['fps'] <= 0:", OFF),
    ('clip-timing', "if abs(model['animations'][clip['id']] - clip['seconds']) > 0.5 / clip['fps']:", OFF),
    ('library model', "if (library.get('assetSha256') or '').lower() != files[model_name]['sha256'].lower():", OFF),
    ('library twice', 'if len(set(clips_in_library)) != len(clips_in_library):', OFF),
    ('library set', 'if set(rows) != set(techniques):', OFF),
    ('library field', 'if theirs != ours:', OFF),
    ('library timing', "if not abs(theirs - model['animations'][name]) <= 0.5 / clip['fps']:", OFF),
    ('rig joint count', "if len(joints) != rig['jointCount']:", OFF),
    ('rig joint names', "if joint_set_sha256(joints) != rig['jointSetSha256']:", OFF),
    ('rig contract list', "if list(rig['contractBones']) != list(CONTRACT_BONES):", OFF),
    ('rig contract bone', 'if missing:', OFF),
    ('family', "if rig['family'] not in supported_families:", OFF),
]
CLAUSES = [
    ('magic only', "if magic != b'glTF' or kind != 0x4E4F534A:", 'if kind != 0x4E4F534A:'),
    ('chunk kind only', "if magic != b'glTF' or kind != 0x4E4F534A:", "if magic != b'glTF':"),
    ('format name only', "manifest.get('format') != FORMAT or manifest.get('formatVersion') != FORMAT_VERSION",
                         "manifest.get('formatVersion') != FORMAT_VERSION"),
    ('format version only', "manifest.get('format') != FORMAT or manifest.get('formatVersion') != FORMAT_VERSION",
                            "manifest.get('format') != FORMAT"),
    ('absolute: root only', "if PurePosixPath(name).is_absolute() or re.match(r'^[A-Za-z]:', name):",
                            "if re.match(r'^[A-Za-z]:', name):"),
    ('absolute: drive only', "if PurePosixPath(name).is_absolute() or re.match(r'^[A-Za-z]:', name):",
                             'if PurePosixPath(name).is_absolute():'),
    ('file bytes only', "if len(data) != entry['bytes'] or sha256_bytes(data) != entry['sha256'].lower():",
                        "if sha256_bytes(data) != entry['sha256'].lower():"),
    ('file hash only', "if len(data) != entry['bytes'] or sha256_bytes(data) != entry['sha256'].lower():",
                       "if len(data) != entry['bytes']:"),
    ('fps type only', "if not isinstance(clip.get('fps'), int) or clip['fps'] <= 0:", "if clip['fps'] <= 0:"),
    ('fps sign only', "if not isinstance(clip.get('fps'), int) or clip['fps'] <= 0:",
                      "if not isinstance(clip.get('fps'), int):"),
]
WRITES = [
    ('path in write', "    _check_paths(manifest)\n    path = Path(folder) / MANIFEST_NAME",
                      '    path = Path(folder) / MANIFEST_NAME'),
    ('restore on refusal', '                written.write_bytes(before)', '                pass'),
    ('remove on failure', '                written.unlink(missing_ok=True)', '                pass'),
]
# Ways a refusal can be lost without its guard being switched off.
ROBUSTNESS = [
    ('glb attribute error', 'except (ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:',
                            'except (ValueError, KeyError, IndexError, TypeError) as exc:'),
    ('library seconds raw', "_seconds(row.get('seconds'))", "row['seconds']"),
    ('NaN passes timing', "if not abs(theirs - model['animations'][name]) <= 0.5 / clip['fps']:",
                          "if abs(theirs - model['animations'][name]) > 0.5 / clip['fps']:"),
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
    if raises != len(REFUSALS):
        print(f'REFUSED: the module has {raises} refusals and REFUSALS has {len(REFUSALS)} rows')
        return 2
    ran, last = run(source)
    print(f'unmutated: {ran}; {last}')
    if last != 'OK':
        print('REFUSED: the unmutated module does not pass, so no mutation can be read')
        return 2
    survivors = []
    for group, rows in (('refusal', REFUSALS), ('clause', CLAUSES), ('write', WRITES), ('robust', ROBUSTNESS)):
        for name, text, replacement in rows:
            found = source.count(text)
            if found != 1:
                print(f'REFUSED: {name!r} text found {found} times')
                return 2
            ran, last = run(source.replace(text, replacement))
            killed = last.startswith('FAILED')
            print(f"{'KILLED  ' if killed else 'SURVIVED'} {group:7} {name:22} {ran}; {last}")
            if not killed:
                survivors.append(name)
    total = len(REFUSALS) + len(CLAUSES) + len(WRITES) + len(ROBUSTNESS)
    print(f'{total - len(survivors)} of {total} mutations killed: {len(REFUSALS)} for the module\'s {raises} '
          f'refusals, {len(CLAUSES)} for clauses inside them, {len(WRITES)} for the write path, '
          f'{len(ROBUSTNESS)} for ways a refusal is lost without its guard off')
    return 1 if survivors else 0


if __name__ == '__main__':
    sys.exit(main())
