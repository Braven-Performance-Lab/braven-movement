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
# THE RIG CONTRACT'S SPELLING (`athlete_manifest.CONTRACT_BONES`, spec 3,
# 12.7). The shared athlete already uses it; `athlete/build.py` makes the same
# two renames on its MPFB body. Only this renderer read `head`.
HEAD_BONE = "Head"
# MPFB's game-engine names that the contract spells differently.
CONTRACT_RENAMES = {"Root": "root", "head": "Head"}


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
    """The head bone, by the contract's name `Head`.

    Main's correction of 12 Nov 2026: the contract spells it `Head` and the
    shared athlete already does, so the renderer reads that name. A body
    without it is refused; the shared athlete is never renamed. The
    renderer's own generated body gets the name from `contract_renames` when
    it is built.
    """
    if HEAD_BONE in set(names):
        return HEAD_BONE
    raise SharedAthleteRefusal(
        f"the rig has no bone named {HEAD_BONE!r}, the rig contract's name "
        f"(spec 3, 12.7)."
    )


def contract_renames(names) -> dict:
    """The renames that give a GENERATED body the contract's bone names.

    Applied to this renderer's own MPFB body only, the same two that
    `athlete/build.py` makes. A body carrying both spellings of one bone is
    refused, because one of them would be lost.
    """
    present = set(names)
    renames = {}
    for old, new in CONTRACT_RENAMES.items():
        if old in present and new in present:
            raise SharedAthleteRefusal(f"the rig has both {old!r} and {new!r}")
        if old in present:
            renames[old] = new
    return renames


def constraint_to_mute(bone: str, kind: str, target: str) -> bool:
    """True for the constraints the renderer mutes; a refusal for any other.

    The shared athlete drives its forearms and calves with IK constraints to
    `CTRL_*` targets, which would override the pose the renderer sets. Those
    are muted. Any other constraint would change the body in a way that was
    never measured (`docs/SHARED_ATHLETE_2026-11-12.md`), so it is refused.
    """
    if kind == "IK" and str(target).startswith("CTRL_"):
        return True
    raise SharedAthleteRefusal(
        f"{bone} carries a {kind} constraint to {target or 'nothing'}; the "
        f"renderer mutes only IK constraints to CTRL_* targets."
    )
