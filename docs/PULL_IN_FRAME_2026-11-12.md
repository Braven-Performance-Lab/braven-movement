# The two-hand catch's pull-in frame: decision 12.8 measured

Measured on 12 November 2026 for spec 1 decision 12.8. The instrument is
`scripts/pull_in_frame.py`, and its tests are in `tests/test_pull_in_frame.py`.

## What was measured, and on which commit

- **The library and the engine:** Braven Movement `main` at `7ad19f8`. The
  branch changes nothing under `spikes/`.
- **The instrument:** commit `1a255ba` on `lane/models-pullin-frame`. The
  working tree had no changes before or after the run.
- **The command:**

      cd spikes
      pixi run --frozen -- python -B ../scripts/pull_in_frame.py

The drill `netball_two_hand_catch_chest` has 98 frames. Its definition grades
the `pull_in` phase at 0.72, which reads frame 70. Its ball key of the same
name is at 0.76 in both key files, which is frame 74. The instrument solves the
drill once with the production `possession_solve`, then reads the `pull_in`
checkpoints at both frames. It moves the definition in memory and writes no
file. A control refuses the run unless the in-memory definition at 0.72 reads
exactly the values of the shipped definition.

Three runs gave the same readings. Only the count line of part 2 changed
between them, when the instrument began to print the second count.

## 1. The two readings

| `pull_in` read at | frame | left elbow flexion (band 105 to 150) | trunk lean (band 0 to 12) |
|---|---:|---:|---:|
| 0.72, the definition, as shipped | 70 | 144.39, within | 1.97, within |
| 0.76, the ball key | 74 | 145.86, within | 1.96, within |

- The elbow moves 1.47 degrees over the four frames, and the trunk lean
  0.01 degrees. The solver noise floor recorded in
  `scripts/retiming_verdicts.py` is 6.00 degrees.
- No verdict changes.
- The values are the same as the earlier reading in
  `spikes/movements/netball_chest_pass.json`, field `trunkLeanNote`, which
  gives 144.39 and 145.86.

## 2. The drills where a coaching phase and its key differ

The instrument pairs each drill's coaching phases with its keys by name, over
the 12 drills that have a definition and a key file. A name is a label, not a
correspondence, so the instrument prints the gaps and a person judges them.

- **Against the technique file:** 7 drills differ and 5 agree. The solve
  reads the ball from this file. The count is the same as the one in
  `docs/KNOWN_ISSUES.md` for 14 September 2026.
- **Against either key file:** 8 drills differ and 4 agree. The eighth drill,
  `netball_two_hand_snatch_pull_in`, differs only from its motion file. The
  solve reads only the frame count, the frame rate and the trunk turn from the
  motion file.

| drill | phase | definition | key | from the record |
|---|---|---:|---:|---|
| `netball_chest_pass` | drive | 0.62 | 0.71 | **By design.** Marius ruled the retiming on 10 September, and it moved only the technique key (`scripts/retiming_verdicts.py`). |
| `netball_bounce_pass` | drive | 0.62 | 0.71 | **By design**, by the same ruling. |
| `netball_deflect_high` | control | 0.70 | 0.62 | **Open issue.** The graded frame reads a straight line between two authored keys (`docs/KNOWN_ISSUES.md`, "A graded phase can sit in the middle of an interpolation"). |
| `netball_deflect_high` | send_on | 1.00 | 0.80 | **Open issue.** The phase is graded at the end of the follow-through. The ball leaves at the key, and there the band holds (`docs/KNOWN_ISSUES.md`, the table of the four release failures). |
| `netball_hooks_jump_pull_in` | release | 1.00 | 0.95 | **Open issue**, in the same table. |
| `netball_hooks_outside_hand` | gather | 0.74 | 0.62 | **No reason found.** |
| `netball_one_hand_snatch_to_other_hand` | join | 0.72 | 0.60 | **No reason found.** |
| `netball_two_hand_catch_chest` | pull_in | 0.72 | 0.76 | **Recorded as below threshold**, in `netball_chest_pass.json`, field `trunkLeanNote`. Section 1 measures it. |
| `netball_two_hand_snatch_pull_in` | contact | 0.55 | 0.50, motion file only | **No reason found.** |

**The scope of "no reason found".** I read the notes on the key in the
technique or motion file and the notes in the definition. I also searched
`docs/` and every `*.md` file for the phase name with the two numbers. A
reason written in other words can still exist.

**No code joins a phase to a key by name.** A search of `spikes/` and
`scripts/` found no code that matches the names in `afterContact` against the
names of the definition's phases.

## 3. Recommendation for decision 12.8

**Keep 0.72. Fix the catch together with the other gaps when the queued
event-anchored phases land.**

1. A move to 0.76 changes no verdict. The change of 1.47 degrees is under the
   noise floor.
2. The library has no rule that a phase sits on its key. `docs/KNOWN_ISSUES.md`
   calls the split "a statement about the design rather than about a lapse",
   and it asks for this class of gap to be fixed together, not one drill at a
   time.
3. The drill file is under gate 4. A gate 4 change that has no effect on the
   grade costs a review for nothing.

