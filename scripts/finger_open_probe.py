"""How far a hand is open before contact, against its grip, on the renderer's own hand.

Coach-morning item 4 renders the finger close as a ramp: at contact the job
asks the holding hands to open by `fingerOpenDegrees`, and the ask falls to
zero over N frames. The ask is a change of the wrist-knuckle-tip angle of the
middle finger past the grip (`finger_curl.knuckle_release_for`). So the value
the ramp starts from is that angle on the hand just before contact, less the
same angle on the grip at contact, read on the hand the renderer draws.

This poses two frames of a job with the renderer's own `pose_phase`, on the
athlete the renderer uses, and prints the angle on each hand at each frame.

    blender -b --python scripts/finger_open_probe.py -- <job.json> <open frame> <grip frame> [--athlete <build folder>]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import blender_movement_render as R  # noqa: E402
from blender_mpfb_reference_catch import world_head, world_tail  # noqa: E402


def middle_angle(rig, side: str) -> float:
    """The angle `pose_articulated_hand` opens: wrist, middle knuckle, middle tip."""
    knuckle = world_head(rig, f"middle_01_{side}")
    one = world_head(rig, f"hand_{side}") - knuckle
    two = world_tail(rig, f"middle_03_{side}") - knuckle
    return math.degrees(one.angle(two))


def main() -> int:
    argv = sys.argv[sys.argv.index("--") + 1:]
    job_path, open_frame, grip_frame = Path(argv[0]), int(argv[1]), int(argv[2])
    athlete = Path(argv[argv.index("--athlete") + 1]) if "--athlete" in argv else None
    job = json.loads(job_path.read_text(encoding="utf-8"))
    studio = R.Studio(R.load_reference_catch_config(R.DEFAULT_CONFIG_PATH), athlete)
    frames = {frame["frame"]: frame for frame in job["frames"]}
    readings = {}
    for number in (open_frame, grip_frame):
        R.pose_phase(studio.rig, frames[number], job["anatomyLimitsDegrees"], studio.basis,
                     studio.foot_baseline, studio.config.finger_curl_degrees,
                     job.get("knuckleLimitsDegrees"))
        readings[number] = {side: middle_angle(studio.rig, side) for side in ("l", "r")}
        print(f"FRAME {number} grip {sorted(frames[number].get('grip') or {})} "
              + " ".join(f"{side} {readings[number][side]:.2f}" for side in ("l", "r")))
    for side in ("l", "r"):
        print(f"OPEN {side} {readings[open_frame][side] - readings[grip_frame][side]:.2f} degrees "
              f"(frame {open_frame} less frame {grip_frame})")
    print("ATHLETE", json.dumps(studio.athlete))
    return 0


if __name__ == "__main__":
    main()
