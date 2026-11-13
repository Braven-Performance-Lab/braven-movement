# Known issues: closed sections, 12 November 2026

Copied unchanged from `docs/KNOWN_ISSUES.md` at `b48512a`. Each section here is
fixed, withdrawn, superseded or retired. The open findings are in
`docs/KNOWN_ISSUES.md`, and the plan that split the register is
`docs/KNOWN_ISSUES_SPLIT_PLAN.md`.

# Rendering and modelling

## `netball_one_hand_high_pass` cannot be posed at its ready phase

**Status: DRAWN since `a484302` (12 Nov 2026) by option C below; the grip
itself is open with the coach.** The renderer no longer raises: where
`axis_complaint` refutes the named axis, `applied_flexion_axis` applies the
limit about the axis that turned. The other eleven drills are identical in
every bone. Everything below the status line was measured on `4a54964` and
earlier, before option C. The grip question is in
`docs/FINDING_HIGH_PASS_READY_GRIP.md`, and the 110.9 degree reading below was
taken on the hand posed about the rejected axis: on the drawn hand it is 27.7.

    FLEXION_AXIS: r index is set to flex about axis 0, which carries only 0.44
    of the turn: x=18.5 y=-7.2 z=42.2 degrees.

The right index knuckle turns 42.2 degrees about z while the limits are applied
to x. The drill is therefore ABSENT from the `2413f9d` library; its `lift` and
`release` phases pose and pass.

It is not caused by the girdle change. Posing the phase with the shift ZEROED
raises the identical error with identical numbers, and a zero shift leaves this
rig at its own rest girdle. Do NOT try it by removing the field: a missing field
is refused before the hands are posed, so the run stops with the refusal
instead.

MEASURED 2026-09-07, `docs/FLEXION_AXIS_PAPER.md`. Across all twelve drills,
216 asserted knuckle readings: 208 of 208 on the eleven that pose already turn
about the axis the guard names, and the only four that do not are this hand of
this phase. The axis is not carried by the job, which never says which component
is flexion; it is a constant in `blender_mpfb_reference_catch.py:437` whose own
comment says nothing checked it.

The cause is measured and separates cleanly. The flexion turns the finger toward
the BALL, so the ball's position relative to the hand decides which axis carries
it. Every gripping phase of the eleven puts the ball 41.8 to 46.6 degrees off
the finger line; this hold puts it 110.9 degrees off, more than a right angle
BEHIND where the fingers point. No overlap.

The paper carries the options and rules on none. It also records a fourth
possibility the brief did not list: the POSE may be the defect rather than the
axis, because a grip 65 degrees outside the range every other hold occupies may
be a target this rig cannot honestly hold. That is the movement lane's grip.

## One failing phase aborted the whole library render

**Status: FIXED 2026-09-07. Owner: the rendering lane.**

`render_job` raised out of the whole run when any one phase raised, so eleven
good drills were lost to one bad one and the library cost a second full render.

The loop now records the failure and carries on. Proven on a run of
`netball_one_hand_high_pass` followed by `netball_chest_pass`: the `ready` phase
failed with its reason on the console, `lift` and `release` rendered, the
drill's receipt named the failure in `failedPhases` with the error text, THE
LATER DRILL RENDERED IN FULL, and the process exited 1 with a line naming every
phase it could not pose.

THE EXIT CODE STAYS HONEST. A loop that carried on quietly would have traded a
loud failure for a silent one, which is the fault `render_receipt.py` exists to
prevent. `render_outcome` gained a third outcome, `SOME PHASES FAILED`, which
outranks both PASS and NOTHING RENDERED, and `main` raises AFTER every drill so
the exit code costs no later drill.

AND THE FIX CREATED A PATH ITS READERS HAD NEVER SEEN. Before it, a failing
drill produced NO receipt: the run died and the stale one had already been
unlinked, so no reader could be misled. Writing a receipt for a partly-drawn
drill made one possible, and `export_manual_page.py` took it: run on the
partial receipt it built a two-figure page for a three-phase drill, exited 0 and
said nothing. `archive_receipts.py` had the same gap by reading, because a
partial receipt carries the same build stamp as a whole one and the stamp check
cannot see the hole.

Both now refuse a receipt with a non-empty `failedPhases` unless
`--allow-partial` is passed, through one shared rule in `render_receipt.py`.
With the flag the page gives each undrawn phase a VISIBLE slot naming its
reason, because permitting an omission is not the same as hiding it.

THE ANIMATION BRANCH ANSWERS THE OPPOSITE WAY. A still with a hole is one
missing figure; an animation with a hole plays over the gap and says nothing,
because the frames either side close across it. A failed frame is recorded and
the EXPORT IS REFUSED, and the receipt is still written.


## The ball is anchored to a landmark the job does not transmit

EVERY NUMBER IN THIS ENTRY was measured on 2026-09-04 against the `aa3f244`
job export in `spikes/poc-output`, with the renderer at `2015424` and the rig
from `load_reference_catch_config`. The engine's figures are the movement
lane's, reported the same day from the solved pose. This attribution is here
because `scripts/docs_number_audit.py` found the first version of this entry
quoting 42.7681 and 0.2648 with NO BUILD NAMED, which is the fault the audit
exists to find.

`pose_phase` places the ball at `shoulders + fromShouldersInArms * arm`. Every
term on that line comes from the job except `shoulders`, which this rig
supplies itself. The ball's position error is therefore the shoulder midpoint's
error, one for one, with nothing to attenuate it.

The movement renderer never poses a clavicle. Measured on 2026-09-04, this rig
holds its shoulder midpoint 42.7681 cm above the pelvis on all 43 graded phases
of all 10 drills, with a range of 0.0000 cm. The engine's midpoint moves on
every drill. Against a one-centimetre rule, 15 of the 43 figures pass and 28
fail. 19 of the failures are HELD phases, where the ball is in her hands and a
coach reads a cue from it. Every one of the 10 drills has at least one failing
phase. The worst is `overhead_pass/lift` at 8.451 cm, which is 77 percent of
the ball's radius.

MEASURE ALL THREE AXES. The first version of this entry reported 7.41 cm at
`overhead_pass/lift` from a vertical-only column and understated the error by a
whole tolerance. The true figure is 8.451 cm, because the midpoint also travels
4.08 cm fore-and-aft. `bounce_pass` is the sharper case: its vertical barely
changes, so a vertical-only column would have called it the cleanest drill in
the library, and it is not.

A width instrument is worse still. A symmetric change of shoulder width does
not move the midpoint at all, and `hooks_outside_hand` is the only drill with a
real across-body component, 1.776 cm at `facing_away`, because she is turned.

The three phases that pass exactly are the neutral-girdle phases. That is the
evidence that this rig is calibrated to the engine's rest pose, because a wrong
calibration point would put the passes somewhere else.

`bounce_pass` has five graded phases in the engine and NO JOB FILE in
`spikes/poc-output`. This lane cannot render it. A drill the renderer never
sees is not a passing drill.

THE FIX MUST BE TRANSMITTED IN THE JOB'S OWN UNITS. `arms.reachFraction`,
`ball.fromShouldersInArms` and `grip.wristFromSurfaceInArms` are all in arm
lengths, and `ball.radiusM` is the only absolute length in the file, because a
real netball is one physical size on every body. A shoulder position has the
opposite property. Shoulder positions sent in metres would place this rig's
ball about 6 cm too high on every frame, including the 15 that pass today.
Send them relative to the pelvis, in arm lengths.

SEND THE DISPLACEMENT, NOT THE POSITION. Transmitting the shoulder POSITION
does not work across these two bodies, even normalised. Resolving the engine's
positions onto this rig at 42.7689 / 49.6456 puts ZERO of the 48 phases under
the one-centimetre rule, with a smallest error of 1.108 cm. `chest_pass/ready`
reads 2.488 cm, and that is a phase where both bodies are at their neutral
girdle and nothing is wrong at all. An instrument that reports an error where
there is none is measuring something else.

It is measuring a constant. This rig's shoulders sit 0.2648 cm BEHIND its
pelvis and the engine's sit 2.4622 cm AHEAD of its own, which is 2.386 cm after
scaling. A divisor scales and it does not translate, so no scalar can remove a
difference in where MHR's `root` sits against MPFB's `pelvis`, or a difference
in neutral posture. Nobody can currently separate those two causes: this rig
has no `root` bone and the movement lane has no MPFB rig.

So the field carries `(position at the frame - that body's REST-POSE shoulder
position) / restTorso`, and each side applies the displacement to its own rest
pose. The reference is the rest pose and not a drill's neutral phase, because
the rest pose is the only reference both sides compute without being told. Every
constant cancels, a neutral phase reads exactly zero, and the quantity
transmitted is the one that is actually missing, which is that this rig's
girdle does not move.

`girdle_agreement.py` holds the consumer guard. It refuses a frame whose
transmitted positions are absent, because a frame nobody can check must not
read the same as a frame that passed. On this rig the clavicle tail and the
upper-arm bone head are the same point to 0.000000 mm, so the bone head is this
rig's own shoulder joint rather than an offset from it.

Do not add a scapula motion to the renderer to close this. A pose that no solve
produced must not reach a figure.

# Movement

## Centimetres are stored in a field called degrees

### Three defects under that one sentence, fixed 2026-09-07

**ONE. The coach was told the wrong unit.** Above. A measure now names its own
unit through `MEASURE_UNITS`, and a measure with no declared unit gets NO unit
word rather than a wrong one.

**TWO. A five-degree threshold was spent on a centimetre band.**
`MINIMUM_MEANINGFUL_BAND_DEGREES` guarded every checkpoint's width and every
phase-separation verdict, whatever the measure was in. A length had to move
three times as far as the evidence requires before a phase counted as distinct.

**THREE. The widest-moving checkpoint of a phase was chosen across units.**
`separation` maximised raw values, so a phase grading a length and an angle
together picked whichever number was larger, which is not a question with an
answer. **Real in the code and INERT in the library**, and the reading names
its path and its frames because a first reviewer read a different path. Taken
on the POSSESSION path, which `build_library` uses for this drill: the only
mixed phases are `netball_double_foot_landing`'s, graded at frames 54, 89 and
109 of 110. Across those three transitions `footHeightGapCm` moves 0.01, 0.00
and 0.01 cm while the angles move 1.92, 0.13 and 25.07, so the raw maximum
picked the angle every time. The gap's largest value anywhere in the clip is
1.22 cm at frame 30, which no phase grades. Fixed anyway, because a
defect that today's numbers happen to hide is still a defect, and the numbers
that hide it belong to the library rather than to the code. The winner
is now chosen in units of each measure's own floor, which asks how many
meaningful steps it moved and is unit-free.

### Four more sites — all four fixed on 2026-09-07, the fourth twice

**They are kept here rather than deleted**, because the row's value is the
shape: four places where one unit's threshold or one unit's silence was spent
on measures of two units, all latent, all in code that had been read many
times. What each was is below; what each is now:

- **`build_library.py:222`** writes `thresholdsByUnit`, the whole table, and
  every phase row carries the `threshold` and `unit` actually applied to it. A
  reader no longer has to know a measure's unit to check its verdict.
- **`build_library.py:338-343`** prints the phase's own threshold and unit.
- **`build_library.py:367`** filters each spread against its own measure's
  floor, and the heading says "each in its own unit" rather than "in degrees".
  **THE FIRST FIX OF THIS ONE WAS INERT AND THE REVIEW CAUGHT IT.** `readings`
  is keyed `"{phase}/{measure}"`, and the whole key went to the lookup, which
  cannot resolve it and answers with the UNDECLARED case: the strictest floor,
  5.0, and no unit. Every reading was therefore still held to 5 degrees while
  the new heading claimed each was held to its own — **a worse statement than
  the "in degrees" it replaced**, because the old one was at least true of what
  the code did. The measure is split out of the key now.

  Two things made it silent, and both are worth naming. `minimum_meaningful_band`
  CATCHES the `KeyError` that `unit_of` raises for an undeclared measure, so a
  caller passing something that is not a measure gets a plausible number
  instead of an error; that tolerance exists for hand-built test checkpoints
  with abstract names. And the filter was inline in `main`, which needs a
  solver and a built library, so **reverting the line failed no test at all**.
  It is a named function now and the guard drives it, not the helper.
- **`MovementAssessment.to_receipt`** writes `unit` beside `band`. **Additive**:
  `band` is unchanged, so a consumer taking `tuple(row["band"])` is unaffected,
  and two tests do exactly that.

**The consumers were checked before the schema moved**, and the conclusion
held while the list behind it did not. `thresholdDegrees` was read by nothing
outside the writer, so the rename is safe. `band` is read as a pair, so the
unit is a sibling key and not a change to the pair — **but the list of readers
this lane gave was wrong in both directions.** `test_hand_orientation` reads
whether the band is `None`, not the pair; and `build_library.py:378` reads
`band[0]` and `band[1]` in PRODUCTION and was not listed at all. A production
reader missing from a consumer list is the more serious half, and the search
that found the other writers should have found it.

### Two more `band` writers — BOTH FIXED on 2026-09-07

Kept rather than deleted, because the pair is the point: they were found by one
search and they are **two different faults**, not one repeated. What each was
is below; what each is now:

- **`export_manual_page.py`** formats the band in Python and passes a label.
  `manual_page_template.html` prints it. **The template rendered
  `${m.band[0]}-${m.band[1]}&deg;` with a hardcoded degree sign**, so a
  centimetre band read as degrees on a page a COACH looks at — the same defect
  as the coach sentence, in the other coach-facing surface. A template cannot
  look a unit up and is no longer asked to; a measure with no declared unit
  gets the numbers and no unit rather than a guessed one.
- **`hand_orientation.py`'s six measures are declared**, all degrees. They stay
  REPORTED and ungraded, and a guard holds them to that, so the declaration
  cannot be read as a licence to band them: bands are coaching content and no
  coach has seen these numbers.

