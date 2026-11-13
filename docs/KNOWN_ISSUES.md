# Known issues

Each entry is one open finding: what is wrong, the build and the instrument it
was measured with, who owns it and what closes it. The full text of every
entry is in this file at `b48512a`, linked from the entry. A **Since then**
line records a later ruling from the specs, not from this register.

Closed sections are in `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`. Rules for engineers are in `docs/ENGINEERING_RULES.md`.
Rules for the product are requirements in the Client Zone specs: the seven from this register are in spec 1 v0.7. The split is described
in `docs/KNOWN_ISSUES_SPLIT_PLAN.md`.

# Rendering and modelling

## This rig cannot reach the girdle the solve asks for

- **Finding:** The rig's clavicle is shorter than the engine's, so the rendered girdle is a median 43.98 mm narrower than the solve asks. The engine's clavicle is 17.65 cm against this rig's 12.63 cm. With the trunk turn, `facing_away` at 18.16 mm and `contact` at 10.22 mm stay over the 10 mm rule.
- **Build:** `0ee45ee`, `09bf701`
- **Instrument:** `scripts/ball_hand_gap_render.py`, `scripts/engine_rest_clavicle.py`, `scripts/rig_rest_clavicle.py`, `scripts/engine_clavicle.py`
- **Owner:** Rendering and modelling
- **Waits for:** Main ruled to keep the gap, and whether the rig is worth fixing waits for the owner's answer on which body the manual figures use.
- **Since then:** Marius answered on 12 November 2026: the manual figures use the shared athlete (spec 1, decision 12.5), so this rig leaves the manual figures.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 10](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L10)

## Reference catch is not yet a final coaching sample

- **Finding:** The MPFB catch render remains a review artifact, and final coaching-sample acceptance is still pending. MPFB's base topology and identity still limit fine facial acting and sport-specific muscle definition.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Rendering and modelling
- **Waits for:** Final coaching-sample acceptance closes it, and until then nobody sets `--reference-compared` or publishes the current pose.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 292](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L292)

## Presentation is ready for review, not final publication

- **Finding:** The presentation is ready for review but not for final publication. The athlete identity, final branded kit, ball artwork and production colour grade remain replaceable through the versioned configuration.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Rendering and modelling
- **Waits for:** Coaching acceptance comes before the final identity, kit, ball artwork and colour grade replace the current ones.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 315](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L315)

## Reference media is local-only

- **Finding:** The source photograph is not committed because publication rights have not been established. The configuration records only its SHA-256 and dimensions, so an authorised local copy can be verified.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Rendering and modelling
- **Waits for:** Not stated in the register.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 323](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L323)

### Moved out of this register

- `netball_one_hand_high_pass` cannot be posed at its ready phase: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- One failing phase aborted the whole library render: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- The ball is anchored to a landmark the job does not transmit: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- Fingertip evidence is soft guidance: a rule, now spec 1 requirement FIG-8. Its text is in this file [at b48512a, line 309](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L309).

# Movement

## Five coaching phases cannot fail

- **Finding:** Five coaching phases grade a measure that barely moves from the previous phase, so their checkpoints pass whatever the athlete does. The `react` phase of 2 Hand Snatches and Pull In moves 0.00. Both snatch drills grade before the ball moves, and `land` grades measures that stay static across a landing.
- **Build:** Not recorded in the register.
- **Instrument:** `build_library.py`
- **Owner:** Movement
- **Waits for:** It waits for the coach review's marks and notes on these phases, with event-anchored phases queued as the durable fix.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 330](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L330)

## The library is not smooth enough to animate

- **Finding:** The worst per-frame arm direction step across the library is still 19.3 degrees at 60 frames a second, which no person makes. The two remaining steps above 15 degrees are both on `netball_hooks_outside_hand`. An 11.7 degree hip-line step also sits between frames 45 and 46 of `netball_two_hand_snatch_pull_in`.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** It waits for a smoothing fix, which the agreed order places after the tactics spike and before the clips ship.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 390](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L390)

## Centimetres are stored in a field called degrees

