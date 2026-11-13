"""One camera per drill-view, moved only where the shared camera cuts a ball."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "spikes"))
sys.path.insert(0, str(ROOT / "scripts"))

import ball_in_frame as B  # noqa: E402
import view_framing as V  # noqa: E402

SHARED = {
    "front": {"locationM": [0.0, -3.20, 1.10], "lensMm": 50.0},
    "quarter": {"locationM": [2.20, -2.35, 1.20], "lensMm": 50.0},
    "side": {"locationM": [3.20, -0.15, 1.10], "lensMm": 50.0},
}
TARGET = [0.0, -0.15, 0.95]

# The drawn ball of every phase of the four drills, from the shared-athlete
# receipts of 13 Nov 2026 (build 96ba152, athlete revision 9).
BALLS = {
    "netball_deflect_high": {"ready": [0.0, -1.9965, 1.464], "contact": [0.1254, -0.395, 1.6161],
                             "control": [0.0114, -0.3677, 1.5679], "send_on": [-0.0048, -1.9099, 1.4911]},
    "netball_two_hand_catch_chest": {"ready": [0.0, -1.9881, 1.2845], "contact": [0.0, -0.5639, 1.3901],
                                     "pull_in": [0.0, -0.2818, 1.2686], "release": [0.0001, -1.1324, 1.3969]},
    "netball_double_foot_landing": {"approach": [0.0, -1.9882, 1.4275], "flight": [0.0, -1.702, 1.434],
                                    "land": [-0.0001, -0.3501, 1.3246], "absorb": [0.0, -0.2888, 1.1602]},
    "netball_hooks_jump_pull_in": {"gather": [0.0001, -1.9882, 1.3743], "contact": [0.0, -0.4454, 1.7433],
                                   "pull_in": [0.0001, -0.2986, 1.3756], "release": [0.0001, -0.9388, 1.4477]},
}


def view(location, target, lens):
    return {"resolutionPx": [1080, 1350], "locationM": location, "targetM": target,
            "lensMm": lens, "sensorWidthMm": 36.0}


def shares(drill, name, framed):
    camera = SHARED[name]
    if framed:
        location, target, lens, _ = V.framed(drill, name, camera["locationM"], TARGET, camera["lensMm"])
    else:
        location, target, lens = camera["locationM"], TARGET, camera["lensMm"]
    return {phase: B.visible_share(view(location, target, lens), ball, 0.11)
            for phase, ball in BALLS[drill].items()}


def cut(values):
    return sorted(phase for phase, share in values.items() if 0.001 < share < 0.999)


class FramingTest(unittest.TestCase):
    def test_each_framed_drill_view_cut_a_ball_with_the_shared_camera(self):
        # Pins the reason: a change with nothing to fix is not kept.
        for drill, views in V.FRAMING.items():
            for name in views:
                self.assertTrue(cut(shares(drill, name, False)), f"{drill} {name}")

    def test_no_framed_drill_view_cuts_a_ball(self):
        for drill, views in V.FRAMING.items():
            for name in views:
                self.assertEqual(cut(shares(drill, name, True)), [], f"{drill} {name}")

    def test_a_ball_wholly_out_stays_out(self):
        for drill, views in V.FRAMING.items():
            for name in views:
                before, after = shares(drill, name, False), shares(drill, name, True)
                for phase, share in before.items():
                    if share <= 0.001:
                        self.assertLessEqual(after[phase], 0.001, f"{drill} {name} {phase}")

    def test_a_raise_lifts_camera_and_target_together(self):
        location, target, lens, change = V.framed("netball_deflect_high", "front",
                                                  [0.0, -3.2, 1.1], TARGET, 50.0)
        self.assertAlmostEqual(location[2], 1.25)
        self.assertAlmostEqual(target[2], 1.10)
        self.assertEqual((lens, change), (50.0, {"raiseM": 0.15}))

    def test_every_other_drill_view_keeps_the_shared_camera(self):
        location, target, lens, change = V.framed("netball_chest_pass", "front",
                                                  [0.0, -3.2, 1.1], TARGET, 50.0)
        self.assertEqual((location, target, lens, change), ([0.0, -3.2, 1.1], TARGET, 50.0, None))
        self.assertIsNone(V.framed("netball_deflect_high", "side", [3.2, -0.15, 1.1], TARGET, 50.0)[3])

    def test_the_job_exporter_frames_every_view_through_the_table(self):
        # The exporter imports the engine, so its source is read here.
        import ast
        source = (ROOT / "spikes" / "export_blender_job.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        camera = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "camera")
        self.assertIn("framed", {n.func.id for n in ast.walk(camera)
                                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)})
        views = [n for n in ast.walk(tree) if isinstance(n, ast.Dict)
                 and any(isinstance(k, ast.Constant) and k.value == "views" for k in n.keys)]
        self.assertEqual(len(views), 1)
        value = views[0].values[[k.value for k in views[0].keys if isinstance(k, ast.Constant)].index("views")]
        self.assertIn("camera", {n.func.id for n in ast.walk(value)
                                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)})

    def test_an_unknown_change_is_refused(self):
        V.FRAMING["netball_test"] = {"front": {"tiltDegrees": 5}}
        try:
            with self.assertRaises(ValueError):
                V.framed("netball_test", "front", [0, 0, 0], TARGET, 50.0)
        finally:
            del V.FRAMING["netball_test"]


if __name__ == "__main__":
    unittest.main()
