"""The ball-to-hand gap in the SOLVE, per graded phase and per hand.

The rendering side draws a figure from a job; this reads what the engine
solved, before any job is written, so the two can be compared. The gap is
measured the way `export_blender_job._grip` measures a grip: wrist to ball
centre, less the radius, in arm lengths. Arm lengths, because the MPFB athlete
is not MHR's size, and the renderer's gap is divided by its own arm.

Run in the engine environment (the junctions and lock in docs, refer to
spikes/README.md):

    cd spikes && pixi run --frozen python ../scripts/ball_hand_gap_solve.py > ../out/gap-solve.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

SPIKE_DIR = Path(__file__).resolve().parent.parent / "spikes"
sys.path.insert(0, str(SPIKE_DIR))

from export_blender_job import blender_arm, to_blender  # noqa: E402
from movement_definition import load as load_definition  # noqa: E402
from movement_engine import definition_path  # noqa: E402
import export_blender_job as exporter  # noqa: E402


def main() -> int:
    character = exporter.load_character()
    rows = []
    for movement_id in sorted(p.name[: -len(".job.json")] for p in exporter.OUTPUT.glob("*.job.json")):
        definition = load_definition(definition_path(movement_id))
        result = exporter.solve_movement(character, movement_id)
        index, points = result["index"], result["points"]
        radius = float(result["radiusCm"]) / 100.0
        frames = len(points)
        for phase in definition.phases:
            # The same frame rule as `export_blender_job.build`, so a row here
            # is the phase the job carries.
            frame = max(0, min(frames - 1, round(phase.at_phase * (frames - 1))))
            held = result["possession"].frames[frame]
            centre = to_blender(held.centre)
            arm = blender_arm(points[frame], index)
            gaps = {}
            for side in ("l", "r"):
                wrist = to_blender(points[frame][index[f"{side}_wrist"]])
                gaps[side] = round(float((np.linalg.norm(wrist - centre) - radius) / arm), 6)
            rows.append({"movementId": movement_id, "phase": phase.name, "frame": frame,
                         "holding": bool(held.holding), "armM": round(float(arm), 6),
                         "wristFromSurfaceInArms": gaps})
    json.dump({"instrument": "scripts/ball_hand_gap_solve.py", "rows": rows}, sys.stdout, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
