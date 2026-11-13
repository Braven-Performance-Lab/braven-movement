"""A job whose holding hands close over N frames instead of one (coach-morning item 4).

The shipped catch closes the fingers in the single frame of contact. Item 4
asks whether that reads like a hand. The alternative is a ramp, made with the
renderer's own `fingerOpenDegrees` (Main, PR 161): at contact each holding
hand opens past its grip by the measured open value, and the ask falls in
equal steps to zero N frames later. Frame `contact + k` asks
`open * (1 - k / N)` for k = 0 .. N-1; from `contact + N` on there is no ask.

THE LENGTHS HAVE NO SOURCE. Main chose 4 and 8 frames as a spread to look at;
nothing in the engine, the manual or a measurement gives a closing time. The
open value is measured: `scripts/finger_open_probe.py`, the wrist-knuckle-tip
angle of the middle finger just before contact less the same angle on the grip.

Every still phase inside the ramp gets the same ask as its frame, so the
contact figure's receipt records it. The job records the ramp in
`fingerOpenRamp`, so a render of it says what it is.

    python scripts/finger_open_ramp.py <job.json> <contact frame> <open degrees> <frames> <out.json>
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


def ramp(job: dict, contact: int, open_degrees: float, length: int) -> dict:
    if length < 1:
        raise SystemExit("a ramp needs at least one frame")
    if open_degrees <= 0:
        raise SystemExit("the open value must be positive: the ramp opens past the grip")
    out = copy.deepcopy(job)
    asks = {contact + k: round(open_degrees * (1 - k / length), 4) for k in range(length)}

    def apply(entry: dict) -> None:
        ask = asks.get(entry["frame"])
        if ask is None:
            return
        holding = sorted(entry.get("grip") or {})
        if not holding:
            raise SystemExit(f"frame {entry['frame']} is inside the ramp and holds nothing")
        for side in holding:
            entry["hands"][side]["fingerOpenDegrees"] = ask

    for entry in out["frames"]:
        apply(entry)
    for entry in out["phases"]:
        apply(entry)
    if not any(entry["frame"] == contact for entry in out["frames"]):
        raise SystemExit(f"the job carries no frame {contact}; export it with every frame")
    out["fingerOpenRamp"] = {
        "contactFrame": contact, "openDegrees": open_degrees, "frames": length,
        "asks": {str(frame): ask for frame, ask in asks.items()},
        "source": "lengths: none, a spread chosen by Main to look at; open value: "
                  "scripts/finger_open_probe.py on the renderer's hand",
    }
    return out


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) != 5:
        print(__doc__)
        return 2
    job = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    out = ramp(job, int(argv[1]), float(argv[2]), int(argv[3]))
    Path(argv[4]).parent.mkdir(parents=True, exist_ok=True)
    Path(argv[4]).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"{argv[4]}: asks {out['fingerOpenRamp']['asks']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
