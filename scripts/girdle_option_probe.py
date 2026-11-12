"""Options A and C for the shoulder reach gap, simulated with the renderer's own code.

Writes the same rows as `ball_hand_gap_render.py`, so `compare_reach.py`
compares them with the current render and with option B. Nothing on disk in
the renderer changes; the substitutions live in this process.

A  Each clavicle turns by the engine clavicle's own rotation from rest
   (`engine_clavicle_directions.py`), applied to THIS rig's rest direction.
   `pose_girdle` still computes its receipt against the job's girdle, so the
   miss and the anchor error are measured exactly as for the current render.
C  This rig's rest clavicles are turned to the engine's rest direction before
   any phase is posed, and the job's shift is applied to that rest.

    blender -b --python scripts/girdle_option_probe.py -- A out/engine-clavicle-dirs.json out/reach-optA.json spikes/poc-output/*.job.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mathutils import Vector  # noqa: E402
import blender_movement_render as R  # noqa: E402
import ball_hand_gap_render as G  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
MODE, DIRS, OUTPUT, JOBS = argv[0], json.loads(Path(argv[1]).read_text()), argv[2], argv[3:]
CURRENT = {}

original_pose_phase = R.pose_phase
original_rotate = R.rotate_bone_toward
original_studio_init = R.Studio.__init__


def pose_phase(rig, phase, *args, **kwargs):
    CURRENT["key"] = (phase["_movementId"], phase["name"])
    return original_pose_phase(rig, phase, *args, **kwargs)


def rotate_bone_toward(rig, bone, child, target):
    if MODE == "A" and bone.startswith("clavicle_"):
        side = bone[-1]
        drill, name = CURRENT["key"]
        engine_rest = Vector(DIRS[drill]["rest"][side])
        engine_now = Vector(DIRS[drill]["phases"][name][side])
        turn = engine_rest.rotation_difference(engine_now)
        head = R.world_head(rig, bone)
        length = (R.world_head(rig, child) - head).length
        target = head + (turn @ RIG_REST[side]) * length
    return original_rotate(rig, bone, child, target)


def studio_init(self, config):
    original_studio_init(self, config)
    R.reset_pose(self.rig, self.basis)
    for side in ("l", "r"):
        head = R.world_head(self.rig, f"clavicle_{side}")
        RIG_REST[side] = (R.world_head(self.rig, f"upperarm_{side}") - head).normalized()
    if MODE == "C":
        # Every drill shares one engine rest; take it from the first drill.
        rest = next(iter(DIRS.values()))["rest"]
        for side in ("l", "r"):
            head = R.world_head(self.rig, f"clavicle_{side}")
            length = (R.world_head(self.rig, f"upperarm_{side}") - head).length
            original_rotate(self.rig, f"clavicle_{side}", f"upperarm_{side}", head + Vector(rest[side]) * length)
        R.bpy.context.view_layer.update()
        self.basis = {bone.name: bone.matrix_basis.copy() for bone in self.rig.pose.bones}


RIG_REST = {}
if MODE == "A":
    # A aims the clavicle by the engine's rotation, not at the job's girdle, so
    # the renderer's girdle refusal reads every phase as a failed aim. The
    # receipt is still written against the job's girdle and read as for B.
    R.refuse_unrenderable_girdle = lambda report, label: None
R.pose_phase = pose_phase
R.rotate_bone_toward = rotate_bone_toward
R.Studio.__init__ = studio_init

# The phases carry their drill, so the substitution knows which engine reading
# belongs to the phase being posed.
staged = Path(OUTPUT).with_suffix(".jobs")
staged.mkdir(exist_ok=True)
paths = []
for path in JOBS:
    job = json.loads(Path(path).read_text(encoding="utf-8"))
    for phase in job["phases"]:
        phase["_movementId"] = job["movementId"]
    copy = staged / Path(path).name
    copy.write_text(json.dumps(job), encoding="utf-8")
    paths.append(str(copy))
sys.argv = [sys.argv[0], "--", OUTPUT, *paths]
G.main()