- **Finding:** `footHeightGapCm` is in centimetres, but its band is held in `minimumDegrees` and `maximumDegrees`, three occurrences across the library. The measure reads the gap between the feet, so a double-foot landing with no flight passes every checkpoint. Its range of 0.00 to 1.22 cm sits below the 1.45 cm landmark noise, and the render shows no flight.
- **Build:** `b214bc4`, `dc50dfc`, `320bd01`
- **Instrument:** `scripts/landing_cue_sweep.py`, `scripts/flight_probe.py`
- **Owner:** Movement
- **Waits for:** It waits for a coach's view, through the content lane's agenda, on whether a foot height should be graded at flight and in what band.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 451](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L451)

## A height measure exists now: `ballHeightCm`, above the court

- **Finding:** On `netball_one_hand_high_pass` the ball peaks at frame 34 and the wrist at frame 31, so a fixed-phase checkpoint must name its quantity. At the shipped lift pose, `rightShoulderElevationDegrees` falls 20.34 degrees at a basin 0.02 torso lengths away that `ballHeightCm` does not see. Two sentences in that drill's `heightGapNote` are now false.
- **Build:** Not recorded in the register.
- **Instrument:** `sweep_ball_height.py`
- **Owner:** Movement
- **Waits for:** Marius's gate-4 ruling on whether the prose note may be corrected, and on the step-1 checkpoint itself, closes it.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 899](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L899)

## No units-correct distance measures, and six cues already want them

- **Finding:** The engine still has no ahead-of-chest measure and no step-length measure, and five cues would use them. The manual's warning against pulling the ball behind the head has no instrument on either pass. A 26 cm pull-back passed at 114.99 on `netball_overhead_pass`, so an angle cannot stand in for the distance.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** It waits for an ahead-of-chest measure built as its own unit of work, with its own anchor argument stated and measured.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 1075](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L1075)

## A release clip ends before its ball lands

- **Finding:** All three passes release at frame 76 of 96, which leaves 0.3167 s of flight in the clip. The `netball_bounce_pass` ball never reaches its target and falls 0.267 s short. The chest and overhead passes complete with only two frames and one to spare.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** It waits for a ruling, through `docs/TACTICS_CLIP_CONTRACT.md` and the coach agenda, on whether a pass clip carries the flight to the catch.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 1270](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L1270)

## The moment gap is recorded every run and compared on none of them

- **Finding:** `verify_tactics_clip.py` writes `momentGapSeconds` into `clip-baseline.json` for every clip, and the gate never reads it back. Both passes sat at −1.267 s against −0.017 to −0.034 for every catch until someone read the column by eye.
- **Build:** Not recorded in the register.
- **Instrument:** `verify_tactics_clip.py`
- **Owner:** Movement
- **Waits for:** It waits for a decision on what a moved moment gap means, because a landing's 0.32 s is correct and must not fail.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 1335](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L1335)

## The coach animation exporter has no tests

- **Finding:** `spikes/export_coach_animations.py` has no test file, and only hand-run regeneration evidences its determinism. Nothing fails if the schema changes shape, a key is dropped, or the output stops being deterministic.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** It waits for a schema and round-trip test, which the register lists as future work.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 1353](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L1353)

## FIVE coaching checkpoints now fail, and no number was changed to stop them

- **Finding:** A fifth checkpoint now fails, on 1 Hand Snatches to Other Hand at contact, where `leftElbowFlexionDegrees` reads 146.01 against a band of 30 to 120. It read 89.64 and passed before the free-hand fix moved the waiting hand to the chest. Erin Burger marked the same checkpoint NOT met, so the verdict flipped toward her with the band untouched.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** Not stated in the register.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 1415](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L1415)

## AND THE DIAGNOSIS BELOW IS SUPERSEDED: the bands were never wrong

- **Finding:** The four release checkpoints fail only at phase 1.000, the end of the follow-through, and all four sit within their bands when the ball leaves. Retimed to the release, each still differs from the phase before by 7.28 to 45.36 degrees against a 5.0 threshold. The deflect clears that threshold by only 2.28 degrees.
- **Build:** Not recorded in the register.
- **Instrument:** `MovementDefinition.separation`
- **Owner:** Movement
- **Waits for:** The coach morning decides which frame is the release, and nothing is retimed until then.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 1435](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L1435)