**The gap was invisible for a nameable reason, and there is a guard on it.**
All six names end in "Degrees" and all six ARE degrees, so a reader applying
the suffix rule would have been right and the table would still have been
silent. `unit_of` refuses that rule on purpose, and a test asserts it still
refuses.

**AND MY OWN GUARD REACHED TWO WRITERS OF THREE.** `test_written_measures` was
written to stand at the writing end of the pipe. It covers the two SOLVERS'
measurement rows; `hand_orientation` is a third writer and it never saw it.
`test_manual_units` now covers that writer, deriving the six names from
`CONVENTIONS` rather than listing them.

*The original row follows.*

**Owner: the movement lane. Queued.** Neither is the receipt, so neither was in
that pack's scope, and they are two different faults rather than one repeated.

- **`export_manual_page.py:102`** writes `{"measure", "band": [min, max]}` —
  the same bare pair the receipt had, and this one is COACH-FACING. It is the
  larger of the two for that reason.
- **`hand_orientation.py:235`** writes `"band": None` with a `REPORTED`
  verdict, so there is no band to carry a unit and it is NOT the band fault.
  Its fault is the declaration gap in a third writer: its six measures —
  `leftFingerUpDegrees`, `leftThumbToBallDegrees`, `leftThumbUpDegrees` and
  the three right-hand names — are **none of them in `MEASURE_UNITS`**, so
  `unit_of` raises for every one. They end in "Degrees", which is exactly the
  suffix rule `unit_of` refuses to apply, and `test_written_measures` does not
  reach them because it covers the two solvers' measurement rows and this is a
  reporter.

*The original row follows.*

**Owner: the movement lane. Queued after Pack B, the height measure.**

All four are recorded rather than changed, because this pack was scoped to the
three defects above and none of these is live today. An earlier version of this
section listed two and gave no owner; a reviewer found the other two in the
same file.

- **`build_library.py:222`** writes `"thresholdDegrees":
  MINIMUM_MEANINGFUL_BAND_DEGREES` into every receipt's `phaseSeparation`. A
  centimetre winner is now judged at 2.0, so the receipt's own field
  misdescribes the threshold that was applied.
- **`build_library.py:341-342`** prints "cannot fail ... under the 5
  threshold" for whichever measure won a phase, in any unit.
- **`build_library.py:367`** filters what a variant changes with
  `MINIMUM_MEANINGFUL_BAND_DEGREES` and prints the survivors under a heading
  reading "in degrees". A variant drill grading a length would have its
  centimetre spread judged by a degrees threshold and printed as degrees.
- **`MovementAssessment.to_receipt`** writes `band` as a bare pair of numbers
  with no unit, so a receipt consumer has exactly the problem the feedback
  sentence had. Latent until something outside this repository reads it.

**Why all four are latent**: the landing is the only drill grading a length,
and its winner is an ANGLE in every phase on both solve paths, so no centimetre
value reaches any of these three prints today. The fourth waits on a consumer
outside this repository.

## A per-hand ready offset is a design candidate, not a gap

`BallOffset` is a point, and `ready` in a technique file uses it. Both hands
are then placed around that point by the grip spread, so an `across` of 0.3
means the point sits to her left rather than that each hand sits out to its
own side. Two hands reaching for an off-centre point carry the far one across
the body, which is what put a hand across the face on
`netball_deflect_high`.

That drill is corrected by putting its point on the midline, which is what its
own cue describes. The type is documented in `ball_track.py` rather than
widened.

**A per-hand form is deliberately not built.** One drill authors a ready
offset today, and a field invented for a need nobody has yet is a field that
ends up meaning nothing. Build it when a second drill needs a genuinely
asymmetric wait, and not before.

The trap for the next author: the motion track's `across` IS per hand, and
this one reads the same and is not.

## The record of the four, as it was diagnosed

The engine sends a released ball back to the passer at the speed it came in,
so the athlete now extends through the pass. She did not before: the ball
drifted out of her hands at 0.13 to 0.57 m/s and her arms stayed folded. At
the last frame the hand now reaches 0.93 to 0.95 of full extension, where it
used to sit at 0.70 to 0.75.

The same checkpoint fails on all four releasing drills:

| drill | phase | leftElbowFlexionDegrees | band | as first written |
|---|---|---|---|---|
| Deflects, High | send_on | 35.83 | 45 to 115 | 35.73 |
| Hooks, Jump and Pull In Ball | release | 49.85 | 50 to 120 | 49.98 |
| 2 Hands Catch | release | 41.04 | 55 to 115 | 41.05 |
| 2 Hand Snatches and Straight Back | return | 41.00 | 45 to 105 | 40.81 |

**The last column is what this table said until 2026-09-01, and every row of
it was stale.** The verdicts never changed and the point of the entry is
untouched: the same checkpoint still fails on all four. The figures are
corrected against two instruments that agree, the clip verifier and a direct
solve, and the old ones are kept beside them rather than deleted.

**Nothing is tuned, in either direction.** Rewidening a band to make the engine
pass is the engine marking its own homework. Shortening the follow-through to
fit the band is the same act in reverse. Both were available and both were
refused.

**What the evidence says.** Every one of these bands is marked in its own file
as authored by this project and PROVISIONAL until a coach sets it. The cue
beside the deflect band is the manual's own words: "Extend through the ball as
it goes." The engine now does that and the provisional number says it should
not. The bands were also authored against a solve in which the arm never
extended at all, so they have never been tested against a real follow-through.

`Hooks, Jump and Pull In Ball` misses by 0.02 degrees, which is worth stating
plainly: on that drill the disagreement is not a disagreement.

This is exactly the question the coach review exists to settle, so it goes to
the morning rather than to a commit.

## RESOLVED: a field called secondsPerFrame held the solver's cost

Renamed to `solveSecondsPerFrame` on 2026-09-02. The entry is kept because the
sizes no longer separate the two quantities and the reason for the name does.

`possession_solve.py` put the SOLVE time per frame in a result field named
`secondsPerFrame`. The animation timestep is 1 over the motion track's own
frame rate, which for this library is 60. Nothing in the name said which one it
held.

**THE FACTOR OF TWO IS GONE, AND THAT MAKES IT WORSE.** This entry used to say
the two "differ by more than a factor of two". Measured again on `92fcb4d` the
ratio is **1.19** — the solve got faster — so the two numbers now look alike
and a reader cannot tell them apart by eye at all.

This cost real work. A release velocity was reported from that field, then
"corrected" to figures that were too high by 2.2 times, then corrected back.
The wrong numbers were written into this file before they were caught.

`build_library.py` reads the same field and prints it as "ms/frame", which is
correct for what it holds and is where the meaning is visible.

**WHAT GUARDS IT NOW, since the sizes cannot.** One is a measurement of the
MACHINE and the other is a property of the FILE. The cost changes between two
solves of the same drill; the timestep cannot. `test_return_pass.py` asserts
exactly that, so the guard holds on any machine at any speed, and it asserts
the old name is absent from the result so it cannot quietly return.

This is the same shape as the entry above about centimetres in a field called
degrees.

## RESOLVED: the free arm started 46 degrees off and snapped through at frame 41

**Closed by the free-hand fix in `c3aa388`.** Measured on that tip, the left
upper arm's worst single-frame turn on this drill is 3.50 degrees, at frame 59.
At frame 41 it is 0.12 degrees and the forearm is 0.49. The numbers below are
kept because they are the record of the fault, not because they still hold.

The entry itself explains why it closed, in its own last paragraph: the free
hand's only positional target before contact was `waiting`, and `waiting` is
exactly what that fix changed. Nobody noticed at the time, because the pack
measured the free hand's POSITION and never its arm's frame-to-frame turn.

**One sentence of it was also wrong about the mechanism**, and that is
corrected in place below. The largest step on this drill is now the RIGHT upper
arm at 11.32 degrees at frame 45, so the "largest step left anywhere in the
library" claim no longer holds either.

## The record of it

`netball_hooks_outside_hand`, frame 41, left arm, 19.3 degrees on the upper and
18.6 on the forearm between two frames while the wrist moves 1.15 cm. It is the
largest step left anywhere in the library.

**The cause is the first frame, not frame 41.** The free arm's elbow angle about
the shoulder-to-wrist axis, against the 34.6 degrees the pole asks for:

| frame | 0 | 10 | 20 | 30 | 40 | **41** | 42 | 50 | 60 | 95 |
|---|---|---|---|---|---|---|---|---|---|---|
| angle | 81 | 84 | 84 | 72 | 66 | **12** | −13 | 20 | 28 | 30 |

It starts 46 degrees away and every one of the 41 frames before the snap sits
more than 20 degrees off. Then it crosses the whole gap in one frame,
overshoots, and settles at 28 to 30 for the remaining 57 frames. The catching
arm starts at 27.2 and stays between 27 and 30 throughout.

Before contact the free hand's only positional target is `waiting`, which
barely constrains the elbow's rotation about the reach axis. So the first
solve leaves the elbow almost straight out to her side, EACH FRAME'S SEED
carries that faithfully into the next, and the pole wins abruptly rather than
gradually.

That sentence said "the continuity term carries that faithfully". It does not
and cannot: it has no target set, so it pulls toward the rest pose. What
carries a pose from one frame to the next here is the seed.

The trunk goes with it. The shoulder line jerks −2.26 degrees at that frame
against a steady +0.85 either side, and this drill has no authored turn at all,
so that rotation is entirely emergent.

**This is a snap-through, not a mode flip:** a term that is correct, opposed by
the seed's inertia, winning all at once. The fix belongs at frame 0. That
sentence said "opposed by continuity", which named a term that pulls toward
rest and cannot oppose anything frame by frame.

**An earlier version of this entry was wrong** and said the pole pack reduced a
21.7 degree flip at frame 47 to 19.3. The frame-47 flip has gone: it is now
under 8 degrees. The 19.3 is a different event at a different frame, and the
two were conflated by reading a per-drill worst without asking where it was.

## RESOLVED: the pole's frame is now orthonormal

**Fixed by Gram-Schmidt.** `down` is kept and `out` is orthogonalised against
it, not the other way round, because `down` is where the angle is measured
FROM: orthogonalising `down` instead would silently redefine what zero means.

Swept over 576 reach directions, calling the solver's own `pole_target` rather
than a copy of it, the deviation from the elbow circle is **0.000000 cm**,
including on the family where the raw `out . down` reaches 0.991. Before, the
worst was 12.30 cm and the median 4.02.

**The feared consequence did not happen, and that is the finding.** This entry
said the angle would have to be re-read and every table depending on it
regenerated. The two-handed calibration mean moves from **36.58** to **36.43
cm**, which is inside the 0.5 cm the test records, so
`ELBOW_POLE_ANGLE_DEGREES` needs no re-read at all. One item leaves the coach
conversation rather than joining it.

Read that twice before taking it as good news. The angle was bisected through
the whole SOLVE rather than derived from the geometry, so it had already
absorbed the basis error. A calibration robust to a 12.30 cm geometry fault is
robust because it is loosely coupled to the geometry, which is not entirely a
compliment.

**What it does move**: 54 graded values, no verdicts flipped, worst
`hooks_outside_hand` facing_away left knee 51.13 to 35.40 and its pull_in trunk
lean 1.90 to 12.05. Those are a different pose rather than a defect: measured
across that drill the trunk lean's worst single-frame step is 0.12 degrees and
the knee's 0.33, both flat throughout. It is still a change to the library's
look and goes to Marius as one.

**And the largest move on that drill is not graded at all.** The RIGHT knee at
contact goes 50.3 to 74.2 degrees, about 24, and it is not a checkpoint on
`netball_hooks_outside_hand`, so no graded figure carries it. It is smoother
than before rather than rougher — its worst single-frame step falls from 2.03
degrees to 0.15, and it holds 72.9 to 75.0 across the whole drill. The look
record should carry the whole body, not only the parts a checkpoint happens to
name.

**On the hand-orientation rows**: 105 is the count above 0.05 degrees. At the
precision the receipts are written to, 177 rows move. Both are the same change
read at two thresholds, and the larger one is the honest headline.

**A reach in her coronal plane now correctly gets NO pole.** There `out` and
`down` collapse onto the same line once the reach axis is removed, so there is
no circle point to name and `pole_target` returns None. The skewed basis
emitted a point anyway. Verified directly rather than by sweep: six coronal
directions all return None, and one two hundredths off the plane still returns
a point, so it is the plane and not a region. A grid sweep MAY MISS IT ENTIRELY, and
whether it does depends on the grid: this lane's sampled at half-step offsets
and stepped over the plane, finding 0 of 576, while the reviewer's landed on it
and found 48 of 576. Neither count is a property of the code. Both are
properties of a grid, which is why the direct test is the one to trust.

`pole_target` now lives outside `elbow_poles` so the guard calls the same code
the solver calls. The measurement that first found the 12.30 cm reimplemented
the basis in a script, which is a second copy of the thing under test.

The guard lost a clause from its name. It was
`test_the_target_is_on_the_elbow_circle_where_the_basis_is_orthogonal`, and its
reaches ran along one axis, where `out . down` is exactly zero and the flaw
vanishes. Its directions are now deliberately oblique, and a second test
asserts they are — otherwise a later edit could make them axis-aligned again
and the guard would pass for the old reason.

## The record of it

`elbow_poles` builds its frame by projecting `out` and `down` off the reach
axis. It never orthogonalises them against each other. On a reach that is
oblique to both they are not perpendicular, `down * cos + out * sin` is not a
unit vector, and the target leaves the circle the elbow can occupy.

Measured over a spread of reach directions, worst deviation **10.2 cm**, where
the hand sits nearly below the shoulder and `out . down` reaches −0.963. On
that family the point target does argue with the reach — the one thing the
angle form was chosen to avoid.

**The calibration survives and the stated property does not.** 34.6 degrees was
bisected through the whole solve, not derived from the geometry, so it already
absorbs whatever the basis does. Every gate is green with the basis as it is.
What was wrong is the claim in the comment and the name of the test.

The guard exercises reaches along one axis, where `out . down` is exactly zero,
so it tests the family the defect cannot reach. It is left that way on purpose:
widening it turns the branch red for a defect whose fix moves figures.

