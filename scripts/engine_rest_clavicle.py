"""The engine's clavicle direction at rest and at a neutral standing phase.

Measured on 12 Nov 2026 (`09bf701`): 17.65 cm, 32.96 degrees back of straight
out at rest and 15.29 at `netball_chest_pass/ready`. The engine stands by
swinging its clavicles about 18 degrees forward from a retracted rest; the
render rig's rest clavicle already points almost straight out. Refer to
`docs/SHOULDER_REACH_2026-11-12.md`.

    cd spikes && pixi run --frozen python ../scripts/engine_rest_clavicle.py
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "spikes"))
import numpy as np  # noqa: E402
import export_blender_job as ex  # noqa: E402
from movement_engine import joint_positions  # noqa: E402

character = ex.load_character()
result = ex.solve_movement(character, "netball_chest_pass")
index = result["index"]
rest = joint_positions(character, result["identity"])
for name, points in (("rest", rest), ("chest_pass/ready", result["points"][0])):
    for side in ("l", "r"):
        # MHR: x left, y up, z forward.
        v = points[index[f"{side}_uparm"]] - points[index[f"{side}_clavicle"]]
        out, up, fwd = abs(v[0]), v[1], v[2]
        print(f"ENGINE {name:18s} {side} len {np.linalg.norm(v):6.2f} cm  out {out:6.2f} up {up:6.2f} "
              f"fwd {fwd:6.2f}  back-angle {math.degrees(math.atan2(-fwd, out)):6.2f} deg  "
              f"up-angle {math.degrees(math.atan2(up, out)):6.2f} deg")
