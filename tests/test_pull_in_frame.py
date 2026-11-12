"""Guards for the instrument behind spec 1 decision 12.8.

`scripts/pull_in_frame.py` reads the two-hand catch's pull-in checkpoints at
the definition's frame (0.72) and at the ball key's frame (0.76), and pairs
every drill's coaching phases with its ball keys by name. These tests cover
the parts that need no solve: the frame a phase reads, the moved definition,
and the pairing. Each test names the mutation it kills.
"""
import dataclasses
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# APPEND, never insert first: spikes/ has its own test_*.py files, and a folder
# placed first would hide tests/ modules of the same name from discovery.
for folder in (ROOT / "scripts", ROOT / "spikes"):
    if str(folder) not in sys.path:
        sys.path.append(str(folder))

import pull_in_frame  # noqa: E402
from movement_definition import MovementDefinitionError, load  # noqa: E402

CATCH = ROOT / "spikes" / "movements" / "netball_two_hand_catch_chest.json"


class TheFrameAPhaseReads(unittest.TestCase):
    """Mutation: the frame index uses the frame count, not the last index."""

    def test_the_catch_reads_frame_70_and_its_key_sits_at_frame_74(self):
        self.assertEqual(70, pull_in_frame.frame_index(0.72, 98))
        self.assertEqual(74, pull_in_frame.frame_index(0.76, 98))

    def test_the_index_matches_what_assess_reads(self):
        # MovementDefinition.assess reads round(at_phase * last).
        self.assertEqual(round(0.5 * 9), pull_in_frame.frame_index(0.5, 10))
        self.assertEqual(9, pull_in_frame.frame_index(1.0, 10))
        self.assertEqual(0, pull_in_frame.frame_index(0.0, 10))


class TheMovedDefinition(unittest.TestCase):
    """Mutations: the move changes another phase, or a wrong name passes."""

    def setUp(self):
        self.definition = load(CATCH)

    def test_only_the_named_phase_moves(self):
        moved = pull_in_frame.moved_definition(self.definition, "pull_in", 0.76)
        before = {p.name: p for p in self.definition.phases}
        after = {p.name: p for p in moved.phases}
        self.assertEqual(0.76, after["pull_in"].at_phase)
        self.assertEqual(before["pull_in"].checkpoints, after["pull_in"].checkpoints)
        for name in before:
            if name != "pull_in":
                self.assertEqual(before[name], after[name])

    def test_an_unknown_phase_is_refused(self):
        with self.assertRaises(SystemExit):
            pull_in_frame.moved_definition(self.definition, "pull_out", 0.76)

    def test_a_move_before_the_previous_phase_is_refused(self):
        # contact is at 0.45, so pull_in at 0.40 breaks the phase order.
        with self.assertRaises(MovementDefinitionError):
            pull_in_frame.moved_definition(self.definition, "pull_in", 0.40)

    def test_assess_reads_the_moved_frame(self):
        # Frame i carries the value i, so the measured value IS the frame read.
        frames = [{"leftElbowFlexionDegrees": float(i), "trunkLeanDegrees": float(i),
                   "leftKneeFlexionDegrees": float(i), "rightElbowFlexionDegrees": float(i)}
                  for i in range(98)]
        for at, frame in ((0.72, 70), (0.76, 74)):
            moved = pull_in_frame.moved_definition(self.definition, "pull_in", at)
            results = moved.assess(frames).results["pull_in"]
            self.assertTrue(results)
            self.assertEqual({float(frame)}, {r.measured for r in results})


class ThePairingByName(unittest.TestCase):
    """Mutations: unnamed keys are paired, a one-sided name is paired, or the
    tolerance swallows a real difference."""

    def test_named_keys_are_found_at_any_depth_and_unnamed_ones_are_skipped(self):
        document = {"release": {"atPhase": 0.92},
                    "afterContact": [{"name": "pull_in", "atPhase": 0.76},
                                     {"name": "send_back", "atPhase": 0.92}],
                    "keys": [{"name": "ready", "atPhase": 0.0}]}
        found = pull_in_frame.named_keys(document)
        self.assertEqual({("pull_in", 0.76), ("send_back", 0.92), ("ready", 0.0)},
                         {(name, at) for _, name, at in found})

    def test_a_shared_name_is_paired_and_its_gap_reported(self):
        rows = pull_in_frame.pair(
            {"phases": [{"name": "pull_in", "atPhase": 0.72},
                        {"name": "ready", "atPhase": 0.0},
                        {"name": "only_here", "atPhase": 0.5}]},
            {"x.technique.json": {"afterContact": [{"name": "pull_in", "atPhase": 0.76}],
                                  "other": [{"name": "ready", "atPhase": 0.0},
                                            {"name": "only_there", "atPhase": 0.3}]}})
        by_name = {row["name"]: row for row in rows}
        self.assertEqual({"pull_in", "ready"}, set(by_name))
        self.assertAlmostEqual(0.04, by_name["pull_in"]["gap"], places=9)
        self.assertTrue(by_name["pull_in"]["differs"])
        self.assertFalse(by_name["ready"]["differs"])

    def test_the_smallest_real_gap_is_a_difference(self):
        rows = pull_in_frame.pair(
            {"phases": [{"name": "drive", "atPhase": 0.62}]},
            {"x.motion.json": {"keys": [{"name": "drive", "atPhase": 0.63}]}})
        self.assertTrue(rows[0]["differs"])

    def test_a_motion_only_gap_is_not_counted_against_the_technique_file(self):
        # Mutation: the technique count also takes motion-only gaps.
        drills = [{"drill": "a", "files": [], "rows": pull_in_frame.pair(
                       {"phases": [{"name": "contact", "atPhase": 0.55}]},
                       {"a.motion.json": {"keys": [{"name": "contact", "atPhase": 0.50}]},
                        "a.technique.json": {"keys": [{"name": "contact", "atPhase": 0.55}]}})},
                  {"drill": "b", "files": [], "rows": pull_in_frame.pair(
                       {"phases": [{"name": "drive", "atPhase": 0.62}]},
                       {"b.technique.json": {"keys": [{"name": "drive", "atPhase": 0.71}]}})}]
        total = pull_in_frame.counts(drills)
        self.assertEqual(2, total["differ"])
        self.assertEqual(1, total["differ_technique"])

    def test_the_library_counts_on_this_tree(self):
        # Mutation: either count drifts from the reading the report records.
        total = pull_in_frame.counts(pull_in_frame.library_pairs(ROOT / "spikes" / "movements"))
        self.assertEqual((12, 8, 7, 4, 0), (total["drills"], total["differ"],
                                            total["differ_technique"], total["agree"],
                                            total["unpaired"]))

    def test_the_library_has_drills_on_both_sides_of_the_split(self):
        drills = pull_in_frame.library_pairs(ROOT / "spikes" / "movements")
        differ = [d for d in drills if any(r["differs"] for r in d["rows"])]
        agree = [d for d in drills if d["rows"] and not any(r["differs"] for r in d["rows"])]
        self.assertIn("netball_two_hand_catch_chest", {d["drill"] for d in differ})
        self.assertTrue(agree, "no drill agrees: the pairing cannot separate")


