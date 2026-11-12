"""The render rig's rest clavicle: length and direction, from the rig itself.

The counterpart of `scripts/engine_rest_clavicle.py`. Measured on 12 Nov 2026
(`09bf701`): 12.63 cm, 2.85 degrees back of straight out and 8.50 degrees
down. Refer to `docs/SHOULDER_REACH_2026-11-12.md`.

    blender -b --python scripts/rig_rest_clavicle.py
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import blender_movement_render as R  # noqa: E402

studio = R.Studio(R.load_reference_catch_config(R.DEFAULT_CONFIG_PATH))
rig = studio.rig
R.reset_pose(rig, studio.basis)
for side in ("l", "r"):
    v = R.world_head(rig, f"upperarm_{side}") - R.world_head(rig, f"clavicle_{side}")
    # Blender: x left, y back, z up; the athlete faces -y.
    out, fwd, up = abs(v.x), -v.y, v.z
    print(f"RIG    rest {side} len {v.length*100:6.2f} cm  out {out*100:6.2f} up {up*100:6.2f} "
          f"fwd {fwd*100:6.2f}  back-angle {math.degrees(math.atan2(-fwd, out)):6.2f} deg  "
          f"up-angle {math.degrees(math.atan2(up, out)):6.2f} deg")
