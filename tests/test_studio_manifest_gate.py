"""Studio's manifest gate, run by the suite that CI and the board already run.

Braven Studio refuses an athlete its manifest does not describe, and serves nothing but the
checked manifest and the files it lists (athlete/viewer/manifest-gate.mjs). Its tests are Node's
own test runner and need no npm install, but no workflow ran them: if the gate stopped refusing,
every hosted check stayed green. This runs them from the host suite.

A machine with no Node fails here rather than skips, because a test that skips guards nothing.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GATE_TESTS = REPO / 'athlete' / 'viewer' / 'tests' / 'manifest-gate.test.mjs'


class StudioManifestGate(unittest.TestCase):
    def test_the_gate_tests_pass_under_node(self):
        node = shutil.which('node')
        self.assertIsNotNone(node, 'Node is not on PATH: the Studio manifest gate cannot be tested on this machine')
        # UTF-8, not the local code page: Node's summary lines start with "ℹ", and a misread
        # summary is a failed read, not a pass.
        # The spec reporter by name: Node before 23 prints TAP when its output is a pipe, and this
        # reads the spec reporter's summary lines.
        run = subprocess.run([node, '--test', '--test-reporter=spec', str(GATE_TESTS)], capture_output=True, text=True, encoding='utf-8',
                             errors='replace', cwd=REPO, env={**os.environ, 'BRAVEN_PYTHON': sys.executable})
        summary = [line for line in run.stdout.splitlines() if line.startswith(('ℹ tests', 'ℹ pass', 'ℹ fail'))]
        self.assertEqual(run.returncode, 0, '\n'.join(summary) + '\n' + run.stdout[-3000:] + run.stderr[-2000:])
        counts = {line.split()[1]: int(line.split()[2]) for line in summary}
        self.assertGreaterEqual(counts.get('pass', 0), 9, f'fewer gate tests ran than exist: {counts}')
        self.assertEqual(counts.get('fail', 0), 0)


if __name__ == '__main__':
    unittest.main()
