# Engineering rules

These rules are in force. They were copied unchanged from
`docs/KNOWN_ISSUES.md` at `b48512a`, where each came out of a finding. A
subsection is shown under the title of the section it came from.

# Movement

## Centimetres are stored in a field called degrees

### A verification trap this pack walked into, and the rule that follows

**A MUTATION RUN CAN TEST THE PREVIOUS MUTATION'S BYTECODE.** This lane ran a
loop that set the band floor to four values in turn and reported the guards
each one failed. One reading was wrong and could not be reproduced; it was
withdrawn from the pack for that reason, and the review then explained it.

CPython validates a `.pyc` by the source's **integer-second mtime and byte
size**. Two values of the same length — `1.0` and `3.5` — give sources of
identical size, so a write landing in the same second as the previous one
reuses the previous bytecode. The review proved it deterministically: compile
the cache from the 1.0 source, write 3.5, set the source mtime to the cache's
second, and the run reports the 1.0 failures; delete the cache and the same
source reports its own four.

**Every mutation loop in this repository that edits a constant to a
same-length value is exposed.** The rule is `python -B`, or clear
`__pycache__` between edits. This is not a defect in any pack; it is a defect
in how packs are verified, which is worse, because it silently returns the
previous answer.

## A height measure exists now: `ballHeightCm`, above the court

### Three ways an instrument reported something it had not measured

All three were found by this lane during the two height packs, and all three
have the same shape as the bytecode trap recorded earlier in this file: **the
run returns an answer, and the answer is not about the thing under test.** They
are recorded as verification rules because a defect in how work is checked
outlives any defect in the work.

**A MUTATION THAT NEVER APPLIED, REPORTED AS A GUARD THAT HELD.** A loop made
the loader's unit refusal unreachable and the guards passed, which reads as
"this refusal is not mutation-proven". The replacement string carried eight
spaces of indentation where the file has four, so `str.replace` matched nothing
and the tests ran on untouched code. **The rule: a mutation asserts the
substitution CHANGED the file before the run.** Re-run properly, the same
mutation fails three guards. This is the bytecode trap's cousin — there the
edit reached the file and not the run; here it reached neither.

**A RESTORE CHECK THAT FAILED FOR EVERY CASE, WHICH IS NOT A RESULT.** The same
loop verified its restores with a shell parameter expansion that split each
path at the first colon — the Windows drive letter — so it compared `C` against
nothing and reported MISMATCH for all three files whether or not they were
restored. **The rule: a check that fails for every case is a broken check.** A
verifier that never passes has not found three faults; it has one of its own.

**A SWEEP THAT REPORTED ITS OWN LEVER INERT.** Found while folding this review.
The sweep script points the movement loaders at a temporary copy, and a rewrite
set `ball_track.MOVEMENT_DIR` but not `technique.MOVEMENT_DIR`. `technique.py`
does `from ball_track import MOVEMENT_DIR`, which binds the VALUE at import, so
the technique file — where this sweep's lever lives — was still read from the
tracked tree. Every one of the ten points came back byte-identical, and the
honest reading of that output is "the lift carry does nothing to the ball
height", which is false. **The rule: an instrument that reports no movement has
not measured no movement; it has usually failed to reach what it was pointed
at.** `sweep_ball_height.py` now refuses to print a sweep whose span is under
1 cm and says which modules to check.

## The environment must be activated, not merely located

**Reproduced, and it is not a defect in the code.** Running the suite by
invoking the environment's interpreter directly fails:

```
cd spikes
./.pixi/envs/default/python.exe -m unittest discover -s . -p "test_*.py"
```

That path is the junction into `.assets/pixi-env`. Reaching the interpreter by
either route fails the same way; what matters is that it is named rather than
activated.

It dies at `test_grip.AxesTest.test_the_frame_is_orthonormal`, exit code 127,
no traceback and no summary line. The same command through `pixi run` passes
all 245 tests from the same directory, with the same `.pixi` present and the
same code.

Exit 127 with no Python traceback means the process died below Python rather
than raising, which points at a native library that could not be loaded.
`pixi run` sets up the environment's search paths; naming the executable does
not. That last sentence is inference from the exit code and the absence of a
traceback, not something measured directly.

**What is exonerated.** Two earlier hypotheses are dead, both by measurement
rather than argument. The assets are not the cause: an independent review
reproduced the crash with `spikes/mhr-assets` junctioned and verified, and
sixty-odd solver-dependent tests including character loads passed first.
Missing `.pixi` state is not the cause either: it reproduces here with the
`.pixi` junction present.

