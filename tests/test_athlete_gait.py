"""What the athlete's procedural jog and run may claim (athlete/gait.py).

The jog in revision 8 was a set of rectified sines: cadence 116 steps/min,
a knee whose angular velocity jumped by 320 deg/s in one frame, a stance
knee locked at 13 degrees, no pelvis motion, no toe joint, and a "planted"
foot that slid at up to 2.8 m/s. These tests hold the claims that replace it.

- A PLANTED FOOT DOES NOT SLIDE. In stance the contact point is on the floor
  and moves back at exactly the running speed (a treadmill frame).
- NO CORNERS. Every joint angle and the pelvis height are C1: the largest
  change of velocity between samples halves when the sampling doubles. A
  corner does not shrink, and the detector is shown to catch one.
- THE NUMBERS ARE THE NORMS. The model reaches the published targets in
  athlete/fit_gait.py within stated tolerances.
- THE RUN IS NOT A FAST JOG. It has a longer stride, a longer flight, more
  knee and more arm, at a higher cadence.
- THE SWING NEVER USES ITS SAFETY LIMIT, and the swing foot clears the floor.

The checks run on the model, not on the Blender rig. The rig and the shoe
mesh are measured by athlete/measure_gait.py when a candidate is built.
"""
from __future__ import annotations

import math
import sys
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'athlete'))

import gait  # noqa: E402
import fit_gait  # noqa: E402

GAITS = (gait.JOG, gait.RUN)
CYCLES = {g.name: gait.Cycle(g) for g in GAITS}


def knee_deg(leg):
    return math.degrees(gait.knee_angle(leg.hip, leg.knee, leg.ankle))


def series(cycle, n, fn):
    return [fn(cycle.frame(i / n)) for i in range(n)]


def worst_velocity_step(values, period):
    n = len(values)
    dt = period / n
    vel = [(values[(i + 1) % n] - values[i]) / dt for i in range(n)]
    return max(abs(vel[(i + 1) % n] - vel[i]) for i in range(n))


QUANTITIES = {
    'knee': lambda f: knee_deg(f.legs['l']),
    'thigh': lambda f: math.degrees(gait.sagittal(gait.sub(f.legs['l'].knee, f.legs['l'].hip))),
    'ankle': lambda f: math.degrees(f.legs['l'].ankle_angle),
    'footPitch': lambda f: math.degrees(f.legs['l'].pitch),
    'toe': lambda f: math.degrees(f.legs['l'].toe),
    'pelvisHeightCm': lambda f: 100 * f.pelvis[2],
    'ankleXcm': lambda f: 100 * f.legs['l'].ankle[0],
    'ankleZcm': lambda f: 100 * f.legs['l'].ankle[2],
}


class PlantedFoot(unittest.TestCase):
    def test_contact_point_is_on_the_floor_and_moves_at_the_running_speed(self):
        for g in GAITS:
            c, body = CYCLES[g.name], gait.Body()
            n = 400
            for i in range(n):
                phase = i / n * g.duty * 0.999
                s = phase / g.duty
                leg = c.leg(phase, 'l')
                self.assertTrue(leg.contact)
                point = body.heel if s < g.heel_rise_at else body.mtp
                p = gait.add(leg.ankle, gait.foot_point(body, point, leg.pitch))
                if s < g.heel_rise_at:
                    self.assertAlmostEqual(p[2], 0.0, places=6, msg=f'{g.name} heel off the floor at s={s:.3f}')
                q_phase = phase + 1e-6
                q = gait.add(c.leg(q_phase, 'l').ankle, gait.foot_point(body, point, c.leg(q_phase, 'l').pitch))
                speed = (q[0] - p[0]) / (1e-6 * g.stride_seconds)
                if (q_phase / g.duty < g.heel_rise_at) == (s < g.heel_rise_at):
                    self.assertAlmostEqual(speed, -g.speed, delta=1e-3, msg=f'{g.name} foot slides at s={s:.3f}')


class NoCorners(unittest.TestCase):
    def test_every_quantity_is_c1(self):
        for g in GAITS:
            c = CYCLES[g.name]
            for name, fn in QUANTITIES.items():
                coarse = worst_velocity_step(series(c, 800, fn), g.stride_seconds)
                fine = worst_velocity_step(series(c, 1600, fn), g.stride_seconds)
                if coarse < 1e-6:
                    continue
                self.assertLess(fine, 0.7 * coarse, f'{g.name} {name}: a corner ({coarse:.1f} -> {fine:.1f})')

    def test_the_detector_catches_the_old_rectified_sine(self):
        # The revision 8 knee: .23 + .92 * max(0, -sin(w)). Its corner must not shrink.
        knee = lambda n: [math.degrees(.23 + .92 * max(0.0, -math.sin(math.tau * i / n))) for i in range(n)]
        coarse = worst_velocity_step(knee(800), 1.0333)
        fine = worst_velocity_step(knee(1600), 1.0333)
        self.assertGreater(fine, 0.9 * coarse)

    def test_the_cycle_loops(self):
        for g in GAITS:
            c = CYCLES[g.name]
            a, b = c.frame(0.0), c.frame(1.0 - 1e-9)
            for side in ('l', 'r'):
                for part in ('hip', 'knee', 'ankle'):
                    self.assertLess(gait.norm(gait.sub(getattr(a.legs[side], part), getattr(b.legs[side], part))), 1e-5)


