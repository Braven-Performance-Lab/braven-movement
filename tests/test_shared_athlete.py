"""The renderer finds the shared athlete through its manifest, never a path.

Goal "Switch the manual figures to the shared athlete", step 2. The athlete is
a build folder whose `athlete-manifest.json` names every file relative to the
folder. The renderer validates that folder with the Models lane's own
validator and takes the editable master from the file whose role is
`master`. Nothing here reads a machine path from the manifest (MAN-5).
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "athlete"))

import athlete_manifest  # noqa: E402
from asset_licences import CC0, LicenceUndetermined  # noqa: E402
from shared_athlete import (  # noqa: E402
    SharedAthleteRefusal,
    athlete_master,
    constraint_to_mute,
    contract_renames,
    external_asset_records,
    head_bone_name,
    master_record,
)


def manifest(files):
    return {"format": "braven-athlete-manifest", "formatVersion": 1,
            "asset": {"name": "x", "revision": 9}, "files": files}


class AthleteMasterTest(unittest.TestCase):
    def test_the_master_is_the_file_whose_role_is_master(self):
        with tempfile.TemporaryDirectory() as folder:
            files = {"netball-athlete.glb": {"role": "model", "sha256": "a" * 64},
                     "netball-athlete.blend": {"role": "master", "sha256": "b" * 64}}
            with mock.patch.object(athlete_manifest, "validate", return_value=manifest(files)) as validate:
                found, master = athlete_master(Path(folder))
            validate.assert_called_once_with(Path(folder))
            self.assertEqual(master, Path(folder) / "netball-athlete.blend")
            self.assertEqual(found["asset"]["revision"], 9)

    def test_a_folder_the_validator_refuses_is_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            refusal = athlete_manifest.ManifestRefusal("rig", "the joint set differs")
            with mock.patch.object(athlete_manifest, "validate", side_effect=refusal):
                with self.assertRaises(SharedAthleteRefusal) as caught:
                    athlete_master(Path(folder))
            self.assertIn("joint set", str(caught.exception))

    def test_no_master_or_two_masters_is_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            for files in ({"a.glb": {"role": "model"}},
                          {"a.blend": {"role": "master"}, "b.blend": {"role": "master"}}):
                with mock.patch.object(athlete_manifest, "validate", return_value=manifest(files)):
                    with self.assertRaises(SharedAthleteRefusal):
                        athlete_master(Path(folder))


class SharedAssetLicenceTest(unittest.TestCase):
    """Step 3: the licence check reads the athlete manifest.

    Each external asset the manifest lists is licensed by THIS repository's
    determination (`asset_licences.licence_for`), never by the manifest's own
    words, which are recorded beside it. The master file is licensed the same
    way; until `docs/LICENSING.md` determines the athlete's own build output,
    it is refused.
    """

    MANIFEST = {
        "source": {"externalAssets": [
            {"name": "mpfb/hair/ponytail01/ponytail01.mhclo",
             "licence": "CC0 declared in source header", "sha256": "c" * 64},
        ]},
        "files": {"netball-athlete.blend": {"role": "master", "sha256": "d" * 64}},
    }

    def test_a_listed_mpfb_asset_takes_the_repository_determination(self):
        records = external_asset_records(self.MANIFEST)
        self.assertEqual(records[0]["licence"], CC0)
        self.assertEqual(records[0]["sha256"], "c" * 64)
        self.assertEqual(records[0]["manifestLicence"], "CC0 declared in source header")

    def test_an_external_asset_with_no_determination_is_refused(self):
        unknown = {"source": {"externalAssets": [
            {"name": "mpfb/hair/bob02/bob02.mhclo", "licence": "CC0", "sha256": "e" * 64}]}}
        with self.assertRaises(LicenceUndetermined):
            external_asset_records(unknown)

    def test_the_athlete_build_output_has_no_determination_yet(self):
        with self.assertRaises(LicenceUndetermined):
            master_record(self.MANIFEST, Path("build") / "netball-athlete.blend")


class ContractNameTest(unittest.TestCase):
    """Main's correction, 12 Nov 2026 (spec 3, 12.7): the rig contract spells
    the bones `Head` and `root`, the shared athlete already does, and only
    this renderer read `head`. The renderer reads the contract names; its own
    generated body is given them when it is built; the athlete is renamed
    in nothing."""

    def test_the_renderer_reads_the_contract_spelling(self):
        self.assertEqual(head_bone_name(["neck_01", "Head"]), "Head")
        self.assertIn("Head", athlete_manifest.CONTRACT_BONES)
        self.assertIn("root", athlete_manifest.CONTRACT_BONES)

    def test_the_old_spelling_is_refused_not_renamed(self):
        with self.assertRaises(SharedAthleteRefusal):
            head_bone_name(["neck_01", "head"])

    def test_the_generated_body_takes_the_contract_names(self):
        """The same two renames `athlete/build.py` makes for the athlete."""
        self.assertEqual(contract_renames(["Root", "pelvis", "neck_01", "head"]),
                         {"Root": "root", "head": "Head"})
        # A body already on the contract needs nothing.
        self.assertEqual(contract_renames(["root", "pelvis", "Head"]), {})

    def test_a_body_with_both_spellings_is_refused(self):
        with self.assertRaises(SharedAthleteRefusal):
            contract_renames(["Root", "root", "head"])


class ConstraintRuleTest(unittest.TestCase):
    """Only the four IK constraints that drive the limbs from the CTRL_*
    targets are muted; any other constraint would change the body in a way
    nobody measured, so it is refused."""

    def test_an_ik_constraint_on_a_control_target_is_muted(self):
        self.assertTrue(constraint_to_mute("lowerarm_l", "IK", "CTRL_hand_l"))

    def test_any_other_constraint_is_refused(self):
        for kind, target in (("COPY_ROTATION", "CTRL_hand_l"), ("IK", "spine_03"), ("CHILD_OF", "")):
            with self.assertRaises(SharedAthleteRefusal):
                constraint_to_mute("skirt_04", kind, target)


class SharedAthleteWiringTest(unittest.TestCase):
    """The Blender side of the switch, pinned on the syntax tree.

    `load_shared_athlete`, the `--athlete` branch of `Studio.__init__` and the
    receipt run only inside Blender, where the host suite cannot reach them.
    These pin the order and the calls a change could quietly lose. The
    behaviour itself was measured in Blender and is recorded in
    `docs/SHARED_ATHLETE_2026-11-12.md`.
    """

    import ast as _ast
    TREE = _ast.parse((REPO / "blender_movement_render.py").read_text(encoding="utf-8"))

    def function(self, name, tree=None):
        for node in self._ast.walk(tree or self.TREE):
            if isinstance(node, self._ast.FunctionDef) and node.name == name:
                return node
        self.fail(f"no function {name}")

    def calls(self, node):
        return [(n.lineno, n.func.id) for n in self._ast.walk(node)
                if isinstance(n, self._ast.Call) and isinstance(n.func, self._ast.Name)]

    def test_the_licence_is_checked_before_the_athlete_is_loaded(self):
        studio = next(n for n in self.TREE.body if isinstance(n, self._ast.ClassDef) and n.name == "Studio")
        init = self.function("__init__", studio)
        order = {name: line for line, name in sorted(self.calls(init), reverse=True)}
        for name in ("athlete_master", "master_record", "external_asset_records", "load_shared_athlete"):
            self.assertIn(name, order, f"Studio.__init__ must call {name}")
        self.assertLess(order["master_record"], order["load_shared_athlete"])
        self.assertLess(order["external_asset_records"], order["load_shared_athlete"])
        self.assertLess(order["athlete_master"], order["master_record"])

    def test_the_loader_checks_the_head_and_the_constraints(self):
        names = {name for _, name in self.calls(self.function("load_shared_athlete"))}
        self.assertIn("head_bone_name", names)
        self.assertIn("constraint_to_mute", names)

    def test_every_receipt_names_its_athlete(self):
        render_job = self.function("render_job")
        keys = [k.value for n in self._ast.walk(render_job) if isinstance(n, self._ast.Dict)
                for k in n.keys if isinstance(k, self._ast.Constant)]
        self.assertIn("athlete", keys)
        self.assertIn("sourceAssets", keys)


if __name__ == "__main__":
    unittest.main()
