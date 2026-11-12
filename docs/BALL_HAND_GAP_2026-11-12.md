# The ball-to-hand gap, solve against render (12 Nov 2026)

Main's goal "Fix the renders that draw the ball off the athlete's hands" started
from a note of 15 Sep: "22 of 51 phases unheld, 15.06 cm median, 26.02 cm max,
8.54 cm floor". That note recorded the numbers and not the instrument. This
document re-measures the gap on `main` at `4a54964` with two instruments that
are now in `scripts/`.

## Instruments

- `scripts/ball_hand_gap_solve.py` reads the engine's solve for each graded
  phase: wrist to ball centre, less the radius, in arm lengths.
- `scripts/ball_hand_gap_render.py` poses each phase with the renderer's own
  `pose_phase` and reads the same quantity from the posed MPFB rig. It also
  reads the drawn hand's digit profile (`finger_surface_clearance`).

Arm lengths, because the MPFB athlete is not the size of MHR's. A difference is
converted to centimetres with the MPFB arm.

## Inputs

- Jobs: `export_blender_job.py --all` on `4a54964`, 12 movements, 51 phases.
  HEAD was the same before and after the export and both measurements.
- 29 phases hold the ball. Every one of them carries a `grip`, so the renderer
  places the gripping hands from the ball. 22 phases do not hold it.
- One phase cannot be posed: `netball_one_hand_high_pass/ready` raises
  `FLEXION_AXIS: r index is set to flex about axis 0, which carries only 0.44
  of the turn`. The renderer records the same failure and draws no figure for
  that phase. 50 phases are measured.

## Result

| Phases | Hands | Render minus solve, median | Maximum |
|---|---:|---:|---:|
| Held | 56 | 0.00 cm | 2.54 cm |
| Free | 44 | 1.04 cm | 4.66 cm |

- The 53 gripping hands sit 3.5 to 4.4 cm from the ball surface at the wrist.
  Their nearest digit is 6.5 to 8.2 mm from it. No digit is inside the ball.
- In free phases the ball is in flight in the solve too. The nearest hand is a
  median 154 cm from it in the solve, and the render follows the solve within
  4.66 cm.
- The 15 Sep numbers are not the free-ball gap (median 154 cm) and not the
  render-minus-solve difference (median 0.00 cm held, 1.04 cm free). Their
  instrument is not recorded, so they cannot be re-measured.

## What the gap cannot see, and the measure that can

In a held phase the renderer places the gripping hands FROM the ball. If the
ball is in the wrong place relative to the body, the hands go with it and the
gap above still reads zero. The gap is blind to that error, and that error is
the defect FIG-2 describes: `pose_phase` places the ball from the rig's own
shoulder midpoint, so the ball carries the girdle's error one for one
(`docs/KNOWN_ISSUES.md`, "The ball is anchored to a landmark the job does not
transmit").

The render instrument therefore also reads the girdle receipt's
`ballAnchorErrorMm`: the distance between the shoulder midpoint the rig reached
and the one the job asks for. On `4a54964`, 50 phases:

| Statistic | Value |
|---|---:|
| Median | 7.55 mm |
| Maximum | 20.45 mm |
| Above the 10 mm rule | 2 |
| Above 5 mm | 40 |

| Phase | Ball | Error |
|---|---|---:|
| `netball_hooks_outside_hand/facing_away` | free | 20.45 mm |
| `netball_hooks_outside_hand/contact` | held | 11.60 mm |
| `netball_bounce_pass/follow_through` | free | 9.16 mm |
| `netball_hooks_outside_hand/gather` | held | 9.06 mm |

Every phase reports the verdict `out of reach`: the clavicle rotates and does
not stretch, so the shoulder lands on a sphere and the residual is measured,
not forced. This agrees with the renderer's docstring ("2 of 51 phases exceed
the ten-millimetre rule").

So FIG-2 ("22 of 51 phases, up to 26 cm") does not reproduce on `4a54964`. The
girdle field and `pose_girdle` (September) took the error from up to 8.45 cm
to at most 2.05 cm. What remains above the rule is two phases of one drill,
the drill where she is turned. The 40 phases above 5 mm include neutral
`ready` phases at about 8.3 mm, so part of the median is a constant of the
clavicle sphere and not a girdle that failed to move. That is not separated
here.

## The look

This look cannot see a 1 to 2 cm anchor error either, because the hands move
with the ball. The renderer drew three held phases in three views each:
`netball_two_hand_catch_chest/contact`, `netball_chest_pass/drive` and
`netball_hooks_outside_hand/contact`. In all nine panels the ball is in the
gripping hands. The one-handed catch shows the free hand clear of the ball.

## What this does not cover

- The renderer's run-to-run pixel band (goal step 2) is not measured here.
- `netball_one_hand_high_pass/ready` has no figure, so nothing about its ball
  is known from the render.
