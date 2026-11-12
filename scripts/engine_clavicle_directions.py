"""The engine's clavicle direction at rest and at every graded phase, in Blender axes.

Input for `scripts/girdle_option_probe.py`, option A: each body turns its own
clavicle by the rotation the engine's clavicle made from rest. Directions are
unit vectors from the sternal end (`*_clavicle`) to the shoulder (`*_uparm`),
converted with the exporter's own `to_blender`.

    cd spikes && pixi run --frozen python ../scripts/engine_clavicle_directions.py ../out/engine-clavicle-dirs.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "spikes"))
import numpy as np  # noqa: E402
import export_blender_job as ex  # noqa: E402
from movement_definition import load as load_definition  # noqa: E402
from movement_engine import definition_path, joint_positions  # noqa: E402


def direction(points, index, side):
    v = ex.to_blender(points[index[f"{side}_uparm"]]) - ex.to_blender(points[index[f"{side}_clavicle"]])
    return [round(float(x), 9) for x in v / np.linalg.norm(v)]


character = ex.load_character()
out = {}
for path in sorted(ex.OUTPUT.glob("*.job.json")):
    movement_id = path.name[: -len(".job.json")]
    result = ex.solve_movement(character, movement_id)
    index, points = result["index"], result["points"]
    rest = joint_positions(character, result["identity"])
    frames = len(points)
    entry = {"rest": {side: direction(rest, index, side) for side in ("l", "r")}, "phases": {}}
    for phase in load_definition(definition_path(movement_id)).phases:
        frame = max(0, min(frames - 1, round(phase.at_phase * (frames - 1))))
        entry["phases"][phase.name] = {side: direction(points[frame], index, side) for side in ("l", "r")}
    out[movement_id] = entry
Path(sys.argv[1]).write_text(json.dumps(out, indent=1), encoding="utf-8")
print(f"wrote {len(out)} drills -> {sys.argv[1]}")