The other answer, a move to 0.76, is also safe. It changes no verdict, and it
puts the graded frame where both key files put the pull-in.

## The full output of the instrument

Commit `1a255ba`, run from `spikes/` with the command above. Exit code 0.

```
PART 1: netball_two_hand_catch_chest, one possession solve, 98 frames.
  control: the shipped definition and the in-memory one at 0.72 read the same values.
  pull_in at 0.72, frame 70, the definition (shipped):
      leftElbowFlexionDegrees       144.39   band 105.0 to 150.0 within
      trunkLeanDegrees                1.97   band 0.0 to 12.0    within
  pull_in at 0.76, frame 74, the ball key:
      leftElbowFlexionDegrees       145.86   band 105.0 to 150.0 within
      trunkLeanDegrees                1.96   band 0.0 to 12.0    within
  every frame from 70 to 74:
      leftElbowFlexionDegrees    144.39  145.06  145.55  145.85  145.86
      trunkLeanDegrees           1.97  1.96  1.95  1.96  1.96

PART 2: 12 drills have a definition and a key file; 8 differ on a shared name against either key file, 7 against the technique file alone, 4 agree, 0 share no name.
  netball_bounce_pass  [DIFFERS]  files: netball_bounce_pass.motion.json, netball_bounce_pass.technique.json
      ready          phase 0.00   key netball_bounce_pass.motion.json/keys[0] 0.00
      pull_to_side   phase 0.32   key netball_bounce_pass.motion.json/keys[1] 0.32; netball_bounce_pass.technique.json/afterContact[1] 0.32
      drive          phase 0.62   key netball_bounce_pass.motion.json/keys[2] 0.62; netball_bounce_pass.technique.json/afterContact[2] 0.71  <- differs by 0.09
      release        phase 0.80   key netball_bounce_pass.motion.json/keys[3] 0.80; netball_bounce_pass.technique.json/afterContact[3] 0.80
      follow_through phase 1.00   key netball_bounce_pass.motion.json/keys[4] 1.00
  netball_chest_pass  [DIFFERS]  files: netball_chest_pass.motion.json, netball_chest_pass.technique.json
      ready          phase 0.00   key netball_chest_pass.motion.json/keys[0] 0.00
      step           phase 0.34   key netball_chest_pass.motion.json/keys[1] 0.34; netball_chest_pass.technique.json/afterContact[1] 0.34
      drive          phase 0.62   key netball_chest_pass.motion.json/keys[2] 0.62; netball_chest_pass.technique.json/afterContact[2] 0.71  <- differs by 0.09
      release        phase 0.80   key netball_chest_pass.motion.json/keys[3] 0.80; netball_chest_pass.technique.json/afterContact[3] 0.80
      follow_through phase 1.00   key netball_chest_pass.motion.json/keys[4] 1.00
  netball_deflect_high  [DIFFERS]  files: netball_deflect_high.motion.json, netball_deflect_high.technique.json
      ready          phase 0.00   key netball_deflect_high.motion.json/keys[0] 0.00
      contact        phase 0.45   key netball_deflect_high.motion.json/keys[1] 0.45
      control        phase 0.70   key netball_deflect_high.motion.json/keys[2] 0.70; netball_deflect_high.technique.json/afterContact[0] 0.62  <- differs by 0.08
      send_on        phase 1.00   key netball_deflect_high.motion.json/keys[3] 1.00; netball_deflect_high.technique.json/afterContact[2] 0.80  <- differs by 0.20
  netball_double_foot_landing  [agrees]  files: netball_double_foot_landing.motion.json, netball_double_foot_landing.technique.json
      approach       phase 0.00   key netball_double_foot_landing.motion.json/keys[0] 0.00
      flight         phase 0.50   key netball_double_foot_landing.motion.json/keys[2] 0.50
      land           phase 0.82   key netball_double_foot_landing.motion.json/keys[4] 0.82; netball_double_foot_landing.technique.json/afterContact[0] 0.82
      absorb         phase 1.00   key netball_double_foot_landing.motion.json/keys[5] 1.00; netball_double_foot_landing.technique.json/afterContact[1] 1.00
  netball_hooks_jump_pull_in  [DIFFERS]  files: netball_hooks_jump_pull_in.motion.json, netball_hooks_jump_pull_in.technique.json
      gather         phase 0.00   key netball_hooks_jump_pull_in.motion.json/keys[0] 0.00
      contact        phase 0.58   key netball_hooks_jump_pull_in.motion.json/keys[2] 0.58
      pull_in        phase 0.82   key netball_hooks_jump_pull_in.motion.json/keys[3] 0.82; netball_hooks_jump_pull_in.technique.json/afterContact[0] 0.82
      release        phase 1.00   key netball_hooks_jump_pull_in.motion.json/keys[4] 1.00; netball_hooks_jump_pull_in.technique.json/afterContact[1] 0.95  <- differs by 0.05
  netball_hooks_outside_hand  [DIFFERS]  files: netball_hooks_outside_hand.motion.json, netball_hooks_outside_hand.technique.json
      facing_away    phase 0.00   key netball_hooks_outside_hand.motion.json/keys[0] 0.00
      contact        phase 0.50   key netball_hooks_outside_hand.motion.json/keys[2] 0.50
      gather         phase 0.74   key netball_hooks_outside_hand.motion.json/keys[3] 0.74; netball_hooks_outside_hand.technique.json/afterContact[0] 0.62  <- differs by 0.12
      pull_in        phase 1.00   key netball_hooks_outside_hand.motion.json/keys[4] 1.00; netball_hooks_outside_hand.technique.json/afterContact[1] 1.00
  netball_one_hand_high_pass  [agrees]  files: netball_one_hand_high_pass.motion.json, netball_one_hand_high_pass.technique.json
      ready          phase 0.00   key netball_one_hand_high_pass.motion.json/keys[0] 0.00
      lift           phase 0.35   key netball_one_hand_high_pass.motion.json/keys[1] 0.35; netball_one_hand_high_pass.technique.json/afterContact[1] 0.35
      release        phase 0.80   key netball_one_hand_high_pass.motion.json/keys[3] 0.80; netball_one_hand_high_pass.technique.json/afterContact[3] 0.80
  netball_one_hand_snatch_to_other_hand  [DIFFERS]  files: netball_one_hand_snatch_to_other_hand.motion.json, netball_one_hand_snatch_to_other_hand.technique.json
      ready          phase 0.00   key netball_one_hand_snatch_to_other_hand.motion.json/keys[0] 0.00
      reach          phase 0.35   key netball_one_hand_snatch_to_other_hand.motion.json/keys[1] 0.35
      contact        phase 0.50   key netball_one_hand_snatch_to_other_hand.motion.json/keys[2] 0.50
      join           phase 0.72   key netball_one_hand_snatch_to_other_hand.motion.json/keys[3] 0.72; netball_one_hand_snatch_to_other_hand.technique.json/afterContact[0] 0.60  <- differs by 0.12
      pull_in        phase 1.00   key netball_one_hand_snatch_to_other_hand.motion.json/keys[4] 1.00; netball_one_hand_snatch_to_other_hand.technique.json/afterContact[1] 1.00
  netball_overhead_pass  [agrees]  files: netball_overhead_pass.motion.json, netball_overhead_pass.technique.json
      ready          phase 0.00   key netball_overhead_pass.motion.json/keys[0] 0.00
      lift           phase 0.35   key netball_overhead_pass.motion.json/keys[1] 0.35; netball_overhead_pass.technique.json/afterContact[1] 0.35
      step           phase 0.58   key netball_overhead_pass.motion.json/keys[2] 0.58; netball_overhead_pass.technique.json/afterContact[2] 0.58
      release        phase 0.80   key netball_overhead_pass.motion.json/keys[3] 0.80; netball_overhead_pass.technique.json/afterContact[3] 0.80
      follow_through phase 1.00   key netball_overhead_pass.motion.json/keys[4] 1.00
  netball_two_hand_catch_chest  [DIFFERS]  files: netball_two_hand_catch_chest.motion.json, netball_two_hand_catch_chest.technique.json
      ready          phase 0.00   key netball_two_hand_catch_chest.motion.json/keys[0] 0.00
      contact        phase 0.45   key netball_two_hand_catch_chest.motion.json/keys[1] 0.45
      pull_in        phase 0.72   key netball_two_hand_catch_chest.motion.json/keys[2] 0.76; netball_two_hand_catch_chest.technique.json/afterContact[0] 0.76  <- differs by 0.04
      release        phase 1.00   key netball_two_hand_catch_chest.motion.json/keys[3] 1.00
  netball_two_hand_snatch_pull_in  [DIFFERS]  files: netball_two_hand_snatch_pull_in.motion.json, netball_two_hand_snatch_pull_in.technique.json
      ready          phase 0.00   key netball_two_hand_snatch_pull_in.motion.json/keys[0] 0.00
      react          phase 0.30   key netball_two_hand_snatch_pull_in.motion.json/keys[1] 0.30
      contact        phase 0.55   key netball_two_hand_snatch_pull_in.motion.json/keys[2] 0.50  <- differs by 0.05
      pull_in        phase 1.00   key netball_two_hand_snatch_pull_in.motion.json/keys[4] 1.00; netball_two_hand_snatch_pull_in.technique.json/afterContact[1] 1.00
  netball_two_hand_snatch_straight_back  [agrees]  files: netball_two_hand_snatch_straight_back.motion.json, netball_two_hand_snatch_straight_back.technique.json
      ready          phase 0.00   key netball_two_hand_snatch_straight_back.motion.json/keys[0] 0.00
      contact        phase 0.50   key netball_two_hand_snatch_straight_back.motion.json/keys[2] 0.50
      control        phase 0.68   key netball_two_hand_snatch_straight_back.motion.json/keys[3] 0.68; netball_two_hand_snatch_straight_back.technique.json/afterContact[0] 0.68
      return         phase 1.00   key netball_two_hand_snatch_straight_back.motion.json/keys[4] 1.00
```