## The follow-through is rough where the arm now moves

- **Finding:** The worst per-frame upper arm swing on deflect high rose from 6.7 to 26.1 degrees once the arm followed through. The steps are single-frame spikes on `netball_deflect_high` at frames 74 and 75, where the solver picks a different branch.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** The smoothness pack, which already owns this class of defect and is queued, closes it.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 1527](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L1527)

## The deflect carry still passes close to her face

- **Finding:** On `netball_deflect_high` the ball surface passes 8.3 cm from her eye, at the authored `control` key at phase 0.62. Raising the route key's `ahead` value from 0.70 through 0.90 leaves it at 8.3 cm. No distance threshold separates this defect from a harmless dip, so no clearance guard exists.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** A coach has to say how far in front of her face the ball is controlled.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 1588](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L1588)

## A graded phase can sit in the middle of an interpolation

- **Finding:** `netball_deflect_high` grades its control checkpoint at phase 0.70, between authored keys at 0.62 and 0.80, so it reads a position nobody authored. Across twelve drills, seven disagree on at least one shared phase name and five agree. Nothing checks that definition and technique phases agree.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** Event-anchored phases, already queued, would fix this together with the landing checkpoints.
- **Since then:** Spec 1 decision 12.8 (13 November 2026) keeps the two-hand catch's pull-in at 0.72 and leaves this class to the event-anchored phases. `scripts/pull_in_frame.py` counts the pairs (`docs/PULL_IN_FRAME_2026-11-12.md`).
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 1612](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L1612)

## What is left above 10 degrees, in full

- **Finding:** Three places in the library still step more than 10 degrees on an arm segment in one frame. Hooks outside hand steps 19.3 and 18.6 at frame 41. Deflect high steps 11.5 and 12.4 at its contact frame 37, and 10.2 to 12.1 at frames 71 to 73.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** Not stated in the register.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 1721](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L1721)

## How wide the elbows sit with the ball at the chest

- **Finding:** With the ball at the chest, the most folded band sits 52.7 cm between the elbows, down from 62.9. The manual's 38.6 cm describes a snatch at contact, so no evidence covers a folded arm. The 52.7 figure is published and not aimed at.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** A coach should say whether 52.7 cm is right, and `elbowAngleDegrees` in the technique file is the dial.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 1735](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L1735)

## The cold-start seed set is four copies of one pose

- **Finding:** `seeds()` yields four candidates that differ only in `{side}_lowarm_twist`, which moves the elbow and wrist 0.000 cm. So the cold start cannot choose which side the elbow goes. Twenty seeds with humeral twist gave identical results, with worst step 12.4 in both.
- **Build:** Not recorded in the register.
- **Instrument:** `spikes/measure_seed_variety.py`, run by `pixi run seeds`
- **Owner:** Movement
- **Waits for:** Not stated in the register.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 1944](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L1944)

## The waiting hand's own history

- **Finding:** Before the correction, `netball_hooks_outside_hand` waited with its free arm at 0.927 to 0.999 of full extension, mean 0.979. After it, the contact elbow separation moved from 30.2 cm to 37.4, against the manual's 38.6.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** A coach may still rule that a facing-away wait belongs nearer full stretch, using the `ready` dial in the technique file.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 1982](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L1982)

## Two callers still measure the reach from the midpoint

- **Finding:** Two callers in `possession.py` place a point from the shoulder midpoint without `within_every_shoulder`, so a turned athlete could overshoot her reach. The fault is latent: all four releasing drills face forward within 0.1 degrees at release. No drill both turns and releases today.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** Not stated in the register.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 1998](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L1998)

## The mean elbow separation agreed with the manual by mixing two populations