**Filed as follow-up, after the render window:** an orthonormal basis by
Gram-Schmidt, then re-read the angle, then regenerate every table that depends
on it. It is not urgent, because nothing measured is wrong. It is not optional,
because the code claims a property it does not have.

## The dial was wired to a term that could not honour it

`elbowWidth` was a technique property, named for the case where a chest catch
folds the elbows where a snatch spreads them. It scaled the aim vector in
`upper_arm_aim`.

Sweeping that term's weight from 2.0 down to 0.0 moved folded elbow separation
by **0.2 cm**, from 65.4 to 65.6. So a coach could have set that dial to
anything and the athlete's elbows would not have moved.

No technique file ever authored it, which is the only reason no harm was done.
Had a coach been asked for a number at the review morning, the number would
have been recorded, honoured in the file, and ignored by the engine.

It is now `elbowAngleDegrees` on the elbow pole, which does control separation,
and it is in degrees rather than in multiples of nothing.

**The general shape, worth more than the instance:** a dial is not connected to
what its name says until something measures the connection. Before asking a
coach for any number, sweep the parameter it will feed and confirm the athlete
moves.

## RESOLVED: the snap check now sees a stall, and does not see a turn

**The instrument is rebuilt and lives in `snap_report.py`**, stdlib only, so a
test of it runs wherever the tests run. It used to sit in `possession_solve.py`
behind a solver import, which is why an instrument this wrong went this long
with no test at all.

Three faults, two recorded here before and one found while fixing them:

- **It divided by the MEAN of two neighbours**, breakdown point zero. Now the
  MEDIAN over three steps either side, excluding the frame itself.
- **It could not see a stall.** Its skip-gate exempted any frame whose
  neighbours were under 0.2 degrees, which is a snap out of stillness, and its
  significance gate required the STEP to be large, which a stall never is. The
  ratio is now symmetric and a frame is judged when EITHER its step or its
  neighbourhood is meaningful.
- **A stall test with no further condition flags every TURNING POINT.** An
  angle that reverses has a step through zero at the reversal. The first
  version of the fix scored 32.75 on `netball_double_foot_landing` for an elbow
  that simply stopped folding and began to open. The discriminator is the SIGN
  of the steps either side, and at an edge the one neighbour that exists
  decides — a version that returned "same direction" wherever a neighbour was
  missing reported the jump hooks' last-frame reversal as a stall of 7.74.

**`SNAP_RATIO` stays at 3.0 and was NOT recalibrated.** The entry said to
recalibrate once the denominator was robust. Having made it robust, the honest
reading is that 3.0 separates real hitches from ordinary movement, which is
what a threshold is for. Moving it to make today's library pass would be tuning
the threshold to the answer.

**So four rows now read over threshold, and they are findings rather than a
broken build.** Nothing in the test suite gates on `SNAP_RATIO`; `proof.py` and
`retarget.py` are reports.

| drill | ratio | kind | where |
|---|---|---|---|
| `two_hand_snatch_straight_back` | 9.42 | stall | right elbow, frame 88 |
| `two_hand_catch_chest` | 8.52 | stall | left elbow, frame 90 |
| `deflect_high` | 7.72 | stall | left elbow, frame 70 |
| `hooks_jump_pull_in` | 3.30 | stall | right elbow, frame 102 |

Two are one-frame pauses in the middle of a monotonic movement — the chest
catch runs -4.15, then -0.96, then -12.06 degrees per frame. One, the deflect,
is a different shape: the elbow is nearly still for six frames and then launches
at 10 to 13 degrees per frame, and the statistic names the last quiet frame
rather than the first fast one. Both frames are honest names for a change that
happens between them.

**AND THE HITCH THIS ENTRY RECORDED IS GONE.** It read "on the `wide` variant of
`netball_two_hand_snatch_pull_in` the elbow steps 8.50, then 0.19 at the contact
frame, then 4.41". Measured now, those steps read 11.36, 8.28, 3.92 — no stall.
Some later pack closed it, and nobody noticed because the instrument that would
have said so was the broken one.

## The record of it

Adjudicated during the pole pack's review. Both halves stand.

**The instrument is faulty.** `spike_report` divides a step by the mean of its
two immediate neighbours. A two-value mean has a breakdown point of zero, so
one small neighbour drags the ratio however it likes: a perfectly normal step
beside a stall is flagged, and a snap out of stillness cannot be seen at all
because the skip-gate exempts it. Filed as follow-up: a median over a window of
two or three either side, excluding the frame itself, with a floored
denominator in place of the skip-gate, and possibly a second-difference
statistic that names a hitch at its own frame. `SNAP_RATIO` recalibrates once
the denominator is robust, and not before.

**And there is a real hitch.** On the `wide` variant of
`netball_two_hand_snatch_pull_in` the elbow steps 8.50, then 0.19 at the
contact frame, then 4.41. That one-frame stall was introduced by the pole pack.
It is the same family as `netball_deflect_high` at frame 37: a discontinuity
where the approach hands over to the carry.

So the red row is honest about there being something wrong, and dishonest about
where and by how much. Neither half excuses the other.

## RESOLVED: the cold start resolved the leg's redundancy differently

**Closed by the backward sweep.** Frame zero was the only frame solved without
a neighbour to start from. It now gets one: the drill is solved forward as
before, then walked back from the last frame, every earlier frame re-solved
from its successor. No frame in the kept answer is a cold start.

On the outside-hand hooks the right knee now opens at 49.9 against the 48 the
drill settles at, and its worst step falls from 9.54 degrees to 2.03. The
record of the fault is kept below.

**The mechanism was proved, not inferred, after the free-hand pack shipped a
fix that passed its acceptance test by luck.** Two controls:

| build | knee at frame 0 | worst right-knee step |
|---|---|---|
| before | 34.1 | 9.54 at frame 6 |
| backward sweep | 49.9 | 2.03 at frame 47 |
| backward sweep, frame zero excluded | 34.1 | **15.43 at frame 0** |
| a second FORWARD sweep, same cost | 34.3 | 5.46 at frame 8 |

The third row is the confirmation: exclude frame zero and the whole
disagreement lands on the frame-zero boundary, which is where the explanation
says it should. The fourth is the refutation of "it is just more solving": the
same number of extra solves, in the same direction, leaves frame zero where it
was and the snap in place.

**What it costs.** The solve doubles, 11.2 to 22.0 milliseconds per frame.

**What it moves.** 38 measured values across the library, largest 5.34 degrees,
and no verdict flips. The signature is a left and a right knee moving in
opposite directions on every drill, by 0.5 to 4.8 degrees — the pelvis trading
one leg against the other, which is the redundancy this fault lives in.

`test_cold_start.py` states the rule as drift against target movement, which is
the pairing the cold start's own docstring used. It fails on the code before
this change and names the fault.

## The record of it

On `netball_hooks_outside_hand` the right knee opens at 34.1 degrees of flexion
against 50.0 before the free-hand fix. It holds 34 to 37 for six frames, steps
9.6 degrees between frames 6 and 7, and settles at about 47 for the rest of the
drill. The free hand's target barely moves across those frames.

**Nothing is broken in the pose.** Both feet read 0.00 cm off the floor
throughout and the pelvis holds 84.04 to 84.06 cm. With the foot planted and
the pelvis fixed, knee flexion is not fully determined — the hip can rotate and
reach the same foot from the same pelvis at a different knee angle. The solver
has freedom there and resolved it one way at the cold start and another once
the drill was running.

**It is the cold start, and it is the free-hand target that moves it.** Isolated
by building the two changes separately:

| build | right knee at frame 0 | worst right-knee step |
|---|---|---|
| main | 50.0 | 2.10 |
| the second solve pass alone | 50.0 | 1.06 |
| both changes | 34.1 | 9.54 |

The second pass alone leaves the opening pose alone and makes that channel
smoother. The free-hand target is what changes which pose the solve from rest
lands in.

**It is the same fault the cold start's own docstring already describes**, in a
new limb. That docstring says solving frame zero once from rest "left the
athlete in a different arm configuration from frame one, and the elbow moved 33
degrees over the first few frames while the target barely moved". The remedy
then was several seeds scored by `contact_miss`. The seeds vary only the forearm
twist and the score reads only hands, so neither can tell two leg poses apart.

**Scale, stated so it is not read as worse than it is.** No drill's worst
single-frame step moved by more than 0.56 degrees over eight angles, and the
library already carries steps of 4 to 19 degrees. The graded checkpoints at
`facing_away` barely moved: the left knee 50.6 to 51.9 and the trunk turn not at
all. The right knee is measured and reported there but is not a checkpoint.

A fix belongs in the cold start rather than here: frame zero is the only frame
not continuous with a neighbour, and a backward pass over the opening frames
would give it what every other frame has. That is a mechanism change and it is
not bundled into the free-hand pack.

## The term named continuity is a pull toward the rest pose

`possession_solve.py` and `movement_engine.py` both build a
`solver2.ModelParametersErrorFunction`, set its weight to 0.02, and call the
variable `continuity`. Neither ever calls `set_target_parameters`.

That class "penalizes the difference between the target model parameters and
the current model parameters". With no target set the target is zero, which is
the rest pose. Every other use of the same class in this repository names the
variable `prior`, which is what it is.

**Frame-to-frame continuity here comes entirely from the seed.** Each frame is
solved starting from the previous frame's answer. Nothing in the objective
prefers the previous pose.

**Five places said otherwise and all five are corrected as of this entry:** the
comment above `CONTINUITY_WEIGHT`; the first-frame comment in
`movement_engine.py`; the continuity paragraph in `spikes/README.md`; and two
sentences in the free-arm snap entry above. A sixth, in the follow-through
entry, listed the term among those resisting a branch change.

**Reread any historical snap reasoning that leans on this term.** Two of the
corrected sentences were load-bearing: "the continuity term carries that
faithfully" and "a term that is correct, opposed by continuity". A pull toward
rest can do neither. It cannot carry a bad pose forward and it cannot oppose a
correct term frame by frame. Wherever an explanation in this ledger turns on
continuity holding a pose, the mechanism is the seed and the explanation should
be checked rather than assumed to survive the rename.

**The behaviour is not changed here, and the variable is not renamed.** The
engine works: continuity does happen, by seeding, and every drill is graded on
what the code actually does. Only the description was wrong.

## RESOLVED: the receiving hand no longer grips before it arrives

The queued finding read: "the job carries `grip.l` at the `contact` phase while
that hand is still 101 to 134 mm from the ball, so all five of its digits read
short." Measured on `a38c43d`, that state is gone.

`export_blender_job.py` emits a grip only for the hands `sides_at` reports, and
only once she is holding the ball. On both one-handed drills the `contact`
phase now emits `grip.r` alone:

| drill | phase | sides_at | left wrist to ball | right wrist to ball |
|---|---|---|---|---|
| one_hand_snatch | contact | `('r',)` | 49.0 cm | 15.2 cm |
| one_hand_snatch | join | `('l', 'r')` | 15.4 cm | 15.4 cm |
| hooks_outside_hand | contact | `('r',)` | 46.7 cm | 15.0 cm |
| hooks_outside_hand | gather | `('l', 'r')` | 15.4 cm | 15.5 cm |

**A hand is described as gripping only when it sits at the same standoff as
the hand that took the ball**, 15.2 to 15.7 cm from the centre. Two fixes closed
it between them: the `sides_at`-only export change, and the free-hand fix in
`c3aa388`, which turned the left hand's 49 cm at contact into a place it is
meant to be rather than a hand caught mid-flight.

## A retired lead: the 29.6-degree grip angle was three errors

Recorded so that nobody raises it again as an anomaly.

A measurement taken while chasing the above reported that at contact every
two-handed drill sits at 46 to 49 degrees between the ball-centre-to-wrist
direction and the ball's path, while the one-hand snatch's catching hand read
29.6. It looked like an outlier. It is not, and it was wrong three ways:

- **The wrong point.** It used the WRIST, which is about 15 cm from the ball
  centre and behind the palm. The contact point is on the surface.
- **The wrong axis.** It measured against the ball's VELOCITY. The grip is not
  built about the velocity. `grip.contacts` says so in its own docstring: "The
  catcher is used rather than the ball's own velocity because a grip is
  symmetric about the body that is taking the ball, not about the path it
  arrived on."
- **An inverted legend.** It was written up as "180 degrees means the hand
  meets the ball head on". The opposite is true: `contacts` places a hand at
  `centre + radius * outward` with `outward` built from `shoulders - centre`,
  and the ball flies toward the shoulders, so a hand on the arriving face reads
  NEAR ZERO.

Measured correctly, on the contact points, there is nothing to explain. The
half-spread is 45 degrees and the ball's velocity sits 22.5 degrees off `near`
on that drill, so the two contacts land at 66.5 and 24.9 — which is 45 plus and
minus 22.5. The two-handed drill, whose velocity is 8.9 degrees off `near`,
reads 45.7 on both hands against a half-spread of 45.

**The docstring predicted the error before it was made.** The lesson is not
about grips: an instrument aimed at a different axis from the one the design
uses will find an anomaly every time, and the anomaly will be the instrument.

## Five figures in this file were stale, and the artefact beside them was not

Raised on 2026-09-01, from the two-records question: this file recorded the
one-hand-snatch contact elbow as 146.13 and the clip pipeline read 146.01.

**There is no divergence between two pipelines.** A direct solve, the clip
export and the clip baseline all read 146.01. The figure in the prose was
simply old.

**It was stale on arrival.** `2d82299`, the pole basis orthogonalisation,
moved that checkpoint from 146.13 to 146.01 at 17:50 and updated
`clip-baseline.json` in the same commit. `1df5e52` wrote 146.13 into this file
at 19:39, an hour and three quarters later. The number was copied from an
earlier reading rather than measured when it was written.

Four more were found by the same check, in the table of failing release
checkpoints: 35.73, 49.98, 41.05 and 40.81 against 35.83, 49.85, 41.04 and
41.00. All four corrected, with the old values kept beside them. No verdict
changed and no conclusion in this file depended on the third decimal.

