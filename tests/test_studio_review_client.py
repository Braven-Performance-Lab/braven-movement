"""Studio's review client tests, run by the suite that CI and the board already run.

The sign-in session, the API calls and the comment rules of the Studio page
(athlete/viewer/src/session.js, review-api.js, comments.js) hold two rules a coach relies on: a
model is shown only when its bytes have the hash the version names, and "approved" is shown only
when a reviewer approved that version. Their tests are Node's own test runner and no workflow
runs `npm test`, so this file runs them from the host suite.

A machine with no Node fails here and does not skip, because a test that skips guards nothing.
"""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TESTS = REPO / 'athlete' / 'viewer' / 'tests'
REVIEW_TESTS = [TESTS / 'review.test.mjs', TESTS / 'review-owner.test.mjs']


class StudioReviewClient(unittest.TestCase):
    def test_the_review_client_tests_pass_under_node(self):
        node = shutil.which('node')
        self.assertIsNotNone(node, 'Node is not on PATH: the Studio review client cannot be tested on this machine')
        # UTF-8 and the spec reporter by name, for the reasons in test_studio_manifest_gate.py.
        run = subprocess.run([node, '--test', '--test-reporter=spec', *map(str, REVIEW_TESTS)], capture_output=True, text=True,
                             encoding='utf-8', errors='replace', cwd=REPO)
        summary = [line for line in run.stdout.splitlines() if line.startswith(('ℹ tests', 'ℹ pass', 'ℹ fail'))]
        self.assertEqual(run.returncode, 0, '\n'.join(summary) + '\n' + run.stdout[-3000:] + run.stderr[-2000:])
        counts = {line.split()[1]: int(line.split()[2]) for line in summary}
        self.assertGreaterEqual(counts.get('pass', 0), 32, f'fewer review client tests ran than exist: {counts}')
        self.assertEqual(counts.get('fail', 0), 0)


if __name__ == '__main__':
    unittest.main()
