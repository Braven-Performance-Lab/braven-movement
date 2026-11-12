"""The shoulder shift crosses in GIRDLE WIDTHS, so each body scales it by its own.

Measured on `0ee45ee`: with the trunk turned, `hooks_outside_hand/facing_away`
still missed the 10 mm anchor rule by 8 mm. The solve's girdle is about 16 per
cent wider relative to its torso than this rig's (339 mm wanted against 291 mm
drawn), so the same 48 degree turn moves the solve's shoulder 16.8 cm and this
rig's 12.6 cm. A shift sent in torso lengths asks this rig for the solve's
16.8 cm, which its shoulders cannot reach without a girdle it does not have.

A turn moves a shoulder along a circle whose radius is half the girdle width.
Divide the displacement by the girdle width and multiply by the receiving
body's own, and a turn lands exactly where that body's own turn puts it.
"""

import ast
import math
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from girdle_agreement import resolve  # noqa: E402

GIRDLE_FIELD = "shoulderShiftFromRestInGirdles"


def turned(point, degrees):
    angle = math.radians(degrees)
    x, y, z = point
    return (x * math.cos(angle) - y * math.sin(angle),
            x * math.sin(angle) + y * math.cos(angle), z)


class GirdleWidthUnitTest(unittest.TestCase):
    # Pelvis-relative rest shoulders, metres. The 339 mm "wanted" width is the
    # solve's girdle already scaled onto this rig by torso length, so the
    # solve's own width over torso is 339 / 428 = 0.79, against this rig's
    # 291 / 428 = 0.68. Its torso is 49.65 cm (`rest_torso`), so its width is
    # about 0.79 * 0.4965 = 0.393 m.
    SOLVE = {"width": 0.393, "torso": 0.4965}
    RIG = {"width": 0.291, "torso": 0.4277}

    def right_shoulder(self, body):
        return (-body["width"] / 2.0, 0.0, body["torso"])

    def test_a_turn_sent_in_girdle_widths_lands_on_the_receiving_bodys_turn(self):
        solve, rig = self.right_shoulder(self.SOLVE), self.right_shoulder(self.RIG)
        for degrees in (48.0, 22.27, -30.0):
            moved = turned(solve, degrees)
            shift = [(a - b) / self.SOLVE["width"] for a, b in zip(moved, solve)]
            landed = resolve(shift, rig, self.RIG["width"])
            for got, want in zip(landed, turned(rig, degrees)):
                self.assertAlmostEqual(got, want, places=12, msg=f"{degrees} degrees")

    def test_the_same_turn_sent_in_torso_lengths_misses(self):
        """The defect this unit removes, at the measured 48 degrees."""
        solve, rig = self.right_shoulder(self.SOLVE), self.right_shoulder(self.RIG)
        moved = turned(solve, 48.0)
        shift = [(a - b) / self.SOLVE["torso"] for a, b in zip(moved, solve)]
        landed = resolve(shift, rig, self.RIG["torso"])
        miss = math.dist(landed, turned(rig, 48.0))
        self.assertGreater(miss, 0.005, "torso units must miss a turned shoulder")


class GirdleWidthWiringTest(unittest.TestCase):
    def test_the_exporter_writes_the_shift_in_girdle_widths(self):
        tree = ast.parse((REPO / "spikes" / "export_blender_job.py").read_text(encoding="utf-8"))
        phase_job = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "phase_job")
        self.assertTrue(any(isinstance(n, ast.Constant) and n.value == GIRDLE_FIELD
                            for n in ast.walk(phase_job)), "phase_job must write the girdle-width shift")
        self.assertTrue(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                            and n.func.id == "rest_girdle_width" for n in ast.walk(phase_job)),
                        "the divisor must be the solve's rest girdle width")

    def test_the_renderer_reads_that_field_and_scales_by_its_own_girdle(self):
        tree = ast.parse((REPO / "blender_movement_render.py").read_text(encoding="utf-8"))
        field = next(
            n.value.value for n in tree.body
            if isinstance(n, ast.Assign) and any(getattr(t, "id", None) == "GIRDLE_FIELD" for t in n.targets)
        )
        self.assertEqual(field, GIRDLE_FIELD)
        pose_girdle = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "pose_girdle")
        scales_by_girdle = any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "shoulder_position"
            and any(isinstance(a, ast.Subscript) and isinstance(a.slice, ast.Constant)
                    and a.slice.value == "girdle" for a in n.args)
            for n in ast.walk(pose_girdle)
        )
        self.assertTrue(scales_by_girdle, 'pose_girdle must resolve with rest["girdle"]')


if __name__ == "__main__":
    unittest.main()
