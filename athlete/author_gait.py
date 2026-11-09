"""Author the Jog and the Run from `gait.py` into a NEW editable athlete candidate.

Run with Blender 4.5:
  blender -b --python athlete/author_gait.py -- \
      --input <candidates/08-jog/netball-athlete.blend> --output <candidates/09-gait>

Jog is replaced and Run is added. Every other Action is asserted unchanged.
The recipe measures the rig's rest geometry (bones and the evaluated shoe
mesh) and builds the gait for THAT body, so the planted foot lands on the
floor of the mesh that is drawn.

Axes: gait.py uses x forward, y left, z up with the floor at z = 0. The rig
faces -Y with +X on the athlete's left, and its floor is the lowest rest sole.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gait  # noqa: E402
from correct_jumps import new_action  # noqa: E402

FINGERS = ('index_', 'middle_', 'ring_', 'pinky_')


class Frame:
    """Conversion between gait.py coordinates and the rig."""

    def __init__(self, floor):
        self.floor = floor

    def point(self, v):
        return Vector((v[1], -v[0], v[2] + self.floor))

    def back(self, v):
        return (-v.y, v.x, v.z - self.floor)


def q_left(angle):      # gait.rot_y: + tips the front down
    return Quaternion((1, 0, 0), angle)


def q_forward(angle):   # gait.rot_x: + lifts the left side
    return Quaternion((0, -1, 0), angle)


def q_up(angle):        # gait.rot_z: + turns the front to the left
    return Quaternion((0, 0, 1), angle)


def rest_pose(rig):
    rig.animation_data.action = None
    for bone in rig.pose.bones:
        bone.rotation_mode = 'QUATERNION'
        bone.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()


def shoe_points(shoes):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = shoes.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [shoes.matrix_world @ v.co for v in mesh.vertices]
    evaluated.to_mesh_clear()
    return points


def measure_body(rig, shoes):
    """Rest geometry of the LEFT leg in gait.py coordinates, from the bones and shoe."""
    rest_pose(rig)
    bones = rig.data.bones
    for obj in (rig, shoes):
        if obj.matrix_world != Matrix.Identity(4):
            raise ValueError(f'{obj.name} has a non-identity transform; bone and mesh points would not agree')
    points = [p for p in shoe_points(shoes) if p.x > 0]
    floor = min(p.z for p in points)
    frame = Frame(floor)
    ankle = bones['foot_l'].head_local
    forward = lambda p: -(p.y - ankle.y)
    heel = max(points, key=lambda p: p.y)                         # back edge of the heel
    heel = min((p for p in points if forward(p) < forward(heel) + 0.012), key=lambda p: p.z)
    sole = min((p for p in points if forward(p) > 0.06), key=lambda p: p.z)
    mtp = bones['ball_l'].head_local
    rel = lambda p: (forward(p), 0.0, p.z - ankle.z)
    tip = min((p for p in points if forward(p) > forward(mtp) + 0.05), key=lambda p: p.z)
    knee = bones['calf_l'].head_local
    body = gait.Body(
        thigh=bones['thigh_l'].length,
        shank=bones['calf_l'].length,
        pelvis_head=frame.back(bones['pelvis'].head_local),
        hip=frame.back(bones['thigh_l'].head_local),
        ankle=frame.back(ankle),
        heel=rel(heel),
        ball=rel(sole),
        mtp=rel(mtp),
        toe_tip=(forward(tip) - forward(mtp), 0.0, tip.z - mtp.z),
        rest_shank_angle=gait.sagittal(gait.sub(frame.back(ankle), frame.back(knee))),
    )
    return body, frame


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def rebind_shoes(rig, shoes):
    """Give each shoe vertex the foot bones it belongs to, from its rest position.

    The revision 8 shoe had its SOLE skinned to the shin (64% at the heel) and
    its midfoot to the toe bone (40-60%), with 10-20% on the foot bone. When
    the ankle or the toes bend, that sole folds and sinks into the floor
    (1.2 cm at mid-stance, 2.4 cm at push-off, measured). Now:
      - the calf bone moves only the collar above the ankle,
      - the heel and the sole follow the foot bone,
      - the toe bone takes over behind the ball-of-foot joint (a 4 cm blend)
        and owns the shoe from the joint forward.
    Returns the number of vertices changed per side.
    """
    bones = rig.data.bones
    # Bone heads are in armature space and vertices in world space; the two
    # agree only while both objects sit at the origin. Refuse otherwise.
    for obj in (rig, shoes):
        if obj.matrix_world != Matrix.Identity(4):
            raise ValueError(f'{obj.name} has a non-identity transform; the shoe weights would shift')
    changed = {}
    for side in ('l', 'r'):
        sign = 1 if side == 'l' else -1
        groups = {n: shoes.vertex_groups.get(f'{n}_{side}') for n in ('calf', 'foot', 'ball')}
        if None in groups.values():
            raise KeyError(f'shoe lacks a {side} foot group')
        ankle = shoes.matrix_world.inverted() @ bones[f'foot_{side}'].head_local
        mtp = shoes.matrix_world.inverted() @ bones[f'ball_{side}'].head_local
        mtp_forward = -(mtp.y - ankle.y)
        indices = {g.index for g in groups.values()}
        count = 0
        for v in shoes.data.vertices:
            co = shoes.matrix_world @ v.co
            if sign * co.x <= 0 or not any(g.group in indices and g.weight > 0 for g in v.groups):
                continue
            forward = -(co.y - ankle.y)
            calf = 0.6 * smooth((co.z - (ankle.z + 0.01)) / 0.05)
            # Full toe weight AT the joint: a vertex ahead of it that keeps
            # some foot weight swings down into the floor as the heel rises.
            toe = smooth((forward - (mtp_forward - 0.04)) / 0.04) * (1 - calf)
            for name, weight in (('calf', calf), ('foot', 1 - calf - toe), ('ball', toe)):
                group = groups[name]
                if weight > 1e-4:
                    group.add([v.index], weight, 'REPLACE')
                else:
                    group.remove([v.index])
            count += 1
        changed[side] = count
    return changed


def frame_matrix(axis_y, hinge):
    """Orthonormal frame with Y along the bone and X along the hinge axis."""
    y = axis_y.normalized()
    x = (hinge - y * hinge.dot(y)).normalized()
    z = x.cross(y)
    return Matrix((x, y, z)).transposed()


class Rig:
    def __init__(self, rig, frame):
        self.rig, self.frame = rig, frame
        bones = rig.data.bones
        self.rest = {b.name: b.matrix_local.to_3x3().normalized() for b in bones}
        self.rest_frames = {}
        for side in ('l', 'r'):
            hip, knee = bones[f'thigh_{side}'].head_local, bones[f'calf_{side}'].head_local
            ankle = bones[f'foot_{side}'].head_local
            hinge = (knee - hip).cross(ankle - knee)
            self.rest_frames[f'thigh_{side}'] = frame_matrix(knee - hip, hinge)
            self.rest_frames[f'calf_{side}'] = frame_matrix(ankle - knee, hinge)
            shoulder, elbow = bones[f'upperarm_{side}'].head_local, bones[f'lowerarm_{side}'].head_local
            wrist = bones[f'hand_{side}'].head_local
            hinge = (elbow - shoulder).cross(wrist - elbow)
            self.rest_frames[f'upperarm_{side}'] = frame_matrix(elbow - shoulder, hinge)
            self.rest_frames[f'lowerarm_{side}'] = frame_matrix(wrist - elbow, hinge)

    def head(self, name):
        return self.rig.pose.bones[name].head.copy()

    def place(self, name, delta, head=None):
        """Set a bone's armature-space orientation to `delta` applied to its rest orientation."""
        bone = self.rig.pose.bones[name]
        head = bone.head.copy() if head is None else head
        bone.matrix = Matrix.Translation(head) @ (delta @ self.rest[name]).to_4x4()
        bpy.context.view_layer.update()

    def place_frame(self, name, axis_y, hinge, head=None):
        new = frame_matrix(axis_y, hinge)
        self.place(name, new @ self.rest_frames[name].transposed(), head)

    def pose(self, f: gait.Frame, cycle: gait.Cycle):
        fr = self.frame
        # Pose with NO Action assigned: an assigned Action is evaluated again on
        # a depsgraph update and can overwrite the bones placed so far.
        rest_pose(self.rig)
        pelvis = q_up(f.turn) @ q_forward(f.drop) @ q_left(f.tilt)
        self.place('pelvis', pelvis.to_matrix(), fr.point(f.pelvis))
        for name, (lean, turn) in zip(('spine_01', 'spine_02', 'spine_03'), f.spine):
            self.place(name, (q_up(turn) @ q_left(lean)).to_matrix())
        lean = f.spine[-1][0]
        self.place('neck_01', q_left(0.5 * (lean + f.head[0])).to_matrix())
        self.place('Head', (q_up(f.head[1]) @ q_left(f.head[0])).to_matrix())
        thorax = q_up(f.spine[-1][1]) @ q_left(f.spine[-1][0])
        error = 0.0
        for side in ('l', 'r'):
            leg = f.legs[side]
            hip, knee, ankle = fr.point(leg.hip), fr.point(leg.knee), fr.point(leg.ankle)
            error = max(error, (self.head(f'thigh_{side}') - hip).length)
            hinge = (knee - hip).cross(ankle - knee)
            if hinge.length < 1e-6:
                raise ValueError('straight knee: no hinge axis')
            self.place_frame(f'thigh_{side}', knee - hip, hinge)
            self.place_frame(f'calf_{side}', ankle - knee, hinge)
            error = max(error, (self.head(f'foot_{side}') - ankle).length)
            self.place(f'foot_{side}', q_left(-leg.pitch).to_matrix())
            self.place(f'ball_{side}', q_left(-(leg.pitch + leg.toe)).to_matrix())
            self.arm(side, thorax, *f.arms[side])
        self.skirt(f)
        for bone in self.rig.pose.bones:
            if bone.name.startswith(FINGERS):
                bone.rotation_quaternion = Quaternion((1, 0, 0), 0.30 if bone.name.endswith(('_01_l', '_01_r')) else 0.42)
        self.rig.pose.bones['Ball_Control'].scale = (0, 0, 0)
        bpy.context.view_layer.update()
        return error

    def arm(self, side, thorax, shoulder, elbow, out):
        sign = 1 if side == 'l' else -1
        local = Vector((sign * math.sin(out), -math.sin(shoulder) * math.cos(out), -math.cos(shoulder) * math.cos(out)))
        upper = thorax @ local
        # The forearm bends forward and a little toward the midline.
        ahead = thorax @ Vector((-sign * 0.28, -1.0, 0.0))
        ahead = (ahead - upper * ahead.dot(upper)).normalized()
        fore = upper * math.cos(elbow) + ahead * math.sin(elbow)
        hinge = upper.cross(fore)
        self.place_frame(f'upperarm_{side}', upper, hinge)
        self.place_frame(f'lowerarm_{side}', fore, hinge)
        delta = (self.rig.pose.bones[f'lowerarm_{side}'].matrix.to_3x3().normalized() @ self.rest[f'lowerarm_{side}'].inverted())
        self.place(f'hand_{side}', delta)

    def skirt(self, f):
        thigh = {s: gait.sagittal(gait.sub(f.legs[s].knee, f.legs[s].hip)) for s in ('l', 'r')}
        for i in range(16):
            name = f'skirt_{i:02}'
            if name not in self.rig.pose.bones:
                continue
            a = math.tau * i / 16
            w = 0.5 + 0.5 * math.cos(a)
            # Panels lift with the thigh that pushes them; never below hanging.
            bend = 0.72 * max(0.0, w * thigh['l'] + (1 - w) * thigh['r'])
            bone = self.rig.pose.bones[name]
            rotation = Quaternion((1, 0, 0), -bend).to_matrix().to_4x4()
            bone.matrix = Matrix.Translation(bone.head) @ rotation @ Matrix.Translation(-bone.head) @ bone.matrix
        bpy.context.view_layer.update()


