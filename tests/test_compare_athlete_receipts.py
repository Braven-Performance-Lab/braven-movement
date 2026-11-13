"""The before-and-after reading of two render receipt sets (step 5)."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import compare_athlete_receipts as C  # noqa: E402


def phase(name, holding, anchor, deepest, inside, verdict="agrees", digit=5.0, free=None):
    def clearance(base):
        return {d: {"nearestOnBone": base + i} for i, d in enumerate(C.DIGITS)}
    return {"name": name, "holding": holding,
            "girdle": {"verdict": verdict, "ballAnchorErrorMm": anchor},
            "hands": {"l": {"surfaceClearanceMm": clearance(digit if free is None else free)},
                      "r": {"surfaceClearanceMm": clearance(digit)}},
            "bodyClearanceMm": {"deepestMm": deepest, "verticesInside": inside}}


class CompareTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.before, self.after, self.jobs = self.root / "before", self.root / "after", self.root / "jobs"
        self.jobs.mkdir()

    def job(self, drill, grips):
        """A job file whose phases name the hands that hold the ball."""
        path = self.jobs / f"{drill}.job.json"
        path.write_text(json.dumps({"phases": [{"name": n, "grip": {s: {} for s in sides}}
                                               for n, sides in grips.items()]}), encoding="utf-8")
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def write(self, folder, drill, phases, job, athlete=None):
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{drill}.render.json").write_text(json.dumps(
            {"jobSha256": job, "failedPhases": [], "phases": phases, "athlete": athlete}), encoding="utf-8")

    def test_each_phase_pairs_and_the_summary_counts_what_moved(self):
        job = self.job("chest", {"ready": "lr", "release": ""})
        self.write(self.before, "chest", [phase("ready", True, 8.0, 0.0, 0),
                                          phase("release", False, 12.0, -2.0, 5)],
                   job, athlete={"kind": "generated"})
        self.write(self.after, "chest", [phase("ready", True, 7.0, -3.0, 9, digit=4.0),
                                         phase("release", False, 9.0, -2.5, 5, verdict="out of reach")],
                   job, athlete={"kind": "shared", "revision": 9})
        result = C.compare(self.before, self.after, self.jobs)
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

    def test_the_free_hand_of_a_one_hand_hold_is_not_read(self):
        # Review round 1 (should): the free hand is 219 to 980 mm from the
        # ball, and the median of the "nearest digit" row counted it.
        job = self.job("high", {"ready": "r"})
        for folder in (self.before, self.after):
            self.write(folder, "high", [phase("ready", True, 2.0, 0.0, 0, digit=6.0, free=500.0)], job)
        row = C.compare(self.before, self.after, self.jobs)["rows"][0]
        self.assertEqual(row["after"]["nearestDigitMm"], {"l": None, "r": 6.0})
        self.assertEqual(C.compare(self.before, self.after, self.jobs)["summary"]["nearestDigitMedianMm"],
                         {"before": 6.0, "after": 6.0})

    def test_a_phase_on_one_side_only_is_refused(self):
        # Review round 1 (should): it was dropped without a word.
        job = self.job("chest", {"ready": "lr", "release": ""})
        self.write(self.before, "chest", [phase("ready", True, 8.0, 0.0, 0),
                                          phase("release", False, 9.0, 0.0, 0)], job)
        self.write(self.after, "chest", [phase("ready", True, 8.0, 0.0, 0)], job)
        with self.assertRaises(SystemExit):
            C.compare(self.before, self.after, self.jobs)

    def test_a_phase_that_holds_on_one_side_only_is_refused(self):
        job = self.job("chest", {"ready": "lr"})
        self.write(self.before, "chest", [phase("ready", True, 8.0, 0.0, 0)], job)
        self.write(self.after, "chest", [phase("ready", False, 8.0, 0.0, 0)], job)
        with self.assertRaises(SystemExit):
            C.compare(self.before, self.after, self.jobs)

    def test_two_sides_from_different_jobs_are_refused(self):
        job = self.job("chest", {"ready": "lr"})
        self.write(self.before, "chest", [phase("ready", True, 8.0, 0.0, 0)], job)
        self.write(self.after, "chest", [phase("ready", True, 8.0, 0.0, 0)], "b" * 64)
        with self.assertRaises(SystemExit):
            C.compare(self.before, self.after, self.jobs)

    def test_a_job_file_the_receipts_were_not_drawn_from_is_refused(self):
        self.job("chest", {"ready": "lr"})
        for folder in (self.before, self.after):
            self.write(folder, "chest", [phase("ready", True, 8.0, 0.0, 0)], "c" * 64)
        with self.assertRaises(SystemExit):
            C.compare(self.before, self.after, self.jobs)

    def test_two_sides_with_different_drills_are_refused(self):
        job = self.job("chest", {"ready": "lr"})
        self.write(self.before, "chest", [phase("ready", True, 8.0, 0.0, 0)], job)
        self.write(self.after, "bounce", [phase("ready", True, 8.0, 0.0, 0)], job)
        with self.assertRaises(SystemExit):
            C.compare(self.before, self.after, self.jobs)


if __name__ == "__main__":
    unittest.main()
