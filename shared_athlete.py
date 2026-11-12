"""The shared athlete, found through its manifest. No Blender in this module.

The owner ruled on 12 Nov 2026 that the manual figures use the shared athlete
(spec 1, 12.5). It is a BUILD FOLDER from the Models lane: an
`athlete-manifest.json` and the files it names, every path relative to the
folder (`docs/ATHLETE_MANIFEST.md`). The renderer is given the folder and
nothing else. The manifest says which file is the editable master; the
Models lane's own validator checks the folder before anything is loaded, so a
model with a different rig, hash or file set is refused here and not drawn.

No Blender here, so a test can call it, as for `asset_licences.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

ATHLETE_DIR = Path(__file__).resolve().parent / "athlete"
if str(ATHLETE_DIR) not in sys.path:
    sys.path.insert(0, str(ATHLETE_DIR))

import athlete_manifest  # noqa: E402
from asset_licences import licence_for  # noqa: E402

MASTER_ROLE = "master"
# The render rig's spelling, then the rig contract's (`CONTRACT_BONES`).
HEAD_BONES = ("head", "Head")


class SharedAthleteRefusal(Exception):
    """The build folder cannot give the renderer an athlete it may draw."""


def athlete_master(folder: Path) -> tuple[dict, Path]:
    """The validated manifest, and the master file it names.

    The validator is called through its module, so the renderer always runs
    the Models lane's current checks rather than a copy of them.
    """
    try:
        manifest = athlete_manifest.validate(Path(folder))
    except athlete_manifest.ManifestRefusal as refusal:
        raise SharedAthleteRefusal(f"{folder}: the athlete manifest is refused: {refusal}") from refusal
    masters = [name for name, entry in manifest["files"].items() if entry.get("role") == MASTER_ROLE]
    if len(masters) != 1:
        raise SharedAthleteRefusal(
            f"{folder}: the manifest names {len(masters)} files with the role "
            f"{MASTER_ROLE!r}; the renderer needs exactly one editable master."
        )
    return manifest, Path(folder) / masters[0]


def external_asset_records(manifest: dict) -> list[dict]:
    """Every external asset the manifest lists, with THIS repository's licence.

    The manifest's own licence words are recorded beside the determination
    and never replace it: `asset_licences` quotes `docs/LICENSING.md` and
    refuses an asset it has no determination for, and the shared athlete is
    held to the same rule as the render rig. The bytes are named by the
    manifest's SHA-256, which the Models lane's validator has checked.
    """
    records = []
    for asset in manifest["source"]["externalAssets"]:
        licence, source = licence_for(asset["name"])
        records.append({"path": asset["name"], "sha256": asset["sha256"],
                        "licence": licence, "licenceSource": source,
                        "manifestLicence": asset["licence"]})
    return records


def master_record(manifest: dict, master: Path) -> dict:
    """The athlete's own build file, licensed like any other asset.

    It holds the kit and the lettering the athlete pipeline authors. Until
    `docs/LICENSING.md` determines that build output, `licence_for` refuses
    it, and the renderer draws nothing.
    """
    licence, source = licence_for(master)
    return {"path": master.name, "sha256": manifest["files"][master.name]["sha256"],
            "licence": licence, "licenceSource": source}


def head_bone_name(names) -> str:
    """The head bone of a rig: the render rig's `head` or the contract's `Head`.

    The rig contract spells it `Head` and the shared athlete follows the
    contract, so the renderer looks the bone up rather than renaming a
    contract bone when it loads one.
    """
    present = set(names)
    for name in HEAD_BONES:
        if name in present:
            return name
    raise SharedAthleteRefusal(f"the rig has no head bone named any of {HEAD_BONES}")