**THE ARTEFACT WAS CORRECT THE WHOLE TIME.** `clip-baseline.json` matched the
engine exactly, because it is regenerated by the commit that moves it and a
gate reads it every run. The prose had neither. That is
"unmeasured is the risk" wearing documentation instead of code: a number under
an instrument stays true, and a number copied into a sentence goes stale in
silence.

**What to do about it is a convention, not a test.** A figure in prose should
name the build it was read on, the way the evidence documents in `docs/` now
do — "Measured on `9cf25a4`". A reader can then tell whether a number is
current instead of assuming it. Checking every figure in this file
automatically was considered and rejected: it would need a solve per assertion
and would break on every deliberate change, which is how a guard becomes noise
and then gets deleted.


## CLOSED: the right hand now opens the way the left one does

Marius ruled on 2026-09-01 that the fix ships, calling it a bug. Shipped in
`fde5d5a`. The six pieces of evidence are in `docs/HAND_MIRROR_EVIDENCE.md`,
which carries the closure and the measured cost.

Both hands now fan 14.37 cm and every fingertip is the reflection of its
opposite. The shipped fix was proved byte-identical to the previewed one on
all eight drills, worst difference 0.0000000000, against a capture taken
before the source changed.

**47 of 69 graded values moved and no verdict flipped.** The failing set is
unchanged in drill and phase; its figures on this build are 35.78, 49.98,
146.01, 40.89 and 40.86, and they name `fde5d5a`.

**THREE THINGS THIS OPENED, all recorded rather than absorbed.**

1. **WITHDRAWN 2026-09-02: "her ready stance changed".** This entry said
   `hooks_outside_hand` starts 15.44 degrees turned where it started 48.23, and
   that she had been turning her shoulders 48 degrees to compensate for the
   broken hand. **She had not.** That drill has two solved poses about 33
   degrees apart, and the parameter set that shipped reached the other one. She
   stands at 48.22 degrees under the correction. Refer to `docs/CLAVICLE_ARTEFACT.md`. The claim was relayed to
   Marius and to the rendering lane and is withdrawn to both.
2. **WITHDRAWN 2026-09-02: the library-content gap.** There was no gap. The
   drill turns 48.22 degrees while a hand waits, so the real library exercises
   the waiting-hand rule as it always did. The inverted clause has been
   restored to its original form and the hand-built fixture is kept as belt and
   braces. The coach-agenda item is STRUCK.
3. **WITHDRAWN 2026-09-02: the populations converged.** They never converged.
   The 3.09 cm reading was the same artefact: `hooks_outside_hand`'s contact
   elbow width read 19.01 cm under a distorted clavicle and reads 54.83 once it
   is pinned. The two populations are 20.96 cm apart, as they were before, and
   the deferred pole-angle question keeps its original two-population form.

**The mirror preview variant is retired.** `preview_variants` is coach-facing,
and a variant rendering the shipped build while a page labels it the
alternative is the byte-identical failure that module was already caught
committing once. The regression is guarded closer to the rig instead.


## The docs-wide stale-figure sweep, and what it could not reach

Run on 2026-09-02 against `ac240b2`. The item was logged as "unclaimed, not
clean" after five stale figures were found in this file by following one
question. This is the wider pass.

**The corpus.** 16 documents, 5113 lines, 1130 decimal figures.

Re-measuring 1130 figures is not possible and would not be useful: most sit
inside an entry describing a past event, and are correct as the record of what
was read then. So the sweep checked every class that HAS a current source of
truth, and says plainly what it left alone.

### What was checked, and what it found

| class | checked | wrong |
|---|---|---|
| code constants cited by name in prose | 10 citations of 4 constants | **0** |
| bands quoted beside a measure name | 13 | **0** |
| the five failing checkpoints against `clip-baseline.json` | 5 | **0** |
| the open-defect figures in `REQUIREMENTS.md` | 2 | **2** |
| documents carrying figures with NO build named | 16 documents | **2** |
| a sample re-measured from the unstamped coach review | 7 | **7 moved** |

### The two that were wrong, and they were the ones presented as CURRENT

`docs/REQUIREMENTS.md` lists two open anatomy defects. Both figures were stale,
and both understated the defect:

- **The elbows.** Recorded as 27.3 cm against the reference photographs' 38.6,
  a gap of 11.3 cm. On `ac240b2` the six drills that put both hands on the ball
  average **36.40 cm**, a gap of **2.20**. The defect is four times smaller than
  the document claimed. The 27.3 figure predates the elbow pole becoming an
  angle.
- **The joint limit.** Recorded as one frame at 0.715 degrees. On `ac240b2`
  `netball_hooks_outside_hand` breaches on **98 of its 98 frames, worst 2.3355
  degrees on `l_clavicle_rx`**.

**The mirror fix did not cause the joint-limit breach**, and that was measured
rather than assumed: across that change the same drill breached 98 of 98 frames
before it too, worst 0.4990 degrees on `l_clavicle_rz`. The breach is older
than the fix. The fix made the worst overshoot 4.7 times larger and moved it to
a different axis. No other drill in the library breaches at all.

**Nothing in the test suite reads it.** `check_joint_limits.py` is a separate
task and it exits 1 today while the suite passes 564 tests. A defect recorded
as rare and small, which is neither, and which no gate reports.

### The class that matters more than any single figure

Two documents carry figures and name no build: `REQUIREMENTS.md`, corrected
above, and `COACH_REVIEW_2026-08-30.md`, which holds **113 figures** and is the
document the coach morning most depends on.

That review is NOT rewritten. Erin's marks and her words are the record of a
real event. What it lacked was the build its engine figures were read against,
and it now carries that as a header. Seven of its rows name a drill, a phase, a
measure and a value, which is enough to re-measure. **All seven moved**, by 0.02
to 0.47 degrees. No verdict or argument in it changes. The point is that not
one was unchanged: three fixes have landed since it was written, and small
universal drift is what that looks like.

### What this sweep did NOT do

- **It did not re-measure the other 1100 figures.** Most name no drill, phase
  and measure together, so there is nothing to re-measure them against without
  guessing what they meant.
- **It did not check `HANDOFF_RENDERING.md`'s 197 figures** beyond the stamp
  test. They belong to another lane's instruments.
- **It did not verify Erin's marks**, which are not engine readings.
- **It found no wrong band and no wrong constant**, which is a real result and
  not an absence of effort: those two classes are mechanically checkable and
  they are clean.


## The joint limits were exceeded on a parameter the model had locked

Raised 2026-09-02 by the docs-wide sweep, ruled a DEFECT rather than a judgement
call, and fixed. Measured in `docs/CLAVICLE_ARTEFACT.md`.

Four parameters have a range of ZERO WIDTH — the model says they must be
exactly zero — and all four were enabled for the solver: `l_clavicle_rx`,
`r_clavicle_rx`, `l_foot_lean1`, `r_foot_lean1`.

**The limit term is soft**, so a locked parameter left enabled sits wherever
the other terms drag it. On `netball_hooks_outside_hand` the left clavicle sat
2.34 degrees outside a range of zero on all 98 frames. **No other drill moved
that parameter at all**: their `l_clavicle_rx` maximum is 0.000006 degrees.

**A CORRECTION.** An earlier version of this entry said the other drills pulled
the same parameter 0.06 to 0.10 degrees. They do not. Those figures are
`clavicle_RZ`, a different axis with a real range, read off the limits table.
Two axes of one joint were conflated.

**The fix removes freedom rather than adding a constraint**, and touches no
weight: those four are excluded from the enabled set. `check_joint_limits` now
passes at exit 0 with a worst overshoot of 0.1033 across the library. 42 graded
values move, no verdict flips, and the largest change to any grip is 2 mm.

**THE MECHANISM FIRST PUBLISHED FOR THIS WAS WRONG.** It said the solver had
absorbed the athlete's turn into a clavicle rotation the body cannot make. A
control refutes it: excluding an UNRELATED axis with a real range, `head_twist`,
undoes the stance change identically, and in those solves the still-enabled
`l_clavicle_rx` sits at 0.0000 degrees. A 2.34 degree rotation cannot hold a 33
degree turn. Refer to the entry below on the two basins.

**IT ALSO REVERSED FOUR PUBLISHED FINDINGS**, three of which had left this
repository. The stance change, the population convergence, the "one-handed
drills are not a population" claim and the library-content gap were all read
from the second basin. Refer to `docs/CLAVICLE_ARTEFACT.md` for the three-state
table that settles it and for the corrected cost of the hand-mirror fix. Its
reported largest graded move of 23.16 degrees belongs to the basin change; the
3.09 that replaced it is a bistable knee, and the fix's largest move away from
the knee channel is 0.17 degrees.

**Two guards found it**, and both had been read as reporting something about the
athlete: the elbow-pole tripwire and the turned-drill clause in
`test_waiting_hand.py`. They went red when the axis was pinned, and reading why
is what produced the finding.

**Nothing in the gate read `check_joint_limits`.** It exited 1 while the suite
passed and the clip gate passed. That is now a suite row in
`test_locked_parameters.py`.

**How long, precisely, because two breaches are easy to conflate.** The 0.499
degree breach on `l_clavicle_rz` — a real axis — was present at `716b3eb`,
along with one frame of `two_hand_catch_chest` at 0.251 degrees on
`r_thumb2_rz`. The 2.34 degree breach on the LOCKED axis dates from `ac240b2`
at 14:04 on 1 September: **one day, not weeks.**


## The root winding is not a defect, and the guard proposed for it would be wrong

Investigated 2026-09-02 and CLOSED WITH NO ACTION. Recorded so it is not raised
again.

The two-basin finding noted that in the retired basin (state B, measured on
`ac240b2` in `docs/CLAVICLE_ARTEFACT.md`) the root rotation was wound to 1030,
769 and 683 degrees. I proposed a general bound on root winding
as a companion guard, on the reasoning that nearly three full turns is not a
pose anybody wants. **Three measurements say otherwise** (all measured on
`7fb351c`, whose solve of this drill is identical on `cc43666`).

1. **The root rotations are unbounded by design.** They carry no recorded limit,
   which is correct for a free root.
2. **The pose repeats modulo 360.** Adding a full turn to any root rotation
   moves the skeleton by 0.00002 cm. A wound angle is the SAME POSE described
   differently.
3. **Nothing on the clip or coach boundary reads the raw angle.**
   `export_tactics_clip` states in its own docstring that every number it
   writes is read off the solved joint POSITIONS, and the coach animation and
   Blender job exporters read positions too, so a wound angle cannot reach the
   clip contract or a coach. (`build_library` does write the raw parameter
   track into a derived, uncommitted GLB; the limit checkers read the track
   for overshoot, which is inert for a limitless root.)

On the shipped build (`7fb351c`) there is no winding to speak of: the root sits
between 119 and 182 degrees on the drill in question, with a largest
frame-to-frame step of 8.81 degrees.

**AND THE GUARD WOULD HAVE BEEN ACTIVELY HARMFUL.** Winding is what keeps an
angle CONTINUOUS from frame to frame. Forcing it into a bounded range would
introduce a jump wherever the value crossed the boundary, and the Tactics
player interpolates between the clip frames it is given — the same reason
`clip_geometry.unwrap()` deliberately lets limb angles count past a half turn.
A bound would have penalised the representation that makes interpolation
correct, in the name of tidiness.

The winding remains a true DESCRIPTION of that basin's parameters and it is
kept in `docs/CLAVICLE_ARTEFACT.md` as such. It is not evidence of a bad pose.


## Three solvable balls are invisible to the library, and they support the claim

### What was built on that measurement

**A variant is the SAME checkpoints to the grader**, because seven of eleven do
not move at all and an eighth moves 1.63 degrees. Per-variant bands would be numbers invented for a difference
that is not there, and at contact the existing bands already hold all four
balls.

So `build_library.py` now solves, grades and receipts **every** ball. Each
receipt names the ball it was solved against, the index lists a movement and a
variant rather than a movement alone, and the summary prints only the readings
that MOVE across the balls:

```
what the ball changes on netball_two_hand_snatch_pull_in, in degrees:
  checkpoint                                       None     high      low     wide
  contact/leftElbowFlexionDegrees                 76.05    83.66    79.70    58.21
  contact/leftShoulderElevationDegrees            66.05    81.63    49.95    70.03
  contact/rightElbowFlexionDegrees                76.03    83.66    79.67    76.01
  the other 8 checkpoints move less than 5 degrees across every ball.
```

**THE LOW BALL IS GRADED AS IT READS: 10 of 11.** A miss by 0.05 degrees is a
miss, and the receipt says so. This entry is why it carries no verdict about
the athlete.

**THE INDEX PUBLISHES `symmetric: false` FOR THE WIDE BALL** beside three
`true` rows on the same drill, and that is right rather than odd: the wide
ball arrives 0.60 arm lengths to her left, which is a one-sided demand however
even the keys are. It is the same reading the left-right knee guard's
population uses, applied to a variant. **That guard measures the PLAIN ball
only** — `test_waiting_hand.py` passes no variant to either the population or
the solve — so a variant's evenness is published and not measured.

## CLOSED: a drill that starts with the ball must declare arrival at 0.02

`load_ball` requires `release < arrival`, so a drill that already holds the
ball cannot say `arrival: 0` and says 0.02 instead — "a formality, not a
catch", as those files put it. The question was whether the schema should
allow `release == arrival`.

**Checked on 2026-09-02: it costs nothing.** Every one of the first six frames
of both ball-in-hand drills reads `carried`. **The 0.02 convention invents no
flight state**, which is the failure mode the authoring rule exists to prevent
and the one that would have justified the change. The change is cosmetic and
is NOT made.

Recorded so the next reader does not reopen it on the strength of the wording
alone.

## The engine solved where the ball goes and threw the answer away

