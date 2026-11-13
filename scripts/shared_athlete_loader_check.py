"""Run the renderer's `load_shared_athlete` on a real build, licence check skipped.

First a clean load: what it links, which constraints it mutes, which drivers
it keeps. Then one defect per case, injected through `R.head_bone_name`, which
the loader calls after it links the athlete and before it checks constraints
and drivers. Every case must print REFUSED; INJECT FAILED proves nothing.
Draws no figure.

    blender -b --python scripts/shared_athlete_loader_check.py -- <repo> <athlete build folder>
"""
import sys
import tempfile
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
    "driver in a node group nested in a material": lambda: nested_group_driver(),
    "driver in a geometry-nodes modifier group": lambda: geometry_nodes_driver(),
    "driver on a later material's node tree": lambda: later_material_driver(),
}


def later_material_driver():
    # Every embedded tree is named 'Shader Nodetree'; a check by name read
    # only a mesh's FIRST material. So the driver goes on the last of two or
    # more DIFFERENT materials: Kit_Shorts has one material in two slots, and
    # a driver there sat on the first tree, which even the old check read.
    for obj in rig().children_recursive:
        materials = {}
        for slot in getattr(obj, "material_slots", ()):
            if slot.material is not None and slot.material.node_tree is not None:
                materials.setdefault(slot.material.name, slot.material)
        if obj.type == "MESH" and len(materials) >= 2:
            last = list(materials.values())[-1]
            print("LATER MATERIAL ON", obj.name, "materials:", list(materials), "driver on", last.name)
            value_node_driver(last.node_tree)
            return
    raise RuntimeError("no mesh under the rig has two different materials with node trees")


def value_node_driver(group):
    group.nodes.new("ShaderNodeValue").outputs[0].driver_add("default_value")


def nested_group_driver():
    group = bpy.data.node_groups.new("Check_Nested", "ShaderNodeTree")
    value_node_driver(group)
    material_tree = body().material_slots[0].material.node_tree
    material_tree.nodes.new("ShaderNodeGroup").node_tree = group


def geometry_nodes_driver():
    group = bpy.data.node_groups.new("Check_Geometry", "GeometryNodeTree")
    value_node_driver(group)
    body().modifiers.new("Check_Geometry", "NODES").node_group = group


# A child the loader must refuse BEFORE the `Head` call, so it goes into a
# saved copy of the build. Only the hash check is skipped for that copy; it
# has its own check (the file is hashed against the manifest).
def empty_under_rig_copy():
    bpy.ops.wm.open_mainfile(filepath=str(master))
    empty = bpy.data.objects.new("Check_Empty", None)
    empty.empty_display_type = "IMAGE"
    bpy.context.scene.collection.objects.link(empty)
    empty.parent = rig()
    # Not `bpy.app.tempdir`: opening a file gave a folder the load then
    # could not find.
    copy = Path(tempfile.mkdtemp()) / "loader-check-empty.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(copy), copy=True)
    return copy


real_sha = R.sha256
try:
    copy = empty_under_rig_copy()
    R.sha256 = lambda path: sha
    R.load_shared_athlete(copy, sha)
    print("NOT REFUSED", "an image empty under the rig")
except SharedAthleteRefusal as refusal:
    print("REFUSED", "an image empty under the rig", "|", str(refusal)[:110])
except Exception as error:
    print("INJECT FAILED", "an image empty under the rig", "|", type(error).__name__, str(error)[:110])
finally:
    R.sha256 = real_sha

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
