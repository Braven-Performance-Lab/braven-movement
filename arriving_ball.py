"""The owner's choice B, 13 Nov 2026: a front view leaves out an arriving ball that hides her.

In the front view of a waiting phase the ball on its way to her sits between
the camera and the athlete and covers her face (8 front views of the manual on
13 Nov). Asked to choose between drawing it as it is, leaving it out with a
caption, a faint outline and a raised camera, the owner chose to LEAVE IT OUT
(board decision Blender/blender-arriving-ball-front-view). The quarter and side
views of the same moment still draw it.

THE RULE, all of it must hold:
- the FRONT view;
- she does not hold the ball in this phase;
- the phase comes BEFORE the drill's first holding phase, so the ball is
  arriving. A ball that has just left her hands is drawn: the owner kept those;
- the ball is nearer the camera than she is, and its projected disc covers her
  head or her chest. Head and chest are read from the posed shoulders: 0.22 m
  above and 0.12 m below their midpoint. On the 51 phases of 13 Nov the rule
  picks exactly the 8 views the owner was shown.

No Blender here, so a host test reads it. The projection is Blender's, sensor
fit AUTO spanning the image height (held to `world_to_camera_view` in the
tests).
"""
from __future__ import annotations

import math

DECISION = ("owner's choice B, 13 Nov 2026 (Blender/blender-arriving-ball-front-view): "
            "the arriving ball covers her face in the front view, so it is not drawn here")
HEAD_ABOVE_SHOULDERS_M = 0.22
CHEST_BELOW_SHOULDERS_M = 0.12


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


def leave_ball_out(view_name: str, view: dict, phase: dict, job_phases: list,
                   ball_centre, radius: float, shoulder_l, shoulder_r) -> str | None:
    """Why the ball is not drawn in this view of this phase, or None to draw it."""
    if view_name != "front" or phase["ball"]["holding"]:
        return None
    holding = [p["frame"] for p in job_phases if p["ball"]["holding"]]
    if not holding or phase["frame"] >= min(holding):
        return None
    ball_x, ball_y, ball_depth = project(view, ball_centre)
    if ball_depth <= radius:
        return None
    focal = view["lensMm"] / view["sensorWidthMm"] * max(view["resolutionPx"])
    disc = focal * radius / ball_depth
    middle = [(a + b) / 2 for a, b in zip(shoulder_l, shoulder_r)]
    for offset in (HEAD_ABOVE_SHOULDERS_M, -CHEST_BELOW_SHOULDERS_M):
        x, y, depth = project(view, [middle[0], middle[1], middle[2] + offset])
        if depth > ball_depth and (x - ball_x) ** 2 + (y - ball_y) ** 2 < disc * disc:
            return DECISION
    return None