`possess` solved the outgoing velocity, used it to walk the ball forward frame
by frame, and discarded it. **Nothing downstream could ask where a pass ENDS
UP**, so every question about the library's one ball speed has been answered by
hand arithmetic outside the engine — and those answers have disagreed with each
other. This entry replaces them with the engine's own.

Measured on `763cabd`. `Possession` now carries `launch_from` and
`launch_velocity`, and `apex()` reads them.

### It must be computed, not sampled

**Every clip in this library ends while its ball is still in the air.** Both
passes release at 0.80 of the clip and are still descending at the last frame.
Worse, the chest pass's ball peaks **0.07 s** after it leaves — four frames at
60 fps — so a peak scanned off the drawn frames would report the release height
and call it the peak.

So `apex()` is the closed form from the launch, and a test asserts that rather
than describing it.

### A concern raised here and then withdrawn by measuring it

A first version of this entry said the `up: 0.0` target lands at 106.5 cm,
called that 26 cm below her shoulders, and asked whether the anchor or the note
describing it was wrong.

**The anchor is `c_spine3`, and it sits at 126.403 cm.** Her shoulder midpoint
at frame 0 is 132.86, so it is **6.5 cm** below her shoulders, which is where a
chest is.

**TWO QUANTITIES SIT THERE AND AN EARLIER VERSION OF THIS ENTRY QUOTED THE
WRONG ONE.** Measured on `aa3f244`, by the calls `solve_movement` itself makes
at `possession_solve.py:138-174`:

```python
zeros = np.zeros(len(character.parameter_transform.names))
rest  = finger_wrap.spread_fingers(character, zeros, method.every_side)
rp    = movement_engine.joint_positions(character, rest)   # c_spine3 y = 134.832
arm   = motion_track.arm_length(rp, index)                 # 52.6801
placed0 = movement_engine.trunk_frame(track, 0.0, rp, index, arm, track.turn_at(0.0))
```

`movement_engine.py:213` sets `chest = place(rest_positions[c_spine3])`, with
the root dropped by `hip_drop_at(0.0)` — 0.1003 leg lengths, 8.43 cm on both
passes. That gives **`placed0.chest = (0, 126.403, −3.713)`**, and
`stance.place(ball.launch.target)` returns **`(0, 126.403, 207.008)`**: the
`up: 0.0` leaves the height untouched, and so does the turn matrix.

| quantity | chest pass | overhead pass | does the launch read it? |
|---|---|---|---|
| the trunk PLACEMENT, `placed0.chest[1]` | **126.403** | **126.403** | **yes** |
| the SOLVED chest, `points[0][c_spine3][1]` | 126.3242 | 126.3170 | **no** |

**`solve_launch(launch_from, stance.place(target), 600)` reproduces the
engine's own `launch_velocity[1]` — 71.4690 and −39.3721 — to 0.000000, and
only with 126.403.** The solver moves the chest 0.08 cm off the placement over
the solve, and `stance_frame` never reads the solved value.

So the earlier 126.32 was **the wrong quantity, not a rounding**. It was
reached by inverting the engine's velocity, which could not detect the error
because the inversion fed the solved anchor back into its own run. Reading the
placement directly settles it, which is what the guard below now does.

The ball files say `up: 0.0` puts the receiver's hands "at the height of this
athlete's chest, where the stance frame is anchored". **That is accurate.**
The 106.5 was mine, and it was the ball's height fifty centimetres PAST the
target while it was still falling.

## The Blender job anchored the ball to a landmark it did not transmit

`ball.fromShouldersInArms` is an offset from the shoulder MIDPOINT, and the job
never said where that midpoint was. A consumer had to guess. **The rendering
lane's guess was to leave the shoulder girdle at rest**, because nothing in the
job asked it to move — so every figure this project has rendered placed the
ball from a girdle that never moved.

Found by the rendering lane on 2026-09-04. Measured on `cc2c20a`.

### The girdle moves on every drill

Midpoint travel relative to the pelvis, over the whole clip:

| drill | travel | | drill | travel |
|---|---|---|---|---|
| `overhead_pass` | **8.45 cm** | | `chest_pass` | 2.21 |
| `deflect_high` | 5.02 | | `two_hand_snatch_pull_in` | 2.14 |
| `hooks_jump_pull_in` | 4.09 | | `two_hand_snatch_straight_back` | 2.02 |
| `hooks_outside_hand` | 3.00 | | `two_hand_catch_chest` | 1.98 |
| `one_hand_snatch_to_other_hand` | 2.40 | | `bounce_pass` | 1.93 |
| | | | `double_foot_landing` | 1.77 |

**31 of the 48 graded phases sit more than a centimetre from the neutral
girdle**, and the re-render is the whole library rather than the four drills a
first reading suggested.

Three definitions that count needs, because a count is only as good as what it
counted:

- **The girdle position is the shoulder midpoint taken from `root`**, the MHR
  pelvis joint. `root` is the landmark on this side of the boundary, and the
  rendering rig has no bone of that name — refer to the residual below.
- **The neutral girdle is `chest_pass/ready`**, which sits at
  `[0.0020, 48.8246, 2.4622]` cm from `root`. It is one graded phase of the 48
  and not an average of them, chosen because it is the phase closest to a
  standing athlete.
- **A phase is measured on ONE frame**, the frame `round(at_phase x
  (frames - 1))` clamped to the clip, which is the frame `build` renders that
  phase at. So these are 48 frames and not 48 spans of frames.
- **The 48 is the library of `cc2c20a`, which held ELEVEN drills and 1084
  frames.** The count is a measurement of that library and does not move when a
  drill is added. `netball_one_hand_high_pass` arrived on 2026-09-04 and took
  the library to twelve drills and 1180 frames; nothing above was re-counted
  for it, and the ratio is what the entry is about.

### A withdrawn number, recorded because it is the fault this field is about

An earlier version of the table above gave the rendering rig's
shoulder-above-pelvis as **0.8759** of this athlete's. That figure is
withdrawn. It is **42.7689 / 48.8246 = 0.87597**, truncated — the rendering
rig's REST torso over
this athlete's POSED shoulder height at `chest_pass/ready`. Two rigs, one at
rest and one posed, one measured in three axes and one vertical, under a single
label. The rendering lane says it never produced that number and is right: its
two ratios are 0.9215 for the arms and 0.861484 for the rest torsos.

The 2.23 cm is unaffected, because it never came from the ratio. It is
`48.8246 x (48.547 / 52.680) - 42.7689 = 2.2252`, and its inputs are now
written beside it.

**A WIDTH RANGE IS THE WRONG STATISTIC AND A FIRST VERSION OF THIS USED IT.**
It read 0.65 to 1.05 cm on seven drills and set them aside. Width is one axis of
three: the overhead's width ranges 5.63 cm while its midpoint travels 8.45, and
`bounce_pass` moves almost entirely FORE AND AFT — 2.46 to 0.54 cm ahead of the
pelvis with the vertical barely changing — so on a width-and-height check **it
would have read as the cleanest drill in the library and shipped**.

### The field took four attempts, and each was killed by a measurement

| attempt | what killed it |
|---|---|
| absolute metres | the job is normalised; `radiusM` is the only absolute, because a netball is one size on every body and a shoulder is not. It raised the consumer's ball ~6 cm on EVERY frame, including the ones that pass today |
| arm lengths | a shoulder-above-pelvis distance is a TORSO quantity. The two rigs' arms are 52.680 and 48.547 cm, a ratio of 0.9215; their rest torsos are 49.6456 and 42.7689, a ratio of 0.8615. An arm divisor is therefore 6.5 per cent wrong on a torso span, and this athlete's 48.8246 cm shoulder height at `chest_pass/ready` resolves to 45.00 cm on a rig whose own rest torso is 42.7689 — **2.23 cm** out against a 1 cm rule |
| a torso-normalised POSITION | failed on **all 48** phases by 1.1 to 5.8 cm, including phases where both girdles are neutral and nothing is wrong. A divisor scales and cannot translate |
| a displacement from the WORLD | carries the root, which is never at its rest position. It read **30.97 cm** on the landing drill, against a girdle that moves 1.77 |

What ships is a **pelvis-relative displacement from rest, in units of each
body's own rest torso**. It cancels every constant — landmark convention,
neutral posture, build — reads zero at rest by construction, and carries the one
thing that was missing.

### The grip fix moved the problem up a level rather than removing it

`_grip`'s docstring already knew shoulder width mattered: it records that
sending shoulder directions closed this athlete's grip from 19.0 cm between the
wrists to 12.1 and put both hands in front of the ball. The fix was to place the
ball first and the hands on it. **So the hands became anchored to the ball, and
the ball stayed anchored to shoulders nobody sent.**

### Two guards of this field were measured on eleven drills and spent on twelve

Both were found on 2026-09-04, when `netball_one_hand_high_pass` merged and the
suite was run on the merged tree. Neither is a defect in that drill, and the
field itself was untouched by both.

**A COVERAGE GUARD THAT COUNTED INSTEAD OF COVERING.** The anchor check ended
with `assertEqual(checked, 1084)`, written to prove it reads the whole library
rather than a sample. It read `1180 != 1084` the moment a 96-frame drill
arrived — a red suite caused by a correct new drill and by the guard. **Any new
drill would have fired it**, so it was a tripwire on library growth wearing a
coverage guard's name. It now takes its population from `library()` and each
drill's span from its own clip, and holds a FLOOR rather than a total: the
drills covered must equal the library's list, each drill's frames must be
exactly `range(0, its clip length)`, and the cover must not shrink below what
the field was proved on. A drill's author satisfies it by adding the drill.

**A ROUNDING BOUND WITH LESS MARGIN THAN IT LOOKED.** The end-to-end ball check
first shipped against one unit in the last place, 1e-6 torso lengths, and
passed at 9.2583e-07 — 8 per cent to spare. On twelve drills it reads
**9.3398e-07**. One drill consumed a tenth of the remaining margin, so the
library sat a few drills from a red suite with nothing wrong in it.

The correct bound is not one unit and never was. That check composes **two
roundings in two different units** — the girdle shift in torso lengths and
`fromShouldersInArms` in arm lengths — so its exact per-coordinate maximum is
`0.5e-6 x (1 + arm / torso) = 1.031e-6` torsos on this athlete. The measured
worst passed one unit by alignment, not by margin. The guard now holds 2e-6 as
a stated ceiling above that derivation.

**Both are the same shape as the rest of this ledger**: a quantity measured in
one regime and spent in another. Here the regime is the library itself — a
count and a bound both measured on eleven drills and spent on every drill that
would ever be added.

## The alignment ranked a sync clap above every real catch

Found 2026-09-04 while looking for the clap Marius said Erin used to sync the
two cameras. It is in the front recording, twice, and it has been in our own
records since 2 September under the wrong name.

**Repetitions 0 and 8 of `spikes/video-annotations/ball-in-frame-0.1.json`,
annotated "gesture", ARE THE CLAPS.** Measured on the front view:

| | hands together | front audio above 4 kHz |
|---|---|---|
| repetition 0 | **5.867 s**, wrists 0.249 shoulder widths apart | **x26.5** over its local floor, at 5.800 s |
| repetition 8 | **17.900 s**, wrists 0.266 apart | **x29.1** over its local floor, at 17.835 s |

**THE COUNT IN AN EARLIER VERSION OF THIS ENTRY WAS FALSE.** It said "only
seven frames in 785 fall under 0.5". **Fifty-five do.** Seven was a count of
local minima after a separation rule, printed as a count of frames, and the
deepest frame in the whole clip — 0.236 at 18.300 s — was not among the seven
named. Corrected from a committed run of `spikes/video_clap_evidence.py`:

| reading | value |
|---|---|
| frames read | 785 |
| median separation | 0.94 shoulder widths |
| **frames under 0.5** | **55** |
| in stretches | **5** |
| local minima | **12** |
| deepest | 0.236 at 18.300 s |

The five stretches are 5.833–6.033 (7 frames), 17.833–19.000 (36),
21.000–21.067 (3), 22.300–22.400 (4) and 22.833–22.967 (5).

**THE IDENTIFICATION DOES NOT REST ON THE COUNT. IT RESTS ON A COINCIDENCE.**
Her hands come together often, because she talks with them; the room has many
loud moments. What is rare is the two at once. Of the **twelve** hands-together
minima, **exactly two** carry a broadband attack within 100 ms — 5.867 s with
x26.5, and 17.900 s with x29.1. **The other ten carry nothing at all.** The
result is not delicate about the 100 ms: it holds unchanged for any window
between 0.067 and 0.230 s. Those
two are the two repetitions the annotation had already singled out as containing
no ball.

The long 17.833–19.000 stretch contains the second clap AND the deepest frame
that follows it, which is consistent with the annotation's own reading of
repetition 8: she claps, then stands and talks with her hands clasped at her
chest.

### Why this matters more than the sync question

**Repetition 0 scored 0.02369 on the whole-curve warp distance against 0.06093
for the next best — BEST OF TWELVE — and rank 1 of 8 drills on both scorings.**

The elbow curve of a woman clapping fits the catch reference better than any
real catch in the set, and no scoring in the alignment can tell the difference.
The informative scoring placed it fifth of twelve, which is luck rather than
detection: it ranks the drill first either way.

This is the blind spot the ball-in-frame condition was built for, and it now has
a name. The gate asked eleven questions and none of them was "is this a catch".
The condition refuses repetitions 0 and 8 already; what is new is knowing WHY
the best-scoring repetition in the set is not a catch, which is a stronger
statement than "a frame strip shows her gesturing".

### What it does not settle

**Nothing about the camera offset.** The clap is in the front and cannot be
found in the side. The front's four broadband spikes include a distinctive pair
0.175 s apart at 26.240 and 26.415 s, and no offset in ±6 s places that pair
anywhere in the side track, whose only gap under half a second is 0.235 s. A
randomly generated side track of 17 spikes matches the front's four as well as
the real one does in **12 per cent** of 2000 trials, so the best alignment is
not a reading.

