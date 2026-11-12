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


class HeadBoneTest(unittest.TestCase):
    """Main's ruling, 12 Nov 2026: Models fixes the bone name in the producer,
    so the renderer refuses a body with no `head` bone and never renames one."""

    def test_head_is_found(self):
        self.assertEqual(head_bone_name(["neck_01", "head"]), "head")

    def test_the_old_spelling_is_refused_not_renamed(self):
        with self.assertRaises(SharedAthleteRefusal) as caught:
            head_bone_name(["neck_01", "Head"])
        self.assertIn("head", str(caught.exception))

    def test_a_rig_with_no_head_is_refused(self):
        with self.assertRaises(SharedAthleteRefusal):
            head_bone_name(["neck_01", "HEAD_top"])


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


if __name__ == "__main__":
    unittest.main()
