"""Pose the SHARED athlete from the engine's jobs with the renderer's own code.

The shared athlete is the Models lane's `netball-athlete.blend` (MPFB body,
the same game-engine bone names as the render rig, plus four IK controls,
`Ball_Control` and 16 skirt bones). This opens that file, makes it posable by
`pose_phase`, and runs `ball_hand_gap_render.py` on it, so its rows compare
row for row with the render rig's.

In this process only, and never saved:
- the assigned Action is cleared and every bone returns to its bind pose;
- the four IK constraints (`lowerarm_*` to `CTRL_hand_*`, `calf_*` to
  `CTRL_foot_*`) are muted, because they would override the arm and leg the
  renderer poses.

    blender -b <netball-athlete.blend> --python scripts/shared_athlete_probe.py -- out/reach-shared.json spikes/poc-output/*.job.json

With `clavicle` first, it prints the rest clavicle of each side.

With `render` first, it runs the renderer's own `main` on this body instead,
with the renderer's camera, lights, floor and ball; the file's own ball and
floor are hidden. Its arguments are the renderer's:

    blender -b <netball-athlete.blend> --python scripts/shared_athlete_probe.py -- render --job <job> --output <dir>
"""
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bpy  # noqa: E402
from mathutils import Matrix  # noqa: E402
import blender_movement_render as R  # noqa: E402
import ball_hand_gap_render as G  # noqa: E402
from build_stamp import generated_from  # noqa: E402

RIG_NAME = "Netball_Athlete"
BODY_NAME = "Athlete_Body"


def shared_studio(config):
    rig = bpy.data.objects[RIG_NAME]
    # The one name the renderer uses that differs: the render rig says `head`,
    # this rig `Head`. Renaming the bone renames the matching vertex group in
    # every skinned child, which is checked rather than assumed.
    rig.data.bones["Head"].name = "head"
    body = bpy.data.objects[BODY_NAME]
    if "head" not in body.vertex_groups or "Head" in body.vertex_groups:
        raise SystemExit("the head vertex group did not follow the bone rename")
    if rig.animation_data:
        rig.animation_data.action = None
    for bone in rig.pose.bones:
        for constraint in bone.constraints:
            constraint.mute = True
        bone.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    basis = {bone.name: bone.matrix_basis.copy() for bone in rig.pose.bones}
    foot_baseline = {f"foot_{side}": rig.pose.bones[f"foot_{side}"].matrix.copy() for side in ("l", "r")}
    studio = SimpleNamespace(rig=rig, basis=basis, foot_baseline=foot_baseline, config=config,
                             human=bpy.data.objects[BODY_NAME], build=generated_from(),
                             sourceBlend=bpy.data.filepath)
    if RENDER:
        # The renderer's own room, so the two bodies are drawn in the same one.
        for name in ("Movement_Ball", "Studio floor"):
            bpy.data.objects[name].hide_render = True
        studio.world_colour = config.presentation.studio.world_color
        studio.assets = [o for o in bpy.data.objects if o.type == "MESH" and o.parent == rig
                         and o.name not in (BODY_NAME, "Movement_Ball")]
        # The shared athlete's assets are licensed by its own manifest, not
        # by this repository's records, so the receipt lists none.
        studio.source_asset_records = []
        studio.camera, studio.lights = R.add_camera_and_lights(config.presentation)
        R.add_floor()
        studio.ball, studio.ball_seams = None, []

        def add_ball(radius):
            studio.ball, studio.ball_seams = R.create_panelled_netball(
                R.Vector((0.0, 0.0, 0.0)), radius, config.presentation)
        studio.add_ball = add_ball
    return studio


argv = sys.argv[sys.argv.index("--") + 1:]
RENDER = bool(argv) and argv[0] == "render"
R.Studio = shared_studio
if argv and argv[0] == "clavicle":
    # The rest clavicle, as `scripts/rig_rest_clavicle.py` reads the render rig.
    import math
    studio = shared_studio(None)
    for side in ("l", "r"):
        v = R.world_head(studio.rig, f"upperarm_{side}") - R.world_head(studio.rig, f"clavicle_{side}")
        out, fwd, up = abs(v.x), -v.y, v.z
        print(f"SHARED rest {side} len {v.length*100:6.2f} cm  back-angle "
              f"{math.degrees(math.atan2(-fwd, out)):6.2f} deg  up-angle {math.degrees(math.atan2(up, out)):6.2f} deg")
elif RENDER:
    sys.argv = [sys.argv[0], "--", *argv[1:]]
    R.main()
else:
    G.main()
