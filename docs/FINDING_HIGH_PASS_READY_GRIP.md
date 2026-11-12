# Finding: the one-hand high pass `ready` grip, a question for the coach

For Main to take to the owner and the coach morning. This is a coaching call
(gate 4), so the grip is reported and not changed.

## Status

Until `a484302` the renderer refused `netball_one_hand_high_pass/ready`
(`FLEXION_AXIS`), so the drill had no `ready` figure. Option C, ruled on 9 Sep,
now draws it: the flexion limit of the right index is applied about the axis
that finger turned (z) and not the axis the rig names for fingers (x).

## The figure option C draws

Rendered on `4220714`. The receipt records the right index with `namedAxis` 0
and `appliedAxis` 2, turned x=26.8 y=-19.9 z=72.7 degrees.

- The right hand is under and behind the ball, wrist bent back, fingers
  pointing up. The ball is at chin height.
- In the front view the ball touches her chin and mouth. The receipt's body
  clearance agrees: 51 skin vertices inside the ball, at most 8.63 mm deep.
  The fingers are outside it (nearest digit 5.42 mm).
- For scale, on `main` `netball_chest_pass/release` already has 188 vertices
  inside the ball, at most 20.25 mm deep.

## The measurements, and what each one is of

Measured with `scripts/ball_off_finger_line.py`:

    blender -b --python-exit-code 9 -P scripts/ball_off_finger_line.py --

| Hand | Pose measured | Ball off the finger line |
|---|---|---:|
| `one_hand_high_pass/ready`, right | flexion limited about x (guard disabled, 7 Sep and `efdab9b`) | 110.9° |
| `one_hand_high_pass/ready`, right | the drawn hand, option C (`4220714`) | 27.7° |
| `one_hand_high_pass/lift`, right | the drawn hand | 46.3° |
| Every gripping hand of the other drills | the drawn hand | 41.8° to 46.4° |

**A CORRECTION.** The first version of this finding gave 110.9° as where the
ball sits behind the fingers. The finger line is read from the POSED finger,
and 110.9° was measured on a hand posed about the axis the guard rejects, which
the renderer does not draw. On the drawn hand the reading is 27.7°.

So the question for the coach is not "the fingers point away from the ball".
It is the knuckle: the right index turns 72.7 degrees about z, the axis no
other grip in the library flexes about (208 of 208 readings on the other
eleven drills turn about x). Option C applies the flexion licence to that
turn. Whether a finger can turn that way is the question the guard existed to
ask, and option C does not answer it.

## The question for the coach

At `ready` in the one-hand high pass, where is the ball relative to the
throwing hand? If the hand is under or behind the ball at chin height with the
fingers pointing up, as drawn, the figure can stand. If not, the solve's grip
is wrong and the technique file must change (Main's file, gate 4). The ball
touching her chin is part of the same question.

## What is not measured

- Whether a 72.7 degree turn about the index knuckle's z is a motion that
  joint has. No instrument here bounds it.
- The coach's own view of the hold.
