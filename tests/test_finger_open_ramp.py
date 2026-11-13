"""Coach-morning item 4: the ramp job that closes the fingers over N frames."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import finger_open_ramp as F  # noqa: E402


def entry(frame, grip):
    return {"frame": frame, "grip": {s: {} for s in grip},
            "hands": {"l": {"palmNormal": [0, 0, 1]}, "r": {"palmNormal": [0, 0, 1]}}}


JOB = {"frames": [entry(n, "" if n < 42 else "lr") for n in range(40, 52)],
       "phases": [entry(42, "lr"), entry(50, "lr")]}


class RampTest(unittest.TestCase):
    def test_the_ask_falls_in_equal_steps_and_stops_after_n_frames(self):
        out = F.ramp(JOB, 42, 61.0, 4)
        asks = {e["frame"]: e["hands"]["l"].get("fingerOpenDegrees") for e in out["frames"]}
        self.assertEqual([asks[n] for n in range(40, 48)],
                         [None, None, 61.0, 45.75, 30.5, 15.25, None, None])
        self.assertEqual(asks, {e["frame"]: e["hands"]["r"].get("fingerOpenDegrees") for e in out["frames"]})
        self.assertEqual(out["fingerOpenRamp"]["frames"], 4)

    def test_a_still_phase_inside_the_ramp_carries_its_frames_ask(self):
        out = F.ramp(JOB, 42, 61.0, 8)
        self.assertEqual(out["phases"][0]["hands"]["l"]["fingerOpenDegrees"], 61.0)
        self.assertNotIn("fingerOpenDegrees", out["phases"][1]["hands"]["l"])

    def test_the_shipped_job_is_left_as_it_was(self):
        F.ramp(JOB, 42, 61.0, 4)
        self.assertFalse(any("fingerOpenDegrees" in e["hands"]["l"] for e in JOB["frames"]))

    def test_a_ramp_over_a_frame_that_holds_nothing_is_refused(self):
        with self.assertRaises(SystemExit):
            F.ramp(JOB, 40, 61.0, 4)

    def test_a_job_without_the_contact_frame_is_refused(self):
        with self.assertRaises(SystemExit):
            F.ramp({"frames": [], "phases": []}, 42, 61.0, 4)

    def test_a_ramp_that_would_close_past_the_grip_is_refused(self):
        with self.assertRaises(SystemExit):
            F.ramp(JOB, 42, -5.0, 4)


if __name__ == "__main__":
    unittest.main()
