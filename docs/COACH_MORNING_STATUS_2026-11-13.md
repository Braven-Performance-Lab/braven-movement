# The coach morning on 13 November 2026: which items are open, answered or changed

Main's goal (13 November 2026) brings `docs/COACH_MORNING_2026-09.md` up to date
for the owner. This file is step 1: each item of the agenda, classed against
`main` at `4798151` and the rulings made since the agenda was last changed on
14 September 2026. No text of the agenda changes here.

## Method

Two readers classed the items, items 1 to 10 and items 11 to 19 with A to C.
Each read the item's section of the agenda in full, then `main`, the open
register (`docs/KNOWN_ISSUES.md`), its class file
(`docs/KNOWN_ISSUES_NO_BUILD_2026-11-13.md`) and the spec decisions. Every class
names its source. Models re-read the claims that rest on one commit or one new
number: `d5607be`, `9328002`, `bc0facb`, `8e2bdec`, `4d5e560`, and the high-pass
finding.

- **Open:** the question still waits for the coach or the owner, and nothing
  since changed what she is asked.
- **Changed:** still for the morning, but what she is asked, what she is shown,
  or a number in it changed.
- **Answered:** a ruling settled it, so it leaves the morning or becomes a
  confirmation.

## Counts

| Status | Items | Count |
|---|---|---:|
| Open | 1, 5, 8, 9, 11, 14, 15, 18, A, C | 10 |
| Changed | 2, 3, 4, 6, 12, 13, 16, 17, 19, B | 10 |
| Answered | 10 | 1 |
| Struck | 7 | 1 |
| **Total** | 21 live items and the struck one | **22** |

## The items

| Item | Status | What changed, and the source | What it needs in the room |
|---|---|---|---|
| 1, which frame is the release | Open | Nothing on `main`: `send_on` is still graded at 1.0, and no ruling picks the frame (class file, line 56). Main's mechanical release (`c98edd1`, not on `main`) will move this item's numbers when it lands. | The four failing checkpoints and a clip. The release footage poster is now frame 612 (`914c449`). No engine clip of the release is on `main`. |
| 2, the elbow width | Changed | She now sees the shared athlete, not the older render body (spec 1, decision 12.5). The figures 36.43 and 38.42 cm were confirmed again on `351ac3a` (`d5607be`). | Two renders, at 31.3 and 37.3. Not made yet: the Blender lane's goal "Render the coach-morning candidates for items 2 and 4" makes them. |
| 3, the ball speeds | Changed | The return speed is ruled: the ball leaves at the speed the hands carry it (spec 1, decision 12.9). Only "is 6 m/s a drill feed?" is left for her. Not built: `author_flight.py:40` still has 600.0. | Two numbers on a card. |
| 4, do her fingers close too fast | Changed | The agenda says 89.95 degrees on 7 of 8 drills, always at contact. On `351ac3a` it is 89.95 on all 8 catching drills, and on 3 of them not at the contact frame (`d5607be`, `spikes/measure_finger_ramp.py`). | A clip at full speed and slowed. Not made yet: the Blender lane makes it with item 2. |
| 5, the second hand's travel | Open | Nothing: the `join` and `gather` keys are unchanged, and nobody has ruled. | The 14 cm figure and a clip. They are on Erin's held page, which spec 2 decision 11.1 replaces with a generated pack. |
| 6, the arm span at ready | Changed | The figures move to the shared athlete, and the paper measured the old body (about 11.4 cm where the question says 20 cm, `docs/TWO_BODIES_PAPER.md:116-127`). The agenda says that paper is not on `main`; it has been since `9328002` (9 September). | A still at the ready frame. The footage poster, frame 560, shows no arm span (`docs/KNOWN_ISSUES.md:438`). No shared-athlete still exists, and no lane makes one. |
| 7 | Struck | Withdrawn in the agenda. | Nothing. |
| 8, the elbow dial's number | Open | Nothing: the dial is still 31.3, and Marius deferred the angle to the morning. | Item 2's renders. |
| 9, the release timing fix | Open | Nothing on `main`. Main's mechanical release changes it when it lands. | Nothing until item 1 is answered. |
| 10, which passes the board needs | Answered | Spec 1 decision 12.4: all eight passes, in the manual's names. "Shoulder pass" is dropped unless she uses it, so only that stays, as a confirmation. Not built: the clip contract still lists `shoulder-pass`. | Nothing. |
| 11, one band floor missed by 0.05 | Open | Nothing: 49.95 against a floor of 50.0, and it waits for her. The reading may move when the release work lands. | Four numbers on a card. |
| 12, the bounce pass has no bounce | Changed | Its speed figures were computed at 600 cm/s, which decision 12.9 replaces. Decision 12.3 grades the six distance cues, and two are this drill's steps. Her question stands. | 15 stills, re-rendered on the shared athlete in pull requests 153 and 154. |
| 13, the one hand high pass | Changed | A height measure now exists (`ballHeightCm`). Its name is answered by decision 12.4. Its `ready` phase is drawn since `a484302`, so she sees it. **The high-pass ready finding** (`docs/FINDING_HIGH_PASS_READY_GRIP.md`, corrected in `d252a34`) adds the question below. | The `ready` figure, rendered on the shared athlete. |
| 14, a one-handed pass is harder to place | Open | Nothing to what she is asked. | Nothing. |
| 15, every pass clip stops before the ball arrives | Open | Nobody has ruled. Its figures were computed at 600 cm/s and may move when the release work lands. | Nothing. |
| 16, the landing's cue | Changed | The agenda says nobody has run a sweep. It ran (`bc0facb`, 15 September): the checkpoints can fail, but with the flight removed all three still pass. The renderer placed no feet before `320bd01`. | 12 stills. The record does not say whether they were rendered after the feet fix. |
| 17, the hand posed wrongly | Changed | The fix stands (`fde5d5a`). She now sees it on the shared athlete. The match "to the decimal" was measured on the old body. | A catch she can turn and step through. |
| 18, the two angles of the release hand | Open | The angles are still unsourced, and she sets them. The agenda's caveat is out of date: the paper is on `main` and says the release is mechanical, as Marius ruled. | Renders of the flick candidates. Not made yet: Main's goal makes them. The renderer can now open the fingers as a job asks (`4d5e560`). |
| 19, which cues are distances | Changed | Marius ruled the instrument already (decision 12.3, not built). Her answer now sizes the cues beyond the six, and no longer gates the decision. | Nothing. |
| A, a second grader | Open | Nothing is ruled. | Nothing. |
| B, vocabulary conflicts | Changed | For the passes, decision 12.4 rules the manual's names. What is left: whether she uses "shoulder pass", and conflicts outside the passes. | Nothing. |
| C, two manual titles | Open | Nothing is ruled. Two technique files still cite the older title, "202526 Netball Coaches Manual". | Nothing. |