**THE NULL IS REPRODUCIBLE.** Python `random.seed(0)`, 2000 trials; each trial
draws 17 times uniformly from 0 to 28 s as a fake side track, scans offsets from
−6 to +6 s in 0.02 s steps, and counts a front spike as matched when it lands
within 50 ms of a fake spike. The real side track scores 3 of 4; 12 per cent of
the fake ones score 3 or more. The front's four spikes are 5.800, 17.835, 26.240
and 26.415 s.

Either the side camera's microphone never registered the claps — its strongest
event is x24 against the front's x44, and it may be several metres away — or the
two files do not contain the same instant. **The audio cannot separate those two
readings**, and until a person does, no offset stands at all. **CORRECTED
2026-09-07: an earlier version of this line said "the by-eye 1.0 s stands as the
only measured offset". It does not.** That offset and a later −0.7295 s are both
withdrawn, and an event ledger over the whole clip finds no constant offset that
beats chance AT ANY TOLERANCE A SYNC COULD USE (at 0.400 s, twelve frames, one
does: 8 matched against a ceiling of 7, and at that width a match spans most of
the 1.866 s toss cycle) — refer to
`spikes/video-annotations/event-ledger-0.1.json`. The pair measured here is
**`f7faf38b5d42` with `253fa551605e`**, and it is not a synchronous pair. It is
unusable for two-view work.

**THE SET NAME IN THAT VERDICT WENT STALE ON 2026-09-07 AND THE FINDING DID
NOT.** Corrected 2026-09-09. The recording measured here as "side 0.1" is
`253fa551605e`, which was renamed that afternoon and is **today's
`side 0.2.mp4`**. So this entry paired the front of one run with the side of
the other, which is why no offset fitted. Everything above stands for that
pair, including the null: 12 per cent of 2000 trials with `random.seed(0)`.

**TODAY'S SET 0.1 IS A DIFFERENT PAIRING AND IT IS ESTABLISHED.**
`f7faf38b5d42` with `6e8f9fb2fe03`, at a side index of the front index minus
five, fitted on three events eleven seconds apart and confirmed on the frames.
Refer to the header of `docs/VIDEO_CAPTURE_FINDINGS.md`. A reader who took the
old sentence at face value would call an established pairing unusable.

**WHY THE SENTENCE SURVIVED.** This entry WAS corrected on 2026-09-07, for the
withdrawn offsets, and not for the rename that happened the same afternoon. A
correction to one claim in an entry is not a review of the entry.

**THE LEDGER FILE ITSELF NEVER WENT STALE**, because it records identity rather
than a label: its side view carries `videoSha256` `253fa551605e`,
`videoFile` `side 0.2.mp4` and `namedBeforeTheRename` `side 0.1.mp4`. The data
was right and the prose about it was wrong, which is the argument for keying a
pipeline by hash: a sentence that names a hash cannot be moved by a rename.

**AND A CORROBORATOR THIS LANE OFFERED IS WITHDRAWN.** A wrist-height scan was
reported as peaking at −0.967 s, agreeing with the recorded −1.000. Three of its
eight input moments had no provenance — they were picked inside annotated
windows where no catch time was ever read — and removing them moves the peak to
+2.4167 s, a swing of 3.383 s. The reading was carried by the unprovenanced
points and is withdrawn. Refer to "A fifth instrument, and a sixth that is
withdrawn" in
`docs/VIDEO_CAPTURE_FINDINGS.md`, where all eight moments are now named with
their provenance.

### Where the numbers come from

`spikes/video_clap_evidence.py`, committed with this entry, and every figure
above is from `python video_clap_evidence.py 0.1`. **It exists because the first
version of this finding was published from a detector that lived in one
session's scratchpad.** An independent reviewer could not re-measure any of it,
reconstructed the detector by hand, and got 25.4 where this says 26.5 and counts
from zero to twenty-seven depending on the rule guessed. A number nobody else
can regenerate is not a measurement, whatever it happens to be.

Every parameter is a named constant with its reason: the 4 kHz band, 5 ms
blocks, a median floor over the preceding 0.5 s stopping 10 ms short, an attack
ratio of 0.5, a 0.15 s separation between reported spikes and a x8 bar.

**THE SPIKE COUNTS ARE CONDITIONAL ON THE SEPARATION CONSTANT, and that is
stated rather than left for a reader to discover.** A reported spike is a
CLUSTER: anything within 150 ms of one is inside it, not beside it. Sweeping
the constant on session 1.0:

| separation | front spikes | side spikes |
|---|---|---|
| 0.05 s | 5 | 17 |
| 0.10 s | 4 | 17 |
| **0.15 s (used)** | **4** | **17** |
| 0.20 s | 3 | 17 |
| 0.30 s | 3 | 16 |

**At 0.05 s the terminal cluster is THREE — 26.240, 26.355 and 26.415 — and at
0.20 s the pair merges into one.** So "a pair 0.175 s apart" is a statement
about this constant as much as about the recording, and the third event between
them is real and merged rather than absent. The constant is now pinned by a test
that fails if it moves in either direction; before that, sweeping it changed
three published counts and no test noticed at any value.

**THE COINCIDENCE WINDOW HAS A STATED MARGIN.** "Exactly two of twelve" holds
for every window from **0.067 s to 0.230 s**. Below 0.067 nothing pairs at all;
at 0.232 a third minimum joins. The 0.100 s used sits inside that plateau with
33 ms below it and 130 ms above. A claim with an unstated window is a threshold
nobody can check.

## A consumer nothing executes is a consumer nobody has checked

Found 2026-09-07, in a tip that had already been pushed and sent to review.

`offsetSecondsToReference` was removed from the sync block, because the
measurement is a frame count and two offsets in seconds had been withdrawn from
the same material. **The field was removed and its two readers were left
behind.** `spikes/video_lift_3d.py:116` and `spikes/video_elbow_curve.py:89`
both still subscripted it.

```
$ python video_lift_3d.py --set 0.2
    offset = float(side["sync"]["offsetSecondsToReference"])
KeyError: 'offsetSecondsToReference'
```

**THE SPIKES SUITE WAS 786 TESTS AND GREEN.** Not one of them executed either
consumer: every test builds a sync block as a dictionary literal and asserts on
that dictionary. A mocked block has whatever fields the mock was given, so
removing a field from the real writer changed nothing any test could see.

### Why it did not show even when the consumers were tried

Both are guarded by `if not side["sync"].get("measured")`, and both load
`keypoints-<view>-<SET>.json` — the same set for both views.

- **Set 0.1**: `side 0.1.mp4` is unmeasured, so the guard fired and the script
  exited 1 with a clear message. That is the case that was tested, and it looked
  right.
- **Set 0.2**: **`side 0.2.mp4` IS measured** — it is half of the real pair,
  with `front 0.1.mp4`. The guard passed, and the next line read the removed
  field.

The set that was tested was the one the author had been thinking about. The set
that broke was the one the change itself created, because the pairing crosses
sets and every consumer built on "both views of a set" rests on an assumption
the mislabel finding had already destroyed.

### And the first repair had the same shape as the fault it fixed

Asking `if not side["sync"]["measured"]` is not the question. `side 0.2.mp4` has
a sync, so `--set 0.2` loaded `front 0.2.mp4` against `side 0.2.mp4`, passed,
and **wrote a plausible lift from two files that are not a pair**. A wrong
artefact is worse than a crash: the crash was found in a minute and the lift
would have been read. The guard now asks whether these two files ARE the pair.

### What was done

- Both consumers resolve through `PAIRS` and take the mapping BY FRAME INDEX,
  so a wrong offset lands on executing code. `--pair` names two files; `--set`
  survives only so the refusal can name the real pairing.
- `spikes/test_video_sync_consumers.py` RUNS both entry points as subprocesses
  and reads their exit codes — including the reachable pass, the lift on the
  established pair, because a refusal-only test proves nothing a syntax error
  would not also prove.
- ~~Mutating the frame offset to −4 or −6 now fails the anchor assertion inside
  the consumer, by event name.~~ **THAT WAS NOT TRUE, and it is corrected
  below.** Each consumer read the offset out of a WRITTEN artefact, so changing
  the offset in `PAIRS` reached neither of them: both ran to exit 0 under both
  mutations. The assertion existed twice, once in each consumer, and no
  mutation could fail either copy. It now lives once, in `frame_offset_of()`
  beside the writer, and it RAISES rather than asserting, because `assert`
  disappears under `python -O` and this is a check on data. Four mutations fail
  it: the offset one frame out either way, a held-back check row moved by one
  frame, the offset in `PAIRS` changed, and the loop emptied.

**The rule, beside "commit the instrument with its numbers": a consumer nothing
executes is a consumer nobody has checked.** A green suite over mocks says the
mocks agree with each other.

### Writing the test found two more, and neither came from the change

The first version of the test file asserted only that a refusal exits non-zero.
**A crash is also non-zero.** Both of these passed it.

**The elbow curve compared a variable it had not loaded yet.** The guard read
`front["source"]["videoFile"]` on a line two above the line that loads `front`.
Every call raised `UnboundLocalError`. It survived because the test read the
exit code and not the reason, and because the shell pipeline it was tried in
reported the exit code of `tail`.

**AND IT WAS MINE, hours old, not six days.** The pack first recorded this
among the faults that "did not come from the change", and the independent
review checked the commits: it is not at 9455a8c, and the first repair
7f2a99e introduced it. So the repair for one fault created another of the same
family in the same file, and the test written to hold the first was too weak to
catch the second. Two of the four faults in this entry are mine, not one.

**The engine's reference curves changed shape and TWO readers did not.**
`reference-curves.json` is at schema version 2, where a curve is
`{"unit": ..., "values": [...]}` rather than a bare list, so that
`footHeightGapCm` can declare centimetres in a file that announces itself as
angles. The widening landed on 1 September. `video_dry_run.py` was widened with
it, deliberately and in writing. Two others were not:

- `video_elbow_curve.py` iterated the curve, collected the dictionary's KEYS,
  and raised a numpy type error on the strings `"unit"` and `"values"`.
- `video_phase_align.py` did the same in TWO places, and the worse of the two
  defeats a guard. `rank_against_library` skips a curve with fewer than two
  points. The mapping has two keys, so it PASSED that guard and carried the two
  words into the ranking across the whole library, which the module's own
  docstring calls the guard on the whole method.

  **THE GUARD PASSED SILENTLY; THE CALL THEN CRASHED.** This entry said the
  fault "is SILENT", and that overstates it: three lines past the guard the
  warp raises, so no ranking was ever produced with the words in it. What is
  silent is the guard, and that is the part worth remembering, because a guard
  that accepts two strings as two data points is a guard that would also accept
  them if the arithmetic below it happened to tolerate strings.

Proven by reading the exported file:

```
LINE 531 SHAPE:
  what it collects: ['unit', 'values']  len 2  passes len<2 guard: True
  then rank_against_library raised, from inside the warp three lines later:
      ValueError: could not convert string to float: np.str_('unit')
LINE 568 SHAPE:
   ValueError: could not convert string to float: 'unit'
```

`test_video_phase_align.py` is 34 tests and was green throughout, because its
fixture builds the reference as a bare list: **the mock had drifted from its
producer, so it tested nothing but itself.**

That is the sharper form of the rule. Two of these four are mine and hours old,
and two are not mine and were six days old, and every suite in the repository
had run over those two while they were broken. **Count the list before writing
the sentence above it**: the first version of this paragraph said one was mine
and three were not, and the review counted.

The shape now lives in `spikes/reference_curves.py` with no heavy imports.
`export_reference_curves.py` takes its version number from there, and all three
readers read through `curve_values` or `curve_length`. `curve_length` counts
values and returns 0 for a bare list, so the shape that passed a length guard
now fails it. The phase-align fixture is at version 2, and
`test_reference_curves.py` reads the REAL exported artefact when it is present.
That last test is the only one here that can catch the next widening.

### And a claim in the commit before this one was wrong

That commit said mutating the frame offset to −4 or −6 fails the consumers'
anchor assertion by event name. **It does not.** Each consumer read the offset
out of a written keypoint artefact, so changing the offset in `PAIRS` reached
neither of them: both ran to exit 0 under both mutations. The assertion existed
twice, in two files, and no mutation could fail either copy.

The check now lives once, in `frame_offset_of()` beside the writer, and it
RAISES rather than asserting, because `assert` disappears under `python -O` and
this is a check on data. Four mutations fail it: the offset one frame out in
either direction, a held-back check row moved by one frame, the offset in
`PAIRS` changed, and the loop emptied.

### What a hosted runner can hold of this

`spikes/poc-output/` is in `.gitignore`, so the keypoint artefacts exist only
on a machine that has processed the footage. The tests that need them skip on
the runner and say so. The tests that need no footage — every refusal that is
decided before a file is opened, the engine-curve schema guard, and the anchor
check — run everywhere. That split is deliberate: the runner holds that both
consumers still import, still parse and still refuse, and the machine with the
footage holds that they still produce.


## A ledger without its reading step nearly cost a real pairing

Found 2026-09-07, establishing the second camera pair.

`front 0.2.mp4` and `side 0.2.mp4` ARE a pair, at a constant frame offset of
**-78**, on three anchors read at a step of one frame, two of them 10.37 s
apart. **The first answer was the opposite, and it was wrong.**

### What the wrong answer looked like

Three frame-exact front catches were tested against the committed side ledger.
Every possible in-order correspondence was tried. The best spread by
**0.3603 s = 10.8 frames**, against 0.13 frames for the pair already
established. On that reading no constant offset fits, and the honest-failure
report was ready to write.

### Why it was wrong

Every event in that side ledger sits at a frame index divisible by eight:

```
248, 256, 296, 352, 416, 472, 512, 560, 640, 696, 752
```

**It was read at every eighth frame**, so each time carries 0.267 s of
quantisation. Worse than the quantisation, the reader recorded the frame where
the ball was clearly HELD rather than the frame where it met the hands, so the
times run LATE by up to ten frames. The ledger's 13.8611 s is not a catch at
all: the catch is at index 406, and by 416 she has the ball overhead and is
bringing it down.

