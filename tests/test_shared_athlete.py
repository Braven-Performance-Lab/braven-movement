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
from types import SimpleNamespace
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "athlete"))

import athlete_manifest  # noqa: E402
import shared_athlete  # noqa: E402
from asset_licences import CC0, LicenceUndetermined  # noqa: E402
from shared_athlete import (  # noqa: E402
    SharedAthleteRefusal,
    athlete_master,
    athlete_record,
    constraint_to_mute,
    contract_renames,
    descendant_is_mesh,
    driver_is_inert,
    external_asset_records,
    head_bone_name,
    master_record,
    node_tree_holders,
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

    def test_the_folder_it_sits_in_cannot_license_the_master(self):
        """The determination is made on the FILE, not the folder's path: a
        build folder under an `assets/kit/` path is not own work by place."""
        with self.assertRaises(LicenceUndetermined):
            master_record(self.MANIFEST, Path("x") / "assets" / "kit" / "netball-athlete.blend")


class AthleteRecordTest(unittest.TestCase):
    """Step 4: every receipt names the athlete by its revision and GLB SHA-256."""

    MANIFEST = {
        "asset": {"name": "Braven netball athlete", "revision": 9},
        "rig": {"family": "braven-athlete-v6"},
        "files": {"netball-athlete.glb": {"role": "model", "sha256": "a" * 64},
                  "netball-athlete.blend": {"role": "master", "sha256": "b" * 64},
                  "movement-library.json": {"role": "library", "sha256": "c" * 64}},
    }

    def test_the_record_names_the_revision_and_both_hashes(self):
        record = athlete_record(self.MANIFEST, Path("build") / "netball-athlete.blend")
        self.assertEqual(record, {
            "kind": "shared", "name": "Braven netball athlete", "revision": 9,
            "glbSha256": "a" * 64, "masterSha256": "b" * 64, "rigFamily": "braven-athlete-v6"})

    def test_every_hash_a_receipt_copies_is_lower_case(self):
        # Review round 5: the validator accepts upper-case hex, and a receipt
        # that copied it would not compare byte for byte with the others.
        upper = {**self.MANIFEST, "files": {
            name: {**entry, "sha256": entry["sha256"].upper()}
            for name, entry in self.MANIFEST["files"].items()}}
        master = Path("build") / "netball-athlete.blend"
        record = athlete_record(upper, master)
        self.assertEqual((record["glbSha256"], record["masterSha256"]), ("a" * 64, "b" * 64))
        with mock.patch.object(shared_athlete, "licence_for", return_value=("CC0", "test")):
            self.assertEqual(master_record(upper, master)["sha256"], "b" * 64)
            assets = {"source": {"externalAssets": [
                {"name": "skin.png", "sha256": "D" * 64, "licence": "CC0"}]}}
            self.assertEqual(external_asset_records(assets)[0]["sha256"], "d" * 64)

    def test_a_manifest_with_no_model_file_is_refused(self):
        files = {k: v for k, v in self.MANIFEST["files"].items() if v["role"] != "model"}
        with self.assertRaises(SharedAthleteRefusal):
            athlete_record({**self.MANIFEST, "files": files}, Path("build") / "netball-athlete.blend")


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


class DriverRuleTest(unittest.TestCase):
    """Review round 2: drivers were neither muted nor refused. Build
    09-gait-v2 has four, and each drives only the influence of one of the
    four IK constraints the loader mutes, so they change nothing. That is
    the only kind of driver accepted; any other is refused."""

    MUTED = {("lowerarm_l", "Hand IK (enable on rig custom properties)")}

    def test_a_driver_on_a_muted_constraints_influence_is_accepted(self):
        path = 'pose.bones["lowerarm_l"].constraints["Hand IK (enable on rig custom properties)"].influence'
        self.assertTrue(driver_is_inert(path, self.MUTED))

    def test_any_other_driver_is_refused(self):
        for path in ('pose.bones["lowerarm_r"].constraints["Hand IK (enable on rig custom properties)"].influence',
                     'pose.bones["spine_02"].rotation_quaternion',
                     'pose.bones["lowerarm_l"].constraints["Hand IK (enable on rig custom properties)"].pole_angle'):
            with self.assertRaises(SharedAthleteRefusal):
                driver_is_inert(path, self.MUTED)


def tree(name, *nodes, drivers=None):
    """A stand-in node tree: a name, nodes, and animation data or none."""
    return SimpleNamespace(name=name, nodes=list(nodes), animation_data=drivers)


class NodeTreeHolderTest(unittest.TestCase):
    """Review rounds 6 and 7 of PR #152: a node group nested in a material's
    node tree, and the group of a geometry-nodes modifier, are node trees of
    their own, each with its own animation data. The loader read neither."""

    def test_every_nested_group_is_read_once(self):
        inner = tree("Inner", drivers="inner-data")
        middle = tree("Middle", SimpleNamespace(node_tree=inner), drivers="middle-data")
        top = tree("Material", SimpleNamespace(node_tree=middle),
                   SimpleNamespace(node_tree=inner), SimpleNamespace(), drivers="top-data")
        self.assertEqual(node_tree_holders(top), ["top-data", "middle-data", "inner-data"])

    def test_two_trees_with_one_name_are_both_read(self):
        # Review round 1 of the re-render branch (must): every material's
        # embedded tree is named 'Shader Nodetree', so a check by name read
        # only the first material on a mesh and skipped every later one.
        first = tree("Shader Nodetree", drivers="first-data")
        second = tree("Shader Nodetree", drivers="second-data")
        seen = set()
        holders = node_tree_holders(first, seen) + node_tree_holders(second, seen)
        self.assertEqual(holders, ["first-data", "second-data"])

    def test_identity_is_the_blender_pointer_when_there_is_one(self):
        # Blender gives a new wrapper at each read, so two reads of one tree
        # share only `as_pointer()`.
        one = tree("Group", drivers="group-data")
        one.as_pointer = lambda: 4096
        again = tree("Group", drivers="group-data")
        again.as_pointer = lambda: 4096
        seen = set()
        self.assertEqual(node_tree_holders(one, seen) + node_tree_holders(again, seen), ["group-data"])

    def test_a_group_that_contains_itself_ends(self):
        loop = tree("Loop", drivers="loop-data")
        loop.nodes.append(SimpleNamespace(node_tree=loop))
        self.assertEqual(node_tree_holders(loop), ["loop-data"])

    def test_no_tree_gives_no_holder(self):
        self.assertEqual(node_tree_holders(None), [])


class DescendantKindTest(unittest.TestCase):
    """Review round 6 of PR #152: an image empty under the rig stopped the
    loader with an AttributeError, not the loader's refusal. Every descendant
    the loader links must be a mesh; build 09-gait-v2 has only meshes."""

    def test_a_mesh_is_accepted(self):
        self.assertTrue(descendant_is_mesh("Kit_Jersey", "MESH"))

    def test_any_other_kind_is_refused(self):
        for kind in ("EMPTY", "CURVE", "LIGHT", "ARMATURE"):
            with self.assertRaises(SharedAthleteRefusal):
                descendant_is_mesh("Thing", kind)


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
        # Review round 2: drivers are checked, not left in place unread.
        self.assertIn("driver_is_inert", names)
        # Review rounds 6 and 7: nested node groups, and only meshes linked.
        self.assertIn("node_tree_holders", names)
        self.assertIn("descendant_is_mesh", names)

    def test_the_loader_hashes_the_file_before_it_reads_it(self):
        loader = self.function("load_shared_athlete")
        hashed = min(line for line, name in self.calls(loader) if name == "sha256")
        loaded = min(n.lineno for n in self._ast.walk(loader)
                     if isinstance(n, self._ast.Attribute) and n.attr == "libraries")
        self.assertLess(hashed, loaded)

    def test_the_receipt_record_comes_from_the_tested_function(self):
        studio = next(n for n in self.TREE.body if isinstance(n, self._ast.ClassDef) and n.name == "Studio")
        names = {name for _, name in self.calls(self.function("__init__", studio))}
        self.assertIn("athlete_record", names)

    def test_the_probe_stands_in_for_studio_with_its_signature_and_record(self):
        """Review round 1: `R.main` calls `Studio(config, args.athlete)` and
        `render_job` reads `studio.athlete`; the probe broke on both."""
        probe = self._ast.parse((REPO / "scripts" / "shared_athlete_probe.py").read_text(encoding="utf-8"))
        stand_in = self.function("shared_studio", probe)
        self.assertEqual(len(stand_in.args.args), 2)
        sets_athlete = any(isinstance(n, self._ast.Attribute) and n.attr == "athlete"
                           and isinstance(n.ctx, self._ast.Store) for n in self._ast.walk(stand_in))
        self.assertTrue(sets_athlete, "the probe's studio must carry an athlete record")

    def test_every_receipt_names_its_athlete(self):
        render_job = self.function("render_job")
        keys = [k.value for n in self._ast.walk(render_job) if isinstance(n, self._ast.Dict)
                for k in n.keys if isinstance(k, self._ast.Constant)]
        self.assertIn("athlete", keys)
        self.assertIn("sourceAssets", keys)


if __name__ == "__main__":
    unittest.main()
