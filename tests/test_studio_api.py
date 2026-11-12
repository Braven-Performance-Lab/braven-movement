"""The Braven Studio API's tests, run by the suite that CI and the board already run.

The Studio Worker (athlete/studio-api) decides who may see an athlete version and keeps the
coaches' comments. Its tests are Node's own test runner and need no npm install, but no workflow
runs Node tests by themselves: without this file a broken sign-in check would leave every hosted
check green.

A machine with no Node, or a Node too old to hold the tests' database, fails here and does not
skip, because a test that skips guards nothing.
"""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
API = REPO / 'athlete' / 'studio-api'
# node:sqlite, which stands in for D1, is in Node from 22.13 with no flag.
NODE_NEEDED = (22, 13)


class StudioApi(unittest.TestCase):
    def test_the_api_tests_pass_under_node(self):
        node = shutil.which('node')
        self.assertIsNotNone(node, 'Node is not on PATH: the Studio API cannot be tested on this machine')
        version = subprocess.run([node, '--version'], capture_output=True, text=True).stdout.strip()
        found = tuple(int(part) for part in version.lstrip('v').split('.')[:2])
        self.assertGreaterEqual(found, NODE_NEEDED, f'Node {version} is too old: the Studio API tests need node:sqlite')

        files = sorted(str(path) for path in (API / 'tests').glob('*.test.mjs'))
        self.assertGreaterEqual(len(files), 4, f'test files are missing: {files}')
        # UTF-8 and the spec reporter by name, for the reasons in test_studio_manifest_gate.py:
        # the summary lines start with "ℹ", and a summary that cannot be read is not a pass.
        run = subprocess.run([node, '--test', '--test-reporter=spec', *files], capture_output=True, text=True,
                             encoding='utf-8', errors='replace', cwd=API)
        summary = [line for line in run.stdout.splitlines() if line.startswith(('ℹ tests', 'ℹ pass', 'ℹ fail'))]
        self.assertEqual(run.returncode, 0, '\n'.join(summary) + '\n' + run.stdout[-3000:] + run.stderr[-2000:])
        counts = {line.split()[1]: int(line.split()[2]) for line in summary}
        self.assertGreaterEqual(counts.get('pass', 0), 57, f'fewer API tests ran than exist: {counts}')
        self.assertEqual(counts.get('fail', 0), 0)


if __name__ == '__main__':
    unittest.main()