Re-read at a step of one frame, the same three events give -78, -78, -78, and
the derived seconds drift -0.0042 s across 10.37 s — the same signature the
other pair shows, which is the two cameras' 11 microsecond period difference.

**The ledger carried no field recording its reading step.** Nothing in it said
that its times were eighth-frame samples, so they read as measurements. Every
row of the new pair table carries `readAtFrameStep`.

### And the unrecorded attempt was one frame from the answer

The previous pack recorded this pairing as UNKNOWN after an attempt that "gave
frame differences of 77 and 75", and the four frames it read were never written
down. The answer is 78. **That attempt was not wrong by much; it was
unrecorded, which is worse** — had its four indices been written down, the next
reader would have started one frame from the answer instead of starting again.
A number without its inputs cannot be corrected, only discarded.

### Two instruments failed on the way, and both are recorded

**The contact sheet could show frames from a different part of the clip.**
`contact_sheet` globbed its scratch directory and never emptied it, so a call
selecting 12 frames after a call that selected 18 produced a sheet of 18 tiles
whose last six were the PREVIOUS sheet's frames. The label had a fallback of
`-1`, and `times[-1]` is a real timestamp, so those tiles were captioned with
the last frame of the whole file: a real moment from elsewhere under a
plausible caption. A ledger read from that sheet would record events that are
not there. It now empties the scratch first and REFUSES when the file count and
the requested count disagree.

**One observation of mine was withdrawn mid-way.** I had noted that front 0.2's
ball looked like a tan medicine ball while side 0.2's was a cream netball, and
was ready to call them different drills on that. At full resolution `front
0.1.mp4` shows the same netball, sharp; front 0.2's only looks olive because it
is motion-blurred and she stands further from the camera. Same ball, same room,
same session. The colour was lighting and blur, and it was nearly evidence.

**A keypoint-based candidate detector does not work here, and is not proposed.**
Calibrated on the view whose ledger is known, local maxima of wrist height
above the hips recovered 4 of 10 events with 15 false candidates. In a self-toss
the hands go high to RELEASE as well as to catch, so height cannot separate
them. The frames have to be read.

### What corroborates the pairing, independently of the anchors

Both consumers run on it. The two views agree on the left elbow angle to a
median of **4.8 degrees** with a correlation of **+0.937**, on 782 frames; the
lift pairs 809 frames with a median residual of 16.9 mm. Under the mislabelled
pairing the same elbow comparison gave 21.2 degrees. A wrong pairing does not
produce agreement like that.

**The rule: a ledger records the step it was read at, on every row. A time
sampled every eighth frame is not a measurement of when something happened, and
without the step recorded nobody can tell the difference.**


## Two pairings, and neither could be re-derived from the tree

Found by review on 2026-09-07, in the pack that established both.

Both camera pairings were recorded as hand-typed anchors in `PAIRS`, and
nothing committed could reproduce either.

**Pair 1 was worse than pair 2.** `git grep 6e8f9fb2` — the sha256 of
`side 0.1.mp4` — found that hash only in prose, in the pair table and in one
test string. **No committed ledger held that recording's events at all.** The
8-of-8 fit that established the pairing had run on rows that were never
committed. "Commit the instrument with its numbers", and the instrument was
missing.

Pair 2 could not be re-derived either: its side rows live in
`event-ledger-0.1.json` at a reading step of eight, so `usable_for_a_fit`
refuses every one of them and the fit returns `None`.

### What was done

`event-ledger-pair1.json` holds `side 0.1.mp4`'s events, read from the frames
at a step of three over 5.0 to 25.3 s, with the two anchors re-read at a step
of one. They were read WITHOUT taking the offset off the pair table first: a
catch found where an offset predicted a catch is not evidence in a clip of
catches, which is how -0.7295 s was published. The two refined anchors came out
at side 269 against front 274 and side 600 against front 605 — **-5 twice,
11.03 s apart** — and the front view's overhead catch was refined from its
coarse 608 to 605 to match.

Two tests now load the COMMITTED ledgers and run the fit:

| pair | fits | best offset | expected | events | span |
|---|---|---|---|---|---|
| front 0.1 + side 0.1 | yes | -0.1750 s | -5 frames = -0.1666 | 2 | 11.03 s |
| front 0.2 + side 0.2 | yes | -2.6083 s | -78 frames = -2.5991 | 4 | 16.43 s |

Each is within one frame period of the table's frame offset. A third test
asserts that every pair in the table has a ledger named here, so the next
hand-typed pairing fails by name.

### One convention for a refined row, because there were two

`event-ledger-front-0.2.json` put the refined index in `frameIndex` with the
coarse one beside it. `event-ledger-0.1.json` did the opposite: coarse in
`frameIndex`, refined beside it. **Two ledgers of one project disagreed about
which field held the measurement**, so a reader taking `frameIndex` got the
fine value from one and the coarse value from the other. Now, everywhere:
`frameIndex` and `seconds` hold the FINEST reading, `readAtFrameStep` is its
step, and a coarser earlier reading keeps `coarseFrameIndex`, `coarseSeconds`,
`coarseAtFrameStep` and `framesFromRefined`.

### A ledger that described a file which does not exist

`event-ledger-0.2.json`'s side block carried `videoSha256: 253fa551605e` with
`frames: 990`. That hash names an 863-frame file; 990 is `6e8f9fb2fe03`'s
count. **A name was re-keyed to the new content's hash while its numbers stayed
with the old content** — the fault class of the day, committed by the person
writing the fix for it. It also still said the pair was "still to be
established" after it had been established at -78, and it held no events. It is
deleted; its one real finding, why run 2's front camera is hard to read, moved
into the ledger that supersedes it.

### Correcting a ledger moved six published figures, and that is the point

Refining four rows of `event-ledger-0.1.json` changed every number computed
from it:

| figure | was | is |
|---|---|---|
| pairing drift, shift 0 | -16.0 % | -15.6 % |
| pairing drift, shift 1 | -13.7 % | -13.2 % |
| pairing drift, shift 2 | -12.6 % | -13.2 % |
| null rate at one frame | 43.2 % | 46.8 % |
| null rate at a quarter second | 83.2 % | 85.2 % |
| the 0.267 s fit | 6 matched against a ceiling of 6 | 5 against 6 |

**A figure that does not move when its ledger is corrected was never computed
from that ledger.** The null-rate pair has now moved twice, and the two moves
are different in kind: 48/88 and 43/85 were wrong because nothing committed
produced them; 43.2/83.2 to 46.8/85.2 is the instrument working.

The last row cost a test. `test_a_count_EQUAL_to_the_chance_ceiling_does_not_fit`
used the real ledger because it happened to sit exactly on the ceiling, and
after refinement it does not. It builds its own fixture now, so the case cannot
disappear when data improves.

### And the writer was still telling readers the second pair had failed

`_sync_block`'s unmeasured note hard-coded one pair and then asserted that "the
remaining two files were tried and FAILED, two targeted anchors gave 77 and
75". Both halves went stale the moment pair 2 was established at -78 — those
ARE the two files. The note read the established pairs out of the table now.

# Video and footage

## The section cutter and its posters

Found 7 and 8 September 2026, building `spikes/video_section_cuts.py`: the
four sections of Erin's page cut from both camera views, and the poster frame
each one shows before it plays. Every fault below was found by an instrument
rather than by reading, and every one is a way a check agreed with the thing
it was checking.

### The PSNR floor was measured in one regime and spent in another

The first version asked whether each clip frame matched the source frame it
claims above a floor of 36 dB. That floor came from ONE section-view —
`catch-rep01` front, the section with the most motion — where a correct pair
scores 39.9 dB at worst and a wrong-by-one pair 33.2 at best. Re-measured
across all four sections and both views, 440 frames:

    section-view          n  right min  wrong-by-one max  separation
    catch-rep01 front    55      39.90             33.17       +6.73
    catch-rep01 side     55      39.86             35.27       +4.59
    release-rep09 front  56      39.91             35.62       +4.29
    release-rep09 side   56      40.86             40.10       +0.76
    hold-rep09 front     62      39.96             37.97       +2.00
    hold-rep09 side      62      40.91             40.63       +0.28
    ready-between front  47      39.95             38.01       +1.94
    ready-between side   47      41.21             41.50       -0.29

On five of the eight a wrong-by-one frame passes 36 dB. On `ready-between`
side the best WRONG frame beats the worst RIGHT frame, so the populations
overlap and no absolute floor can separate them there at all. That section is
her stance between repetitions, nearly still, on the softer camera: when
nothing moves, the neighbour frame is nearly the frame.

**The criterion is relative now.** Frame k must be closer to source frame
`start+k` than to both neighbours — three numbers measured the same way in the
same regime, needing no constant calibrated anywhere. The same 440 frames
support it, and the smallest winning margin is 1.14 dB, on `ready-between`
side. `RELATIVE_MARGIN_DB` is 1.0 and `MEASURED_MIN_MARGIN_DB` records 1.14,
which a test reads back.

This is the same fault as `footHeightGapCm` and the arm constants: a number
taken under one condition and spent under another. The condition here is how
much the picture moves, and it is exactly what varies between sections.

### Agreement with another instrument is not correctness

The clips reproduced an earlier instrument's cuts exactly: eight clips, 440
frames, zero differing. That was presented as proof they were right. It is
not. Both tools took the same windows and the same frame offset, so a wrongly
mapped index would have produced the same 440 agreeing rows.

**What answers the question is a comparison against the SOURCE, through a
different mechanism.** The cut uses `trim=start_frame:end_frame`, whose end is
exclusive. The check selects source frames with `select='between(n,a,b)'`,
inclusive at both ends, sharing no arithmetic with it. Checking trim with trim
agrees with itself.

And a shifted window keeps its frame count, so every count assertion passes
while every frame is wrong. Only a test that NAMES the frame sees it: frame 0
against `start` and against `start - 1`, the last frame against `end` and
against `end + 1`.

### The side clip was guarded only through a file outside git

Every source check cut its own clip, so the side path of `cut_section` was
never driven. The one test that saw a side clip compared it against an
artefact at an absolute, gitignored path present on one machine, and skipped
everywhere else. Three mutations survived on any other machine: the side clip
cut from the FRONT file, the side window shifted by one, and the output frame
rate changed from 30 to 25.

**Fixed by moving the comparison into the repository.** 440 per-frame sha256
digests of that earlier instrument's clips are committed under
`spikes/video-annotations/section-cuts/pair1/`, compared element by element,
with no `skipTest` inside the loop. `PROVENANCE.md` beside them names the
eight clips by their own file sha256 and states what the comparison proves:
reproduction, not correctness.

### The poster pins are decoded pixels, and they are tied to an ffmpeg build

Each section shows one still before it plays. The eight already on Erin's page
were rendered from the recordings at `-q:v 3`; rendering the same frames from
the tool at the same setting gives byte-identical files, both views, four
sections, measured before the setting was written down.

**The pinned digest is of the DECODED pixels, not the file.** A different
quality setting changes every byte while showing the same picture, and the
wrong frame re-encoded at the same setting changes nothing a file hash would
notice. The manifest carries both hashes, because a swapped file and a wrong
instant are different questions.

**The poster pins can fail on the right frame if ffmpeg changes.** They were
taken on `ffmpeg 8.1.2-full_build-www.gyan.dev`. H.264 decoding is exact, so
the CLIP digests are a property of the recordings; JPEG decoding is not
normatively bit-exact and the mjpeg encoder's transform can differ between
builds. A different build could therefore fail
`test_every_poster_matches_the_digest_committed_for_it` on the correct frame,
with a message saying the poster shows a different frame. The build is
recorded beside the poster table so that is diagnosable in one look.

### A refusal that had already written a file

`posters()` checked each index inside the render loop, so an index outside the
side recording refused only after the FRONT poster was on disk. Measured: with
front index 4, which maps to side index −1 at this pair's offset of −5,

    refused: the side poster index -1 is outside that recording
    left behind: ['refusal-probe-front-poster.jpg']

A section half written, and a manifest that never mentions it because the
manifest is written last. This was the second time in two days: `proof_sheet`
created its scratch directory before judging its argument. **A refusal that
still writes to disk is not a refusal.** Both indices are checked before
either render now, and a test asserts the output directory is empty
afterwards.

### A reason keyed by section name rather than bound to its subject

Each section carries a sentence saying why it exists, and each poster a
sentence saying why that frame is the one. `main` looked them up by section
NAME and passed them whatever window or poster the caller gave. Measured on
the real command line:

    --section catch-rep01=258:262        posterFrontIndex None, and the
                                         sentence written for frame 276
    --section catch-rep01=258:262@260    poster 260, and the same sentence,
                                         which describes frame 276
    --section other=258:262@260          no sentences

A reason for a poster that does not exist, and a reason describing a frame
nobody cut. Both read in the manifest as though somebody had chosen them.
`reasons_for()` binds the section's reason to the window and the poster's
reason to the poster, and returns an empty string otherwise.

### A mutation driver that would have reported a survivor it never ran

Two mutations quote a loop header plus the line below it, because the header
alone occurs three times in the file. Moving the poster index check out of the
render loop leaves two loops under the same header, one checking and one
drawing, and the line below moved with it. Measured on the patched text before
the change was committed:

    OLD anchor after the patch: 1 occurrence  (the CHECK loop)
    NEW anchor after the patch: 1 occurrence  (the RENDER loop)
    the bare loop header alone: 3 occurrences

An un-re-aimed driver would not have complained. It would have matched once,
applied cleanly, mutated the bounds check instead of the render, and reported
a completed run — and that experiment passes every poster test, so it would
have come back a SURVIVOR and sent somebody hunting a hole that does not
exist.

The day before, a reviewer's mutation stopped applying to the same file
because new code repeated the shape it targeted. That one matched TWICE and
the driver refused: loud, and safe. **A count of two is a safety net. A count
of one after a refactor is not a vindication; it is only a failure to
complain.**

## The anchor sheets

