"""Run the renderer's `load_shared_athlete` on a real build, licence check skipped.

First a clean load: what it links, which constraints it mutes, which drivers
it keeps. Then one defect per case, injected through `R.head_bone_name`, which
the loader calls after it links the athlete and before it checks constraints
and drivers. Every case must print REFUSED; INJECT FAILED proves nothing.
Draws no figure.

    blender -b --python scripts/shared_athlete_loader_check.py -- <repo> <athlete build folder>
"""
import sys
from pathlib import Path

import bpy

REPO = Path(sys.argv[sys.argv.index("--") + 1])
FOLDER = Path(sys.argv[sys.argv.index("--") + 2])
sys.path.insert(0, str(REPO))
import blender_movement_render as R  # noqa: E402
from shared_athlete import SharedAthleteRefusal, athlete_master  # noqa: E402

manifest, master = athlete_master(FOLDER)
sha = manifest["files"][master.name]["sha256"]
real_head = R.head_bone_name

athlete, armature, others = R.load_shared_athlete(master, sha)
print("LOADED", athlete.name, armature.name, sorted(o.name for o in others))
for curve in armature.animation_data.drivers:
    print("KEPT", curve.data_path)
print("MUTED", sorted((b.name, c.name) for b in armature.pose.bones for c in b.constraints if c.mute))


def body():
    return bpy.data.objects["Athlete_Body"]


def rig():
    return bpy.data.objects["Netball_Athlete"]


CASES = {
    "object constraint on the body": lambda: body().constraints.new("COPY_LOCATION"),
    "driver on the rig object": lambda: rig().driver_add("location", 0),
    "driver on the armature data": lambda: rig().data.driver_add("display_type"),
    "driver on the mesh data": lambda: (body().data.__setitem__("probe", 0.0),
                                        body().data.driver_add('["probe"]')),
    "driver on a material": lambda: body().material_slots[0].material.driver_add("roughness"),
    "driver on a material node tree": lambda: next(
        socket for node in body().material_slots[0].material.node_tree.nodes
        for socket in node.inputs if socket.type == "VALUE" and not socket.is_linked
    ).driver_add("default_value"),
    "driver on a mesh object": lambda: body().driver_add("location", 0),
}

for name, inject in CASES.items():
    def head(names, inject=inject):
        inject()
        return real_head(names)
    R.head_bone_name = head
    try:
        R.load_shared_athlete(master, sha)
        print("NOT REFUSED", name)
    except SharedAthleteRefusal as refusal:
        print("REFUSED", name, "|", str(refusal)[:110])
    except Exception as error:  # an injection that failed is not a pass
        print("INJECT FAILED", name, "|", type(error).__name__, str(error)[:110])
R.head_bone_name = real_head
