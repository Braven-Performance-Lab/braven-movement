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
