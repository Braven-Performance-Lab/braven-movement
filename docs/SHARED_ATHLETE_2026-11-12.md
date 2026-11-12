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

    blender -b <netball-athlete.blend> --python scripts/shared_athlete_probe.py -- out/reach-shared.json spikes/poc-output/*.job.json

Three things are done in that process only and never saved:

- The bone `Head` is renamed `head`, the only name the renderer uses that
  differs; the vertex group follows the rename, and the probe checks it.
  The owner's spec 3 (12.7) rules that the producer fixes the bone-name case.
- The assigned Action (`Jog`) is cleared and every bone returns to its bind
  pose.
- The four IK constraints are muted, because they would override the arm and
  the leg the renderer poses.

All 51 phases of the 12 drills pose, with no failure.

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
