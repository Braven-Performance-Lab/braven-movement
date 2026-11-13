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
        records.append({"path": asset["name"], "sha256": asset["sha256"].lower(),
                        "licence": licence, "licenceSource": source,
                        "manifestLicence": asset["licence"]})
    return records


def master_record(manifest: dict, master: Path) -> dict:
    """The athlete's own build file, licensed like any other asset.

    It holds the kit and the lettering the athlete pipeline authors. Until
    `docs/LICENSING.md` determines that build output, `licence_for` refuses
    it, and the renderer draws nothing.
    """
    # The FILE NAME, never the folder's path: `licence_for` matches path parts,
    # and a build folder placed under `assets/kit/` would otherwise be
    # licensed as own work by where it sits.
    licence, source = licence_for(master.name)
    return {"path": master.name, "sha256": manifest["files"][master.name]["sha256"].lower(),
            "licence": licence, "licenceSource": source}


def athlete_record(manifest: dict, master: Path) -> dict:
    """What every receipt says about the athlete that drew the figure.

    The GLB is the file whose role is `model`, the runtime asset Tactics and
    Studio load; the master is the file this renderer loads.

    Every hash is written in lower case: the validator accepts upper-case
    hex, and a receipt must compare byte for byte with the others.
    """
    models = [name for name, entry in manifest["files"].items() if entry.get("role") == "model"]
    if len(models) != 1:
        raise SharedAthleteRefusal(f"the manifest names {len(models)} files with the role 'model'")
    return {
        "kind": "shared",
        "name": manifest["asset"]["name"],
        "revision": manifest["asset"]["revision"],
        "glbSha256": manifest["files"][models[0]]["sha256"].lower(),
        "masterSha256": manifest["files"][master.name]["sha256"].lower(),
        "rigFamily": manifest["rig"]["family"],
    }


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


def driver_is_inert(data_path: str, muted) -> bool:
    """True for a driver that can change nothing; a refusal for any other.

    Review round 2 of PR #152: drivers were neither muted nor refused. Build
    09-gait-v2 has four, and each drives the INFLUENCE of one of the four IK
    constraints the loader mutes (`IK_hand_l` and its siblings, rig custom
    properties). A muted constraint has no effect at any influence, so those
    drivers are left in place. `muted` holds (bone, constraint) pairs. Any
    other driver could move the body the renderer poses, so it is refused.
    """
    for bone, constraint in muted:
        if data_path == f'pose.bones["{bone}"].constraints["{constraint}"].influence':
            return True
    raise SharedAthleteRefusal(
        f"the rig carries a driver on {data_path}; the renderer accepts only "
        f"drivers on the influence of a constraint it mutes."
    )


def node_tree_holders(tree, seen=None) -> list:
    """The animation data of a node tree and of every group nested in it.

    Review rounds 6 and 7 of PR #152: a node group inside a material's tree,
    and the group of a geometry-nodes modifier, are node trees of their own
    with their own animation data, and a driver there can change what is
    drawn. Each group is read once, by NAME: Blender gives a new Python
    wrapper at every access, so `id()` or `is` cannot tell two reads apart,
    and a node tree's name is unique among node trees.
    """
    if tree is None:
        return []
    seen = set() if seen is None else seen
    if tree.name in seen:
        return []
    seen.add(tree.name)
    holders = [tree.animation_data]
    for node in tree.nodes:
        holders.extend(node_tree_holders(getattr(node, "node_tree", None), seen))
    return holders


def descendant_is_mesh(name: str, kind: str) -> bool:
    """True for a mesh; a refusal for any other object under the rig.

    The loader links every descendant of the rig and draws it. Build
    09-gait-v2 has only meshes there. Any other kind (an empty, a curve, a
    light) was never measured, and an image empty stopped the loader with an
    AttributeError rather than this refusal (review round 6 of PR #152).
    """
    if kind == "MESH":
        return True
    raise SharedAthleteRefusal(
        f"{name} under the rig is a {kind}; the renderer draws only meshes there."
    )


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
