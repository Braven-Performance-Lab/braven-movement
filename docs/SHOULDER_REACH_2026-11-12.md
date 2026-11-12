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

## The cause (goal step 2)

Measured with `scripts/engine_rest_clavicle.py` (engine) and
`scripts/rig_rest_clavicle.py` (render rig), both sides, on `09bf701`:

| Clavicle | Length | Back of straight out | Up |
|---|---:|---:|---:|
| Engine, rest | 17.65 cm | 32.96 deg | 5.37 deg |
| Engine, `chest_pass/ready` | 17.65 cm | 15.29 deg | 5.78 deg |
| Render rig, rest | 12.63 cm | 2.85 deg | -8.50 deg |

- The engine's clavicle is rigid: 17.65 cm at rest and in every pose measured.
- The engine's REST pose holds the clavicles retracted, 33 degrees back. To
  stand, it swings them about 18 degrees forward. Because the bone points
  back, that swing carries the shoulder FORWARD AND OUTWARD: 4.9 cm and 1.9 cm.
- The render rig's REST clavicle already points almost straight out, close to
  the engine's standing posture. Asked for the same 4.9 cm forward, its
  clavicle can only swing forward, which carries the shoulder INWARD. So it
  misses across, by about 22 mm, at every neutral phase.
- The length difference (17.65 against 12.63 cm, 20.4 per cent per torso,
  as recorded) adds to this on large movements.

So the gap is mainly the two REST postures, which the displacement field
assumes are equivalent, and second the clavicle length. It is not a defect
in how the renderer applies the shift: `rotate_bone_toward` lands on the
nearest reachable point by construction.

## Options (goal step 3)

**Ruling, 12 Nov 2026 (Main): keep the gap (option D).** No shift convention
closes it. The option probes are PARKED, not on main:
`scripts/girdle_option_probe.py`, `scripts/engine_clavicle_directions.py`,
`scripts/compare_reach.py` and `scripts/compare_options.py` are on branch
`lane/shoulder-reach-option-probes` at `d900c70`. Every command below that
names them runs on that branch.

### B, measured: send the shift from the engine's STANDING posture, not its rest

Simulated by subtracting the engine's `chest_pass/ready` shift (left
0.044048, -0.114037, -0.014476; right -0.043878, -0.114333, -0.014548
torsos) from every phase of copies of the jobs, then posing all phases with
the unchanged renderer. `python scripts/compare_reach.py out/reach-main.json
out/reach-optB.json`:

| | Now (`09bf701`) | Option B |
|---|---:|---:|
| Shoulder miss, median / max | 23.19 / 41.13 mm | 3.35 / 24.80 mm |
| Anchor error, median / max | 7.53 / 18.16 mm | 0.19 / 17.61 mm |
| Phases over 10 mm | 2 | 1 (`hooks_outside_hand/facing_away`) |
| Ball centre moves, median / max | | 41.9 / 52.7 mm |
| Largest bone move per drill | | 42.9 to 54.7 mm |

Six phases get worse by more than 0.5 mm: `overhead_pass` lift, step and
release (to 4.50, 4.52, 3.73 mm), `one_hand_high_pass` ready and lift (to
7.68, 3.34 mm) and `deflect_high/ready` (to 4.21 mm), the drills that raise
the arms.

The cost is that EVERY figure's ball moves about 4 cm back, because on main
the drawn shoulders already follow most of the 4.9 cm forward part of the
shift and B removes it. Whether that is a correction depends on whether this
rig's rest pose is the engine's rest or its standing posture. Its clavicle,
2.85 degrees back, lies between them (32.96 at rest, 15.29 standing). That is
a modelling judgment and no number here settles it. B also changes a job
field that the movement side owns.

### A and C, measured, beside B

`scripts/engine_clavicle_directions.py` exports the engine's clavicle
direction at rest and at every graded phase. `scripts/girdle_option_probe.py`
poses all 51 phases with the renderer's own code and one substitution:

- A: each clavicle turns by the engine clavicle's own rotation from rest,
  applied to this rig's rest direction. The renderer's girdle refusal is off
  in that process only, because A aims at its own target; the receipt is
  still written against the job's girdle.
- C: this rig's rest clavicles are first turned to the engine's rest
  direction (32.96 deg back, 5.37 deg up); the job's shift is then applied
  unchanged.

`python scripts/compare_options.py out/reach-main.json A=out/reach-optA.json B=out/reach-optB.json C=out/reach-optC.json`:

| | Shoulder miss, median / max | Anchor error, median / max | Over 10 mm | Worse | Ball moves, median / max | Largest bone move |
|---|---:|---:|---:|---:|---:|---:|
| Now | 23.19 / 41.13 mm | 7.53 / 18.16 mm | 2 | | | |
| A | 24.56 / 41.81 | 13.72 / 21.14 | 49 | 51 | 7.0 / 21.3 mm | 21.9 mm |
| B | 3.35 / 24.80 | 0.19 / 17.61 | 1 | 6 | 41.9 / 52.7 | 54.7 |
| C | 0.85 / 39.02 | 0.21 / 26.70 | 3 | 7 | 57.9 / 66.7 | 72.4 |

"Worse" counts phases whose anchor error rises by more than 0.5 mm.

- A moves the figures least but misses the job's girdle on every phase. The
  rotation is the engine's own value, but a 12.63 cm clavicle turned from a
  nearly straight rest does not put the shoulder where a 17.65 cm clavicle
  turned from 33 degrees back puts it. The anchor error measures that.
- B and C close the gap on most phases, and each moves every ball 4 to 6 cm
  and makes the arm-raising phases worse. C also makes
  `hooks_outside_hand/facing_away` worse (26.70 mm) and adds
  `one_hand_high_pass/ready` over the rule (12.46 mm).
- None of the three meets "every phase under 10 mm and no phase worse".

### D: keep and record

The gap stays as recorded in `docs/KNOWN_ISSUES.md`.