**What is unresolved.** Which native library, and why those two modules rather
than an earlier one. `test_grip` and `test_multi_camera_fit` are where it bites
because they are the first to make the call that needs it, not necessarily
because they are special.

**Mitigated rather than left as folklore.** `spikes/pixi.toml` had an empty
`[tasks]` section. It now defines `test`, `library`, `limits` and `proof`, so
the correct invocation is a file that can be run and checked rather than
knowledge someone has to be told:

```
cd spikes && pixi run test
```


## A comment is not a test

Three defects this month were a comment describing the right behaviour sitting
directly above code that did the opposite:

- the bisection's "never inside";
- `curved_directions` and its first bone;
- `possession_solve`'s "only the hand that is taking the ball goes out to meet
  it", above a line that sent both hands to wait.

The third was the largest single-frame step in the library: 19.9 cm of wrist
travel in the contact frame and a 48.1 degree arm swing behind it.

Every one was found by an instrument reading output. None was found by anyone
reading the code, including the people who read that code closely enough to
change the lines around it. A comment states intent, and intent is not
enforced by anything.

The practical consequence for this project: when a comment states a behaviour,
that is a candidate for a test, not evidence that the behaviour happens.

## The overhead pull-back has no boundary, and the checkpoint was right to go

### What this adds to the sweep method

`1fed5a1` established that method and already warns that **a coarse sweep can
imitate a basin**, having caught its own follow-through sweep doing exactly
that. Two things go beside it:

- **A coarse sweep can also imitate a single BOUNDARY where there are many.**
  Three points cannot establish an edge. What lies between the samples is not
  known, and here it alternates.
- **A sweep must watch joints it is not grading.** The earliest and one of the
  largest discontinuities here is invisible to every measure the checkpoint
  reads.
- **A suspected crossing must be RESAMPLED IN A NARROW WINDOW, and then judged
  on its JOINTS.** Refining the spacing over a wide window only samples the
  same field more finely. Narrowing the window resolves one edge; whether that
  edge is a basin is answered by whether the pose moves continuously across
  it.

**A DIFFERENT KEY ON THIS SAME DRILL BEHAVES DIFFERENTLY**, which is why a
sweep must name its key as well as its spacing. Under the lateral-asymmetry
sweep used for the left-right knee guard, `netball_overhead_pass` is piecewise
continuous with a single crossing. Under the pull-back key it alternates. One
drill, two inputs, two answers.

**THE SOLVE IS NOT NOISY WITHIN A BUILD.** Two adjacent inputs 1.5 cm apart
that land in opposite families each reproduce exactly across three runs, to
every decimal place. The alternation is a property of the solver's dependence
on its input and not of the run.

**IT IS NOT STABLE ACROSS BUILDS, AND THAT CAUGHT THIS ENTRY OUT.** The same
input gave mirrored knees on two different tips while this branch was open —
57.42 and 62.38 on one, 62.32 and 57.43 on the other. **So every reading here
names its build, and a figure quoted without one is not reproducible.**

**AN INPUT STEP OF 0.00005 cm DOES FLIP IT, AT SOME POINTS.** The review found
that on `netball_overhead_pass`, sweeping the technique's `afterContact` `step`
key by ±1e-6 torso lengths, read at frame 55: at 20.20 cm and 26.42 cm of
pull-back the left and right answers EXCHANGE on all four measures — shoulders
116.86 / 108.17 becoming 108.17 / 116.86, knees 54.47 / 59.36 becoming 59.36 /
54.47 — and at 6.22 cm and 7.77 cm neither perturbation exchanges anything.
**So the flip is POINT-DEPENDENT**, which is why an earlier probe here found
none: it read frame 0 at points that do not flip.

**THE CROSS-PROCESS CAVEAT IS CLOSED.** That result was measured with the two
solves in two processes, so process noise had not been separated from input
sensitivity. **It has now: the same input solved in three separate processes
returns 108.1500, 116.8400, 59.3600, 54.4700 every time, identical to four
decimal places.** The solver is deterministic across processes, so two inputs
0.00005 cm apart returning mirrored answers is the input and not the run.

**IT IS ALSO BUILD-DEPENDENT.** At 20.20 cm on THIS build, ±1e-6 does not flip
— all three readings agree to 0.01 degrees. The review's flip was on `36de191`.
So a point that flips on one build need not flip on another, which is the same
across-build instability recorded above and one more reason every figure here
names its build.

## The alignment ranked a sync clap above every real catch

### The instruction it produced

Section 18 of `docs/VIDEO_CAPTURE_FINDINGS.md`: the clap must be **in frame for
both cameras**, not merely audible, and both files must be opened on the day to
confirm that each one heard and saw it. A clap that only one camera records is
worth nothing, and this session spent a morning proving that the hard way.


