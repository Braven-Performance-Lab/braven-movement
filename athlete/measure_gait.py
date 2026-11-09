"""Measure a locomotion Action of the netball athlete against running gait norms.

Run inside Blender 4.5:
  blender -b <candidate>/netball-athlete.blend --python athlete/measure_gait.py -- \
      --action Jog --out <report.json>

Every angle is measured from the evaluated pose. Foot contact comes from the
evaluated shoe mesh, the surface that is drawn, not from a bone. The rig
faces -Y; Z is up.

Conventions (degrees), with ANATOMICAL zeros, as in the published norms:
  hip flexion      thigh in the pelvis frame, sagittal, 0 = vertical thigh
                   with the pelvis as it is at rest, + = thigh forward
  knee flexion     angle between thigh and shank, 0 = straight, + = bent
  ankle            0 = sole line (heel to forefoot, from the shoe mesh) at a
                   right angle to the shank; + = dorsiflexion, - = plantarflexion
  toe              + = toes bent up at the ball of the foot
  pelvis tilt      + = anterior; obliquity and rotation as ranges
  trunk lean       spine_01 head to neck head, + = forward of vertical
  shoulder         upper arm in the thorax frame, + = forward (flexion)
  elbow flexion    angle between upper arm and forearm, + = bent
"""
import argparse
import json
import math
import sys

import bpy
from mathutils import Matrix, Vector

DOWN, FORWARD, UP = Vector((0, 0, -1)), Vector((0, -1, 0)), Vector((0, 0, 1))
CONTACT_M = 0.012


def deg(x):
    return math.degrees(x)


def sagittal(v):
    """Signed angle of v from straight down, in the YZ plane, + = forward."""
    return deg(math.atan2(-v.y, -v.z))


def angle(a, b):
    return deg(a.angle(b))


class Pose:
    def __init__(self, rig):
        self.rig = rig
        self.world = rig.matrix_world

    def head(self, name):
        return self.world @ self.rig.pose.bones[name].head

    def tail(self, name):
        return self.world @ self.rig.pose.bones[name].tail

    def delta(self, name):
        """World rotation of a bone relative to its rest orientation."""
        pose = (self.world @ self.rig.pose.bones[name].matrix).to_3x3().normalized()
        rest = (self.world @ self.rig.data.bones[name].matrix_local).to_3x3().normalized()
        return pose @ rest.inverted()


def raw(pose, side, sole_rest=None):
    p = pose
    hip, knee, ankle = p.head(f'thigh_{side}'), p.head(f'calf_{side}'), p.head(f'foot_{side}')
    ball, toe = p.head(f'ball_{side}'), p.tail(f'ball_{side}')
    pelvis_inv = p.delta('pelvis').inverted()
    thorax_inv = p.delta('spine_03').inverted()
    shoulder, elbow, wrist = p.head(f'upperarm_{side}'), p.head(f'lowerarm_{side}'), p.head(f'hand_{side}')
    ankle_anatomical = None
    if sole_rest is not None:
        sole_now = p.delta(f'foot_{side}') @ sole_rest
        ankle_anatomical = 90.0 - angle(knee - ankle, sole_now)
    return {
        'ankle': ankle_anatomical,
        'hip': sagittal(pelvis_inv @ (knee - hip)),
        'knee': angle(knee - hip, ankle - knee),
        'ankleRaw': angle(knee - ankle, ball - ankle),
        'toe': angle(ball - ankle, toe - ball),
        'shoulder': sagittal(thorax_inv @ (elbow - shoulder)),
        'elbow': angle(elbow - shoulder, wrist - elbow),
    }


def pelvis_angles(pose):
    d = pose.delta('pelvis').to_euler('XYZ')
    # Rig faces -Y: a rotation about +X takes the top of the pelvis toward -Y,
    # which is forward, so + is anterior tilt.
    return {'tilt': deg(d.x), 'obliquity': deg(d.y), 'rotation': deg(d.z)}


def trunk(pose):
    v = pose.head('neck_01') - pose.head('spine_01')
    lean = deg(math.atan2(-v.y, v.z))
    shoulders = pose.head('upperarm_l') - pose.head('upperarm_r')
    hips = pose.head('thigh_l') - pose.head('thigh_r')
    s = math.atan2(shoulders.y, shoulders.x)
    h = math.atan2(hips.y, hips.x)
    return {'lean': lean, 'thoraxRotation': deg(s), 'pelvisLineRotation': deg(h),
            'counterRotation': deg((s - h + math.pi) % math.tau - math.pi)}


def shoe_vertices(shoes, depsgraph):
    evaluated = shoes.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    m = shoes.matrix_world
    points = [m @ v.co for v in mesh.vertices]
    evaluated.to_mesh_clear()
    return points


