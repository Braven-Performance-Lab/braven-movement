"""Whether the camera sees the ball: the projection, held to Blender's own."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import ball_in_frame as B  # noqa: E402

# The three cameras every job carries (spikes/export_blender_job.py VIEWS).
VIEWS = {
    "front": {"resolutionPx": [1080, 1350], "locationM": [0.0, -3.2, 1.1],
              "targetM": [0.0, -0.15, 0.95], "lensMm": 50.0, "sensorWidthMm": 36.0},
    "quarter": {"resolutionPx": [1080, 1350], "locationM": [2.2, -2.35, 1.2],
                "targetM": [0.0, -0.15, 0.95], "lensMm": 50.0, "sensorWidthMm": 36.0},
    "side": {"resolutionPx": [1080, 1350], "locationM": [3.2, -0.15, 1.1],
             "targetM": [0.0, -0.15, 0.95], "lensMm": 50.0, "sensorWidthMm": 36.0},
}

# Blender 4.5.12, `bpy_extras.object_utils.world_to_camera_view`, with the
# camera set as `render_still` sets it (sensor fit AUTO), 13 Nov 2026. Pixel x,
# and pixel y down from the top.
BLENDER = [
    ("front", (0.0, -0.15, 0.95), 540.0, 675.0),
    ("front", (0.3, -0.5, 1.6), 750.5, 231.5),
    ("front", (-0.4, -0.3, 2.1), 276.6, -76.5),
    ("front", (0.2, 0.1, 0.4), 652.6, 977.4),
    ("quarter", (0.0, -0.15, 0.95), 540.0, 675.0),
    ("quarter", (0.3, -0.5, 1.6), 514.6, 236.2),
    ("quarter", (-0.4, -0.3, 2.1), 312.5, -3.8),
    ("quarter", (0.2, 0.1, 0.4), 726.4, 994.5),
    ("side", (0.0, -0.15, 0.95), 540.0, 675.0),
    ("side", (0.3, -0.5, 1.6), 311.6, 260.5),
    ("side", (-0.4, -0.3, 2.1), 460.8, 58.2),
    ("side", (0.2, 0.1, 0.4), 694.7, 1020.8),
]


class ProjectionTest(unittest.TestCase):
    def test_the_projection_is_blenders_to_a_tenth_of_a_pixel(self):
        for view, point, x, y in BLENDER:
            px, py, _ = B.project(VIEWS[view], point)
            self.assertAlmostEqual(px, x, delta=0.06, msg=f"{view} {point}")
            self.assertAlmostEqual(py, y, delta=0.06, msg=f"{view} {point}")

    def test_a_ball_at_the_target_is_wholly_in_frame(self):
        self.assertEqual(B.visible_share(VIEWS["front"], [0.0, -0.15, 0.95], 0.11), 1.0)

    def test_a_ball_above_the_frame_is_not_seen(self):
        self.assertEqual(B.visible_share(VIEWS["quarter"], [0.0, -0.15, 3.5], 0.11), 0.0)

    def test_a_ball_on_the_top_edge_is_half_seen(self):
        view = VIEWS["front"]
        # Find the height whose projection is the top edge, then check the share.
        low, high = 0.95, 3.0
        for _ in range(60):
            middle = (low + high) / 2
            if B.project(view, [0.0, -0.15, middle])[1] > 0:
                low = middle
            else:
                high = middle
        self.assertAlmostEqual(B.visible_share(view, [0.0, -0.15, low], 0.11), 0.5, delta=0.03)


class SurveyTest(unittest.TestCase):
    def test_every_phase_and_view_is_read_from_the_receipt(self):
        root = Path(tempfile.mkdtemp())
        renders, jobs = root / "renders", root / "jobs"
        renders.mkdir()
        jobs.mkdir()
        (jobs / "drill.job.json").write_text(json.dumps({
            "views": VIEWS, "phases": [{"name": "a", "ball": {"radiusM": 0.11}},
                                       {"name": "b", "ball": {"radiusM": 0.11}}]}), encoding="utf-8")
        (renders / "drill.render.json").write_text(json.dumps({"phases": [
            {"name": "a", "ballCentreM": [0.0, -0.15, 0.95]},
            {"name": "b", "ballCentreM": [0.0, -0.15, 3.5]}]}), encoding="utf-8")
        rows = B.survey(renders, jobs)
        self.assertEqual(len(rows), 6)
        self.assertEqual({r["visibleShare"] for r in rows if r["phase"] == "a"}, {1.0})
        self.assertEqual({r["visibleShare"] for r in rows if r["phase"] == "b"}, {0.0})


if __name__ == "__main__":
    unittest.main()