- **Finding:** `ELBOW_POLE_ANGLE_DEGREES` matched the manual's 38.6 cm only as a library mean of 38.58 cm. Six two-handed drills averaged 36.57 cm and two one-handed drills averaged 44.60. With locked parameters pinned, the two groups remain about 21 cm apart.
- **Build:** Not recorded in the register.
- **Instrument:** `test_elbow_pole.py`
- **Owner:** Movement
- **Waits for:** Marius ruled to defer the angle retune until the coach-morning data, because it moves every drill.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 2025](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L2025)

## A free hand with no post-contact key would rest at the contact point

- **Finding:** `resting_point` in `possession.py` would rest the free hand at the contact point if a technique's only key is the contact offset. No drill trips this, because every technique with a free hand authors a chest key past contact. It is recorded and not guarded.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** Not stated in the register.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 2076](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L2076)

## The term named continuity is a pull toward the rest pose

- **Finding:** Setting the continuity target to the previous frame was measured and deferred. It moved 35 values by at most 2.3 degrees and flipped 0 verdicts. It does not fix the cold start: a control run left the knee at 34.1.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** The change belongs with a better cold start, and Marius's ruling holds the library's look until a second coach has seen it.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 2176](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L2176)

## The residual the cold-start test cannot see, and why it is excluded

- **Finding:** `test_cold_start.py` excludes `netball_hooks_jump_pull_in` because its hand target moves 2.15 cm, above the 1 cm rule. That hides a real drift of 5.65 degrees at the right knee over twelve frames.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** A discriminator that says how much of an opening's drift the target accounts for, which nobody has built.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 2235](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L2235)

## The second hand travels 14 cm out to meet the ball, and a coach must rule

- **Finding:** On the one-hand snatch the free hand goes from the chest out to 26.0 cm and back to 12.0 as the ball arrives. Erin Burger's note asks that the other hand not go away from centre. The movement is smooth, so the question is intent.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** A coach must rule, and any retune of the `join` and `gather` keys goes to Marius first.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 2316](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L2316)

## The ball speed for the whole library is one undocumented constant

- **Finding:** Every drill derives 600 cm/s from flights that `author_flight.DEFAULT_SPEED_CM` authored at 600 cm/s. The value has no coach, measurement or source, and nothing grades it. Its own comment says a game pass is faster.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** The coach morning answers whether 6.00 m/s is a drill feed and whether she returns the ball at its arrival pace.
- **Since then:** Spec 1 decision 12.9: the ball leaves at the speed the hands carry it into release, and the assigned speed goes in the same change. Main's release goal builds it. It is not on `main` at `b48512a`.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 2367](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L2367)

## The four contact hitches are one sub-frame timing defect

- **Finding:** The release frame falls 24 to 65 per cent of a frame after the declared release phase. On that frame the carry has stopped and the flight has not started, so the ball stalls. Predicting the step this way reproduces all four measurements to 0.000000 cm.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** A solve must measure the graded values before the flight is timed from the release key.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 2389](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L2389)

## The sub-frame defect is at the athlete's release only

- **Finding:** Contact and the incoming pass are clean on all eight drills, and only the athlete's release is affected, on four drills. The outgoing flight measures elapsed time from the release frame instead of the key. The incoming release key misses a frame by 11 to 85 per cent harmlessly.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** Not stated in the register.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 2420](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L2420)

## One drill has two solved poses 33 degrees apart

- **Finding:** `netball_hooks_outside_hand` reaches two solutions, with ready-stance shoulder turn 48.22 against 15.44 degrees. The composition of the enabled parameter set decides which one. Any change to that set can move the drill's look, and nothing would report it.
- **Build:** `ac240b2`
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** Not stated in the register.
- **Since then:** A flip now reports itself. `spikes/test_waiting_hand.py` pins each drill's ready-stance shoulder turn (the register, "A basin flip now reports itself, on one drill").
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 2651](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L2651)

## The wrist moves after the ball has gone, and could not drive it anyway

- **Finding:** The hand bends 22 to 35 degrees through every release, but each movement peaks after the ball has left. No property of the hand enters `return_velocity`, so the possession model cannot express a flick. The measure sees flexion and is nearly blind to pronation.
- **Build:** `02b25cd`
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** Not stated in the register.
- **Since then:** Spec 1 decision 12.6: the flick at release is mechanical (Marius, 8 September and 9 November 2026). Main's release goal builds it. It is not on `main` at `b48512a`.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 2683](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L2683)

