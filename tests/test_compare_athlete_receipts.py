"""The before-and-after reading of two render receipt sets (step 5)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import compare_athlete_receipts as C  # noqa: E402


def phase(name, holding, anchor, deepest, inside, verdict="agrees", digit=5.0):
    clearance = {d: {"nearestOnBone": digit + i} for i, d in enumerate(C.DIGITS)}
    return {"name": name, "holding": holding,
            "girdle": {"verdict": verdict, "ballAnchorErrorMm": anchor},
            "hands": {"l": {"surfaceClearanceMm": clearance}, "r": {"surfaceClearanceMm": clearance}},
            "bodyClearanceMm": {"deepestMm": deepest, "verticesInside": inside}}


def write(folder: Path, drill: str, phases, job="a" * 64, athlete=None):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{drill}.render.json").write_text(json.dumps(
        {"jobSha256": job, "failedPhases": [], "phases": phases, "athlete": athlete}), encoding="utf-8")


class CompareTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.before, self.after = self.root / "before", self.root / "after"

    def test_each_phase_pairs_and_the_summary_counts_what_moved(self):
        write(self.before, "chest", [phase("ready", True, 8.0, 0.0, 0), phase("release", False, 12.0, -2.0, 5)],
              athlete={"kind": "generated"})
        write(self.after, "chest", [phase("ready", True, 7.0, -3.0, 9, digit=4.0),
                                    phase("release", False, 9.0, -2.5, 5, verdict="out of reach")],
              athlete={"kind": "shared", "revision": 9})
        result = C.compare(self.before, self.after)
        self.assertEqual(len(result["rows"]), 2)
        ready = result["rows"][0]
        self.assertEqual(ready["before"]["nearestDigitMm"], {"l": 5.0, "r": 5.0})
        self.assertEqual(ready["after"]["nearestDigitMm"], {"l": 4.0, "r": 4.0})
        # Not holding: no digit reading, never a distance to a ball in flight.
        self.assertEqual(result["rows"][1]["after"]["nearestDigitMm"], {"l": None, "r": None})
        s = result["summary"]
        self.assertEqual(s["ballAnchorErrorMedianMm"], {"before": 10.0, "after": 8.0})
        self.assertEqual(s["ballAnchorOver10Mm"], {"before": 1, "after": 0})
        self.assertEqual(s["girdleVerdictChanged"], ["chest.release: agrees -> out of reach"])
        self.assertEqual(s["bodyInsideBallPhases"], {"before": 1, "after": 2})
        self.assertEqual(s["bodyDeeperByOver1Mm"], ["chest.ready"])
        self.assertEqual(s["bodyShallowerByOver1Mm"], [])
        self.assertEqual(result["after"]["athlete"], {"kind": "shared", "revision": 9})

    def test_two_sides_from_different_jobs_are_refused(self):
        write(self.before, "chest", [phase("ready", True, 8.0, 0.0, 0)])
        write(self.after, "chest", [phase("ready", True, 8.0, 0.0, 0)], job="b" * 64)
        with self.assertRaises(SystemExit):
            C.compare(self.before, self.after)

    def test_two_sides_with_different_drills_are_refused(self):
        write(self.before, "chest", [phase("ready", True, 8.0, 0.0, 0)])
        write(self.after, "bounce", [phase("ready", True, 8.0, 0.0, 0)])
        with self.assertRaises(SystemExit):
            C.compare(self.before, self.after)


if __name__ == "__main__":
    unittest.main()
