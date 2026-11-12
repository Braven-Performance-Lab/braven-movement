"""The trunk turn: the solve's own value, crossed into this rig's axes.

`netball_hooks_outside_hand` turns the trunk 48 degrees at `facing_away`. The
job carried that turn only as shoulder displacements, and this rig can reach
them only with its clavicles, so the right shoulder missed by 52 mm and the
ball inherited 20.45 mm (`docs/BALL_HAND_GAP_2026-11-12.md`). The job now
carries the turn itself, read from the solve (`result["turns"]`), and the
renderer turns the trunk before it poses the girdle.

The sign is the part a person gets wrong. The engine is Y up and Blender is Z
up, and the exporter's `to_blender` swaps and negates an axis. So the test
runs the engine's own `turn_matrix` and the exporter's own `to_blender`,
read from its source, and never a copy of either.
"""

import ast
import math
import sys
import unittest
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "spikes"))

from girdle_agreement import (  # noqa: E402
    TRUNK_TURN_FIELD,
    trunk_turn_degrees,
    trunk_turn_matrix,
)
from motion_track import turn_matrix  # noqa: E402


def producers_to_blender():
    """`to_blender` as the exporter defines it, executed from its source.

    The exporter imports the engine, which a host test cannot load. Its axis
    conversion is three lines of numpy, so it is lifted out of the file by its
    syntax tree and run, rather than retyped here.
    """
    source = (REPO / "spikes" / "export_blender_job.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "to_blender"
    )
    namespace = {"np": np}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "to_blender", "exec"), namespace)
    return namespace["to_blender"]


class TrunkTurnTest(unittest.TestCase):
    def test_a_turn_in_the_engine_is_the_same_turn_in_blender(self):
        """Turn then convert must equal convert then turn, for any point."""
        to_blender = producers_to_blender()
        point = np.array([12.0, 140.0, -7.5])  # centimetres, MHR, off every axis
        for degrees in (48.0, 22.27, -30.0, 4.0):
            engine = to_blender(turn_matrix(degrees) @ point)
            rig = np.array(trunk_turn_matrix(degrees)) @ to_blender(point)
            np.testing.assert_allclose(rig, engine, atol=1e-12, err_msg=f"{degrees} degrees")

    def test_the_turn_is_about_the_vertical_and_moves_nothing_vertical(self):
        matrix = np.array(trunk_turn_matrix(48.0))
        np.testing.assert_allclose(matrix @ [0.0, 0.0, 1.0], [0.0, 0.0, 1.0], atol=1e-15)
        self.assertAlmostEqual(np.linalg.det(matrix), 1.0, places=12)

    def test_no_turn_is_exactly_no_rotation(self):
        """Eleven drills turn 0.00 at every graded phase and must not move."""
        self.assertEqual(
            trunk_turn_matrix(0.0),
            ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        )

    def test_a_missing_turn_stops_the_frame(self):
        """A job without the field would render the trunk unturned, which is
        the defect the field removes. It must not read as a turn of zero."""
        with self.assertRaises(ValueError) as caught:
            trunk_turn_degrees({"name": "facing_away"}, "hooks/facing_away")
        self.assertIn(TRUNK_TURN_FIELD, str(caught.exception))
        with self.assertRaises(ValueError):
            trunk_turn_degrees({TRUNK_TURN_FIELD: float("nan")}, "hooks/facing_away")
        self.assertEqual(trunk_turn_degrees({TRUNK_TURN_FIELD: 48.0}, "x"), 48.0)

    def test_the_exporter_writes_the_solves_turn_into_each_phase(self):
        """The field is read from the solve's `turns`, at the phase's frame.

        Matched on the syntax tree, so a mention in a comment cannot satisfy
        it. The value itself is measured against the solve by running the
        exporter; this pins that the producer reads `result["turns"]` and
        nothing rebuilt from the shoulders.
        """
        source = (REPO / "spikes" / "export_blender_job.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        phase_job = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "phase_job"
        )
        keys = [
            node for node in ast.walk(phase_job)
            if isinstance(node, ast.Constant) and node.value == TRUNK_TURN_FIELD
        ]
        self.assertTrue(keys, "phase_job must write the trunk turn")
        reads_turns = any(
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name) and node.value.id == "result"
            and isinstance(node.slice, ast.Constant) and node.slice.value == "turns"
            for node in ast.walk(phase_job)
        )
        self.assertTrue(reads_turns, 'phase_job must read result["turns"]')


class TrunkTurnWiringTest(unittest.TestCase):
    def test_the_renderer_turns_the_trunk_before_it_poses_the_girdle(self):
        """After the girdle would be too late: the clavicles would already be
        aimed at shoulders the unturned trunk cannot reach. Matched on the
        syntax tree of `pose_phase`, in call order."""
        tree = ast.parse((REPO / "blender_movement_render.py").read_text(encoding="utf-8"))
        pose_phase = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "pose_phase"
        )
        order = [
            node.func.id for node in ast.walk(pose_phase)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in ("pose_stance", "pose_trunk_turn", "trunk_turn_degrees", "pose_girdle")
        ]
        calls = sorted(
            (node.lineno, node.func.id) for node in ast.walk(pose_phase)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in order
        )
        names = [name for _, name in calls]
        for needed in ("pose_trunk_turn", "trunk_turn_degrees", "pose_girdle"):
            self.assertIn(needed, names)
        self.assertLess(names.index("pose_trunk_turn"), names.index("pose_girdle"))
        self.assertLess(names.index("pose_stance"), names.index("pose_trunk_turn"))


if __name__ == "__main__":
    unittest.main()
