# The 31 register entries with no build: which are still true

`docs/KNOWN_ISSUES.md` on `main` at `9b35621` has 31 entries whose build is
"Not recorded in the register". Main's goal (13 November 2026) asks which of
them are still true, so that only those are measured again. This file classes
each one. No entry of the register changes here.

## Method

Three readers classed the entries, 10, 10 and 11 each, by reading the full
record of each entry (`docs/KNOWN_ISSUES.md` at `b48512a`) and then `main` at
`9b35621` with `git show` and `git grep`. Each class needs evidence that can be
checked:

- **True**: the cause is still in the code or files on `main`, at a path and line.
- **Gone**: a change on `main` removed the cause, with its commit.
- **Ruled**: a decision in a spec, or a ruling on the lane board, settles it.
- **Unknown**: only a new measurement can tell.

Models re-read the evidence for entries 1335, 1353, 1944, 1982, 1998 and 4723
on `main`. A reader gave entry 1982 the class "gone"; Models changed that, as
the row says.

## Counts

| Class | Entries |
|---|---:|
| True | 21 |
| Ruled | 6 |
| Gone | 1 |
| Unknown | 3 |
| **Total** | **31** |

None of the 6 ruled entries is built on `main`. A ruling settles what to do,
so these entries need no new measurement. But the defect stays until the
ruling is built.

## The entries

The number is the entry's line in the register at `b48512a`, which its Full
record link names.

