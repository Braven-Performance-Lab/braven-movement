"""The athlete manifest, version 1, and every refusal it makes.

`athlete/athlete_manifest.py` converts a build folder's legacy `manifest.json` to
`athlete-manifest.json` and validates a folder against it (docs/ATHLETE_MANIFEST.md).
Each test builds its own folder with a small GLB written here, so nothing depends on
the 17 MB athlete on one workstation, and nothing skips. Every refusal code in the
document has a test that makes it fire, and a valid folder is accepted first, so a
refusal that fires on everything is caught too.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "athlete"))

import athlete_manifest as am  # noqa: E402

TECHNIQUE = "netball_chest_pass"
GENERAL = "Ready"
GAIT = "Jog"


def glb_bytes(animations: dict[str, float], joints: list[str]) -> bytes:
    """A GLB with named joint nodes, one skin, and one sampler input per animation."""
    nodes = [{"name": n} for n in joints]
    accessors, anims = [], []
    for name, seconds in animations.items():
        accessors.append({"count": 2, "type": "SCALAR", "componentType": 5126, "min": [0.0], "max": [seconds]})
        anims.append({"name": name, "samplers": [{"input": len(accessors) - 1, "output": 0}], "channels": []})
    doc = {"asset": {"version": "2.0"}, "nodes": nodes, "skins": [{"joints": list(range(len(joints)))}],
           "accessors": accessors, "animations": anims}
    body = json.dumps(doc).encode()
    body += b" " * (-len(body) % 4)
    chunk = struct.pack("<II", len(body), 0x4E4F534A) + body
    return struct.pack("<4sII", b"glTF", 2, 12 + len(chunk)) + chunk


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Folder:
    """A build folder in the legacy layout, as the athlete pipeline writes it."""

    def __init__(self, root: Path, *, joints=None, animations=None):
        self.root = root
        self.joints = list(joints or am.CONTRACT_BONES + ("Ball_Control", "skirt_01"))
        self.animations = dict(animations or {GENERAL: 3.0333, GAIT: 0.7, TECHNIQUE: 1.5833})
        self.glb = glb_bytes(self.animations, self.joints)
        (root / "netball-athlete.glb").write_bytes(self.glb)
        (root / "netball-athlete.blend").write_bytes(b"master")
        self.library = {
            "assetSha256": sha(self.glb), "sourceCommit": "b4f7074", "defaultClip": GENERAL,
            "techniques": [{"movementId": TECHNIQUE, "clip": TECHNIQUE, "label": "Chest Pass",
                            "sourceCommit": "b4f7074", "fps": 60.0, "frameCount": 96, "seconds": 1.5833,
                            "contactFrame": 0, "releaseFrame": 70, "sourceChecksPassed": True,
                            "coachApproved": False, "jobSha256": "ab" * 32}],
        }
        (root / "movement-library.json").write_text(json.dumps(self.library))
        legacy = {
            "schemaVersion": 1, "name": "Braven netball athlete", "revision": 9, "blender": "4.5.12 LTS",
            "generator": "Independent Blender/MPFB authoring", "movementSourceCommit": "b4f7074",
            "parentAssetSha256": "cd" * 32, "animations": sorted(self.animations, key=str.lower),
            "roles": {"Athlete_Body": "body", "Kit_Jersey": "jersey", "Kit_Skirt": "skirt",
                      "Kit_Shorts": "shorts", "Position_GS": "lettering", "Team_Braven": "lettering"},
            "sources": [{"path": "C:\\Users\\someone\\AppData\\Roaming\\Blender Foundation\\Blender\\4.5"
                                 "\\extensions\\.user\\blender_org\\mpfb\\data\\hair\\ponytail01\\ponytail01.mhclo",
                         "sha256": "97" * 32, "licence": "CC0 declared in source header"}],
            "files": {"netball-athlete.glb": {"bytes": len(self.glb), "sha256": sha(self.glb)},
                      "netball-athlete.blend": {"bytes": 6, "sha256": sha(b"master")}},
            "gaitRebuild": {"gaits": {GAIT: {"frames": 42, "fps": 60}}, "recipe": "gait.py + author_gait.py"},
        }
        (root / "manifest.json").write_text(json.dumps(legacy))

    def write_v1(self) -> dict:
        manifest = am.convert_legacy(self.root, kit_id="braven-netball-fitted-v1")
        am.write(self.root, manifest)
        return manifest

    def edit(self, change) -> None:
        path = self.root / am.MANIFEST_NAME
        manifest = json.loads(path.read_text())
        change(manifest)
        path.write_text(json.dumps(manifest))


class ManifestTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def assertRefuses(self, code: str, call, *args, **kwargs):
        with self.assertRaises(am.ManifestRefusal) as caught:
            call(*args, **kwargs)
        self.assertEqual(caught.exception.code, code, str(caught.exception))


class ConvertAndAccept(ManifestTest):
    def test_a_converted_folder_is_accepted(self):
        Folder(self.root).write_v1()
        manifest = am.validate(self.root, supported_families={am.RIG_FAMILY})
        self.assertEqual(manifest["format"], am.FORMAT)
        self.assertEqual(manifest["formatVersion"], 1)

    def test_the_conversion_carries_identity_timing_and_review(self):
        manifest = Folder(self.root).write_v1()
        self.assertEqual(manifest["sport"], "netball")
        self.assertEqual(manifest["asset"]["revision"], 9)
        self.assertEqual(manifest["rig"]["jointCount"], 23)
        self.assertEqual(manifest["rig"]["contractBones"], list(am.CONTRACT_BONES))
        clips = {c["id"]: c for c in manifest["clips"]}
        self.assertEqual(list(clips), sorted(clips, key=str.lower))
        self.assertEqual((clips[TECHNIQUE]["kind"], clips[TECHNIQUE]["fps"], clips[TECHNIQUE]["releaseFrame"]),
                         ("technique", 60, 70))
        self.assertEqual(clips[TECHNIQUE]["review"], "passes-source-checks")
        self.assertEqual((clips[GENERAL]["kind"], clips[GENERAL]["fps"], clips[GENERAL]["review"]),
                         ("general", 30, "not-graded"))
        self.assertEqual(clips[GAIT]["fps"], 60)
        self.assertEqual({f["role"] for f in manifest["files"].values()}, {"model", "master", "library"})

    def test_external_assets_keep_name_licence_and_hash_but_no_path(self):
        manifest = Folder(self.root).write_v1()
        [asset] = manifest["source"]["externalAssets"]
        self.assertEqual(asset["name"], "mpfb/hair/ponytail01/ponytail01.mhclo")
        self.assertNotIn("path", asset)
        self.assertNotIn("someone", json.dumps(manifest))

    def test_a_coach_approved_technique_says_so(self):
        folder = Folder(self.root)
        folder.library["techniques"][0]["coachApproved"] = True
        (self.root / "movement-library.json").write_text(json.dumps(folder.library))
        clips = {c["id"]: c for c in folder.write_v1()["clips"]}
        self.assertEqual(clips[TECHNIQUE]["review"], "coach-approved")


class Refusals(ManifestTest):
    """One test per code in section 3 of docs/ATHLETE_MANIFEST.md."""

    def setUp(self):
        super().setUp()
        self.folder = Folder(self.root)
        self.folder.write_v1()
        am.validate(self.root)

    def test_format(self):
        self.folder.edit(lambda m: m.update(formatVersion=2))
        self.assertRefuses("format", am.validate, self.root)

    def test_path_absolute_file_key(self):
        self.folder.edit(lambda m: m["files"].update({"C:/Users/someone/x.glb": {"role": "master", "bytes": 1, "sha256": "0" * 64}}))
        self.assertRefuses("path", am.validate, self.root)

    def test_path_parent_part(self):
        self.folder.edit(lambda m: m["files"].update({"../x.glb": {"role": "master", "bytes": 1, "sha256": "0" * 64}}))
        self.assertRefuses("path", am.validate, self.root)

    def test_path_backslash(self):
        self.folder.edit(lambda m: m["files"].update({"sub\\x.glb": {"role": "master", "bytes": 1, "sha256": "0" * 64}}))
        self.assertRefuses("path", am.validate, self.root)

    def test_path_leaked_anywhere_in_the_manifest(self):
        self.folder.edit(lambda m: m["source"]["externalAssets"][0].update(note="from C:\\Users\\someone\\mpfb"))
        self.assertRefuses("path", am.validate, self.root)

    def test_the_writer_refuses_an_absolute_path_before_it_writes(self):
        manifest = am.convert_legacy(self.root, kit_id="k")
        manifest["source"]["externalAssets"][0]["path"] = "/home/someone/mpfb/x"
        before = (self.root / am.MANIFEST_NAME).read_bytes()
        self.assertRefuses("path", am.write, self.root, manifest)
        self.assertEqual((self.root / am.MANIFEST_NAME).read_bytes(), before)

    def test_file_hash(self):
        (self.root / "netball-athlete.blend").write_bytes(b"MASTER")
        self.assertRefuses("file", am.validate, self.root)

    def test_file_model_is_not_a_glb(self):
        data = b"PK" + b"\0" * 30
        (self.root / "netball-athlete.glb").write_bytes(data)
        self.folder.edit(lambda m: m["files"]["netball-athlete.glb"].update(bytes=len(data), sha256=sha(data)))
        self.assertRefuses("file", am.validate, self.root)

    def test_file_missing(self):
        (self.root / "netball-athlete.blend").unlink()
        self.assertRefuses("file", am.validate, self.root)

    def test_role_no_model(self):
        self.folder.edit(lambda m: m["files"]["netball-athlete.glb"].update(role="master"))
        self.assertRefuses("role", am.validate, self.root)

    def test_role_no_library_with_techniques(self):
        self.folder.edit(lambda m: m["files"].pop("movement-library.json"))
        self.assertRefuses("role", am.validate, self.root)

    def test_format_legacy_folder_with_no_manifest(self):
        (self.root / am.MANIFEST_NAME).unlink()
        self.assertRefuses("format", am.validate, self.root)

    def test_format_unknown_review_state(self):
        self.folder.edit(lambda m: m["clips"][0].update(review="approved"))
        self.assertRefuses("format", am.validate, self.root)

    def test_clip_set(self):
        self.folder.edit(lambda m: m["clips"].pop(0))
        self.assertRefuses("clip-set", am.validate, self.root)

    def test_clip_timing(self):
        # Half a frame at 60 fps is 0.00833 s; one frame is outside it.
        self.folder.edit(lambda m: [c.update(seconds=c["seconds"] + 1 / 60) for c in m["clips"] if c["id"] == TECHNIQUE])
        self.assertRefuses("clip-timing", am.validate, self.root)

    def test_clip_timing_inside_half_a_frame_is_accepted(self):
        self.folder.edit(lambda m: [c.update(seconds=c["seconds"] + 0.4 / 60) for c in m["clips"] if c["id"] == TECHNIQUE])
        am.validate(self.root)

    def test_library_release_frame(self):
        self.folder.library["techniques"][0]["releaseFrame"] = 71
        self._rewrite_library()
        self.assertRefuses("library", am.validate, self.root)

    def test_library_for_another_model(self):
        self.folder.library["assetSha256"] = "ee" * 32
        self._rewrite_library()
        self.assertRefuses("library", am.validate, self.root)

    def test_library_technique_set(self):
        self.folder.library["techniques"].append(dict(self.folder.library["techniques"][0], clip="netball_bounce_pass"))
        self._rewrite_library()
        self.assertRefuses("library", am.validate, self.root)

    def test_rig_joint_set(self):
        self._replace_model(joints=list(am.CONTRACT_BONES) + ["Ball_Control", "skirt_02"])
        self.assertRefuses("rig", am.validate, self.root)

    def test_rig_contract_bone_case(self):
        joints = [("head" if j == "Head" else j) for j in self.folder.joints]
        self._replace_model(joints=joints, keep_rig=False)
        self.assertRefuses("rig", am.validate, self.root)

    def test_family(self):
        self.assertRefuses("family", am.validate, self.root, supported_families={"braven-athlete-v7"})

    def _rewrite_library(self):
        data = json.dumps(self.folder.library).encode()
        (self.root / "movement-library.json").write_bytes(data)
        self.folder.edit(lambda m: m["files"]["movement-library.json"].update(bytes=len(data), sha256=sha(data)))

    def _replace_model(self, joints, keep_rig=True):
        """Swap the GLB for one with other joints, keeping every hash honest.

        With keep_rig the manifest keeps its old joint set, so only the rig check can see it.
        Without it the manifest is rewritten for the new joints, so only the contract bones can.
        """
        glb = glb_bytes(self.folder.animations, list(joints))
        (self.root / "netball-athlete.glb").write_bytes(glb)
        self.folder.library["assetSha256"] = sha(glb)
        self._rewrite_library()

        def change(m):
            m["files"]["netball-athlete.glb"].update(bytes=len(glb), sha256=sha(glb))
            if not keep_rig:
                m["rig"].update(jointCount=len(joints), jointSetSha256=am.joint_set_sha256(joints))
        self.folder.edit(change)


if __name__ == "__main__":
    unittest.main()
