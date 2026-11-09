# Jog and Run rebuild, 9 November 2026

Marius found the revision 8 Jog robotic: "stiff joints, weird feet movement". The Gait lane rebuilt it from a gait model and added a Run from the same model. No motion capture and no third-party animation is used.

## Candidate

- External folder: `Netball Athlete/candidates/09-gait-v2/` (revision 9). Revisions 07 and 08 are unchanged.
- GLB SHA-256: `2b48758b228e30a78ad163697d1a9963ee62234a06606cd38a1634c8b34dc208`. The build is byte-reproducible from `08-jog/netball-athlete.blend` with `author_gait.py`.
- `candidates/09-gait/` is a superseded first build. Its ankle plantarflexes to -46 degrees (Jog) and -58 degrees (Run) after toe-off. Do not ship it.
- Receipts are in `09-gait-v2/verification/`: the Blender measurement of both clips (`gait-measure-09.json`), the revision 8 measurement (`gait-measure-08.json`), the norm grade (`fit-grade.json`) and the scope check (`scope.json`).

## Why the old jog looked robotic

Measured with `athlete/measure_gait.py` on revision 8:

| Quantity | Revision 8 | Norm at about 3 m/s |
| --- | --- | --- |
| Cadence | 116 steps/min | 168-172 |
| Stance knee | fixed at 13 deg | 17.5 at contact, 46 at its deepest |
| Swing knee | 66 deg | 101 |
| Ankle at toe-off | -5.5 deg | -20 |
| Toe joint, pelvis, elbow | no movement | all move |
| Planted foot | slides at up to 2.8 m/s | does not slide |
| Knee velocity | changes by 320 deg/s in one frame | smooth |

Every joint was a sine wave of one phase. The knee was a rectified sine, which has a corner.

## How the new gait is made

- `athlete/gait.py` is one model with two speeds: Jog at 3.0 m/s (42 frames at 60 fps, 171 steps/min) and Run at 4.5 m/s (39 frames, 185 steps/min). The Run has a longer stride, a longer flight and more knee and arm movement, so it is not a fast Jog.
- In stance the contact point is fixed to the floor, and the floor moves back at the running speed. The foot rolls from the heel, to the flat sole, to the ball of the foot, and the toes stay on the floor.
- The pelvis height follows a ballistic flight and a stance bounce. The stance knee follows a curve to its late-stance minimum; the model solves the heel lift that gives it.
- The swing is in joint space (leg direction, knee angle), so it cannot ask for more reach than the leg has.
- Every curve is C1. `tests/test_athlete_gait.py` proves it: the largest velocity step halves when the sampling doubles. The test catches the old rectified sine.
- `athlete/fit_gait.py` fits the free values to Fukuchi 2017 (PeerJ 5:e3298), Heiderscheit 2011, Tsuji 2015 and Dorn 2012, and writes the grade with each source.

## The shoe skin defect

The revision 8 shoe had its sole skinned to the shin (64% at the heel) and its midfoot to the toe bone (40-60%). When the ankle or the toes bend, the sole folds into the floor (1.2 cm in stance, measured). `author_gait.py` gives each shoe vertex new weights from its rest position: the calf moves only the collar above the ankle, the sole follows the foot, and the toe bone owns the shoe from 4 cm behind the ball joint. This changes the shoe in every clip. The other 16 animations are unchanged, and no vertex position changed (`verify_jog_asset.py --reskinned shoes05`).

## Result against the norms

Two instruments give this table. Knee at contact, the deepest stance knee, peak dorsiflexion and the ankle at toe-off come from the gait model (`python athlete/fit_gait.py --grade-only`, exact at the contact and toe-off events). The deepest swing knee, the most plantarflexion, the hip range and the pelvis bounce come from `measure_gait.py` on the built rig (`09-gait-v2/verification/gait-measure-09.json`). For the pelvis bounce the model gives 5.6 cm (Jog) and the rig 4.7 cm; the table shows the rig value. The cause of the difference is not measured.

| Quantity | Jog | Norm | Run | Norm |
| --- | --- | --- | --- | --- |
| Knee at contact | 17.0 | 17.5 | 19.1 | about 20 |
| Deepest stance knee | 44.8 | 46 | 45.2 | about 46 |
| Deepest swing knee | 101 | 101 | 119 | 119 |
| Peak dorsiflexion | 32 | 26.5 | 33 | 26.8 |
| Ankle at toe-off | -17 | -20 | -21.5 | -23 |
| Most plantarflexion | -21 | -18.6 | -25 | -23.2 |
| Hip range | 53 | 54 | 72 | 72 |
| Pelvis bounce, cm | 4.7 | 6-8.7 | 5.2 | about 6.5 |

Two values stay outside the norm: peak dorsiflexion (6-7 deg high) and the pelvis bounce (1.5-2 cm low). This leg cannot cover the published stance length without one of the two. Run values marked "about" have no confirmed source.

## Checks

- `python -m unittest discover -s tests`: the gait tests (planted foot, C1, norms, run not a fast jog, swing clearance including the toe tip).
- Blender: `measure_gait.py` on `09-gait-v2` (the stance sole within 4 mm of the floor, the swing foot clear); `verify_jog_asset.py --changed Jog --added Run --reskinned shoes05`.
- Studio at 5398 with this candidate: `npm test`, `tests/studio-browser.mjs` (45 checks), `tests/jog.mjs` (10 checks: Jog and Run, the original 55-140 degree ankle envelope).
- `tests/gait-frames.mjs` saves every authored frame from the live Studio canvas; the phone page clips come from it.

## Open

- The rebuilt Jog Action still carries the custom properties of the revision 8 Jog (`correction: jog-ankle-v1 ...`), because `correct_jumps.new_action` copies them, and the GLB exports them as extras. Nothing reads them. Removing them changes the GLB bytes, so it waits for the next rebuild of the candidate.

- Tactics loads its clip list from `src/data/athlete-motions.json`. It shows the old Jog and no Run until `tools/import-athlete.mjs` runs on this candidate, in a separate braven-tactics change.
- The ordinary Tactics path locomotion uses its own capture clips (`figures/clips.json`) and is not changed here.
