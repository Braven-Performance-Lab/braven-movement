# Can the shared athlete carry the manual figures? (12 Nov 2026)

The Blender lane's goal "Measure whether the shared athlete can carry the
manual figures", set by Main after the owner ruled that the manual figures
move to the shared athlete (spec 1, recommendation 12.5).

## The body measured

The shared athlete is the Models lane's `netball-athlete.blend`, candidate
`09-gait-v2` (revision 9, GLB `2b48758b228e`, with `athlete-manifest.json`),
in the athlete delivery folder outside the repository. It is an MPFB body with
the same game-engine bone names as the render rig, plus four IK controls
(`CTRL_hand_*`, `CTRL_foot_*`), `Ball_Control` and 16 skirt bones: 74 bones
against 53.

## Its rest clavicle, against the engine's rest and standing posture

Measured with `scripts/shared_athlete_probe.py -- clavicle` (shared athlete),
`scripts/rig_rest_clavicle.py` (render rig) and
`scripts/engine_rest_clavicle.py` (engine):

| Clavicle | Length | Back of straight out | Up |
|---|---:|---:|---:|
| Engine, rest | 17.65 cm | 32.96 deg | 5.37 deg |
| Engine, standing (`chest_pass/ready`) | 17.65 cm | 15.29 deg | 5.78 deg |
| Render rig, rest | 12.63 cm | 2.85 deg | -8.50 deg |
| **Shared athlete, rest** | **12.53 cm** | **3.47 deg** | **-9.04 deg** |

The shared athlete's rest clavicle is further forward than the engine's
standing posture and far from its rest, like the render rig's. It has the same
reach limit as the render rig: `docs/KNOWN_ISSUES.md`, "This rig cannot reach
the girdle the solve asks for".

## Posing it from the engine's jobs (step 2)

