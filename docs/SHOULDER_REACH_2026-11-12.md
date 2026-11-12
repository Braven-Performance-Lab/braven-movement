# The shoulder reach gap, measured per drill and phase (12 Nov 2026)

Goal step 1 of the Blender lane's goal "Measure and close the shoulder reach
gap between the solve and the render rig". The issue on record is
`docs/KNOWN_ISSUES.md`, "This rig cannot reach the girdle the solve asks for".

## Instrument and inputs

- `main` at `09bf701`. Jobs exported with `export_blender_job.py --all` on
  that tip (12 movements, 51 phases), HEAD unchanged across the export.
- `scripts/ball_hand_gap_render.py` poses every phase with the renderer's own
  `pose_phase` and now also records, per shoulder, the girdle receipt's
  `offsetMm`, `perAxisMm`, `reachableMissMm` and `clavicleTurnedDegrees`:

      blender -b --python scripts/ball_hand_gap_render.py -- out/reach-main.json spikes/poc-output/*.job.json

`perAxisMm` is the drawn shoulder minus the wanted one, in Blender axes
(x left, y back, z up; the athlete faces -y).

## The whole library, 51 phases, 102 shoulders

| Quantity | Median | Range |
|---|---:|---|
| Shoulder miss | 23.19 mm | 0.09 to 41.13 mm |
| Drawn shoulder toward the midline of the wanted one | 21.85 mm | -1.96 to 25.03 mm |
| Drawn shoulder behind the wanted one | 6.98 mm | -3.18 to 35.35 mm |
| Drawn shoulder above the wanted one | 1.96 mm | -2.34 to 5.49 mm |
| Girdle width, wanted minus drawn | 43.53 mm | -1.06 to 50.04 mm |
| Clavicle's own turn | 20.55 deg | 0.56 to 28.80 deg |

The miss is mostly ACROSS: each drawn shoulder sits about 22 mm toward the
midline of where the job asks.

## Per drill

| Drill | Median shoulder miss | Worst | Median anchor error |
|---|---:|---:|---:|
| `bounce_pass` | 21.3 mm | 26.7 mm | 6.11 mm |
| `chest_pass` | 24.1 | 25.5 | 7.93 |
| `deflect_high` | 12.9 | 19.7 | 4.46 |
| `double_foot_landing` | 23.7 | 25.5 | 7.47 |
| `hooks_jump_pull_in` | 22.9 | 24.0 | 7.40 |
| `hooks_outside_hand` | 25.3 | 41.1 | 9.31 |
| `one_hand_high_pass` | 5.2 | 11.1 | 2.17 |
| `one_hand_snatch_to_other_hand` | 24.5 | 25.3 | 7.81 |
| `overhead_pass` | 6.5 | 25.5 | 1.99 |
| `two_hand_catch_chest` | 23.7 | 25.4 | 7.68 |
| `two_hand_snatch_pull_in` | 24.1 | 25.3 | 7.60 |
| `two_hand_snatch_straight_back` | 22.2 | 24.1 | 7.21 |

The two drills that raise the arms overhead miss least.

## What the job asks for at a neutral phase

The job's `shoulderShiftFromRestInTorsos` at each drill's first phase, scaled
onto this rig (rest torso 0.427689 m), in cm:

| Drill, phase | Left: out, forward, up | Right: out, forward, up |
|---|---|---|
| `chest_pass/ready` | 1.88, 4.88, -0.62 | 1.88, 4.89, -0.62 |
| `bounce_pass/ready` | 1.87, 4.90, -0.61 | 1.89, 4.88, -0.63 |
| `overhead_pass/ready` | 1.88, 4.89, -0.62 | 1.88, 4.90, -0.62 |
| `two_hand_catch_chest/ready` | 1.79, 5.06, 0.16 | 1.80, 5.07, 0.16 |
| `two_hand_snatch_pull_in/ready` | 1.79, 5.07, 0.20 | 1.79, 5.06, 0.19 |
| `double_foot_landing/approach` | 1.74, 5.13, 0.50 | 1.74, 5.11, 0.49 |
| `deflect_high/ready` | -0.19, 2.70, 5.81 | -0.18, 2.70, 5.81 |

At a neutral standing phase the job asks each shoulder to sit about 4.9 cm
forward and 1.9 cm out of the ENGINE'S rest pose, nearly the same on every
drill. A clavicle that swings forward pulls the shoulder toward the midline,
so this rig cannot do both, and it misses by about 22 mm across. A constant
this size at phases where nothing moves points at the two REST poses, which
the field assumes are equivalent, and not at the motion. That is the
question for step 2.