Found 8 September 2026, building `spikes/video_anchor_sheets.py`: one sheet per
moment, the front view above the side view at the same mapped instant, seven
columns two frames apart, so a person can read a camera pairing off the
pictures. A frame offset is a claim about two recordings and the arithmetic
that produces it agrees with itself whatever it is given; a human eye on the
frames is the only check that shares nothing with the fit.

### Three kinds of evidence, and one that must never be drawn

`PAIRS` records three kinds of event and the instrument that drew the first
sheets treated them as one.

- **anchors** — the events the offset was FITTED to. A ball meeting hands,
  where the contact frame is not a judgement call. Pair 1: front 274 and 605.
  Pair 2: front 324 and 635.
- **checks** — events the fitted offset must also explain afterwards. Pair 1:
  front 534. Pair 2: front 484. An event that produced the answer and an event
  that agreed with it later are different evidence, and a sheet that names them
  alike invites a reader to weigh them alike.
- **setAside** — events deliberately not used, each with its reason recorded.
  Pair 1's first clap reads four frames apart where the offset says five,
  because "nearly together" and "together" are one frame apart in both views.
  Pair 2's one-handed catch gives −78 or −77 depending on which frame is called
  contact. **Never drawn.** A sheet is what a reader trusts, and putting a
  knowingly ambiguous event on one asks that reader to resolve by eye the
  ambiguity the entry exists to record.

The scratch instrument drew 324, 484 and 635 and called all three anchors. The
sheets are the same pictures; the names are now `anchor-324`, `check-484`,
`anchor-635`.

A test asserts the table's own consistency — `otherIndex == referenceIndex +
offset` for every anchor and check of both pairs — and a companion test
requires at least one set-aside row to DISAGREE with the offset. If every
set-aside row ever agrees exactly, somebody has resolved an ambiguity by
picking the frame that suits the answer.

### Two kinds of pin, worth different things

The sheets are composed the way the confirmed ones were: 7 × 2 tiles of
202 × 360, built by ffmpeg (`scale=-2:360`, the label burned in by `drawtext`,
`vstack` then `hstack`). That is not this repository's other sheet layout, and
the divergence is deliberate: reproducing the confirmed composition exactly is
what makes those sheets pinnable at all. All 42 tiles of pair 2's three sheets
reproduce byte for byte, and so do the whole sheets.

84 tile digests are committed, cropped out of a FINISHED sheet so the identical
measurement can be taken on a sheet this tool did not draw. Hashing an
intermediate file would have pinned something only this pipeline produces.

**The two pins do not prove the same thing.**

- **pair 2** — the sheets came from an instrument outside this repository, so
  matching them is two instruments agreeing.
- **pair 1** — the sheets came from THIS tool, so matching them is this tool
  agreeing with itself: a change detector. It catches a change to the pipeline,
  the font, the scaler or the frames, and it catches nothing about whether −5 is
  right.

What makes −5 right is a person reading the pictures, and the reading is
recorded column by column: on `anchor-274` the ball reaches her hands in column
four of both rows (front 274, side 269) with the gap still there in column
three; `anchor-605` the same (front 605 with the ball above at 603, side 600
with it above at 598); `check-534` the hands meeting in column four (front 534,
side 529) and apart in column three. Three moments about 11 seconds apart.

The pins depend on more than the frames, because the label is rendered into the
picture: ffmpeg `8.1.2-full_build-www.gyan.dev` and
`C:/Windows/Fonts/arialbd.ttf`, 989780 bytes, sha256 `e8f4e3ba…7a43f5`. The
tool refuses by name when that font is absent rather than letting ffmpeg fall
back to another face, which would fail all 84 pinned tiles with a message about
the pictures — the wrong place to go looking.

### What the pins cover, and one sentence that was false

A tile is 202 px wide and `FRONT idx 268  t=8.933s` at fontsize 20 does not
fit, so the FRONT row's seconds read truncated as `t=8.9`. **The side row
fits**: `SIDE idx 263  t=8.763s` is one character shorter.

An earlier version of this record said every tile was truncated. That was
wrong, and a mutation disproved it: cutting the front label alone failed on
three of the six sheets rather than all six.

So a tile digest pins the frame, the whole side label, and the part of the front
label inside 202 px — which includes the entire index. It does NOT pin the front
row's seconds beyond that edge: those characters are never drawn. A pairing is
made of indices, every index is inside the edge, and the manifest carries the
seconds in full to four decimals. Fixing the overrun would re-pin all 84 tiles
against sheets nobody has read, so it is recorded instead.

### The only check that looks at a picture

Every other guard is an index checked against an index, or a digest pinned
against a confirmed sheet — and a pin covers only the pairs that have been
pinned. A third pair would have arithmetic and nothing else.

`centre_tile_alignment` crops the centre tile below the label band and compares
it against the source frame and both neighbours. **The source frame is resized
by a different resampler**: the tile is ffmpeg's `scale=-2:360`, the frame it is
compared with is decoded and resized by PIL's LANCZOS. Checking swscale with
swscale would agree with itself.

Measured over every sheet of both pairs, twelve centre tiles:

    pair   sheet        view    right      -1      +1  margin
    pair1  anchor-274   front   47.89   23.14   26.82   21.07
    pair1  anchor-274   side    50.04   30.74   30.19   19.30
    pair1  anchor-605   front   47.98   23.22   24.81   23.16
    pair1  anchor-605   side    50.14   31.73   32.79   17.36
    pair1  check-534    front   47.95   26.84   26.86   21.09
    pair1  check-534    side    49.89   33.66   33.04   16.23
    pair2  anchor-324   front   49.60   29.41   29.92   19.68
    pair2  anchor-324   side    49.97   25.99   26.41   23.56
    pair2  anchor-635   front   49.82   30.11   33.50   16.31
    pair2  anchor-635   side    49.89   26.81   27.39   22.51
    pair2  check-484    front   49.73   29.55   33.51   16.22
    pair2  check-484    side    50.30   30.51   31.34   18.96

The criterion is relative, not a floor: the right frame must beat both
neighbours. `TILE_MARGIN_DB` is 10.0, pinned above zero and below the measured
minimum; `MEASURED_MIN_TILE_MARGIN_DB` records 16.22 and a test reads it back.

**The whole-tile figure is 20.9 dB and means nothing.** The tile carries a
burned-in label and the source frame does not. Below the 40-row band the same
comparison is 49.6. A reader who meets 20.9 without that sentence concludes the
tile shows the wrong picture.

### A boundary test that refused for the other view's reason

`check_span` must refuse a sheet that runs off either recording. The first
tests refused at centre 3 and at 944 and accepted at 324, which leaves the
boundaries themselves unmeasured: `first < 0` could have been `first < -1`,
`last >= frames` could have been `last > frames`, and the side recording's far
edge was never approached. Three mutations of exactly that shape survived.

The replacement put both views on their edge at once — and **under a single
offset the two views cannot both sit at a boundary**, so two cases refused for
the other view's reason. That is precisely what a front-only check would do,
which is the fault the test exists to catch: it would have passed against the
very bug it was written for. Each of the eight cases now isolates one edge by
choosing the offset that gives the other view room, and the fixtures carry that
explanation.

### A guard made unfalsifiable by a correctness fix

`centreSideIndex` is `centre + offset`. A mutation replacing it with the
table's own `otherIndex` survived — after, and BECAUSE OF, a fix three lines
away that proved the table consistent (`otherIndex == referenceIndex + offset`
on every row). Once that holds, the two expressions produce identical numbers
everywhere the table can reach.

Neither change was wrong. Together they removed the only case that could
distinguish the two behaviours, and turned a live mutation into an equivalent
mutant.

The case had to be BUILT: `anchor_sheet` is handed a fabricated moment whose
`otherIndex` is 40 out, and the test asserts the manifest field follows the
offset rather than the lie, that the drawn side row does too, and that the tiles
still match the pins. This is the repository's existing rule about a guard whose
case must exist in data, arriving from the opposite direction.

### The machine the tests ran on was not the machine that checks them

Every check on this machine was green and three went red on the hosted runner,
which is Linux and has no `C:/Windows/Fonts/arialbd.ttf`. `Ran 972 tests,
FAILED (failures=2, errors=1, skipped=179)`:

- `test_the_font_this_machine_pinned_with_is_present` called `check_font()`
  unguarded, which raises `SystemExit` where the file is absent. That is an
  ERROR, and an error on a runner is that runner saying a test meant to run and
  could not. It skips by name now, beside the tests gated on the recordings.
- an import-hygiene guard counts errors across the suite, so the one above made
  it fail too. One ungated test took a second check down with it.
- `main()` called `check_font()` BEFORE `resolve()`, so an unknown pair was
  refused with a message about a Windows font path rather than the list of
  known pairs. **The same wrong argument gave a different answer depending on
  where it ran.** The pair is resolved first now.

The font gate is beside the recordings gate, and a test loads every other test
in the module with the font patched away and requires ZERO errors: a pass or a
skip that names its reason. Measured that way, `ran=34 errors=0 failures=0
skipped=11`, every skip naming the font or the recordings.

## The hand at release

The band of hand speed the movement lane cites, the shoot requirement that came
out of the same morning, and the two withdrawals it took to get there. Branch
`lane/video-hand-speed`, off main `1c3d9d7`. The band itself never moved: the
same twelve rows, 2.5 to 5.4 m/s, survived an independent review that
re-derived every one of them with its own code.

### A range spent as a sigma, and a window that was not still

The re-derivation disagreed with the old note about the PRICE — it asked for 29
to 49 px where the note asked for about a hundred — and the re-derivation was
wrong, in the lax direction, twice over.

- **The first figure compared a fast movement against a slow statistic.** A
  flick lasting 100 ms is three frames at 30 fps, so what it must clear is the
  frame-to-frame scatter, not a swing accumulated over a 29-frame window.
- **The second figure was built on a range wearing a sigma's clothes.** Redone,
  the requirement came out at 88 / 73 / 41 / 69 px from a landmark error of
  `e = 3.0 px`, and that `e` was the RANGE of the angle over the same window,
  max minus min, put into a formula that wants a one-sigma value. For 29
  samples that inflates it about fourfold. Measured as a per-frame quantity the
  same window gives 0.30 px and the pack's own searched null gives 0.14.
- **The window was not still, and "still" is a claim about the data.** The
  forearm's pixel length grows 39 per cent inside it, because she is raising
  the arm. The one window this pack proved still by its own search changes by
  3 per cent.
- **The cross-check compared two different statistics and called them one.**
  "245 deg/s predicted against the 197 measured — the same quantity, from two
  directions" set a one-sigma prediction against a measured MAXIMUM.

**Both figures are withdrawn.** The instruction rests on the 2026-09-02
MEASURED floor and nothing else: median 40, 90th 104, maximum 197 deg/s on a
30 px lever, and the floor scales with the lever. Three times the maximum needs
71 px for a 25 degree flick in 100 ms and 59 px for 15 degrees in 50 ms. The
hundred pixels asked for on 2026-09-02 sits above both and stands.

This is another instance of the repository's oldest fault class: a quantity
measured in one regime and spent in another. **Name the statistic before it
goes into a formula** — a range, a standard deviation, a 90th, a maximum — and
check the formula wants that one. A range grows with the sample count; a sigma
does not.

### A guard that measured the right thing and gated nothing

`check_near_arm` measured which arm the camera sees. Nothing in the measurement
path called it: `speed_rows`, `search_null` and `hand_centre` all took the
`NEAR_ARM` constant, and the only caller was a test, at two windows of twelve.
A recording shot from the other side would have been measured on the OCCLUDED
arm, and that failure is silent — the model reports an occluded wrist smoothly,
as a guess, so the trace looks like a clean slow release.

Writing the gate's test found a second fault: the refusal read a `name` key the
recordings do not carry, so the path raised `KeyError` instead of refusing.
**That is proof it had never run once.** The lane and an independent review
found this defect separately, within the same hour.

### A guard need not skip to guard nothing

Three levers in the same module RAN, on every row, and changed no result.

- The null search ignored frames where the wrist tracks below 0.7, and the
  quietest window passed the filter anyway.
- A speed was divided by the file's measured 30.012 fps, where a nominal 30.0
  is 0.04 per cent out and invisible at two decimals.
- A sentence claimed per-frame timing where the code used one mean rate, and
  the intervals vary by 0.3 per cent.

Each is inert on THIS footage and each would matter on a recording that tracks
worse or runs at another rate. **The signature is a mutation that deletes the
lever and survives.** The answer is the same as for a guard that skips: build
the case. The visibility filter now has a stretch with frozen landmarks and a
half-visible wrist, which is the quietest window in the file and which the
filter must refuse — and a second test asserting the filter changes nothing on
the real recordings, so a later reader knows the built case is not decoration.

### A band without its inputs cannot be checked

`BAND.md` named no hash, no frame rate and no model. The module defined
`sha256` and never called it, keyed the keypoint files BY NAME, and never read
the `videoSha256` those files carry — on two recordings that swapped names at
source on 2026-09-07 and record the swap in their own `renamedFrom` block.
A filename does not say which recording this is.

`load` now refuses unless the file hashes to what is pinned, describes the
video that is pinned, and carries the athlete figures the module was calibrated
on. The mutation that swaps the two side files by name now fails with that
refusal, naming both hashes, instead of failing because the numbers happen to
differ. Only the two side recordings are pinned, because only they are
measured; a front recording is refused with "no hash is recorded", which is
correct and is not a defect.

### A mutation string that matches nothing runs no experiment

One mutation in this pack reported no match, because the document sentence it
targeted wraps mid-phrase. A driver that scored it as a kill would have counted
an experiment that never ran. Two rules follow, and the second is the one that
bites later: **require every mutation string to match EXACTLY once**, and after
any edit to the files a mutation set targets, RE-RUN the set — a string that
stops matching, or starts matching twice, is running a different experiment
under the old name.

The same wrapping caught a test: a document sentence cannot be checked against
an instrument when the sentence wraps between the number and its unit. The
figures moved into a table, where each row names the window or the statistic it
belongs to and a test pairs them by that name rather than by row order.
