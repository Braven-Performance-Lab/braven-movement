# Splitting the known-issues register: classes and plan

The owner ruled on 6 November 2026 that the four Client Zone specs are the
record. This plan splits `docs/KNOWN_ISSUES.md` to match: the rules go into
the specs, each open finding becomes a short entry, and the closed sections go
to an archive. Main set the goal and answered the plan's three questions on
13 November 2026 (lane board, Models/models-ki-split-plan-to-main).

## What was read

`docs/KNOWN_ISSUES.md` on `main` at `b48512a`: 5,275 lines, 3 areas (`#`),
76 sections (`##`) and 103 subsections (`###`). Three readers classed the
sections by line range, 18 + 45 + 13 = 76. Models re-read the doubtful classes
(the sections at lines 209, 2343 and 2743). Line numbers below are the lines
of that file at `b48512a`.

## Counts

| Class | Whole sections | Mixed sections that also hold it |
|---|---:|---:|
| Open finding | 33 | 9 |
| Closed (fixed, withdrawn, superseded or retired) | 25 | 10 |
| Rule for a spec | 3 | 4 |
| Engineering method (how to measure or guard), not a product rule | 2 | 7 |
| Mixed | 13 | - |
| **Total** | **76** | |

The mixed sections start at lines 209, 451, 899, 2176, 2826, 3330, 3474, 3609,
3984, 4199, 4723, 4917 and 5130.

## The sections, by class

Open (33): 10, 292, 315, 323, 330, 390, 1075, 1270, 1335, 1353, 1415, 1435,
1527, 1588, 1612, 1721, 1735, 1944, 1982, 1998, 2025, 2076, 2235, 2316, 2367,
2389, 2420, 2651, 2683, 2723, 3034, 3747, 3840.

Closed (25): 127, 169, 1314, 1486, 1557, 1662, 1679, 1754, 1819, 1845, 1867,
1921, 2093, 2131, 2261, 2284, 2443, 2479, 2520, 2595, 2785, 3458, 4374, 4538,
4624.

Rule (3): 309, 2343, 2743.

Engineering method (2): 1368, 1641.

Mixed (13), by part:

| Line | Open parts | Closed parts | Rule parts | Method parts |
|---:|---|---|---|---|
| 209 | | body | last paragraph | |
| 451 | body, 598, 675 | 486, 760, 802 | 513 | 878 |
| 899 | 962, 971, 1055 | | 905, 927, 947 | 1019 |
| 2176 | 2209 | body | | |
| 2826 | body, 2867, 2898, 2935, 3027 | | | 2971 |
| 3330 | body, 3341, 3350, 3389, 3435, 3445 | 3402 | | |
| 3474 | 3496, 3516 | body, 3485, 3561 | | |
| 3609 | 3734 | 3619, 3655, 3677, 3691, 3699 | | |
| 3984 | 3995, 4033, 4051, 4062, 4071, 4090, 4191 | | 4169 | |
| 4199 | | body, 4246, 4262, 4326 | | 4366 |
| 4723 | 4880 | 4731, 4766, 4784, 4800, 4822, 4838, 4856 | | 4894 |
| 4917 | | 4926, 4956, 4992, 5009, 5046, 5062, 5108 | | 5080 |
| 5130 | | 5152, 5187, 5201, 5220, 5236 | | 5138, 5251 |

## The rules, and where each goes

| Line | Rule | Spec 1 |
|---:|---|---|
| 209 (end) | A pose that no solve produced must not reach a figure. | Section 7 (figures) |
| 309 | Joint limits and visual anatomy take priority over exact fingertip pixels. | Section 7 |
| 513 | The length floor is 2.0 cm, derived, with what the derivation lacks. | GRD-2 (adds the derivation) |
| 905, 927, 947 | `ballHeightCm`: the zero is the court, there is no wrist height, and it is written only while she holds the ball. | Section 5 |
| 2343 | Archive a graded build before a pack goes out, with its refusals. | RCP-6 (adds the refusals) |
| 2743 | A change of basin must name its drill (a pinned ready-stance shoulder turn, 2 degree tolerance). | Section 4 |
| 4169 | A below-the-hips checkpoint claims a reading only on the build that produced it. | Section 5 |

Main's condition (answer 2): spec 1 v0.7 is published for the record only if
each rule names the ruling it comes from and none is new or changed. A rule
that is new or changed goes to the owner through Main.

## Open findings

Each open section, and each open part, becomes a short entry: the fact, its
build, its instrument, its owner and what it waits for. Where a section names
no build or no instrument, the entry says so instead of inventing one.

## Closed sections

The closed sections and the closed parts move unchanged to
`docs/archive/KNOWN_ISSUES_CLOSED_2026-11-12.md`, with their original titles.

## Engineering methods

The methods are in force, so they go to a new `docs/ENGINEERING_RULES.md`, not
to the archive (Main, answer 1).

## References

- 108 references in 55 files on `main` cite `KNOWN_ISSUES`. None uses an
  anchor. About 27 also cite a section title, by a text search. Step 5 lists
  them exactly.
- 8 of the 55 files are drill files under gate 4 (decision 12.7 of spec 1).
- One drill file already cites a title that is not in the register: "No
  units-correct height measure, and one cue already wants it".

The path `docs/KNOWN_ISSUES.md` stays, and so does the title of each open
entry. For each closed title, the register keeps one line that names the
archive file. Then a reference by path or by title stays correct, and no
gate-4 file needs an edit. The one stale citation goes to Main as a gate-4
item. It is not edited here.

## Branches

One branch holds the register, the archive and the rules file (Main, answer 3).
Spec 1 v0.7 is published in the Client Zone separately.
