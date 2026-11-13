# What the Tactics board plays, and what Movement can deliver next

Main's goal (13 November 2026): count what the Tactics board plays of the 12
Movement techniques, and deliver what is missing. This file is steps 1 and 2:
the count and the gap list. It changes no code.

Read on Tactics `main` at `e61a539` and on Movement `main` at `0cbc254`, on
13 November 2026.

## How a board plays a technique

A board plays a pass or a catch through the rigged athlete. The pass card asks
`athletePassTechniques` (`src/core/athleteMotion.ts`), which reads
`src/data/athlete-motions.json`: the shared athlete at revision 9, whose source
hash is `2b48758b`, the same athlete as the local Studio.

Each rig clip names its graded record in `gradedClip`: a pose clip in
`public/figures/clips.json`, its graded flag and the Movement build it came
from. Marius ruled that the pose clip is the graded record (spec 3, decision
12.1), and that the board may play a technique with no graded record if it
says so (spec 3, decision C-6). The pass card marks such a technique "not
graded".

## The count

All 12 rig clips come from Movement build `b4f7074` (11 September 2026,
208 commits before `main` at `0cbc254`).

| Technique | Pose clip (graded record) | Graded | Pose clip build |
|---|---|---|---|
| `netball_chest_pass` | `pass.netball.chest-pass` | yes | `1624678` |
| `netball_double_foot_landing` | `land.netball.double-foot` | yes | `0353b76` |
| `netball_hooks_outside_hand` | `catch.netball.hooks-outside-hand` | yes | `0353b76` |
| `netball_two_hand_snatch_pull_in` | `catch.netball.two-hand-snatch` | yes | `0353b76` |
| `netball_deflect_high` | `block.netball.deflect-high` | no | `0353b76` |
| `netball_hooks_jump_pull_in` | `catch.netball.hooks-jump` | no | `0353b76` |
| `netball_one_hand_snatch_to_other_hand` | `catch.netball.one-hand-snatch` | no | `0353b76` |
| `netball_two_hand_catch_chest` | `catch.netball.two-hand-chest` | no | `0353b76` |
| `netball_two_hand_snatch_straight_back` | `catch.netball.two-hand-snatch-back` | no | `0353b76` |
| `netball_bounce_pass` | **none** | not graded | - |
| `netball_one_hand_high_pass` | **none** | not graded | - |
| `netball_overhead_pass` | **none** | not graded | - |

So the board plays all 12. Four have a graded record, five have a pose clip
that is not graded, and three have no pose clip at all. Both pose-clip builds,
`0353b76` and `1624678`, are from 14 September, 181 and 183 commits before
`main`.

## The gap

| Technique | What is missing | What it needs |
|---|---|---|
| Bounce pass | A pose clip | Movement exports it from `main`: `spikes/clip_geometry.py` has its class. The clip has no bounce in it: the release at frame 76 of 96 leaves 0.3167 s of flight, 0.267 s short of the court (`CLASSES` comment). Coach item 12 asks whether that is useful. |
| Overhead pass | A pose clip | Movement exports it from `main`. Its class is in the table, and `overhead-pass` is in Tactics' release kinds since 14 September. |
| One-hand high pass | A pose clip, and a name | Movement exports it from `main` as `one-hand-high-pass`, which is not in Tactics' release kinds. Tactics maps `shoulder-pass` onto it (`athleteMotion.ts:104`), and Movement refuses that mapping on purpose: the drill releases 59.31 cm above the shoulder. Spec 1 decision 12.4 drops "shoulder pass" unless the coach uses it (coach item B). |
| The five not graded | A graded record | Their pose clips do not pass their checkpoints. A new export from `main` would show whether 181 commits of fixes changed that. |
| All 12 rig clips | A newer build | They are from `b4f7074`. A new athlete export would carry the fixes since. |

## What changes the delivery

**The mechanical release is not on `main`.** Main's branch
`lane/mechanical-release` (`c98edd1`) launches the ball at the speed of the
hands and retimes the release. That changes every pass clip: the chest,
bounce, overhead and one-hand high passes. Pass clips exported from `main`
today would need a second export after it lands.

## Main's answers, and the export (13 November 2026)

Main answered (lane board, Models/models-tactics-gap-to-main): export the
three passes now and again after the release lands; the one-hand high pass
takes the manual's name (spec 1, decision 12.4); re-export the five that are
not graded, report how far each moved, and do not re-export a graded clip.

`spikes/export_tactics_clip.py` ran through pixi on `b9deaeb` with a clean
tree (the head was the same before and after the run). It wrote 8 clips:

| Clip | Frames | Hit | Graded | Moved since 14 September |
|---|---:|---:|---|---|
| `pass.netball.bounce-pass` | 96 | 0.792 | yes | new |
| `pass.netball.overhead-pass` | 96 | 0.792 | yes | new |
| `pass.netball.one-hand-high-pass` | 96 | 0.792 | yes | new |
| `block.netball.deflect-high` | 88 | 0.443 | no | not at all |
| `catch.netball.hooks-jump` | 108 | 0.574 | no | not at all |
| `catch.netball.one-hand-snatch` | 98 | 0.490 | no | not at all |
| `catch.netball.two-hand-chest` | 98 | 0.449 | no | not at all |
| `catch.netball.two-hand-snatch-back` | 98 | 0.490 | no | not at all |

