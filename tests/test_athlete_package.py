"""The delivery package takes its athlete from the checked manifest, never from the legacy one.

athlete/package.py copies the built studio into the delivery folder that Open-Athlete-Studio.ps1
serves. It once read the legacy manifest.json for the model hash, which a studio build no longer
carries, and copied over an earlier package so a stale file could stay. checked_studio is the
check it now makes before it copies anything; each test makes one of its refusals fire, on a
folder built by the manifest tests' own fixture.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "athlete"))
sys.path.insert(0, str(REPO / "tests"))

import athlete_manifest as am  # noqa: E402
import package  # noqa: E402
from test_athlete_manifest import Folder  # noqa: E402


class CheckedStudio(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.output, self.dist = root / "athlete", root / "dist"
        self.output.mkdir()
        Folder(self.output).write_v1()
        built = self.dist / "athlete-assets"
        built.mkdir(parents=True)
        for name in (am.MANIFEST_NAME, "netball-athlete.glb"):
            shutil.copy(self.output / name, built / name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_a_build_of_the_checked_athlete_is_packaged(self):
        checked = package.checked_studio(self.output, self.dist)
        self.assertEqual(checked["model"], am.sha256_bytes((self.output / "netball-athlete.glb").read_bytes()))
        self.assertEqual(checked["revision"], 9)

    def test_an_athlete_its_manifest_refuses_is_not_packaged(self):
        (self.output / "netball-athlete.blend").write_bytes(b"MASTER")
        with self.assertRaisesRegex(ValueError, "refused: file"):
            package.checked_studio(self.output, self.dist)

    def test_a_build_with_another_manifest_is_not_packaged(self):
        (self.dist / "athlete-assets" / am.MANIFEST_NAME).write_text("{}")
        with self.assertRaisesRegex(ValueError, "different athlete-manifest.json"):
            package.checked_studio(self.output, self.dist)

    def test_a_build_with_another_model_is_not_packaged(self):
        (self.dist / "athlete-assets" / "netball-athlete.glb").write_bytes(b"glTF old build")
        with self.assertRaisesRegex(ValueError, "different model"):
            package.checked_studio(self.output, self.dist)

    def test_the_legacy_manifest_is_not_what_decides(self):
        # A legacy manifest.json naming another model hash changes nothing: it is not read.
        (self.output / "manifest.json").write_text('{"files": {"netball-athlete.glb": {"sha256": "' + "0" * 64 + '"}}}')
        package.checked_studio(self.output, self.dist)


if __name__ == "__main__":
    unittest.main()