`scripts/shared_athlete_probe.py` opens the shared file and poses every phase
with the renderer's own `pose_phase`, through `scripts/ball_hand_gap_render.py`:

    blender -b --python scripts/shared_athlete_probe.py -- <netball-athlete.blend> measure out/reach-shared.json spikes/poc-output/*.job.json

**Status (12 Nov 2026, `lane/shared-athlete-switch`):** the renderer now
reads the rig contract's `Head` and the probe renames nothing; the rename
below describes the measured runs, made against the renderer before that
change.

**The renderer draws the shared athlete since 13 Nov 2026.** Until then the
`--athlete` option refused every run with `LicenceUndetermined`, because the
athlete's own build file had no licence determination. The owner ruled it
own work, all rights reserved (`Main/athlete-build-licence`), and
`docs/LICENSING.md` records the ruling. The licence check still runs before
the load. The shared-athlete numbers above this point in the report come
from the probe, which skips the licence check and marks its receipts "NOT
CHECKED". Before the ruling, the renderer's loader (`load_shared_athlete`)
ran once on build 09-gait-v2 from a script that skips the licence check. It
loaded `Athlete_Body` and 11 more meshes, muted the four IK constraints and
kept the four drivers below.

The loader links only meshes under the rig, and refuses any other kind of
object there. It refuses any object constraint on the rig or its meshes. It
also refuses any driver on those objects, on their data (the armature, the
meshes), on shape keys, on materials, on material node trees, on every node
group nested in those trees and on the group of each geometry-nodes
modifier, with one exception.
Build 09-gait-v2 has four drivers, one on the influence of each muted IK
constraint, from the rig custom properties `IK_hand_l`, `IK_hand_r`,
`IK_foot_l` and `IK_foot_r`. A muted constraint has no effect at any
influence, so the loader keeps those four drivers.

`scripts/shared_athlete_loader_check.py` runs the loader on a build with the
licence check skipped, and draws no figure:

    blender -b --python scripts/shared_athlete_loader_check.py -- <repo> <athlete build folder>

On 09-gait-v2 the clean load passed, with the four drivers kept and the four
IK constraints muted. Then the script added one defect at a time after the
load. The loader refused all seven: an object constraint on the body, and a
driver on the rig object, the armature data, the mesh data, a material, a
material node tree and a mesh object.

On 13 Nov 2026 the check gained three cases: a driver in a node group
nested in a material, a driver in a geometry-nodes modifier group, and an
image empty under the rig, put in a saved copy of the build. A fourth case
puts a driver on the node tree of a later material: on `Kit_Skirt`, the
second of `Kit_Primary` and `Kit_Accent`. Every material's embedded tree is
named 'Shader Nodetree', so the first version of the check, which kept
trees by name, read only the first material on each mesh. That case printed
NOT REFUSED with it. The loader now keeps trees by their Blender pointer, and
it refused all eleven cases. The output of that run is
`docs/evidence/shared-athlete-loader-check-2026-11-13.txt`.

Three things are done in that process only and never saved:

- The bone `Head` is renamed `head`, the only name the renderer uses that
  differs; the vertex group follows the rename, and the probe checks it.
  The contract spells it `Head` (spec 3, 12.7); the renderer is the side
  that changes to read it (Main, 12 Nov 2026).
- The assigned Action (`Jog`) is cleared and every bone returns to its bind
  pose.
- The four IK constraints are muted, because they would override the arm and
  the leg the renderer poses.

All 51 phases of the 12 drills pose, with no failure.

Re-run at `b3c8685` plus the round 2 fix, with the stricter probe (only the
four `CTRL_` IK constraints muted, any other refused; every descendant
linked, the ball's subtree left out): 51 phases, no failure, and every bone
0.0 mm from the first run. So build 09-gait-v2 carries only those four
constraints.

## The same instrument on both bodies (step 3)

`main` at `09bf701`, jobs exported on that tip:

| | Shoulder miss, median / max | Anchor error, median / max | Over 10 mm | Held, nearest fingertip |
|---|---:|---:|---:|---:|
| Render rig | 23.19 / 41.13 mm | 7.53 / 18.16 mm | 2 | 6.9 mm median, 6.5 min |
| Shared athlete | 22.46 / 40.32 mm | 7.13 / 18.03 mm | 1 | 6.8 mm median, 6.5 min |

| Drill | Anchor median, render rig to shared | Shoulder miss median |
|---|---|---|
| `bounce_pass` | 6.11 to 5.95 mm | 21.3 to 20.8 mm |
| `chest_pass` | 7.93 to 7.57 | 24.1 to 23.4 |
| `deflect_high` | 4.46 to 4.12 | 12.9 to 12.1 |
| `double_foot_landing` | 7.47 to 7.15 | 23.7 to 23.1 |
| `hooks_jump_pull_in` | 7.40 to 7.04 | 22.9 to 22.2 |
| `hooks_outside_hand` | 9.31 to 9.02 | 25.3 to 24.7 |
| `one_hand_high_pass` | 2.17 to 2.11 | 5.2 to 5.1 |
| `one_hand_snatch_to_other_hand` | 7.81 to 7.53 | 24.5 to 24.0 |
| `overhead_pass` | 1.99 to 1.69 | 6.5 to 5.7 |
| `two_hand_catch_chest` | 7.68 to 7.34 | 23.7 to 23.0 |
| `two_hand_snatch_pull_in` | 7.60 to 7.29 | 24.1 to 23.4 |
| `two_hand_snatch_straight_back` | 7.21 to 6.85 | 22.2 to 21.4 |

- No phase is worse on the shared athlete by more than 0.5 mm.
- `hooks_outside_hand/contact` comes under 10 mm; `facing_away` stays over,
  at 18.03 mm.
- The gains are small, 0.06 to 0.36 mm per drill median, because the two
  bodies have the same clavicle. These numbers measure the girdle and the
  hand; they cannot see how the figure looks. That is step 4.

## Both bodies drawn, every pair looked at (step 4)

All 12 drills, 51 phases, three views each (153 images per body), rendered
with the renderer's own `main` on the same jobs:

    blender -b --python blender_movement_render.py -- --job <job> [--job <job> ...] --output out/step4-render
    blender -b --python scripts/shared_athlete_probe.py -- <netball-athlete.blend> render --job <job> [--job <job> ...] --output out/step4-shared2

**A first shared render was not a fair pair and was discarded.** Opening the
shared file brought its own Key, Fill and Rim lights (700, 500 and 850 W),
which lit the shared athlete on top of the renderer's lights. The probe now
starts from the renderer's empty factory scene and appends only the rig and
its children. Checked on `chest_pass/ready` quarter: floor corner brightness
199.1 against the render rig's 199.5. An earlier version of the probe left the
startup cube in front of the athlete; the brightness number did not show it
and the picture did.

The re-measure with the appended athlete gives the same poses: 0.000000 mm
on every bone and 0.0000 mm on every anchor error against the opened file.

Every pair was looked at, sheet by sheet (`scripts/before_after_sheet.py`):

- Every phase takes the same pose on both bodies, with the ball and the
  hands in the same places. 7 to 14 per cent of pixels differ per view, which
  is the body and the kit, not the pose.
- The shared athlete's dress, bib and shoes render without a visible defect
  in all 153 views.
- `one_hand_high_pass/ready` shows the same hold on both bodies (hand behind
  the ball at chin height), so the open grip question for the coach
  (`docs/FINDING_HIGH_PASS_READY_GRIP.md`) applies to the shared athlete too.

## Report (step 5)

**Better or worse, per drill:** better on all 12, by 0.06 to 0.36 mm of
median anchor error; worse on none. Phases over 10 mm: 2 to 1. The shoulder
reach limit stays, because both MPFB bodies have the same clavicle.

**What a switch needs:**

1. The renderer must load the shared athlete instead of building its own MPFB
   body: append the rig and its children from the delivered file into the
   empty scene, clear its Action, and mute its four IK constraints (the build's
   only constraints; refuse any other). This probe
   does exactly that, in its own process.
2. The bone-name case: `Head` against the renderer's `head`. The rig
   contract spells it `Head` (and `root`) and the athlete already does; Main
   corrected on 12 Nov that the RENDERER reads the contract names and the
   athlete is renamed in nothing. Only this probe renames it, in its own
   process, because the renderer on main still reads `head`.

   **A CORRECTION.** An earlier version of this item said that the renderer
   refuses a body with no `head` bone and that the producer fixes the name.
   Main withdrew that ruling the same day.
3. The athlete's location: the delivered file is outside the repository. The
   renderer must find it through the athlete manifest, never a machine path
   (MAN-5).
4. The licence check: the renderer refuses a figure whose assets this
   repository has not licensed. The shared athlete's assets are licensed by
   its own manifest, so the check must read that manifest; this probe left
   the records empty.
5. Every receipt must name the athlete revision and its GLB SHA-256, as it
   names the build.
6. Every manual figure is re-rendered, and the coach sees the new kit.

## The switch, rendered (13 Nov 2026)

Items 1 to 5 of the list above are on main (#152, #153, #154). With the
owner's licence ruling, the renderer drew every manual figure on the shared
athlete. To find what moved, it also drew the same jobs on the older render
body, from the same commit:

- Both runs: commit `96ba152`, tree clean before and after, the same 12
  jobs (each receipt's `jobSha256` paired), 51 phases each, none failed.
- Shared athlete: `09-gait-v2`, revision 9, GLB SHA-256 `2b48758b...`,
  master SHA-256 `95234296...`, the master licensed under the 13 Nov ruling.

`scripts/compare_athlete_receipts.py` reads the two sets of receipts phase by
phase, and the jobs for which hand holds the ball. Its output is
`docs/evidence/shared-athlete-what-moved-2026-11-13.json`.

**A CORRECTION.** The first version of this table gave the nearest digit as
7.04 to 6.85 mm. It counted the free hand of each one-hand hold, 219 to
980 mm from the ball (review round 1). Only the holding hands are counted
now: 54 readings, the largest 8.65 mm.

| Measure, 51 phases | Older body | Shared athlete |
|---|---|---|
| Ball anchor error, median | 7.53 mm | 7.13 mm |
| Phases with ball anchor error over 10 mm | 2 | 1 |
| Worst ball anchor error (hooks, outside hand, `facing_away`) | 18.16 mm | 18.03 mm |
| Girdle verdict changed | | none |
| Nearest digit to the ball, median, each holding hand | 6.97 mm | 6.80 mm |
| Phases with any body vertex inside the ball | 20 | 24 |
| Phases more than 1 mm deeper inside the ball | | none |
| Phases more than 1 mm shallower | | 3 |

The renderer's own route gives the same anchor figures as the probe
measured on 12 Nov (7.53 to 7.13 mm, 2 to 1 over 10 mm).

**Body inside the ball.** The net change is 4 phases: 9 phases touch the
ball on the shared athlete and not on the older body, and 5 do the reverse.
The 9 are contacts under 1 mm, 3 to 6 vertices, at most 0.82 mm deep (the
hooks jump pull-in). The 5 were at most 1.59 mm deep (the deflect high
contact). The deep contacts are the same on both
bodies and a little shallower on the shared athlete: the chest pass release
20.25 to 19.85 mm, the bounce pass release 17.75 to 17.61 mm, the overhead
release 9.55 to 8.75 mm, the one-hand high ready 8.63 to 8.15 mm. They are
recorded in `docs/FINDING_HIGH_PASS_READY_GRIP.md`; the switch did not make
them.

**Looked at.** A before-and-after sheet of each of the 12 drills, quarter
view (`scripts/before_after_sheet.py`). In every phase the pose and the ball
are where they were; the body, the kit and the bib letters changed, and 7.6 to
10.3 % of the pixels moved. One framing defect is on both bodies: at the
two-hand chest catch release, the frame cuts the ball.