## The high-pass ready finding, for item 13

From `docs/FINDING_HIGH_PASS_READY_GRIP.md` on `main`:

- At `ready`, the right hand is under and behind the ball at chin height,
  fingers up. The ball touches her chin: 51 skin vertices are inside it, at
  most 8.63 mm deep.
- On the hand as drawn, the ball is 27.7 degrees off the finger line, inside
  the other grips' 41.8 to 46.4 degrees. An earlier figure of 110.9 degrees was
  withdrawn, because it was measured on a pose the renderer does not draw.
- The open point is the right index knuckle: it turns 72.7 degrees about z,
  and 208 of 208 readings on the other drills turn about x. No instrument says
  whether that joint can make that turn.
- The question for her: at `ready`, where is the ball relative to the throwing
  hand? If the drawn hold is wrong, the technique file changes, under gate 4.

## The renders the morning waits on

| Item | Render | Who makes it |
|---|---|---|
| 2 and 8 | Elbow width at 31.3 and 37.3 | The Blender lane's goal for items 2 and 4 (step 7 of 8 at 14:05) |
| 4 | Fingers, full speed and slowed | The Blender lane; its render waits for Main to land the renderer's finger field |
| 18 | The flick candidates | Main's goal "Make the release mechanical". Five candidates are rendered, and the owner decides whether they go before the coach (Main/flick-candidates-look) |
| 6 | A ready still on the shared athlete | Nobody yet |

The state of the renders is read from the lane board at 14:05 on 13 November
2026, not from `main`.

## Questions for Main

1. Item 6 needs a ready still on the shared athlete, and no lane makes one. Who
   makes it?
2. Item 10 is answered except for "shoulder pass". Does it leave the agenda and
   go into item B as one confirmation?
3. The running order counts 21 live items in 20 entries. With item 10 merged
   into item B, the count changes. Do I update the running order in the same
   change?
