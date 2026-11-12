# Finding: the one-hand high pass holds the ball behind its fingers at `ready`

For Main to take to the owner and the coach morning. This is a coaching call
(gate 4), so the grip is reported and not changed.

## The measurement

Measured on `efdab9b` (`main` at `4a54964` plus measuring scripts only), with
`scripts/ball_off_finger_line.py`:

    blender -b --python-exit-code 9 -P scripts/ball_off_finger_line.py --

| Hand | Ball off the finger line | Ball off the palm plane |
|---|---:|---:|
| `netball_one_hand_high_pass/ready`, right | **110.9°** | 7.7° |
| `netball_one_hand_high_pass/lift`, right | 46.3° | 36.7° |
| Every gripping hand of the other drills | 41.8° to 46.4° | 33.8° to 39.8° |

"Ball off the finger line" is the angle between the direction the fingers
point and the direction from the hand to the ball. At 110.9° the ball is more
than a right angle behind where the fingers point. That is 65° outside the
range every other hold in the library uses. The same number was first
measured on 7 Sep (`docs/FLEXION_AXIS_PAPER.md`), and it has not changed.

## Why it matters

- The renderer refuses this phase (`FLEXION_AXIS`), so the drill has no
  `ready` figure.
- The fix ruled on 9 Sep (option C) draws the figure by applying the joint
  limit about the axis the finger actually turned. **It does not show that the
  grip is a hold a person can make.** The guard that refused it existed to
  catch a finger turning past its licence, and at this grip the finger turns
  through more than a right angle to reach the ball.

## The figure option C draws

Rendered on `a484302`, the commit that implements option C. The receipt
records the right index with `namedAxis` 0 and `appliedAxis` 2, turned
x=26.8 y=-19.9 z=72.7 degrees.

- The right hand is under and behind the ball, wrist bent back, fingers
  pointing up. The ball is at chin height.
- In the front view the ball touches her chin and mouth. The receipt's body
  clearance agrees: 51 skin vertices inside the ball, at most 8.63 mm deep.
  The fingers are outside it (nearest digit 5.42 mm).
- For scale, on `main` `netball_chest_pass/release` already has 188 vertices
  inside the ball, at most 20.25 mm deep.

## The question for the coach

At `ready` in the one-hand high pass, where is the ball relative to the
throwing hand? If the hand is under or behind the ball with the fingers
pointing up and back, the solve's grip is wrong and the technique file must
change (Main's file, gate 4). If the drill really holds the ball this way, the
figure from option C can stand.

## What is not measured

- Whether the drawn hand after option C stays inside the knuckle licence by
  more than the guard's own test. Step 4 of the Blender goal reads the receipt.
- The coach's own view of the hold.
