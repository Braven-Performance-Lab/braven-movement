"""Fit the free parameters of `gait.JOG` and `gait.RUN` to published running norms.

  python athlete/fit_gait.py [--receipt out.json]

This is the instrument behind the values in gait.py. It prints the fitted
values and what the gait model reaches with them, beside each target. The
model is graded by the same quantities in Blender afterwards
(`measure_gait.py`), on the rig and the shoe mesh that are drawn.

Hip angles are graded by their RANGE only. Fukuchi 2017 measures the hip
against a pelvis whose zero is not the standing pose of this rig, so its
peak values are not on this rig's scale; its range is.
"""
import argparse
import json
import math
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gait  # noqa: E402

SOURCES = {
    'F': 'Fukuchi, Fukuchi & Duarte 2017, PeerJ 5:e3298, Table 4 (treadmill 2.5/3.5/4.5 m/s)',
    'H': 'Heiderscheit et al. 2011, Med Sci Sports Exerc 43:296, Tables 1 and 3 (2.9 m/s, preferred step rate)',
    'T': 'Tsuji et al. 2015, J Phys Ther Sci 27, Table 4 (10.4 km/h)',
    'D': 'Dorn, Schache & Pandy 2012, J Exp Biol 215:1944, Table 2',
    'A': 'Arellano & Kram 2014, J Exp Biol 217:2456, Table 1 (3.0 m/s)',
    'P': 'Female runners, pelvis at 10/12/14 km/h, Front Sports Act Living 2025, Table 1',
}

# target, weight (deg or cm per unit cost), source. Jog values at 3.0 m/s are
# interpolated between Fukuchi's 2.5 and 3.5 m/s rows where marked.
TARGETS = {
    'Jog': {
        'kneeAtContact': (17.5, 2, 'H, T: 17.8 and 17.2 at 2.9 m/s'),
        'peakStanceKnee': (46.0, 3, 'H: 46.3 at 2.9 m/s'),
        'peakSwingKnee': (101.0, 5, 'F: 93.5 at 2.5, 108.7 at 3.5 m/s (interpolated)'),
        'peakDorsiflexion': (26.5, 3, 'F: 26.4 at 2.5, 26.5 at 3.5 m/s'),
        'ankleAtToeOff': (-20.0, 3, 'T: -20.1; F: max plantarflexion -16.6 to -20.5'),
        'ankleAtContact': (6.0, 3, 'T: 6.2 dorsiflexion'),
        'maxPlantarflexion': (-18.6, 3, 'F: max plantarflexion -16.6 at 2.5, -20.5 at 3.5 m/s (interpolated)'),
        'hipRange': (54.0, 4, 'F: 47.4 at 2.5, 60.8 at 3.5 m/s (peak to peak, interpolated)'),
        'pelvisOscillationCm': (7.0, 1.5, 'H: 8.7 cm at 2.9 m/s; median about 6 cm (centre of mass)'),
    },
    'Run': {
        'kneeAtContact': (20.0, 2, 'unconfirmed at 4.5 m/s; slightly above the jog value'),
        'peakStanceKnee': (46.0, 3, 'unconfirmed at 4.5 m/s; jog value kept'),
        'peakSwingKnee': (119.0, 5, 'F: 119.1 at 4.5 m/s'),
        'peakDorsiflexion': (26.8, 3, 'F: 26.8 at 4.5 m/s'),
        'ankleAtToeOff': (-23.0, 3, 'F: max plantarflexion -23.2 at 4.5 m/s'),
        'ankleAtContact': (3.0, 3, 'unconfirmed; less dorsiflexion than the jog'),
        'maxPlantarflexion': (-23.2, 3, 'F: max plantarflexion -23.2 at 4.5 m/s'),
        'hipRange': (72.0, 4, 'F: 72.3 at 4.5 m/s (peak to peak)'),
        'pelvisOscillationCm': (6.5, 1.5, 'unconfirmed at 4.5 m/s'),
    },
}

# The stance knee minimum is held at 15-25 deg: a fit left free put it at
# 5 deg, a straight push-off knee that looks stiff. The stance fraction moves
# inside the published range for each speed (Dorn 2012; Heiderscheit 2011).
FREE = ['duty', 'lead', 'bounce', 'knee_ic', 'toe_off_drop', 'foot_ic_pitch', 'heel_rise_at',
        'swing_hip_thigh', 'swing_knee', 'knee_to']
LOW = [None, 0.10, 0.0, 10, 0.0, 0, 0.30, 20, 80, 15]
HIGH = [None, 0.45, 0.06, 22, 0.03, 25, 0.55, 60, 135, 25]
DUTY = {'Jog': (0.30, 0.36), 'Run': (0.25, 0.29)}