## The pace has no author either

- **Finding:** The engine takes 2.24 times the athlete's time from contact to the deepest point of the hold, 0.7275 s against her median 0.325. The typed frame count sets the pace and carries no note anywhere. Five of the eight drills share 98 frames.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** Not stated in the register.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 2723](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L2723)

## The overhead pull-back has no boundary, and the checkpoint was right to go

- **Finding:** On `netball_overhead_pass`, the shoulder verdict alternates as the ball moves back: it fails at 24.8 cm and passes again at 26.4. At 7.76 cm a leg joint moves 17.50 cm while the graded shoulder measure moves 0.00. The graded knee never changes verdict, but `test_no_even_drill_solves_more_crookedly_than_it_did` goes red from 6.15 cm.
- **Build:** `32663a9`, `1da8843`
- **Instrument:** `test_no_even_drill_solves_more_crookedly_than_it_did`
- **Owner:** Movement
- **Waits for:** Not stated in the register.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 2826](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L2826)

## The release seam and the frame-81 stall are one defect

- **Finding:** The shipped ease-out starts at full speed, so hand speed multiplies by 10.2 and 7.4 at release, causing both hitches. No easing wins across the library: the overhead stays over the 3.0 threshold under all three. The window also closes early on four drills, freezing `deflect_high` for 11 exported frames.
- **Build:** `2169157`, `eaecbb2`
- **Instrument:** `spike_report`'s `worstNeighbourRatio`
- **Owner:** Movement
- **Waits for:** The easing needs a ruling, and the library table is what that ruling needs.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 3034](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L3034)

## Three solvable balls are invisible to the library, and they support the claim

- **Finding:** `netball_two_hand_snatch_pull_in` has four balls that all solve, but three reach neither the library nor a clip. Forty-three of forty-four readings are within band, and the low ball misses its contact shoulder floor of 50.0 at 49.95. The `wide` ball turns her 45.97 degrees, and nothing grades a turn.
- **Build:** `2215713`
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** Erin rules on the low-ball shoulder floor, and Marius answers the clip contract question before any variant clip is exported.
- **Since then:** Marius chose option A for ball variants in clips on 12 November 2026 (spec 3, decision 12.8). The contract on `main` at `b48512a` still writes `variant` as null.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 3330](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L3330)

## The engine solved where the ball goes and threw the answer away

- **Finding:** Six of the ten drills return the ball, including four that read as catches. `netball_overhead_pass` throws its ball downward at 39.4 cm/s, releasing at 180.4 cm toward a target at 126.32. At the manual's 7.00 m, the overhead pass peaks at 321.4 cm, over a 305 cm goalpost.
- **Build:** `763cabd`
- **Instrument:** `apex()` and `solve_launch`
- **Owner:** Movement
- **Waits for:** Not stated in the register.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 3474](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L3474)

## The Blender job anchored the ball to a landmark it did not transmit

- **Finding:** The two rigs' rest poses differ, leaving a 0.059-torso gap of about 2.5 cm fore-and-aft on the consumer's rig. Nothing here can separate a landmark convention from a posture difference, because that rig has no `root` bone. No figure should claim accuracy better than 2.5 cm fore-and-aft.
- **Build:** `cc2c20a`
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** A landmark comparison closes it, as a separate piece of work.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 3609](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L3609)

## A one-handed release is far less determined than a two-handed one

- **Finding:** Sweeping the release carry's `up` on `netball_one_hand_high_pass` gives 4 pose jumps over 5 cm, the largest 21.87 cm. The two-handed passes give 1 or 2 jumps, the largest 7.50 cm. Its continuous region for `ahead` runs only from 0.80 to 1.12.
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** The movement lane tests the hypothesis and decides on an additional constraint for one-handed techniques, after a ruling.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 3747](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L3747)

## The lower body has no stable solution