# Video and footage

## The section cutter and its posters

### The rules that came out of it

1. Measure a threshold across every case it will be spent on, not one.
2. Prefer a comparison between numbers measured in the same regime to a
   constant calibrated in one of them.
3. When a check agrees with another instrument, ask what the two share. If
   they share inputs or arithmetic, it is a reproduction test; label it, and
   build the one that does not share.
4. Select the thing under test by one mechanism and the thing you check it
   against by a different one.
5. A shifted window keeps its frame count. Name the frame.
6. A guard that reads an artefact outside git protects one machine.
7. Pin what a thing SHOWS, not the bytes it is stored in, and record the tool
   version when the decoder is not bit-exact.
8. A refusal must write nothing. Check every argument before the first write.
9. Bind a description to what it describes, never to a name.
10. Re-run a mutation set on the change it was written against, and require
    each string to match exactly once. A string that still matches once after
    a refactor may be matching the wrong place.
11. Ask what a mutation set CANNOT reach; that is where the untested line is.
12. An exit code of 1 is not a failing test. Read the summary line and the
    named tests.

## The anchor sheets

### The rules that came out of it

1. Name the kinds of evidence apart. An event that produced an answer and an
   event that agreed with it later are not the same thing.
2. An ambiguity recorded as unresolved must not appear on the artefact a person
   reads to resolve things.
3. Require at least one recorded exception to keep disagreeing. When every
   exception agrees, somebody has picked the frame that suits the answer.
4. Take the composition of the artefact somebody confirmed, even when a nicer
   one exists, if that is what makes the confirmation reusable.
5. Say what a pin is worth. Matching another instrument is agreement; matching
   yourself is a change detector; a person reading the picture is the evidence.
6. Record what a pin does NOT cover, in the same place as what it does.
7. Compare a picture against its source through a DIFFERENT implementation, and
   state which comparison regions are meaningless and why.
8. Measure a threshold on every case it will be spent on, and record the
   measured minimum where a test reads it back.
9. Test a boundary AT the boundary, one step either side, and make each case
   isolate the thing it names — a case that fails for the neighbouring reason
   passes against the bug it was written for.
10. After a fix that makes data provably consistent, re-run the mutations that
    depended on it being possibly inconsistent. A correctness fix can make a
    guard unfalsifiable; build the case the data can no longer supply.
11. The hosted runner is a different machine. A test that asserts a machine
    property — a font, a recording, a solver — SKIPS BY NAME where the property
    is absent, and a refusal that depends on the machine comes after the
    refusals that do not.

## The hand at release

### The finding was already in main, and nobody looked

Marius asked on 2026-09-08 whether the footage could show the athlete's wrist
flick. The answer had been in `docs/VIDEO_CAPTURE_FINDINGS.md` since
`bde122e` of 2026-09-02, under a heading that names the question, written after
he asked the SAME question six days earlier. Neither the lane nor the
orchestrator searched. One `git grep` would have found it.

**The rule: before measuring, grep `docs/` and this file for the topic.** A
finding that already exists in main is re-derived only to CHECK it, and the two
readings are then reconciled in ONE place, with the stricter published and the
withdrawn one named. A number living in two documents is a number that will
disagree with itself, which is exactly what happened next.

### The rules that came out of it

1. Grep `docs/` and this file before measuring. Re-derive a merged finding only
   to check it, then reconcile both readings in one place.
2. Name the statistic before it enters a formula. A range is not a sigma, and a
   maximum is not a prediction.
3. "Still" is a claim about the data. Measure it — the forearm's own pixel
   length here — rather than reading it off a frame strip.
4. When two readings disagree, publish the STRICTER and name the withdrawn one
   with its reason. Being too lax is the dangerous direction: it sends a shoot
   away with footage that still cannot answer.
5. A guard that only a test calls is advice. Call it from the measurement path
   and make it refuse.
6. A guard that runs and changes nothing is inert. Its signature is a deletion
   mutation that survives; build the case the data does not supply, and keep a
   test saying the lever is inert on the real data.
7. Publish a number with its inputs, hashed. Resolve artefacts by hash, refuse
   on a mismatch, and put the hashes in the document a lane reads.
8. Read a figure the file carries rather than typing it, and let the typed
   value be the CHECK the file must agree with.
9. Require every mutation string to match exactly once, and re-run a mutation
   set after any edit to the files it targets.
10. Give a document's figures a table, not a sentence. A wrapped sentence
    cannot be checked, and a test that cannot match its target passes.
