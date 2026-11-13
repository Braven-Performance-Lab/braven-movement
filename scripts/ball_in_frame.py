"""Whether the camera sees the ball, for every phase and view of a set of renders.

The cameras are fixed per view (`views` in each job), and the receipt records
where the drawn ball is (`phases[].ballCentreM`), so the question needs no new
render: project the ball into each camera and ask how much of it lands inside
the picture. Found by eye on 13 Nov 2026: the two-hand chest catch release and
deflect high ready and send on lose the ball off the frame.

The projection follows Blender's camera as `render_still` sets it: the camera
looks from `locationM` at `targetM` with world Z up, and with the default sensor
fit (AUTO) the sensor width spans the LONGER side of the image, which is the
height here (1080 x 1350). That assumption is measured, not trusted:
`tests/test_ball_in_frame.py` holds this projection to the pixel values
Blender's own `world_to_camera_view` gave for 12 points through the three job
cameras, and the projected disc was drawn on two renders and sits on the ball.
A first check against the ball's coral pixels was off by 50 to 90 px because
skin passed the colour test; it is not used.

    python scripts/ball_in_frame.py --renders out/step5-shared --jobs spikes/poc-output
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


def _sub(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def _unit(a):
    length = math.sqrt(_dot(a, a))
    return [a[0] / length, a[1] / length, a[2] / length]


def project(view: dict, point) -> tuple[float, float, float]:
    """Pixel x, pixel y (down from the top) and depth of a world point."""
    location, target = view["locationM"], view["targetM"]
    width, height = view["resolutionPx"]
    forward = _unit(_sub(target, location))
    right = _unit(_cross(forward, [0.0, 0.0, 1.0]))
    up = _cross(right, forward)
    offset = _sub(point, location)
    depth = _dot(offset, forward)
    focal = view["lensMm"] / view["sensorWidthMm"] * max(width, height)
    return (width / 2 + focal * _dot(offset, right) / depth,
            height / 2 - focal * _dot(offset, up) / depth,
            depth)


def visible_share(view: dict, centre, radius: float, samples: int = 64) -> float:
    """The share of the ball's projected disc inside the picture, from a grid."""
    width, height = view["resolutionPx"]
    x, y, depth = project(view, centre)
    if depth <= radius:
        return 0.0
    focal = view["lensMm"] / view["sensorWidthMm"] * max(width, height)
    r = focal * radius / depth
    inside = total = 0
    for i in range(samples):
        for j in range(samples):
            dx = (i + 0.5) / samples * 2 - 1
            dy = (j + 0.5) / samples * 2 - 1
            if dx * dx + dy * dy > 1:
                continue
            total += 1
            px, py = x + dx * r, y + dy * r
            inside += 0 <= px < width and 0 <= py < height
    return inside / total


def survey(renders: Path, jobs: Path) -> list[dict]:
    rows = []
    for receipt_path in sorted(renders.glob("*.render.json")):
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        drill = receipt_path.name.removesuffix(".render.json")
        job = json.loads((jobs / f"{drill}.job.json").read_text(encoding="utf-8"))
        radius = {p["name"]: p["ball"]["radiusM"] for p in job["phases"]}
        for phase in receipt["phases"]:
            for name, view in job["views"].items():
                share = visible_share(view, phase["ballCentreM"], radius[phase["name"]])
                rows.append({"drill": drill, "phase": phase["name"], "view": name,
                             "visibleShare": round(share, 3)})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--renders", type=Path, required=True)
    parser.add_argument("--jobs", type=Path, required=True)
    parser.add_argument("--below", type=float, default=0.999,
                        help="list the views whose visible share is below this")
    args = parser.parse_args()
    rows = survey(args.renders, args.jobs)
    short = [r for r in rows if r["visibleShare"] < args.below]
    for row in short:
        print(f"{row['drill']:40} {row['phase']:15} {row['view']:8} {row['visibleShare'] * 100:6.1f} % of the ball in frame")
    print(f"{len(short)} of {len(rows)} phase views show less than {args.below * 100:.1f} % of the ball")
    return 0


if __name__ == "__main__":
    sys.exit(main())