def grade(g, body=gait.Body(), samples=240):
    """What the model reaches, in the units of TARGETS, plus a penalty for shape faults."""
    c = gait.Cycle(g, body)
    # The heel lift at its limit anywhere in stance means the knee could not
    # follow its target there: the leg geometry, not the gait, set the knee.
    rolls = [c._roll(s * g.duty, 'l', s) for s in [g.heel_rise_at + (1 - g.heel_rise_at) * i / 20 for i in range(1, 21)]]
    penalty = 50.0 if min(rolls) - c.roll_limit < 1e-3 else 0.0
    frames = [c.frame(i / samples) for i in range(samples)]
    stance = [f for f in frames if f.legs['l'].contact]
    knee = lambda f: math.degrees(gait.knee_angle(f.legs['l'].hip, f.legs['l'].knee, f.legs['l'].ankle))
    hip = [math.degrees(gait.sagittal(gait.sub(f.legs['l'].knee, f.legs['l'].hip)) + f.tilt) for f in frames]
    ankle = [math.degrees(f.legs['l'].ankle_angle) for f in stance]
    cycle_ankle = [math.degrees(f.legs['l'].ankle_angle) for f in frames]
    z = [f.pelvis[2] for f in frames]
    zs = [f.pelvis[2] for f in stance]
    low_at = zs.index(min(zs)) / max(1, len(zs) - 1)
    # The pelvis is lowest in mid-stance, as the centre of mass is in running.
    if not 0.35 <= low_at <= 0.65:
        penalty += 3000 * min(abs(low_at - 0.35), abs(low_at - 0.65)) ** 2
    reached = {
        'kneeAtContact': knee(stance[0]),
        'peakStanceKnee': max(knee(f) for f in stance),
        'peakSwingKnee': max(knee(f) for f in frames),
        'peakDorsiflexion': max(ankle),
        # Events are evaluated exactly, not at the nearest sample: the ankle
        # moves at over 1000 deg/s at toe-off.
        'ankleAtToeOff': math.degrees(c.leg(g.duty - 1e-9, 'l').ankle_angle),
        'ankleAtContact': math.degrees(c.leg(0.0, 'l').ankle_angle),
        'maxPlantarflexion': min(cycle_ankle),
        'hipRange': max(hip) - min(hip),
        'pelvisOscillationCm': 100 * (max(z) - min(z)),
    }
    return reached, penalty, low_at


def fit(base, targets, body=gait.Body()):
    from scipy.optimize import minimize

    low, high = list(LOW), list(HIGH)
    low[0], high[0] = DUTY[base.name]

    def clip(x):
        return [min(max(v, a), b) for v, a, b in zip(x, low, high)]

    def cost(x):
        g = replace(base, **dict(zip(FREE, clip(x))))
        try:
            reached, penalty, _ = grade(g, body)
        except ValueError:
            return 1e4
        return sum(((reached[k] - t) / w) ** 2 for k, (t, w, _) in targets.items()) + penalty

    x0 = [getattr(base, n) for n in FREE]
    best = None
    for start in range(5):
        x = [v * (1 + 0.08 * (start - 2)) for v in x0]
        result = minimize(cost, x, method='Nelder-Mead', options=dict(maxiter=900, xatol=1e-3, fatol=1e-3))
        if best is None or result.fun < best.fun:
            best = result
    return dict(zip(FREE, clip(best.x))), float(best.fun)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--grade-only', action='store_true', help='grade the shipped values; do not fit')
    args = parser.parse_args()
    receipt = {'sources': SOURCES, 'gaits': {}}
    for base in (gait.JOG, gait.RUN):
        targets = TARGETS[base.name]
        if args.grade_only:
            values, g = {n: getattr(base, n) for n in FREE}, base
        else:
            values, _ = fit(base, targets)
            g = replace(base, **values)
        reached, penalty, low_at = grade(g)
        rows = {k: {'target': t, 'reached': round(reached[k], 1), 'source': src} for k, (t, w, src) in targets.items()}
        receipt['gaits'][base.name] = {'speed': g.speed, 'cadence': round(g.cadence, 1), 'strideLength': round(g.stride_length, 3),
                                       'duty': g.duty, 'values': {k: round(float(v), 4) for k, v in values.items()},
                                       'grade': rows, 'penalty': penalty, 'pelvisLowestAtStance': round(low_at, 2)}
        print(base.name, json.dumps(receipt['gaits'][base.name]['values']))
        for k, row in rows.items():
            print(f"   {k:20s} target {row['target']:7.1f}  reached {row['reached']:7.1f}")
        print('   penalty', penalty, 'pelvis lowest at', round(low_at, 2), 'of stance')
    if args.receipt:
        args.receipt.write_text(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
