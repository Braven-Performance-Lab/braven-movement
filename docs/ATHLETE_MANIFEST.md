# The athlete manifest, version 1

This document defines the manifest that describes one build of the shared netball
athlete: its model, rig, kit, clips, sport, source and files. It is a capability
document. It holds no per-build figure except in the example, which names its build.

It implements requirements MAN-1, MAN-2 and MAN-5 of "Athlete assets and integration:
functional specification" (Ironwire Client Zone, project Braven Movement).

## 1. Why a new format

The manifest that the athlete pipeline writes today has these defects. Each was read
on candidate `09-gait-v2`, whose GLB SHA-256 is `2b48758b…dc208`.

| Defect | Effect |
|---|---|
| `schemaVersion` is 1 on every revision, but each correction script adds its own keys (`gravityCorrections`, `jogCorrection`, `gaitRebuild`). | A reader cannot know which keys to expect. |
| `sources[].path` holds absolute paths on one workstation. | A published manifest leaks a user profile path and means nothing on another machine (MAN-5). |
| `movement-library.json` has no hash in the manifest. | A consumer can pair a model with a library from a different build. |
| The manifest has no clip durations or timing. | A consumer cannot refuse a clip set whose timing changed. |
| The manifest has no rig identity. The family name `braven-athlete-v6` exists only as a constant in Braven Tactics. | A consumer cannot refuse a model with a different bone set. |
| The manifest has no kit identity and no sport. | Two kits or two sports cannot be told apart. |
| The Tactics importer and Braven Studio check only the GLB hash. | Every other mismatch passes. |

## 2. The format

The manifest is one JSON file named `athlete-manifest.json` in the root of the build
folder. Every path in it is relative to that folder.

```json
{
  "format": "braven-athlete-manifest",
  "formatVersion": 1,
  "asset":  { "name": "...", "revision": 9, "parentSha256": "..." },
  "sport":  "netball",
  "rig":    { "family": "...", "contractBones": [...], "jointCount": 70, "jointSetSha256": "..." },
  "kit":    { "id": "...", "garments": {...}, "lettering": {...} },
  "source": { "movementCommit": "...", "generator": "...", "blender": "...", "externalAssets": [...] },
  "files":  { "netball-athlete.glb": { "role": "model", "bytes": 0, "sha256": "..." } },
  "clips":  [ { "id": "...", "kind": "technique", "seconds": 1.5833, "fps": 60, ... } ],
  "history": [ { "revision": 6, "change": "...", "recipeSha256": "..." } ]
}
```

### 2.1 `asset`

| Field | Meaning |
|---|---|
| `name` | The athlete's name, for people. |
| `revision` | A whole number. A new revision for every change to any file. |
| `parentSha256` | The model hash of the revision this one was made from, or `null` for the first. |

### 2.2 `sport`

One sport identifier, for example `netball`. A consumer uses it to choose its
technique selection rules. A second sport is a second manifest (MAN-4).

### 2.3 `rig`

| Field | Meaning |
|---|---|
| `family` | The name of the bone interface. A consumer names the family it supports. |
| `contractBones` | The 21 bone names that Braven Tactics requires, spelled and cased exactly as the contract spells them. |
| `jointCount` | The number of joints in the model's skin. |
| `jointSetSha256` | The SHA-256 of the skin's joint names, sorted, joined with `\n`, UTF-8. |

The family changes when a bone is added, removed or renamed. A change of family
makes every consumer refuse the model until it names the new family.

### 2.4 `kit`

| Field | Meaning |
|---|---|
| `id` | The kit design, for example `braven-netball-fitted-v1`. |
| `garments` | Each kit mesh name and its role: `jersey`, `skirt`, `shorts`, `lettering`. |
| `lettering` | Each lettering mesh name and what it shows. |

### 2.5 `source`

| Field | Meaning |
|---|---|
| `movementCommit` | The Braven Movement commit that the technique clips were imported from. |
| `generator`, `blender` | The authoring path and the Blender version. |
| `externalAssets` | Each asset that the build used and that is not in the folder: its name, licence and SHA-256. It has no path. An MPFB asset is named by its path under MPFB's own `data` folder, for example `mpfb/hair/ponytail01/ponytail01.mhclo`; any other asset by its file name alone. The SHA-256 identifies the exact version. |
| `poseClipsSha256` | The SHA-256 of the Braven Tactics pose clips file (`public/figures/clips.json`) that the techniques were linked to, so the manifest says which graded clips it names. Required when `clips` holds a technique. |

### 2.6 `files`

One entry for each file in the folder that a consumer reads. The key is the path
relative to the folder, with `/` as the separator.

| Field | Meaning |
|---|---|
| `role` | `model` (the GLB), `master` (the editable Blender file), `body-source` (the body Blender file) or `library` (the technique library). |
| `bytes` | The file size. |
| `sha256` | The file hash, lower case. |

### 2.7 `clips`

One entry for each animation in the model, in the order of their `id`.

| Field | Meaning |
|---|---|
| `id` | The animation name in the GLB. |
| `kind` | `technique` (from the Movement library) or `general` (authored on the athlete). |
| `seconds` | The duration, read from the GLB. |
| `fps` | The frame rate the clip was authored at. |
| `movementId`, `jobSha256` | A technique only: the drill and the hash of the solved job it came from. |
| `contactFrame`, `releaseFrame` | A technique only: the frame of first contact and of release, or `null`. |
| `review` | `passes-source-checks`, `needs-review` or `coach-approved` for a technique; `not-graded` for a general clip. Any other value is refused with the code `format`. |
| `gradedClip` | A technique only, and required for each: the graded pose clip that is the record for this technique, as `{clipId, graded, build}`, or `null` when Tactics has no pose clip made from this drill. `clipId` is the pose clip's id (`<class>.<sport>.<technique>`), `graded` is the pose clip's own graded flag, and `build` is the full commit in its `generatedFrom` stamp. The link is made by `movementId`, which both come from. A general clip has no `gradedClip`. |