class Norms(unittest.TestCase):
    TOLERANCE = {
        'kneeAtContact': 3.0, 'peakStanceKnee': 5.0, 'peakSwingKnee': 5.0, 'peakDorsiflexion': 8.0,
        'ankleAtToeOff': 5.0, 'ankleAtContact': 4.0, 'maxPlantarflexion': 6.0, 'hipRange': 8.0,
        'pelvisOscillationCm': 3.5,
    }

    def test_the_model_reaches_the_published_targets(self):
        for g in GAITS:
            reached, penalty, low_at = fit_gait.grade(g)
            self.assertEqual(penalty, 0.0, f'{g.name}: a shape fault (pelvis lowest at {low_at:.2f} of stance)')
            for key, (target, _, source) in fit_gait.TARGETS[g.name].items():
                self.assertAlmostEqual(reached[key], target, delta=self.TOLERANCE[key],
                                       msg=f'{g.name} {key}: {reached[key]:.1f} vs {target} ({source})')

    def test_cadence_and_stance(self):
        # Fukuchi 2017 Table 4 and Dorn 2012 Table 2: about 168-172 steps/min at
        # 3 m/s and 183.5 at 4.5 m/s; toe-off at about 32-35% (jog) and 28-30% (run).
        self.assertTrue(160 <= gait.JOG.cadence <= 176, gait.JOG.cadence)
        self.assertTrue(178 <= gait.RUN.cadence <= 192, gait.RUN.cadence)
        self.assertTrue(0.31 <= gait.JOG.duty <= 0.37)
        self.assertTrue(0.26 <= gait.RUN.duty <= 0.31)


class RunIsNotAFastJog(unittest.TestCase):
    def test_run_differs_in_form(self):
        jog, run = gait.JOG, gait.RUN
        self.assertGreater(run.stride_length, 1.3 * jog.stride_length)
        self.assertGreater(0.5 - run.duty, 0.5 - jog.duty)                 # longer flight
        self.assertGreater(run.cadence, jog.cadence)
        self.assertGreater(run.shoulder_amp, jog.shoulder_amp)
        jr, rr = fit_gait.grade(jog)[0], fit_gait.grade(run)[0]
        self.assertGreater(rr['peakSwingKnee'], jr['peakSwingKnee'] + 10)
        self.assertGreater(rr['hipRange'], jr['hipRange'] + 10)


class SwingRefusals(unittest.TestCase):
    def test_refuses_an_ankle_that_dorsiflexes_at_toe_off(self):
        # The swing ankle spline needs a plantarflexing ankle at toe-off; with a
        # dorsiflexing one its knots fall out of order. Tilt the stance ankle so
        # that it rises with phase, and the cycle must refuse.
        original = gait.Cycle._leg_angles

        def dorsiflexing(self, phase, side):
            direction, knee, lateral, angle = original(self, phase, side)
            return direction, knee, lateral, angle + 100.0 * phase

        with unittest.mock.patch.object(gait.Cycle, '_leg_angles', dorsiflexing):
            with self.assertRaisesRegex(ValueError, 'not plantarflexing at toe-off'):
                gait.Cycle(gait.JOG)


class Swing(unittest.TestCase):
    def test_never_reaches_the_safety_limit(self):
        for g in GAITS:
            knees = series(CYCLES[g.name], 1000, lambda f: knee_deg(f.legs['l']))
            self.assertGreater(min(knees), gait.SWING_KNEE_LIMIT_DEG + 2.0, g.name)

    def test_heel_ball_joint_and_toe_tip_clear_the_floor(self):
        body = gait.Body()
        for g in GAITS:
            c = CYCLES[g.name]
            for i in range(1000):
                leg = c.frame(i / 1000).legs['l']
                if leg.contact:
                    continue
                points = [gait.add(leg.ankle, gait.foot_point(body, p, leg.pitch)) for p in (body.heel, body.mtp)]
                points.append(gait.toe_tip(body, leg))
                for z in (p[2] for p in points):
                    self.assertGreater(z, -0.002, f'{g.name}: swing foot in the floor at phase {i / 1000:.3f}')


if __name__ == '__main__':
    unittest.main()