- **Finding:** Between the configurations of `716b3eb` and `ac240b2`, six of the nine drills flipped their pelvis line, with a worst move of 61.45 degrees. Fifteen of the sixteen below-the-hips checkpoints move between the two solutions, by up to 20.65 degrees. No verdict flips, but the figures shown to Erin come from whichever solution the build reached.
- **Build:** `a775502`, reconstructing the configurations of `716b3eb` and `ac240b2`
- **Instrument:** Not recorded in the register.
- **Owner:** Movement
- **Waits for:** Engine work on why the lower body is under-determined, which needs a ruling first.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 3840](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L3840)

## Every square drill solves with one knee more bent than the other

- **Finding:** Six square drills solve with one knee more bent than the other, by 4.02 to 6.48 degrees on the shipped build. A hip step planted on `two_hand_catch_chest` in increments of 0.01 makes the knee gap oscillate between 1.80 and 7.05 rather than rise. `MotionTrack.is_symmetric()` read only the hands and published `double_foot_landing` as `symmetric: true`.
- **Build:** `32663a9`
- **Instrument:** `test_an_even_drill_solves_evenly` and `test_no_even_drill_solves_more_crookedly_than_it_did`
- **Owner:** Movement
- **Waits for:** It closes when the solver answers evenly, which turns the expected failure red so someone records what changed.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 3984](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L3984)

### Moved out of this register

- A per-hand ready offset is a design candidate, not a gap: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- The environment must be activated, not merely located: an engineering rule: refer to `docs/ENGINEERING_RULES.md`.
- The record of the four, as it was diagnosed: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- RESOLVED: a field called secondsPerFrame held the solver's cost: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- A comment is not a test: an engineering rule: refer to `docs/ENGINEERING_RULES.md`.
- RESOLVED: the free arm started 46 degrees off and snapped through at frame 41: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- The record of it: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- RESOLVED: the pole's frame is now orthonormal: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- The record of it: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- The dial was wired to a term that could not honour it: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- RESOLVED: the snap check now sees a stall, and does not see a turn: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- The record of it: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- RESOLVED: the cold start resolved the leg's redundancy differently: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- The record of it: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- RESOLVED: the receiving hand no longer grips before it arrives: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- A retired lead: the 29.6-degree grip angle was three errors: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- RESOLVED: an archive of a graded build now has to be made on purpose: a rule, now spec 1 requirement RCP-6. Its text is in this file [at b48512a, line 2343](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L2343).
- Five figures in this file were stale, and the artefact beside them was not: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- CLOSED: the right hand now opens the way the left one does: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- The docs-wide stale-figure sweep, and what it could not reach: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- The joint limits were exceeded on a parameter the model had locked: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- A basin flip now reports itself, on one drill: a rule, now spec 1 requirement SOL-9. Its text is in this file [at b48512a, line 2743](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L2743).
- The root winding is not a defect, and the guard proposed for it would be wrong: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- CLOSED: a drill that starts with the ball must declare arrival at 0.02: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- The alignment ranked a sync clap above every real catch: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- A consumer nothing executes is a consumer nobody has checked: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- A ledger without its reading step nearly cost a real pairing: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- Two pairings, and neither could be re-derived from the tree: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.

# Video and footage

## The section cutter and its posters

- **Finding:** Two posters the page already ships are poor coaching stills. `release-rep09` at front index 619 smears the ball and both hands with motion blur. `ready-between` at front index 560 shows no arm span in a section named "the arm-span ready".
- **Build:** Not recorded in the register.
- **Instrument:** Not recorded in the register.
- **Owner:** Video and footage
- **Waits for:** Marius decides whether to move either poster, which costs one number in `PAIR1_SECTIONS` and a re-pin of two digests.
- **Full record:** [docs/KNOWN_ISSUES.md at b48512a, line 4723](https://github.com/Braven-Performance-Lab/braven-movement/blob/b48512a61aee700bb6cd3b3be94d097acf31aef2/docs/KNOWN_ISSUES.md#L4723)

### Moved out of this register

- The anchor sheets: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
- The hand at release: closed: refer to `docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`.
