"""scripts/clip_moved.py must see a difference, or its 0.000 means nothing."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import clip_moved  # noqa: E402


def clip(frames, ball, graded=False, commit="0" * 40):
    return {"clipId": "catch.netball.x", "frames": frames, "ball": ball, "graded": graded,
            "generatedFrom": {"commit": commit}}


class ClipMoved(unittest.TestCase):
    def test_identical_clips_read_zero(self):
        a = clip([[0.1] * 15, [0.2] * 15], [[0, 1, 2, 1], [0, 1, 3, 1]])
        m = clip_moved.moved(a, a)
        self.assertEqual((m["poseMax"], m["poseMean"], m["ballMaxM"]), (0, 0, 0))

    def test_a_changed_pose_number_and_ball_are_seen(self):
        old = clip([[0.1] * 15, [0.2] * 15], [[0, 1, 2, 1], [0, 1, 3, 1]])
        new = clip([[0.1] * 15, [0.2] * 14 + [0.5]], [[0, 1, 2, 1], [0, 1.5, 3, 1]])
        m = clip_moved.moved(old, new)
        self.assertAlmostEqual(m["poseMax"], 0.3)
        self.assertAlmostEqual(m["poseMean"], 0.3 / 30)
        self.assertAlmostEqual(m["ballMaxM"], 0.5)

    def test_a_clip_from_before_build_stamps_is_named_unstamped(self):
        old = clip([[0.1] * 15], [[0, 1, 2, 1]])
        del old["generatedFrom"]
        m = clip_moved.moved(old, clip([[0.1] * 15], [[0, 1, 2, 1]], commit="a" * 40))
        self.assertEqual((m["buildBefore"], m["buildAfter"]), ("unstamped", "a" * 40))

    def test_a_different_frame_count_is_refused(self):
        with self.assertRaises(SystemExit):
            clip_moved.moved(clip([[0] * 15] * 2, []), clip([[0] * 15] * 3, []))


if __name__ == "__main__":
    unittest.main()