| Line | Entry | Class | Evidence on `main` at `9b35621` |
|---:|---|---|---|
| 292 | Reference catch is not yet a final coaching sample | True | `blender_mpfb_reference_catch.py:69` still has `--reference-compared`, and nothing records a coaching-sample acceptance. |
| 315 | Presentation is ready for review, not final publication | True | `blender_mpfb_reference_catch.py:950` still makes the placeholder graphite kit. Coaching acceptance has not happened. |
| 323 | Reference media is local-only | True | `config/reference_catch.v1.json:8` records only the hash. `references/README.md:3`: reference images are ignored by Git. |
| 330 | Five coaching phases cannot fail | True | Phases are still fixed fractions (`netball_two_hand_snatch_pull_in.json:37`), and no event-anchored phase code is on `main`. |
| 390 | The library is not smooth enough to animate | Ruled | Spec 1 decision 12.2: the limit is the worst value a coach saw without comment, taken to the coach morning. No per-frame step gate is on `main`. |
| 899 | A height measure exists now: `ballHeightCm`, above the court | Ruled | Spec 1 decision 12.7 decides gate 4. Not built: `netball_one_hand_high_pass.json:6` still says no measure reads a height. |
| 1075 | No units-correct distance measures, and six cues already want them | Ruled | Spec 1 decision 12.3: grade the six distance cues, chest pass first. Not built: `segment_measures.py:141-157` has no ahead-of-chest or step-length measure. |
| 1270 | A release clip ends before its ball lands | True | `netball_bounce_pass.json:61` still releases at 0.8, and the clip contract does not say where ball data stops. |
| 1335 | The moment gap is recorded every run and compared on none of them | True | `verify_tactics_clip.py:301` compares only the worst asserted gap. The symptom has gone: `clip-baseline.json:10` now reads -0.001 s. |
| 1353 | The coach animation exporter has no tests | True | No file in `spikes/test_*.py` or `tests/` names `export_coach_animations`. |
| 1415 | FIVE coaching checkpoints now fail, and no number was changed to stop them | True | The band in `netball_one_hand_snatch_to_other_hand.json:52-54` is still 30 to 120. Whether it still reads 146.01 needs a solve. |
| 1435 | AND THE DIAGNOSIS BELOW IS SUPERSEDED: the bands were never wrong | True | `netball_deflect_high.json:69-70` still grades `send_on` at 1.0, and no ruling picks the release frame. |
| 1527 | The follow-through is rough where the arm now moves | Unknown | Release work landed after it was recorded. Measure the upper-arm step on `netball_deflect_high`, frames 74 and 75, on a solve of `main`. |
| 1588 | The deflect carry still passes close to her face | True | `netball_deflect_high.technique.json:16-17` still keys `control` at 0.62, and no ruling sets the distance. |
| 1612 | A graded phase can sit in the middle of an interpolation | Ruled | Board ruling Main/catch-pullin-12-8 leaves this class to the event-anchored phases, which are not built. |
| 1721 | What is left above 10 degrees, in full | Unknown | A library-wide list of measured steps. Only a new sweep on `main` can confirm it or empty it. |
| 1735 | How wide the elbows sit with the ball at the chest | True | `contact_solve.py:127` still has `ELBOW_POLE_ANGLE_DEGREES = 31.3`, and no technique file sets `elbowAngleDegrees`. |
| 1944 | The cold-start seed set is four copies of one pose | True | `contact_solve.py:463-467`: `seeds()` still varies only `{side}_lowarm_twist`. |
| 1982 | The waiting hand's own history | Gone, a coach question left | The defect was fixed in `a6c7406` (27 August), before the register: `possession.py:521` wraps the ready point in `within_every_shoulder`. What is left is the coach's question about the `ready` dial, which needs no build. |
| 1998 | Two callers still measure the reach from the midpoint | True | `possession.py:626` and `:678` still call `toward` without `within_every_shoulder`. Latent, as the entry says. |
| 2025 | The mean elbow separation agreed with the manual by mixing two populations | True | `contact_solve.py:127` is still 31.3. Marius ruled on 30 August to defer the angle, and that ruling is in the full record. |
| 2076 | A free hand with no post-contact key would rest at the contact point | True | `possession.py:558-560`: `resting_point` still has no guard for a technique whose only key is the contact offset. |
| 2176 | The term named continuity is a pull toward the rest pose | True | `possession_solve.py:286-287` and `movement_engine.py:594-595` still set no target. |
| 2235 | The residual the cold-start test cannot see, and why it is excluded | True | `test_cold_start.py:75` still has `STILL_CM = 1.0`, so `hooks_jump_pull_in` is still excluded. |
| 2316 | The second hand travels 14 cm out to meet the ball, and a coach must rule | True | The `join` and `gather` keys are unchanged (`netball_one_hand_snatch_to_other_hand.technique.json:20`, `netball_hooks_outside_hand.technique.json:20`). No ruling. |
| 2367 | The ball speed for the whole library is one undocumented constant | Ruled | Spec 1 decision 12.9 decides it. Not built: `author_flight.py:40` still has `DEFAULT_SPEED_CM = 600.0`. |
| 2389 | The four contact hitches are one sub-frame timing defect | True | `possession.py:597` still times the flight from the release frame, not the release key. |
| 2420 | The sub-frame defect is at the athlete's release only | True | Same line as 2389, `possession.py:582-597`, unchanged. |
| 2723 | The pace has no author either | True | `netball_two_hand_catch_chest.motion.json:3` still types `"frames": 98` with no note. The library now has 12 drills, not 8. |
| 3747 | A one-handed release is far less determined than a two-handed one | Unknown | The cause is a hypothesis. Repeat the `up` and `ahead` sweeps on `netball_one_hand_high_pass`, with and without a constraint on the free arm and trunk. |
| 4723 | The section cutter and its posters | Ruled | Spec 2 decision 11.7: "Use the stance frame for both". Not built: `video_section_cuts.py:644` still has poster 619. **The ruling cannot be built as worded**: refer to the next section. |

## Decision 11.7 cannot be built as worded

Spec 2 decision 11.7 says to use the stance frame, 560, as the poster for both
open sections. Frame 560 is inside the `ready-between` window, 538 to 584. It
is outside the `release-rep09` window, 598 to 653. `check_poster` in
`spikes/video_section_cuts.py` refuses a poster outside its clip, because the
poster is the one frame a coach is certain to see. Models wrote that
recommendation in spec 2 and did not check it against the window. The owner's
sign-off accepted the recommendation as written. A sharper release poster
inside 598 to 653, or a new window, needs his choice.

## What follows from this, for Main

- Step 3 of the goal closes entries that are gone or ruled. Only entry 1982 is
  gone. The 6 ruled entries are not built, so closing them would hide a defect
  that is still on `main`. Models proposes to mark them "Ruled, not built" with
  the decision, and to keep them open until the ruling is built.
- The 21 true entries and the 3 unknown entries need a build and an instrument.
  Step 4 lists the lane and the script for each.
