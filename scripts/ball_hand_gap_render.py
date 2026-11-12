"""The ball-to-hand gap in the RENDER, per graded phase and per hand.

The counterpart of `ball_hand_gap_solve.py`. It poses every phase with the
renderer's own `pose_phase`, the call `render_job` makes before it draws, and
reads the same quantity from the posed rig: wrist (the head of `hand_<side>`)
to the ball centre `pose_phase` returns, less the radius, divided by this
rig's arm. No image is rendered, so a run costs the athlete build and the
solves, not the pictures.

It also carries the receipt's `surfaceClearanceMm`, the nearest digit to the
ball surface on the DRAWN hand, because a wrist can sit at the right distance
while the fingers point away.

    blender -b --python scripts/ball_hand_gap_render.py -- out/gap-render.json spikes/poc-output/*.job.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPOSITORY))

import blender_movement_render as R  # noqa: E402


def main() -> int:
    argv = sys.argv[sys.argv.index("--") + 1:]
    output, job_paths = Path(argv[0]), [Path(p) for p in argv[1:]]
    jobs = [json.loads(p.read_text(encoding="utf-8")) for p in job_paths]
    studio = R.Studio(R.load_reference_catch_config(R.DEFAULT_CONFIG_PATH))
    rig = studio.rig
    rows = []
    for job in jobs:
        for phase in job["phases"]:
            # A phase the renderer cannot pose costs that figure only, as in
            # `render_job`; it is recorded with its reason, never skipped.
            try:
                centre, receipt = R.pose_phase(
                    rig, phase, job["anatomyLimitsDegrees"], studio.basis, studio.foot_baseline,
                    studio.config.finger_curl_degrees, job.get("knuckleLimitsDegrees"), studio.human,
                )
            except Exception as error:
                rows.append({"movementId": job["movementId"], "phase": phase["name"], "frame": phase["frame"],
                             "failed": f"{type(error).__name__}: {error}"})
                continue
            radius = phase["ball"]["radiusM"]
            # The divisor `pose_phase` itself uses to place the ball.
            arm = R.bone_chain_length(rig, "upperarm_l", "lowerarm_l", "hand_l")
            gaps, nearest = {}, {}
            for side in ("l", "r"):
                wrist = R.world_head(rig, f"hand_{side}")
                gaps[side] = round(((wrist - centre).length - radius) / arm, 6)
                # One profile per digit (`finger_surface_clearance`). The tip is
                # what a coach sees on the ball; the lowest value anywhere says
                # whether a finger is inside it.
                profile = receipt["hands"][side]["surfaceClearanceMm"]
                tips = [entry["tip"] for entry in profile.values()]
                # `knuckleToTip` is a difference of two distances, not a
                # distance, so it is not a place a finger can be inside the ball.
                every = [entry[k] for entry in profile.values()
                         for k in ("knuckle", "mid", "distal", "tip", "nearestOnBone")]
                nearest[side] = {"tip": round(min(tips), 2), "anywhere": round(min(every), 2)}
            rows.append({"movementId": job["movementId"], "phase": phase["name"], "frame": phase["frame"],
                         "holding": receipt["holding"], "armM": round(arm, 6),
                         "wristFromSurfaceInArms": gaps, "nearestDigitMm": nearest,
                         # The ball is placed from the shoulder midpoint, so the
                         # ball moves with the girdle's error and the hands move
                         # with the ball: the gap above cannot see it. This can.
                         "girdle": {k: receipt["girdle"].get(k) for k in
                                    ("verdict", "worstOffsetMm", "ballAnchorErrorMm")}})
    output.write_text(json.dumps({"instrument": "scripts/ball_hand_gap_render.py",
                                  "build": studio.build, "rows": rows}, indent=1), encoding="utf-8")
    print(f"[ball-hand-gap] {len(rows)} phases -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