### 2.8 `history`

One entry for each revision that the build still records: its number, a sentence on
what changed, and the hash of the recipe file that made the change, or `null` when the
build did not record that hash. A converted legacy build has only the revisions that
its old manifest still names. For example, candidate `09-gait-v2` records revisions 6,
7 and 9: the gait script deleted the jog correction's key, so revision 8 is absent.
The history is information for people. No refusal reads it.

## 3. The refusals

A validator reads the folder and the manifest, and refuses the set if any of these
holds. Each refusal has a code, so that a test can name the refusal it expects.

| Code | The validator refuses when |
|---|---|
| `format` | The folder has no `athlete-manifest.json` (a build from before this format); the manifest is not JSON or is not a JSON object; `format` is not `braven-athlete-manifest`; `formatVersion` is not a version it knows; a clip's `review` is not one of the four states; or a clip's `fps` is not a whole number above zero.; a technique has no `gradedClip` key, or one that is neither `null` nor a pose clip id with a boolean `graded` and a full commit; a general clip has a `gradedClip`; or `source.poseClipsSha256` is missing or not a SHA-256 while `clips` holds a technique. |
| `path` | A file path has a `\`, is absolute or starts with a drive letter, or has a `..` part; or any text in the manifest names a place on one machine: a drive letter with a separator, a UNC share, a home folder (`~/`), or a root path of two or more parts such as `/opt/x` (MAN-5). The validator does not follow symbolic links: the pipeline writes none, and the `file` check hashes what it reads. |
| `file` | A file in `files` is missing, or its size or hash differs; or the model is not a GLB, is too short, or has a JSON chunk that cannot be read or is not a JSON object. |
| `role` | `files` has no `model`, or more than one, or no `library` while `clips` holds a technique. |
| `clip-set` | The GLB's animations are not exactly the ids in `clips`, the manifest lists one clip twice, or the GLB has two animations with one name. |
| `clip-timing` | A clip's duration in the GLB differs by more than half a frame at its `fps` from the manifest's `seconds`, from the library's `seconds`, or from the library's frame count (`(frameCount - 1) / fps`); or the library gives no `seconds`, or one that is not a number. |
| `library` | The library is not JSON or is not a JSON object; it was made for another model (its `assetSha256` is not the model's hash); it lists one technique twice; its techniques are not exactly the `technique` clips; or a technique's frame count, frame rate, contact or release differs from its clip entry. |
| `rig` | The GLB's joint count is not `jointCount`; its joint names do not hash to `jointSetSha256`; `contractBones` is not the list this validator knows; or a contract bone is missing from the model with that exact spelling and case. |
| `family` | `rig.family` is not a family the consumer supports. The family is always checked: a consumer that names no family supports `braven-athlete-v6` only. |

A consumer runs the validator before it uses the set.

- **Braven Studio** runs `athlete_manifest.py check` before its dev server, build or preview
  starts, and stops with the refusal code. It then serves only `athlete-manifest.json` and the
  files it lists, and hashes each file again when it serves or copies it, so a folder that
  changes after the check is not served (athlete/viewer/manifest-gate.mjs).
- **The Braven Tactics importer** runs a mirror of this validator, with the same codes, before
  it writes its sidecar: pull request Braven-Performance-Lab/braven-tactics#730, not yet merged.
  Until it lands, Tactics checks only the model's hash.

`write` writes the manifest beside the build and swaps it in, so a failed write leaves the
manifest that was there before. The command line puts that manifest back, or removes the new
one, when the check that follows fails for any reason.

## 4. The graded record

Braven Tactics takes Braven Movement's work by two routes: the pose route (the clip
contract, docs/TACTICS_CLIP_CONTRACT.md) and the rig route (this athlete). Marius ruled
on 12 November 2026 (spec 3, decision 12.1): **both stay, and the pose clip is the
graded record.** The athlete's animation of a technique is a rendition of that record,
so each technique names it in `gradedClip`.

The writer takes the shipped pose clips file as an input
(`athlete_manifest.py write <folder> --pose-clips <tactics>/public/figures/clips.json`)
and refuses, with the code `format`, a file that:

- is not JSON, or is not an object of clips by id;
- has a pose clip whose `movementId` is not a drill name (a non-empty string);
- has two pose clips made from one drill;
- has a pose clip with no build, because a clip that cannot say what made it cannot
  be a record;
- has a pose clip whose `graded` is not `true` or `false`;
- links none of the folder's techniques. A wrong file passed by mistake, such as the
  athlete's own library, links nothing, and the manifest would then say that no
  technique has a graded record.

Read on 12 November 2026, candidate `09-gait-v2` against Tactics `main` at `14c9b38`:
9 of the 12 techniques have a pose clip, and 4 of those 9 pose clips are graded. The
bounce pass, the one-hand high pass and the overhead pass have none, so their
`gradedClip` is `null`. The athlete's techniques were imported
from Movement `b4f7074`; the pose clips were made by `0353b76` (8) and `16246780` (the
chest pass). The manifest records the difference and does not refuse it: no ruling says
the two must match.

## 5. What this does not decide
- How a published setup for Braven Training names its manifest. That is TRN-2, which
  builds on this format.