def synthetic_frames(count=98):
    """Frame i carries the value i in every measure the catch grades."""
    return [{"leftElbowFlexionDegrees": float(i), "trunkLeanDegrees": float(i),
             "leftKneeFlexionDegrees": float(i), "rightElbowFlexionDegrees": float(i)}
            for i in range(count)]


class TheRefusals(unittest.TestCase):
    """Every refusal of the solve path, reached without a solve. Each test is
    the mutation that disables that refusal."""

    def setUp(self):
        self.definition = load(CATCH)
        self.technique = json.loads(CATCH.with_name(
            "netball_two_hand_catch_chest.technique.json").read_text(encoding="utf-8"))

    def test_the_committed_files_pass(self):
        self.assertEqual((0.72, 0.76), pull_in_frame.held_frames(self.definition, self.technique))

    def test_a_moved_definition_phase_is_refused(self):
        moved = pull_in_frame.moved_definition(self.definition, "pull_in", 0.74)
        with self.assertRaisesRegex(SystemExit, "the files hold 0.74 and 0.76"):
            pull_in_frame.held_frames(moved, self.technique)

    def test_a_moved_technique_key_is_refused(self):
        self.technique["afterContact"][0]["atPhase"] = 0.78
        with self.assertRaisesRegex(SystemExit, "the files hold 0.72 and 0.78"):
            pull_in_frame.held_frames(self.definition, self.technique)

    def test_a_second_definition_phase_of_the_name_is_refused(self):
        phases = self.definition.phases
        pull_in = next(p for p in phases if p.name == "pull_in")
        doubled = dataclasses.replace(self.definition, phases=tuple(
            q for p in phases for q in ((p, pull_in) if p is pull_in else (p,))))
        with self.assertRaisesRegex(SystemExit, "holds 2 pull_in phases"):
            pull_in_frame.held_frames(doubled, self.technique)

    def test_a_second_technique_key_of_the_name_is_refused(self):
        self.technique["afterContact"].append({"name": "pull_in", "atPhase": 0.76})
        with self.assertRaisesRegex(SystemExit, "holds 2 pull_in keys"):
            pull_in_frame.held_frames(self.definition, self.technique)

    def test_a_missing_technique_key_is_refused(self):
        self.technique["afterContact"][0]["name"] = "pulled_in"
        with self.assertRaisesRegex(SystemExit, "holds 0 pull_in keys"):
            pull_in_frame.held_frames(self.definition, self.technique)

    def test_both_readings_come_from_their_own_frames(self):
        readings = pull_in_frame.read_both(self.definition, synthetic_frames(), 0.72)
        self.assertEqual({70.0}, {r.measured for r in readings[0.72]})
        self.assertEqual({74.0}, {r.measured for r in readings[0.76]})

    def test_a_move_that_misses_the_shipped_frame_fails_the_control(self):
        def drifting(definition, name, at):
            return pull_in_frame.moved_definition(definition, name, round(at + 0.02, 6))
        with self.assertRaisesRegex(SystemExit, "does not reproduce the shipped one"):
            pull_in_frame.read_both(self.definition, synthetic_frames(), 0.72, move=drifting)


class TheCommittedFiles(unittest.TestCase):
    """Mutation: the instrument measures a state the files no longer hold."""

    def test_the_files_still_hold_0_72_and_0_76(self):
        definition = json.loads(CATCH.read_text(encoding="utf-8"))
        technique = json.loads(CATCH.with_name(
            "netball_two_hand_catch_chest.technique.json").read_text(encoding="utf-8"))
        self.assertEqual(0.72, {p["name"]: p["atPhase"] for p in definition["phases"]}["pull_in"])
        self.assertEqual(0.76, {n: a for _, n, a in pull_in_frame.named_keys(technique)}["pull_in"])
        self.assertEqual((0.72, 0.76), pull_in_frame.FRAMES_AT)


if __name__ == "__main__":
    unittest.main()
