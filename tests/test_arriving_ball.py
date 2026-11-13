"""The owner's choice B (13 Nov 2026): a front view leaves out an arriving ball that hides her."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import arriving_ball as A  # noqa: E402

FRONT = {"resolutionPx": [1080, 1350], "locationM": [0.0, -3.2, 1.1],
         "targetM": [0.0, -0.15, 0.95], "lensMm": 50.0, "sensorWidthMm": 36.0}
# The two-hand chest catch at ready, from the shared-athlete receipt of 13 Nov.
SHOULDERS = ([0.1458, -0.0605, 1.263], [-0.1458, -0.0604, 1.263])
ARRIVING = [0.0, -1.9881, 1.2845]
JOB_PHASES = [{"name": "ready", "frame": 0, "ball": {"holding": False}},
              {"name": "contact", "frame": 42, "ball": {"holding": True}},
              {"name": "release", "frame": 90, "ball": {"holding": False}}]


def phase(name):
    return next(p for p in JOB_PHASES if p["name"] == name)


class LeaveOutTest(unittest.TestCase):
    def test_the_arriving_ball_over_her_face_is_left_out_of_the_front_view(self):
        reason = A.leave_ball_out("front", FRONT, phase("ready"), JOB_PHASES, ARRIVING, 0.11, *SHOULDERS)
        self.assertIn("13 Nov 2026", reason)

    def test_every_other_view_keeps_the_ball(self):
        self.assertIsNone(A.leave_ball_out("quarter", FRONT, phase("ready"), JOB_PHASES, ARRIVING, 0.11, *SHOULDERS))

    def test_a_held_ball_is_always_drawn(self):
        self.assertIsNone(A.leave_ball_out("front", FRONT, phase("contact"), JOB_PHASES, ARRIVING, 0.11, *SHOULDERS))

    def test_a_leaving_ball_is_drawn_even_over_her_face(self):
        # The release comes after the first holding phase: the owner kept those.
        self.assertIsNone(A.leave_ball_out("front", FRONT, phase("release"), JOB_PHASES, ARRIVING, 0.11, *SHOULDERS))

    def test_an_arriving_ball_clear_of_her_is_drawn(self):
        beside = [0.9, -1.9881, 1.2845]
        self.assertIsNone(A.leave_ball_out("front", FRONT, phase("ready"), JOB_PHASES, beside, 0.11, *SHOULDERS))

    def test_a_ball_behind_her_is_drawn(self):
        # On the line from the camera through her head, beyond her: it covers
        # her head in the picture, so only the depth check can keep it.
        behind = [0.0, 1.0, 1.612]
        self.assertIsNotNone(A.leave_ball_out("front", FRONT, phase("ready"), JOB_PHASES,
                                              [0.0, -1.0, 1.35], 0.11, *SHOULDERS))
        self.assertIsNone(A.leave_ball_out("front", FRONT, phase("ready"), JOB_PHASES, behind, 0.11, *SHOULDERS))

    def test_a_drill_that_never_holds_the_ball_keeps_it(self):
        never = [dict(p, ball={"holding": False}) for p in JOB_PHASES]
        self.assertIsNone(A.leave_ball_out("front", FRONT, never[0], never, ARRIVING, 0.11, *SHOULDERS))


class RendererWiringTest(unittest.TestCase):
    """The renderer runs only in Blender, so its source is read here."""

    def render_job(self):
        import ast
        source = (Path(__file__).resolve().parents[1] / "blender_movement_render.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        return next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "render_job")

    def test_each_still_view_asks_the_rule_before_it_renders(self):
        function = self.render_job()
        calls = [(n.lineno, n.func.id) for n in ast_walk(function)
                 if type(n).__name__ == "Call" and type(n.func).__name__ == "Name"]
        asked = min(line for line, name in calls if name == "leave_ball_out")
        rendered = min(line for line, name in calls if name == "render_view")
        self.assertLess(asked, rendered)

    def test_the_ball_is_shown_again_after_each_render(self):
        function = self.render_job()
        tries = [n for n in ast_walk(function) if type(n).__name__ == "Try" and n.finalbody]
        restored = [t for t in tries
                    if any(type(a).__name__ == "Assign" and getattr(a.targets[0], "attr", "") == "hide_render"
                           and getattr(a.value, "value", None) is False
                           for s in t.finalbody for a in ast_walk(s))]
        self.assertTrue(restored, "no finally block sets hide_render back to False")

    def test_the_receipt_says_whether_the_ball_was_drawn(self):
        source = (Path(__file__).resolve().parents[1] / "blender_movement_render.py").read_text(encoding="utf-8")
        self.assertIn('["ballDrawn"]', source)
        self.assertIn('["ballLeftOut"]', source)


def ast_walk(node):
    import ast
    return ast.walk(node)


class ProjectionTest(unittest.TestCase):
    def test_the_projection_is_blenders(self):
        # Blender 4.5.12 world_to_camera_view, front camera, 13 Nov 2026.
        x, y, _ = A.project(FRONT, (0.3, -0.5, 1.6))
        self.assertAlmostEqual(x, 750.5, delta=0.06)
        self.assertAlmostEqual(y, 231.5, delta=0.06)


if __name__ == "__main__":
    unittest.main()
