"""One camera per drill and view, moved only where the shared camera cuts a ball.

Every job carries the same three cameras (`export_blender_job.VIEWS`). On 13
Nov 2026 `scripts/ball_in_frame.py` found five drill-views in which one phase
shows a ball cut in half by an edge of the picture; no phase that holds the
ball was cut, and a ball wholly out of the picture (arriving or gone) stays
out. Main ruled: never move the camera for one phase alone, because a reader
compares a drill's phases side by side, so each drill-view keeps ONE camera,
chosen so that no phase cuts a ball on an edge.

Each change is the smallest of the ones measured that leaves the nearest ball
at least about one ball radius (50 px) from the edge:

- a RAISE lifts the camera and its target together, so the view keeps its
  angle and the picture slides up;
- a LENS change widens the view about the same target. The chest catch needs
  it, because its release ball leaves at the side, where a raise cannot help.

The numbers are a framing, not a measurement of the athlete, and they are
re-measured with `scripts/ball_in_frame.py` whenever the solve moves a ball.
No engine import here, so a host test reads it.
"""
from __future__ import annotations

FRAMING = {
    # ready and send on: 52 % of the ball in the picture, cut by the top edge.
    "netball_deflect_high": {"front": {"raiseM": 0.15}},
    # release: 46 % (quarter) and 15 % (side), cut by the side edge.
    "netball_two_hand_catch_chest": {"quarter": {"lensMm": 38.0}, "side": {"lensMm": 38.0}},
    # approach: 75 %, cut by the top edge.
    "netball_double_foot_landing": {"front": {"raiseM": 0.10}},
    # gather: 97 %, cut by the top edge.
    "netball_hooks_jump_pull_in": {"front": {"raiseM": 0.05}},
}

ALLOWED = {"raiseM", "lensMm"}


def framed(movement_id: str, view: str, location: list, target: list, lens_mm: float):
    """The camera for one drill and view: location, target, lens, and the change made.

    The change is None where the shared camera is kept.
    """
    change = FRAMING.get(movement_id, {}).get(view)
    if change is None:
        return list(location), list(target), float(lens_mm), None
    unknown = set(change) - ALLOWED
    if unknown:
        raise ValueError(f"{movement_id} {view}: unknown framing {sorted(unknown)}")
    raise_m = float(change.get("raiseM", 0.0))
    location = [location[0], location[1], location[2] + raise_m]
    target = [target[0], target[1], target[2] + raise_m]
    return location, target, float(change.get("lensMm", lens_mm)), dict(change)
