"""Coach-morning item 4: how far the fingers curl in a single frame.

The agenda says the fingers change by up to 89.95 degrees in one frame, at the
contact frame, on seven of eight drills, and 88.18 on `hooks_outside_hand`. No
committed instrument printed that number, so this one does, from the solve's
own per-frame parameters (`result["motion"]`) and the curl set the solve applies
(`finger_wrap.curl_parameters`, 15 per hand).

For each catching drill and hand it prints the largest change of any one curl
parameter between two consecutive frames, the frame it lands on, and the drill's
contact frame. A catch only, by the same rule as `measure_elbow_width.py`.

    cd spikes
    pixi run --frozen python measure_finger_ramp.py
"""

from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import numpy as np

SPIKE_DIR = Path(__file__).resolve().parent
if str(SPIKE_DIR) not in sys.path:
    sys.path.insert(0, str(SPIKE_DIR))

from ball_track import has_ball  # noqa: E402
from finger_wrap import curl_parameters  # noqa: E402
from movement_engine import library, load_character  # noqa: E402
from possession_solve import solve_movement  # noqa: E402
from technique import has_technique, load_technique, technique_path  # noqa: E402


def main() -> int:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=SPIKE_DIR, capture_output=True, text=True
    ).stdout.strip()
    character = load_character()
    names = list(character.parameter_transform.names)
    print(f"HEAD {head}")
    print(f"{'drill':40} {'hand':4} {'max deg/frame':>13} {'at frame':>8} {'contact':>7} {'fps':>5}")
    worst = 0.0
    for movement_id in library():
        if not (has_ball(movement_id) and has_technique(movement_id)):
            continue
        if not load_technique(technique_path(movement_id)).possession_ready:
            continue
        result = solve_movement(character, movement_id)
        contact = result["possession"].contact_frame
        states = [frame["ballState"] for frame in result["measurements"]]
        if "flight" not in states[:contact]:
            continue
        motion = np.asarray(result["motion"], dtype=float)
        fps = float(result["track"].frames_per_second)
        for side in ("l", "r"):
            where = [names.index(n) for n in curl_parameters(character, (side,))]
            steps = np.abs(np.diff(motion[:, where], axis=0))
            frame, _ = np.unravel_index(int(np.argmax(steps)), steps.shape)
            degrees = math.degrees(float(steps.max()))
            worst = max(worst, degrees)
            print(
                f"{movement_id:40} {side:4} {degrees:13.2f} {frame + 1:8d} "
                f"{contact:7d} {fps:5.0f}"
            )
    print(f"largest one-frame curl change in the library: {worst:.2f} degrees")
    return 0 if worst > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
