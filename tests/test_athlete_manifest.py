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
import io
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "athlete"))

import athlete_manifest as am  # noqa: E402

TECHNIQUE = "netball_chest_pass"
GENERAL = "Ready"
GAIT = "Jog"
CHEST_BUILD = "1624678" + "0" * 33
# The shipped Tactics pose clips, in their shape: the chest pass has a graded clip; a bounce pass
# clip exists for another drill the fixture's athlete does not carry.
POSE_CLIPS = json.dumps({
    "pass.netball.chest-pass": {"movementId": TECHNIQUE, "graded": True,
                                "generatedFrom": {"commit": CHEST_BUILD, "treeWasClean": True}},
    "pass.netball.bounce-pass": {"movementId": "netball_bounce_pass", "graded": False,
                                 "generatedFrom": {"commit": "0353b76" + "0" * 33}},
    "catch.capture.goalkeeper": {"skill": "catch"},
}).encode()


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
        manifest = am.convert_legacy(self.root, kit_id="braven-netball-fitted-v1", pose_clips=POSE_CLIPS)
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

    def _pose_clips(self) -> Path:
        path = self.root.parent / (self.root.name + "-pose-clips.json")
        path.write_bytes(POSE_CLIPS)
        self.addCleanup(path.unlink, missing_ok=True)
        return path

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

    def test_a_technique_names_its_graded_pose_clip_and_build(self):
        clips = {c["id"]: c for c in Folder(self.root).write_v1()["clips"]}
        self.assertEqual(clips[TECHNIQUE]["gradedClip"],
                         {"clipId": "pass.netball.chest-pass", "graded": True, "build": CHEST_BUILD})
        self.assertNotIn("gradedClip", clips[GENERAL])
        self.assertNotIn("gradedClip", clips[GAIT])

    def test_a_technique_with_no_pose_clip_says_null(self):
        # Two techniques: the chest pass links, and a second drill with no pose clip says null.
        folder = Folder(self.root)
        second = dict(folder.library["techniques"][0], clip="netball_overhead_pass", movementId="netball_overhead_pass")
        folder.library["techniques"].append(second)
        (self.root / "movement-library.json").write_text(json.dumps(folder.library))
        folder.animations["netball_overhead_pass"] = folder.animations[TECHNIQUE]
        glb = glb_bytes(folder.animations, folder.joints)
        (self.root / "netball-athlete.glb").write_bytes(glb)
        clips = {c["id"]: c for c in am.convert_legacy(self.root, kit_id="k", pose_clips=POSE_CLIPS)["clips"]}
        self.assertIsNotNone(clips[TECHNIQUE]["gradedClip"])
        self.assertIn("gradedClip", clips["netball_overhead_pass"])
        self.assertIsNone(clips["netball_overhead_pass"]["gradedClip"])

    def test_writer_refuses_a_pose_clips_file_that_links_no_technique(self):
        # The wrong file passed by mistake: the athlete's own library, an empty object.
        folder = Folder(self.root)
        for wrong in (b"{}", json.dumps(folder.library).encode()):
            with self.subTest(wrong=wrong[:30]):
                self.assertRefuses("format", am.convert_legacy, self.root, kit_id="k", pose_clips=wrong)

    def test_the_manifest_names_the_pose_clips_it_was_linked_to(self):
        manifest = Folder(self.root).write_v1()
        self.assertEqual(manifest["source"]["poseClipsSha256"], sha(POSE_CLIPS))

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
        # Neither key has a root path of two parts or a drive with a separator, so the
        # local-path text check cannot see them: only the absolute-path rule can refuse them.
        for key in ("/x.glb", "D:x.glb"):
            with self.subTest(key=key):
                self.assertIsNone(am.LOCAL_PATH.search(key))
                self.folder.edit(lambda m, k=key: m["files"].update({k: {"role": "master", "bytes": 1, "sha256": "0" * 64}}))
                self.assertRefuses("path", am.validate, self.root)
                self.folder.edit(lambda m, k=key: m["files"].pop(k))

    def test_path_drive_and_home_in_a_file_key(self):
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

    def test_path_root_and_home_folders_of_any_name(self):
        for text in ("/opt/athlete/mpfb", "/srv/x/y", "/Volumes/Work/mpfb", "~/mpfb/hair", "built in /root/athlete/"):
            with self.subTest(text=text):
                self.folder.edit(lambda m, t=text: m["source"].update(note=t))
                self.assertRefuses("path", am.validate, self.root)

    def test_relative_names_are_not_local_paths(self):
        for text in ("mpfb/hair/ponytail01/ponytail01.mhclo", "Independent Blender/MPFB authoring", "gait.py + author_gait.py"):
            with self.subTest(text=text):
                self.assertIsNone(am.LOCAL_PATH.search(text))

    def test_the_writer_refuses_an_absolute_path_before_it_writes(self):
        manifest = am.convert_legacy(self.root, kit_id="k", pose_clips=POSE_CLIPS)
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

    def test_format_wrong_format_name(self):
        self.folder.edit(lambda m: m.update(format="braven-athlete"))
        self.assertRefuses("format", am.validate, self.root)

    def test_format_frame_rate_not_a_whole_number(self):
        self.folder.edit(lambda m: m["clips"][0].update(fps=29.97))
        self.assertRefuses("format", am.validate, self.root)

    def test_file_byte_count_wrong_with_the_right_hash(self):
        self.folder.edit(lambda m: m["files"]["netball-athlete.blend"].update(bytes=7))
        self.assertRefuses("file", am.validate, self.root)

    def _glb_refusal_detail(self, data: bytes) -> str:
        path = self.root / "odd.glb"
        path.write_bytes(data)
        with self.assertRaises(am.ManifestRefusal) as caught:
            am.read_glb(path)
        self.assertEqual(caught.exception.code, "file")
        return caught.exception.detail

    def test_file_glb_first_chunk_not_json(self):
        body = b"\0" * 8
        data = struct.pack("<4sII", b"glTF", 2, 20 + len(body)) + struct.pack("<II", len(body), 0x004E4942) + body
        self.assertIn("not a GLB", self._glb_refusal_detail(data))

    def test_file_glb_wrong_magic_with_a_readable_json_chunk(self):
        # Only the magic word is wrong: without that check the JSON chunk would parse and pass.
        body = b"{}  "
        data = struct.pack("<4sII", b"glTX", 2, 20 + len(body)) + struct.pack("<II", len(body), 0x4E4F534A) + body
        self.assertIn("not a GLB", self._glb_refusal_detail(data))

    def test_file_not_a_glb_at_all_says_so(self):
        self.assertIn("not a GLB", self._glb_refusal_detail(b"PK" + b"\0" * 30))

    def test_format_technique_without_its_graded_clip_key(self):
        self.folder.edit(lambda m: [c.pop("gradedClip") for c in m["clips"] if c["id"] == TECHNIQUE])
        self.assertRefuses("format", am.validate, self.root)

    def test_format_graded_clip_with_a_short_build(self):
        self.folder.edit(lambda m: [c["gradedClip"].update(build="1624678") for c in m["clips"] if c["id"] == TECHNIQUE])
        self.assertRefuses("format", am.validate, self.root)

    def test_format_graded_clip_with_an_odd_clip_id(self):
        self.folder.edit(lambda m: [c["gradedClip"].update(clipId="Chest Pass") for c in m["clips"] if c["id"] == TECHNIQUE])
        self.assertRefuses("format", am.validate, self.root)

    def test_format_graded_clip_graded_not_a_boolean(self):
        self.folder.edit(lambda m: [c["gradedClip"].update(graded="yes") for c in m["clips"] if c["id"] == TECHNIQUE])
        self.assertRefuses("format", am.validate, self.root)

    def test_format_a_general_clip_with_a_graded_clip(self):
        self.folder.edit(lambda m: [c.update(gradedClip=None) for c in m["clips"] if c["id"] == GENERAL])
        self.assertRefuses("format", am.validate, self.root)

    def test_format_pose_clips_hash_of_the_wrong_form(self):
        self.folder.edit(lambda m: m["source"].update(poseClipsSha256="abc"))
        self.assertRefuses("format", am.validate, self.root)

    def test_format_no_pose_clips_hash(self):
        self.folder.edit(lambda m: m["source"].pop("poseClipsSha256"))
        self.assertRefuses("format", am.validate, self.root)

    def test_writer_refuses_pose_clips_that_are_not_an_object(self):
        self.assertRefuses("format", am.graded_pose_clips, b"[]")

    def test_writer_refuses_a_movement_id_that_is_not_a_drill_name(self):
        for odd_id in (["netball_chest_pass"], ""):
            with self.subTest(movementId=odd_id):
                odd = json.loads(POSE_CLIPS)
                odd["pass.netball.chest-pass"]["movementId"] = odd_id
                self.assertRefuses("format", am.graded_pose_clips, json.dumps(odd).encode())

    def test_writer_refuses_a_graded_flag_that_is_not_a_boolean(self):
        odd = json.loads(POSE_CLIPS)
        odd["pass.netball.chest-pass"]["graded"] = "false"
        self.assertRefuses("format", am.graded_pose_clips, json.dumps(odd).encode())

    def test_writer_refuses_pose_clips_that_are_not_json(self):
        self.assertRefuses("format", am.graded_pose_clips, b"{not json")

    def test_writer_refuses_two_pose_clips_for_one_drill(self):
        two = json.loads(POSE_CLIPS)
        two["pass.netball.chest-pass-copy"] = dict(two["pass.netball.chest-pass"])
        self.assertRefuses("format", am.graded_pose_clips, json.dumps(two).encode())

    def test_writer_refuses_a_pose_clip_with_no_build(self):
        unstamped = json.loads(POSE_CLIPS)
        unstamped["pass.netball.chest-pass"].pop("generatedFrom")
        self.assertRefuses("format", am.graded_pose_clips, json.dumps(unstamped).encode())

    def test_write_on_the_command_line_needs_the_pose_clips(self):
        before = (self.root / am.MANIFEST_NAME).read_bytes()
        with self.assertRaises(SystemExit) as caught, mock.patch("sys.stderr", io.StringIO()):
            am.main(["write", str(self.root)])
        self.assertEqual(caught.exception.code, 2)
        self.assertEqual((self.root / am.MANIFEST_NAME).read_bytes(), before)

    def test_format_zero_frame_rate(self):
        self.folder.edit(lambda m: m["clips"][0].update(fps=0))
        self.assertRefuses("format", am.validate, self.root)

    def test_format_manifest_json_but_not_an_object(self):
        (self.root / am.MANIFEST_NAME).write_text("[]")
        self.assertRefuses("format", am.validate, self.root)

    def test_library_json_but_not_an_object(self):
        data = b"[]"
        (self.root / "movement-library.json").write_bytes(data)
        self.folder.edit(lambda m: m["files"]["movement-library.json"].update(bytes=len(data), sha256=sha(data)))
        self.assertRefuses("library", am.validate, self.root)

    def test_file_glb_json_chunk_not_an_object(self):
        body = b"[]  "
        path = self.root / "list.glb"
        path.write_bytes(struct.pack("<4sII", b"glTF", 2, 20 + len(body)) + struct.pack("<II", len(body), 0x4E4F534A) + body)
        self.assertRefuses("file", am.read_glb, path)

    def test_clip_timing_library_row_with_no_seconds(self):
        del self.folder.library["techniques"][0]["seconds"]
        self._rewrite_library()
        self.assertRefuses("clip-timing", am.validate, self.root)

    def test_format_manifest_not_json(self):
        (self.root / am.MANIFEST_NAME).write_text("{not json")
        self.assertRefuses("format", am.validate, self.root)

    def test_clip_set(self):
        self.folder.edit(lambda m: m["clips"].pop(0))
        self.assertRefuses("clip-set", am.validate, self.root)

    def test_clip_set_one_clip_listed_twice(self):
        self.folder.edit(lambda m: m["clips"].append(dict(m["clips"][0])))
        self.assertRefuses("clip-set", am.validate, self.root)

    def test_clip_set_two_animations_with_one_name(self):
        glb = glb_bytes(self.folder.animations, self.folder.joints)
        doc_len = struct.unpack_from("<I", glb, 12)[0]
        doc = json.loads(glb[20:20 + doc_len])
        doc["animations"].append(dict(doc["animations"][0]))
        body = json.dumps(doc).encode()
        body += b" " * (-len(body) % 4)
        twice = struct.pack("<4sII", b"glTF", 2, 20 + len(body)) + struct.pack("<II", len(body), 0x4E4F534A) + body
        path = self.root / "twice.glb"
        path.write_bytes(twice)
        self.assertRefuses("clip-set", am.read_glb, path)

    def test_file_glb_too_short(self):
        path = self.root / "short.glb"
        path.write_bytes(b"glTF")
        self.assertRefuses("file", am.read_glb, path)

    def test_file_glb_json_chunk_unreadable(self):
        body = b"{broken    "
        path = self.root / "broken.glb"
        path.write_bytes(struct.pack("<4sII", b"glTF", 2, 20 + len(body)) + struct.pack("<II", len(body), 0x4E4F534A) + body)
        self.assertRefuses("file", am.read_glb, path)

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

    def test_library_one_technique_listed_twice(self):
        self.folder.library["techniques"].append(dict(self.folder.library["techniques"][0]))
        self._rewrite_library()
        self.assertRefuses("library", am.validate, self.root)

    def test_library_with_no_model_hash(self):
        self.folder.library["assetSha256"] = None
        self._rewrite_library()
        self.assertRefuses("library", am.validate, self.root)

    def test_library_not_json(self):
        data = b"{not json"
        (self.root / "movement-library.json").write_bytes(data)
        self.folder.edit(lambda m: m["files"]["movement-library.json"].update(bytes=len(data), sha256=sha(data)))
        self.assertRefuses("library", am.validate, self.root)

    def test_clip_timing_library_seconds_disagree_with_the_model(self):
        self.folder.library["techniques"][0]["seconds"] += 1 / 60
        self._rewrite_library()
        self.assertRefuses("clip-timing", am.validate, self.root)

    def test_clip_timing_library_frame_count_disagrees_with_the_model(self):
        # Library and manifest agree on 97 frames, so only the model's clip length can disagree.
        self.folder.library["techniques"][0]["frameCount"] = 97
        self._rewrite_library()
        self.folder.edit(lambda m: [c.update(frameCount=97) for c in m["clips"] if c["id"] == TECHNIQUE])
        self.assertRefuses("clip-timing", am.validate, self.root)

    def test_rig_joint_set(self):
        self._replace_model(joints=list(am.CONTRACT_BONES) + ["Ball_Control", "skirt_02"])
        self.assertRefuses("rig", am.validate, self.root)

    def test_rig_contract_bone_case(self):
        joints = [("head" if j == "Head" else j) for j in self.folder.joints]
        self._replace_model(joints=joints, keep_rig=False)
        self.assertRefuses("rig", am.validate, self.root)

    def test_rig_joint_count_alone(self):
        self.folder.edit(lambda m: m["rig"].update(jointCount=m["rig"]["jointCount"] + 1))
        self.assertRefuses("rig", am.validate, self.root)

    def test_rig_manifest_lists_other_contract_bones(self):
        self.folder.edit(lambda m: m["rig"]["contractBones"].remove("root"))
        self.assertRefuses("rig", am.validate, self.root)

    def test_family(self):
        self.assertRefuses("family", am.validate, self.root, supported_families={"braven-athlete-v7"})

    def test_family_is_checked_with_no_argument(self):
        self.folder.edit(lambda m: m["rig"].update(family="braven-athlete-v7"))
        self.assertRefuses("family", am.validate, self.root)


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