def sole(points, pose, side):
    """Lowest shoe vertex of one foot, and where along the foot it lies (0 heel, 1 toe)."""
    sign = 1 if side == 'l' else -1
    mine = [q for q in points if sign * q.x > 0]
    low = min(mine, key=lambda q: q.z)
    heel = max(mine, key=lambda q: q.y)
    front = min(mine, key=lambda q: q.y)
    # Position along the foot, measured in the foot's own frame so that a
    # pitched foot still reports heel or forefoot correctly.
    ankle, ball = pose.head(f'foot_{side}'), pose.head(f'ball_{side}')
    axis = (ball - ankle).normalized()
    along = [(q - ankle).dot(axis) for q in mine]
    lo, hi = min(along), max(along)
    position = ((low - ankle).dot(axis) - lo) / (hi - lo)
    return {'z': low.z, 'y': low.y, 'along': position,
            'heelZ': heel.z, 'toeZ': front.z}


def summary(values):
    return {'min': round(min(values), 2), 'max': round(max(values), 2), 'range': round(max(values) - min(values), 2),
            'mean': round(sum(values) / len(values), 2)}


def rough(values, fps):
    """Largest jump in angular velocity between consecutive frames, deg/s per frame.

    A smooth cycle changes velocity gradually; a corner (a rectified sine, a
    LINEAR key) shows as a single large change.
    """
    vel = [(b - a) * fps for a, b in zip(values, values[1:] + values[:1])]
    acc = [abs(b - a) for a, b in zip(vel, vel[1:] + vel[:1])]
    ordered = sorted(acc)
    median = ordered[len(ordered) // 2] or 1e-9
    return {'maxVelocityStep': round(max(acc), 1), 'medianVelocityStep': round(median, 1),
            'cornerRatio': round(max(acc) / median, 1)}


def measure(action_name):
    scene = bpy.context.scene
    fps = scene.render.fps / scene.render.fps_base
    rig = bpy.data.objects['Netball_Athlete']
    shoes = bpy.data.objects['Athlete_Shoes']
    action = bpy.data.actions[action_name]
    rig.animation_data.action = action
    first, last = (round(f) for f in action.frame_range)
    frames = list(range(first, last))  # the last key equals the first in a loop
    pose = Pose(rig)
    # Rest references, from the bind pose of the armature: the sole line of
    # each shoe (back of the heel to the lowest forefoot point).
    rig.animation_data.action = None
    for b in rig.pose.bones:
        b.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    rest_points = shoe_vertices(shoes, bpy.context.evaluated_depsgraph_get())
    sole_rest = {}
    for side in ('l', 'r'):
        sign = 1 if side == 'l' else -1
        mine = [q for q in rest_points if sign * q.x > 0]
        ankle = pose.head(f'foot_{side}')
        back = max(q.y for q in mine)
        heel = min((q for q in mine if q.y > back - 0.012), key=lambda q: q.z)
        fore = min((q for q in mine if ankle.y - q.y > 0.06), key=lambda q: q.z)
        sole_rest[side] = (fore - heel).normalized()
    rest = {s: raw(pose, s, sole_rest[s]) for s in ('l', 'r')}
    rig.animation_data.action = action
    rows = []
    bpy.context.view_layer.update()
    rest_scene = scene.frame_current
    for f in frames:
        scene.frame_set(f)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        points = shoe_vertices(shoes, depsgraph)
        row = {'frame': f, 'pelvisZ': pose.head('pelvis').z}
        for side in ('l', 'r'):
            row[side] = raw(pose, side, sole_rest[side])
            row[side]['sole'] = sole(points, pose, side)
        row['pelvis'] = pelvis_angles(pose)
        row['trunk'] = trunk(pose)
        rows.append(row)
    scene.frame_set(rest_scene)
    out_rest = {s: {k: round(v, 2) for k, v in rest[s].items() if isinstance(v, float)} for s in rest}

    floor = min(min(r['l']['sole']['z'], r['r']['sole']['z']) for r in rows)
    n = len(rows)
    out = {'action': action_name, 'fps': fps, 'framesPerCycle': n, 'cycleSeconds': round(n / fps, 4),
           'cadenceStepsPerMin': round(2 * 60 * fps / n, 1), 'floorZ': round(floor, 4),
           'contactThresholdM': CONTACT_M, 'restPose': out_rest, 'sides': {}}
    contact = {s: [r[s]['sole']['z'] - floor < CONTACT_M for r in rows] for s in ('l', 'r')}
    for side in ('l', 'r'):
        series = {
            'hipFlexion': [r[side]['hip'] for r in rows],
            'kneeFlexion': [r[side]['knee'] for r in rows],
            'ankleDorsiflexion': [r[side]['ankle'] for r in rows],
            'toeExtension': [r[side]['toe'] - rest[side]['toe'] for r in rows],
            'shoulderFlexion': [r[side]['shoulder'] for r in rows],
            'elbowFlexion': [r[side]['elbow'] for r in rows],
        }
        c = contact[side]
        stance = sum(c) / n
        # Initial contact: first contact frame after a non-contact frame.
        strikes = [i for i in range(n) if c[i] and not c[i - 1]]
        offs = [i for i in range(n) if not c[i] and c[i - 1]]
        side_out = {name: summary(v) for name, v in series.items()}
        side_out['smoothness'] = {name: rough(series[name], fps) for name in ('hipFlexion', 'kneeFlexion', 'ankleDorsiflexion')}
        side_out['stanceFraction'] = round(stance, 3)
        side_out['strikeFrames'] = [frames[i] for i in strikes]
        side_out['toeOffFrames'] = [frames[i] for i in offs]
        events = {}
        if strikes:
            i = strikes[0]
            events['atContact'] = {k: round(series[k][i], 1) for k in ('hipFlexion', 'kneeFlexion', 'ankleDorsiflexion')}
            events['contactAlongFoot'] = round(rows[i][side]['sole']['along'], 2)
        if offs:
            i = offs[0] - 1
            events['atToeOff'] = {k: round(series[k][i], 1) for k in ('hipFlexion', 'kneeFlexion', 'ankleDorsiflexion', 'toeExtension')}
            events['toeOffAlongFoot'] = round(rows[i][side]['sole']['along'], 2)
        stance_idx = [i for i in range(n) if c[i]]
        if stance_idx:
            events['peakStanceKnee'] = round(max(series['kneeFlexion'][i] for i in stance_idx), 1)
            events['peakStanceDorsiflexion'] = round(max(series['ankleDorsiflexion'][i] for i in stance_idx), 1)
            ys = [rows[i][side]['sole']['y'] for i in stance_idx]
            vel = [(rows[(i + 1) % n][side]['sole']['y'] - rows[i][side]['sole']['y']) * fps for i in stance_idx if c[(i + 1) % n]]
            events['stanceSoleTravelM'] = round(max(ys) - min(ys), 3)
            if vel:
                events['stanceSoleSpeed'] = summary(vel)
            along = [rows[i][side]['sole']['along'] for i in stance_idx]
            events['stanceContactAlongFoot'] = summary(along)
        swing = [i for i in range(n) if not c[i]]
        if swing:
            events['peakSwingKnee'] = round(max(series['kneeFlexion'][i] for i in swing), 1)
            events['swingClearanceM'] = round(max(rows[i][side]['sole']['z'] - floor for i in swing), 3)
        side_out['events'] = events
        out['sides'][side] = side_out
    both = [contact['l'][i] or contact['r'][i] for i in range(n)]
    double = [contact['l'][i] and contact['r'][i] for i in range(n)]
    out['flightFraction'] = round(1 - sum(both) / n, 3)
    out['doubleSupportFraction'] = round(sum(double) / n, 3)
    z = [r['pelvisZ'] for r in rows]
    out['pelvisVerticalOscillationCm'] = round(100 * (max(z) - min(z)), 2)
    out['pelvis'] = {k: summary([r['pelvis'][k] for r in rows]) for k in ('tilt', 'obliquity', 'rotation')}
    out['trunk'] = {k: summary([r['trunk'][k] for r in rows]) for k in ('lean', 'counterRotation')}
    out['series'] = {
        'frame': frames,
        'contactL': contact['l'], 'contactR': contact['r'],
        'pelvisZ': [round(v, 4) for v in z],
        'kneeL': [round(r['l']['knee'], 2) for r in rows],
        'hipL': [round(r['l']['hip'], 2) for r in rows],
        'ankleL': [round(r['l']['ankle'], 2) for r in rows],
        'shoulderL': [round(r['l']['shoulder'], 2) for r in rows],
        'elbowL': [round(r['l']['elbow'], 2) for r in rows],
        'soleZL': [round(r['l']['sole']['z'] - floor, 4) for r in rows],
        'soleYL': [round(r['l']['sole']['y'], 4) for r in rows],
        'soleAlongL': [round(r['l']['sole']['along'], 3) for r in rows],
    }
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', action='append', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    report = {'blend': bpy.data.filepath, 'actions': [measure(a) for a in args.action]}
    with open(args.out, 'w') as handle:
        json.dump(report, handle, indent=1)
    for a in report['actions']:
        print('GAIT', json.dumps({k: v for k, v in a.items() if k != 'series'}))


if __name__ == '__main__':
    main()