**The five did not move.** Their 15 pose numbers a frame and their ball paths
are equal to the clips on Tactics main, to every decimal. The comparison can
see a difference: against a different clip of the same length it reads up to
0.593. So 181 commits since 14 September did not change these five solves, and
a re-export changes only the build and the timestamp they record. They still
miss a coaching checkpoint each.

**The three passes come out graded.** The exporter sets `graded` when a clip
meets every coaching checkpoint it is graded against
(`export_tactics_clip.py:243-245`), and each pass does. Main asked for them
to be marked not graded. Writing `false` into the clip would record a value
the measurement does not support. The board's "not graded" mark comes from
the athlete manifest's `gradedClip` link (`athleteGraded` in Tactics
`src/core/athleteMotion.ts`), so the link can stay empty for the three passes
until the release lands. Then the board shows them as not graded, and the clip
files stay true to what was measured.

## What Main ruled on the export, and where it is built

Main agreed on 13 November 2026 (lane board, Models/models-tactics-export-to-main),
with two conditions:

1. **The three passes** ship as measured, and their `gradedClip` stays `null`,
   with the reason where the link is made. `athlete/athlete_manifest.py` holds
   `HELD_FROM_GRADED_RECORD`: each pass meets its checkpoints on this build, the
   mechanical release changes it, and the bounce pass also has a defect its
   checkpoints cannot see (coach item 12). `convert_legacy` writes `null` for a
   held technique even when its pose clip is shipped.
   `tests/test_athlete_manifest.py` has the test, which failed on all three
   links before the rule existed.
2. **The five that did not move** change no file in Tactics. The equality is
   recorded here, with its instrument.

### The instrument, and its reading

`scripts/clip_moved.py` compares each new clip with the clip on Tactics
`origin/main`, by `clipId`. `tests/test_clip_moved.py` shows that it reads 0 for
equal clips and sees a change of one pose number or of the ball.

```
python -B scripts/clip_moved.py F:/Repositories/braven-tactics-netball-athlete spikes/poc-output
```

Run on 13 November 2026, against Tactics `origin/main` at `e61a539`, with the
clips exported on `b9deaeb`:

```
clip                                 graded         pose max  pose mean ball max m  build
pass.netball.bounce-pass             new: True             -          -          -  b9deaeb  (not shipped yet)
block.netball.deflect-high           False->False      0.000     0.0000     0.0000  0353b76->b9deaeb
catch.netball.hooks-jump             False->False      0.000     0.0000     0.0000  0353b76->b9deaeb
pass.netball.one-hand-high-pass      new: True             -          -          -  b9deaeb  (not shipped yet)
catch.netball.one-hand-snatch        False->False      0.000     0.0000     0.0000  0353b76->b9deaeb
pass.netball.overhead-pass           new: True             -          -          -  b9deaeb  (not shipped yet)
catch.netball.two-hand-chest         False->False      0.000     0.0000     0.0000  0353b76->b9deaeb
catch.netball.two-hand-snatch-back   False->False      0.000     0.0000     0.0000  0353b76->b9deaeb
```

## What a board draws: the new pose clips are records, not animations

Read on Tactics `main` at `e61a539` while proving step 4. A board draws a body
by one of two routes:

- **The rigged athlete** (`athleteEnabled`: netball with the athlete library).
  `athleteThrowClip` and `athletePassTechniques` in `src/core/athleteMotion.ts`
  pick the athlete's own clip by release kind: `bounce-pass` plays
  `netball_bounce_pass`, `overhead-pass` and `lob` play `netball_overhead_pass`,
  and `shoulder-pass` plays `netball_one_hand_high_pass`. These are the rig
  clips of `b4f7074`, and they played before this change.
- **The pose clips**, for any other figure. `capturedAction` in
  `src/engine/clips.ts` asks `techniqueFor` for the class `pass`, never for a
  release kind, and `techniqueChosenFor` returns the named default,
  `pass.netball.chest-pass`. No other code picks a pose clip.

**So no board draws the three new pose clips.** On Tactics they are graded
records, which `athleteGraded` reads through `gradedClip`, and Main held that
link. The delivery changes no picture and no "not graded" mark: both are the
same before and after. What a coach sees of these three passes is the rig
clip, which comes with the athlete export, not with a pose clip.

## Questions for Main

1. Deliver the three pass clips from `main` now and export them again after
   the mechanical release lands, or wait for it and export once?
2. The one-hand high pass: deliver it under its own name,
   `one-hand-high-pass`, which needs Tactics to add it to its release kinds, or
   hold it until the coach answers item B?
3. Do the five that are not graded (four catches and the deflect) get a new
   export from `main` in this goal, to see whether they now pass? "Graded"
   means the clip met every coaching checkpoint it was graded against
   (`spikes/export_tactics_clip.py`).
