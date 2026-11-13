"""How far each re-exported technique clip moved from the clip Braven Tactics ships.

    python -B scripts/clip_moved.py <tactics checkout> <folder of new *.clip.json>

WHY. Main asked on 13 November 2026 (lane board, Models/models-tactics-export-to-main)
how far each pose clip that is not graded moved since the 14 September export,
before any of them goes to Tactics again. A graded clip is never re-exported: it
is the record of the build the coach graded.

It reads `public/figures/clips.json` from the Tactics checkout's `origin/main`, so a
local branch there cannot change the answer, and each new clip file. It compares by
`clipId`. The pose is Tactics' 15 numbers a frame; the ball is metres.

A result of 0.000 needs a control, because a comparison that reads nothing also
says 0.000. `moved` is tested against two clips that differ
(`tests/test_clip_moved.py`).
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path


def moved(old: dict, new: dict) -> dict:
    """The largest and mean change in pose, and the largest change in ball position."""
    # zip() stops at the shorter list without a word, so every length that pairs two lists is
    # checked first. A list it cut short would read as "unchanged", which is the 0.000 this
    # instrument exists to make trustworthy.
    name = new.get("clipId")
    if not old["frames"] or not new["frames"]:
        raise SystemExit(f"REFUSED: {name} has no frames to compare")
    if len(old["frames"]) != len(new["frames"]):
        raise SystemExit(f"REFUSED: {name} has {len(new['frames'])} frames, "
                         f"the shipped clip {len(old['frames'])}; a frame-by-frame reading would misalign")
    widths = {len(f) for f in old["frames"]} | {len(f) for f in new["frames"]}
    if len(widths) != 1:
        raise SystemExit(f"REFUSED: {name} has frames of {sorted(widths)} numbers; "
                         "a shorter frame would read its missing numbers as unchanged")
    if len(old["ball"]) != len(new["ball"]):
        raise SystemExit(f"REFUSED: {name} has {len(new['ball'])} ball samples, "
                         f"the shipped clip {len(old['ball'])}; the missing samples would read as unchanged")
    pose = [abs(a - b) for of, nf in zip(old["frames"], new["frames"]) for a, b in zip(of, nf)]
    ball = [math.dist(o[:3], n[:3]) for o, n in zip(old["ball"], new["ball"])]
    return {"poseMax": max(pose), "poseMean": sum(pose) / len(pose), "ballMaxM": max(ball, default=0.0),
            "gradedBefore": old["graded"], "gradedAfter": new["graded"],
            "buildBefore": _build(old), "buildAfter": _build(new)}


def _build(clip: dict) -> str:
    """The build a clip names. Clips exported before 14 September 2026 name none."""
    return (clip.get("generatedFrom") or {}).get("commit") or "unstamped"


def shipped_clips(tactics: Path) -> dict:
    out = subprocess.run(["git", "-C", str(tactics), "show", "origin/main:public/figures/clips.json"],
                         capture_output=True, text=True, encoding="utf-8", check=True).stdout
    return json.loads(out)


def main(argv: list[str]) -> int:
    tactics, new_dir = Path(argv[1]), Path(argv[2])
    shipped = shipped_clips(tactics)
    print(f"{'clip':36s} {'graded':13s} {'pose max':>9s} {'pose mean':>10s} {'ball max m':>10s}  build")
    for path in sorted(new_dir.glob("*.clip.json")):
        new = json.loads(path.read_text(encoding="utf-8"))
        old = shipped.get(new["clipId"])
        if old is None:
            print(f"{new['clipId']:36s} {'new: ' + str(new['graded']):13s} {'-':>9s} {'-':>10s} {'-':>10s}  "
                  f"{new['generatedFrom']['commit'][:7]}  (not shipped yet)")
            continue
        m = moved(old, new)
        print(f"{new['clipId']:36s} {str(m['gradedBefore']) + '->' + str(m['gradedAfter']):13s} "
              f"{m['poseMax']:9.3f} {m['poseMean']:10.4f} {m['ballMaxM']:10.4f}  "
              f"{m['buildBefore'][:7]}->{m['buildAfter'][:7]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