class CommandLine(ManifestTest):
    def test_check_refuses_another_family_by_default(self):
        Folder(self.root).write_v1()
        manifest = json.loads((self.root / am.MANIFEST_NAME).read_text())
        manifest["rig"]["family"] = "braven-athlete-v7"
        (self.root / am.MANIFEST_NAME).write_text(json.dumps(manifest))
        self.assertEqual(am.main(["check", str(self.root)]), 1)

    def test_write_leaves_no_manifest_when_the_folder_does_not_match(self):
        folder = Folder(self.root)
        folder.library["assetSha256"] = "ee" * 32
        (self.root / "movement-library.json").write_text(json.dumps(folder.library))
        self.assertEqual(am.main(["write", str(self.root), "--pose-clips", str(self._pose_clips())]), 1)
        self.assertFalse((self.root / am.MANIFEST_NAME).exists())

    def test_write_puts_back_the_manifest_that_was_there_when_refused(self):
        folder = Folder(self.root)
        folder.write_v1()
        before = (self.root / am.MANIFEST_NAME).read_bytes()
        folder.library["assetSha256"] = "ee" * 32
        (self.root / "movement-library.json").write_text(json.dumps(folder.library))
        self.assertEqual(am.main(["write", str(self.root), "--pose-clips", str(self._pose_clips())]), 1)
        self.assertEqual((self.root / am.MANIFEST_NAME).read_bytes(), before)

    def test_write_leaves_no_manifest_when_the_check_fails_with_any_error(self):
        Folder(self.root)
        with mock.patch.object(am, "validate", side_effect=RuntimeError("not a refusal")):
            with self.assertRaises(RuntimeError):
                am.main(["write", str(self.root), "--pose-clips", str(self._pose_clips())])
        self.assertFalse((self.root / am.MANIFEST_NAME).exists())

    def test_write_that_fails_on_disk_leaves_the_old_manifest_whole(self):
        folder = Folder(self.root)
        folder.write_v1()
        before = (self.root / am.MANIFEST_NAME).read_bytes()
        with mock.patch.object(am.os, "replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                am.write(self.root, am.convert_legacy(self.root, kit_id="another-kit", pose_clips=POSE_CLIPS))
        self.assertEqual((self.root / am.MANIFEST_NAME).read_bytes(), before)
        self.assertEqual(sorted(p.name for p in self.root.glob("*.partial")), [], "no .partial file is left behind")

    def test_check_prints_the_hash_of_the_manifest_it_checked(self):
        Folder(self.root).write_v1()
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            self.assertEqual(am.main(["check", str(self.root)]), 0)
        printed = json.loads(out.getvalue().strip().splitlines()[-1])
        self.assertEqual(printed["manifestSha256"], sha((self.root / am.MANIFEST_NAME).read_bytes()))

    def test_check_refuses_a_manifest_rewritten_while_it_was_checked(self):
        Folder(self.root).write_v1()
        real = am.validate

        def rewrite_then_check(folder, families):
            manifest = real(folder, families)
            path = Path(folder) / am.MANIFEST_NAME
            path.write_text(path.read_text() + " ")
            return manifest
        with mock.patch.object(am, "validate", side_effect=rewrite_then_check):
            self.assertEqual(am.main(["check", str(self.root)]), 1)

    def test_write_keeps_the_manifest_when_the_folder_matches(self):
        Folder(self.root)
        self.assertEqual(am.main(["write", str(self.root), "--pose-clips", str(self._pose_clips())]), 0)
        self.assertTrue((self.root / am.MANIFEST_NAME).exists())


class ExternalAssetNames(unittest.TestCase):
    def test_a_user_folder_called_data_does_not_leak(self):
        source = {"path": "D:\\data\\people\\mpfb\\data\\hair\\h.mhclo", "sha256": "0" * 64, "licence": "CC0"}
        self.assertEqual(am._external_asset(source)["name"], "mpfb/hair/h.mhclo")

    def test_an_asset_outside_mpfb_keeps_only_its_file_name(self):
        source = {"path": "D:\\data\\assets\\shoe.obj", "sha256": "0" * 64}
        self.assertEqual(am._external_asset(source)["name"], "shoe.obj")



if __name__ == "__main__":
    unittest.main()
