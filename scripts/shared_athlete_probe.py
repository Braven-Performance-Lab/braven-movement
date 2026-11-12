"""Pose the SHARED athlete from the engine's jobs with the renderer's own code.

The shared athlete is the Models lane's `netball-athlete.blend` (MPFB body,
the same game-engine bone names as the render rig, plus four IK controls,
`Ball_Control` and 16 skirt bones). Blender starts as the renderer starts,
with no file opened, and this APPENDS only the rig and its child meshes from
that file. Its own lights (Key, Fill, Rim), camera, floor, world and scene
settings never enter the scene, so both bodies are drawn in the renderer's
room. Opening the file instead lit the shared athlete with two light rigs.

In this process only, and never saved:
- the bone `Head` is renamed `head`, the one name the renderer uses that
  differs, and the vertex group follows (checked);
- the assigned Action is cleared and every bone returns to its bind pose;
- the four IK constraints (`lowerarm_*` to `CTRL_hand_*`, `calf_*` to
  `CTRL_foot_*`) are muted, because they would override the arm and leg the
  renderer poses.

The first argument is the shared file. Then a mode:

    blender -b --python scripts/shared_athlete_probe.py -- <netball-athlete.blend> clavicle
    blender -b --python scripts/shared_athlete_probe.py -- <netball-athlete.blend> measure out/reach-shared.json spikes/poc-output/*.job.json
    blender -b --python scripts/shared_athlete_probe.py -- <netball-athlete.blend> render --job <job> --output <dir>

`measure` runs `ball_hand_gap_render.py`, so its rows compare row for row with
the render rig's. `render` runs the renderer's own `main` with the renderer's
camera, lights, floor and ball.
"""
import math
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
# Children of the rig that are not the athlete: the file's own ball.
LEFT_OUT = ("Movement_Ball",)


def append_athlete(path: str):
    # The renderer's `create_athlete` starts from this call; without it the
    # startup scene's cube stood in front of the athlete.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # ONE load, so every child keeps its own rig. Two loads appended a second
    # copy of the rig with the children, and the bone rename then reached
    # only one copy (the vertex-group check below caught it).
    with bpy.data.libraries.load(path, link=False) as (source, target):
        target.objects = list(source.objects)
    rig = next(obj for obj in target.objects if obj is not None and obj.name == RIG_NAME)
    collection = bpy.context.scene.collection
    collection.objects.link(rig)
    # Only the athlete enters the scene. The file's lights, camera, floor and
    # ball stay loaded but unlinked, so they do not render.
    for obj in target.objects:
        if obj is not None and obj.parent is rig and obj.name not in LEFT_OUT:
            collection.objects.link(obj)
    if any(o.name.startswith(RIG_NAME + ".") for o in bpy.data.objects):
        raise SystemExit("a second copy of the rig was appended")
    return rig


def shared_studio(config):
    rig = bpy.data.objects[RIG_NAME]
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
                             human=body, build=generated_from(), sourceBlend=SOURCE)
    if MODE == "render":
        studio.world_colour = config.presentation.studio.world_color
        studio.assets = [o for o in bpy.data.objects
                         if o.type == "MESH" and o.parent == rig and o.name != BODY_NAME]
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
SOURCE, MODE, rest = argv[0], argv[1], argv[2:]
append_athlete(SOURCE)
R.Studio = shared_studio
if MODE == "clavicle":
    # The rest clavicle, as `scripts/rig_rest_clavicle.py` reads the render rig.
    studio = shared_studio(None)
    for side in ("l", "r"):
        v = R.world_head(studio.rig, f"upperarm_{side}") - R.world_head(studio.rig, f"clavicle_{side}")
        out, fwd, up = abs(v.x), -v.y, v.z
        print(f"SHARED rest {side} len {v.length*100:6.2f} cm  back-angle "
              f"{math.degrees(math.atan2(-fwd, out)):6.2f} deg  up-angle {math.degrees(math.atan2(up, out)):6.2f} deg")
elif MODE == "render":
    sys.argv = [sys.argv[0], "--", *rest]
    R.main()
elif MODE == "measure":
    sys.argv = [sys.argv[0], "--", *rest]
    G.main()
else:
    raise SystemExit(f"unknown mode {MODE!r}: clavicle, measure or render")