def key(rig, frame, previous):
    for bone in rig.pose.bones:
        if not bone.bone.use_deform:
            continue
        q = bone.rotation_quaternion
        last = previous.get(bone.name)
        if last is not None and q.dot(last) < 0:   # keep the shortest path between keys
            bone.rotation_quaternion = -q
        previous[bone.name] = bone.rotation_quaternion.copy()
        bone.keyframe_insert('rotation_quaternion', frame=frame, group=bone.name)
        if bone.name in ('pelvis', 'Ball_Control'):
            bone.keyframe_insert('location', frame=frame, group=bone.name)
        if bone.name == 'Ball_Control':
            bone.keyframe_insert('scale', frame=frame, group=bone.name)


def author(rig, frame, body, g):
    cycle = gait.Cycle(g, body)
    if g.name in bpy.data.actions:
        action = new_action(rig, g.name)
    else:
        rig.animation_data.action = None
        action = bpy.data.actions.new(g.name)
        action.use_fake_user = True
        rig.animation_data.action = action
    action['recipe'] = 'gait.py + author_gait.py: procedural treadmill gait, heel-flat-ball foot roll'
    action['gait'] = json.dumps({k: v for k, v in g.__dict__.items()})
    driver = Rig(rig, frame)
    previous, worst = {}, 0.0
    for i in range(g.frames + 1):
        bpy.context.scene.frame_set(i)
        worst = max(worst, driver.pose(cycle.frame(i / g.frames), cycle))
        rig.animation_data.action = action
        key(rig, i, previous)
        rig.animation_data.action = None
    for curve in action.fcurves:
        for k in curve.keyframe_points:
            k.interpolation = 'LINEAR'
    rig.animation_data.action = action
    return action, worst, cycle


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    source, out = args.input.parent.resolve(), args.output.resolve()
    if source == out or (out / 'netball-athlete.blend').exists():
        raise ValueError('Write a fresh candidate; keep the preceding editable master.')
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(args.input))
    rig = bpy.data.objects['Netball_Athlete']
    shoes = bpy.data.objects['Athlete_Shoes']

    def fingerprint(action):
        return [(c.data_path, c.array_index, [(tuple(k.co), k.interpolation) for k in c.keyframe_points]) for c in action.fcurves]
    untouched = {a.name: fingerprint(a) for a in bpy.data.actions if a.name not in ('Jog', 'Run')}
    body, frame = measure_body(rig, shoes)
    print('GAIT_BODY', json.dumps(body.__dict__), 'floor', frame.floor, flush=True)
    rebound = rebind_shoes(rig, shoes)
    print('GAIT_SHOES', json.dumps(rebound), flush=True)
    receipts = {}
    for g in (gait.JOG, gait.RUN):
        action, worst, cycle = author(rig, frame, body, g)
        receipts[g.name] = {'frames': g.frames, 'fps': g.fps, 'speed': g.speed, 'cadence': round(g.cadence, 1),
                            'strideLengthM': round(g.stride_length, 3), 'duty': g.duty,
                            'toeOffFootPitchDeg': round(math.degrees(cycle.to_pitch), 2),
                            'maxJointPlacementErrorM': round(worst, 6)}
        print('GAIT_AUTHORED', g.name, json.dumps(receipts[g.name]), flush=True)
        if worst > 0.002:
            raise AssertionError(f'{g.name}: rig joints miss the gait targets by {worst:.4f} m')
    assert untouched == {a.name: fingerprint(a) for a in bpy.data.actions if a.name not in ('Jog', 'Run')}
    rest_pose(rig)
    bpy.context.scene.frame_set(0)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.data.objects:
        if obj == rig or obj.get('bravenRole'):
            obj.hide_set(False)
            obj.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.gltf(filepath=str(out / 'netball-athlete.glb'), export_format='GLB', use_selection=True,
        export_animations=True, export_animation_mode='ACTIONS', export_frame_range=False, export_force_sampling=True,
        export_skins=True, export_extras=True, export_def_bones=True, export_morph=True, export_materials='EXPORT',
        export_image_format='AUTO', export_yup=True)
    rig.animation_data.action = bpy.data.actions['Jog']
    bpy.context.scene.frame_start, bpy.context.scene.frame_end = 0, gait.JOG.frames
    bpy.context.scene.frame_set(0)
    bpy.ops.wm.save_as_mainfile(filepath=str(out / 'netball-athlete.blend'))
    shutil.copy2(source / 'athlete-source.blend', out / 'athlete-source.blend')
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    metadata = json.loads((source / 'movement-library.json').read_text())
    correction = {'clips': ['Jog', 'Run'], 'recipe': 'gait.py + author_gait.py', 'gaits': receipts,
                  'shoeWeights': {'rule': 'calf on the collar only; sole on foot; toe bone from 4 cm behind the ball joint',
                                  'verticesPerSide': rebound},
                  'body': body.__dict__, 'unchangedActions': sorted(untouched),
                  'parentAssetSha256': metadata['assetSha256']}
    metadata.pop('jogCorrection', None)
    metadata.update(assetSha256=digest(out / 'netball-athlete.glb'), gaitRebuild=correction)
    (out / 'movement-library.json').write_text(json.dumps(metadata, indent=2))
    manifest = json.loads((source / 'manifest.json').read_text())
    manifest.pop('jogCorrection', None)
    manifest.update(revision=9, parentAssetSha256=manifest['files']['netball-athlete.glb']['sha256'], gaitRebuild=correction)
    if 'Run' not in manifest['animations']:
        manifest['animations'] = sorted(manifest['animations'] + ['Run'], key=str.lower)
    manifest['files'] = {n: {'bytes': (out / n).stat().st_size, 'sha256': digest(out / n)} for n in ('netball-athlete.glb', 'netball-athlete.blend')}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    for name in ('gait.py', 'author_gait.py', 'measure_gait.py', 'motion.py', 'correct_jumps.py', 'realism.v1.json'):
        shutil.copy2(HERE / name, out / name)
    print('GAIT_CANDIDATE', metadata['assetSha256'], flush=True)


if __name__ == '__main__':
    main()
