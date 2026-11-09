"""A procedural running gait for the netball athlete, with no Blender import.

The jog and the run are the same model at two speeds. `cycle()` returns, for
one phase of the stride, where each ankle is, how each foot and toe is pitched,
where the pelvis is and how it is turned, and the trunk and arm angles. The
Blender recipe (`author_gait.py`) applies these targets to the rig; the
repository tests check them here.

How it is built, and why each part exists:

- STANCE IS A TREADMILL CONTACT. The contact point is fixed to the floor and
  the floor moves back at the running speed, so a planted foot never slides.
  The foot rolls over three pivots in turn: the heel (from initial contact to
  foot flat), the whole sole (flat), and the ball of the foot (heel rise to
  toe-off), with the toes flat on the floor while the heel lifts.
- THE PELVIS HEIGHT COMES FROM THE STANCE KNEE. During stance the knee follows
  a flexion profile (it bends to absorb, then extends), and the hip height is
  the height that leg geometry allows. In flight the pelvis follows a smooth
  arc that joins the two stances with matching height and velocity.
- THE SWING IS A SMOOTH PATH THROUGH TWO POSES. The ankle leaves the floor with
  the stance velocity, passes through the pose of peak knee flexion and the pose
  of peak hip flexion, and arrives at the next contact with the floor velocity.
- EVERY CURVE IS C1 AND PERIODIC. Cubic Hermite segments with matched end
  velocities replace the rectified sines of the old jog, whose knee changed
  angular velocity by 320 deg/s in one frame.

Coordinates here: x forward, y to the athlete's left, z up, metres, radians.
The pelvis travels at x = 0; the floor moves at -speed. Phase 0 is initial
contact of the LEFT foot; the right foot is the same cycle half a stride later.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

TAU = math.tau


# --------------------------------------------------------------------------
# Small vector helpers (tuples), so that this module needs no numpy.

def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def mul(a, s):
    return tuple(x * s for x in a)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def norm(a):
    return math.sqrt(dot(a, a))


def unit(a):
    n = norm(a)
    return mul(a, 1 / n)


def rot_x(v, a):
    """Rotate about the forward axis (roll); + lifts the left side."""
    x, y, z = v
    c, s = math.cos(a), math.sin(a)
    return (x, y * c - z * s, y * s + z * c)


def rot_y(v, a):
    """Rotate about the left axis; + tips the front DOWN (x toward -z)."""
    x, y, z = v
    c, s = math.cos(a), math.sin(a)
    return (x * c + z * s, y, -x * s + z * c)


def rot_z(v, a):
    """Rotate about the vertical axis; + turns the front to the left."""
    x, y, z = v
    c, s = math.cos(a), math.sin(a)
    return (x * c - y * s, x * s + y * c, z)


def hermite(p0, m0, p1, m1, t, span):
    """Cubic Hermite on [0, 1], with end velocities given per unit of `span`."""
    t2, t3 = t * t, t * t * t
    h00, h10 = 2 * t3 - 3 * t2 + 1, t3 - 2 * t2 + t
    h01, h11 = -2 * t3 + 3 * t2, t3 - t2
    return h00 * p0 + h10 * m0 * span + h01 * p1 + h11 * m1 * span


def spline(knots, values, slopes, t):
    """Piecewise cubic Hermite through knots, with the given slopes at each knot."""
    for i in range(len(knots) - 1):
        a, b = knots[i], knots[i + 1]
        if t <= b or i == len(knots) - 2:
            u = (t - a) / (b - a)
            return hermite(values[i], slopes[i], values[i + 1], slopes[i + 1], u, b - a)
    raise ValueError(t)


def interior_slopes(knots, values, first, last):
    """Catmull-Rom slopes inside, given slopes at both ends."""
    slopes = [first]
    for i in range(1, len(knots) - 1):
        slopes.append((values[i + 1] - values[i - 1]) / (knots[i + 1] - knots[i - 1]))
    slopes.append(last)
    return slopes


def limit_slopes(knots, values, slopes):
    """Fritsch-Carlson limit on interior slopes, so that no segment overshoots.

    End slopes are kept: they carry a velocity in from stance. An interior
    slope that disagrees in sign with a neighbouring secant becomes zero, and
    no slope may exceed three times its secants.
    """
    out = list(slopes)
    for i in range(1, len(knots) - 1):
        left = (values[i] - values[i - 1]) / (knots[i] - knots[i - 1])
        right = (values[i + 1] - values[i]) / (knots[i + 1] - knots[i])
        if left * right <= 0 or out[i] * left < 0:
            out[i] = 0.0
            continue
        bound = 3 * min(abs(left), abs(right))
        out[i] = math.copysign(min(abs(out[i]), bound), out[i])
    return out


def ease(t):
    """Smoothstep: zero velocity at both ends."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Body:
    """Rest geometry of one leg and the pelvis, measured from the rig.

    Offsets are for the LEFT side; the right side is the mirror (y negated).
    Foot points are relative to the ankle joint in the REST pose, in which the
    shoe is not flat: its heel is 3.2 cm above the ball of the foot. The
    defaults are the revision 8 rig (bones and the evaluated shoe mesh);
    `author_gait.py` measures them again from the rig it writes.
    """
    thigh: float = 0.46047
    shank: float = 0.38277
    pelvis_head: tuple = (0.01921, 0.0, 0.95016)  # pelvis bone head above the floor
    hip: tuple = (0.02446, 0.09483, 0.92312)      # left hip joint at rest, above the floor
    ankle: tuple = (0.00932, 0.17447, 0.08593)    # left ankle joint at rest, above the floor
    heel: tuple = (-0.04897, 0.0, -0.05588)       # lowest sole point at the back of the heel
    ball: tuple = (0.12967, 0.0, -0.08593)        # lowest sole point, under the forefoot
    mtp: tuple = (0.11266, 0.0, -0.06413)         # ball-of-foot joint (the toe bone's head)
    toe_tip: tuple = (0.067, 0.0, -0.019)         # front sole point of the shoe, relative to the MTP joint
    rest_shank_angle: float = -0.09642            # sagittal angle of knee->ankle at rest

    @property
    def flat_pitch(self):
        """Pitch (+ toes up) that puts heel and forefoot on the floor together."""
        return math.atan2(self.heel[2] - self.ball[2], self.ball[0] - self.heel[0])


@dataclass(frozen=True)
class Gait:
    """One running speed. Angles in degrees where noted, so they read like the norms."""
    name: str
    speed: float                 # m/s
    frames: int                  # frames per stride (two steps)
    fps: int = 60
    duty: float = 0.38           # stance fraction of the stride, per foot
    lead: float = 0.32           # fraction of the stance travel the heel lands ahead of the hip
    step_half_width: float = 0.06
    # Stance knee (deg) at initial contact and toe-off. Between them the knee
    # is whatever the leg solve gives for the pelvis height below.
    knee_ic: float = 18.0
    knee_to: float = 22.0           # the stance knee's minimum, reached at `knee_min_at` of stance
    knee_min_at: float = 0.88
    knee_to_rise: float = 4.0       # the knee is flexing again by toe-off, by this much (deg)
    # Pelvis height in stance: it drops by `bounce` (m), lowest at `bounce_at`
    # of stance, and leaves and meets the floor with the flight velocity.
    bounce: float = 0.055
    bounce_at: float = 0.45
    # The hip leaves the floor this much lower than it met it (m); the flight
    # rises by the same amount. Published hip and knee angles at contact and
    # toe-off put the toe-off hip about 2.5 cm lower at a jog.
    toe_off_drop: float = 0.025
    # Foot roll (fractions of stance) and pitches (deg, + toes up).
    foot_ic_pitch: float = 12.0
    foot_flat_at: float = 0.14
    heel_rise_at: float = 0.48
    ankle_to: float = -20.0      # ankle angle at toe-off, rel. rest (+ dorsiflexion)
    ankle_swing: float = 4.0     # ankle angle in mid swing
    # Swing via poses: phase of the stride, world thigh angle (deg, + forward), knee (deg).
    swing_knee_at: float = 0.70
    swing_knee: float = 95.0
    swing_knee_thigh: float = 10.0
    swing_hip_at: float = 0.87
    swing_hip_thigh: float = 30.0
    swing_hip_knee: float = 55.0
    # Pelvis (deg) and centre of mass.
    pelvis_tilt: float = 6.0     # mean anterior tilt relative to standing
    pelvis_tilt_amp: float = 2.0
    pelvis_drop: float = 4.0     # obliquity amplitude
    pelvis_turn: float = 4.0     # transverse rotation amplitude
    pelvis_sway: float = 0.012   # lateral shift toward the stance foot, m
    # Trunk and head (deg).
    trunk_lean: float = 6.0
    thorax_turn: float = 9.0     # counter-rotation of the thorax, world amplitude
    # Arms (deg): shoulder flexion in the thorax frame, elbow flexion.
    shoulder_mean: float = -8.0
    shoulder_amp: float = 26.0
    elbow_mean: float = 88.0
    elbow_amp: float = 12.0
    arm_out: float = 12.0
    arm_lead: float = 0.0        # phase shift of the arm relative to the opposite leg

    @property
    def stride_seconds(self):
        return self.frames / self.fps

    @property
    def cadence(self):
        return 120.0 / self.stride_seconds

    @property
    def stride_length(self):
        return self.speed * self.stride_seconds

    @property
    def stance_travel(self):
        return self.speed * self.duty * self.stride_seconds


# Fitted to published norms by `athlete/fit_gait.py`; the receipt lists the
# targets, their sources and what each fitted value reaches.
JOG = Gait(
    name='Jog', speed=3.0, frames=42, duty=0.3111, lead=0.2494, step_half_width=0.06,
    knee_ic=17.0413, knee_to=23.0651, bounce=0.0341, bounce_at=0.45, toe_off_drop=0.0,
    foot_ic_pitch=10.0148, foot_flat_at=0.14, heel_rise_at=0.3,
    ankle_swing=4.0, swing_knee_at=0.70, swing_knee=100.9914, swing_knee_thigh=10.0,
    swing_hip_at=0.87, swing_hip_thigh=38.7224, swing_hip_knee=55.0,
    pelvis_tilt=6.0, pelvis_tilt_amp=3.0, pelvis_drop=5.0, pelvis_turn=5.0, pelvis_sway=0.012,
    trunk_lean=6.0, thorax_turn=14.0,
    shoulder_mean=-8.0, shoulder_amp=22.0, elbow_mean=88.0, elbow_amp=14.0, arm_out=12.0,
)
RUN = Gait(
    name='Run', speed=4.5, frames=39, duty=0.2667, lead=0.2889, step_half_width=0.05,
    knee_ic=19.0863, knee_to=21.3948, bounce=0.0173, bounce_at=0.45, toe_off_drop=0.0002,
    foot_ic_pitch=11.0516, foot_flat_at=0.12, heel_rise_at=0.5075,
    ankle_swing=6.0, swing_knee_at=0.66, swing_knee=119.0216, swing_knee_thigh=18.0,
    swing_hip_at=0.85, swing_hip_thigh=53.3388, swing_hip_knee=70.0,
    pelvis_tilt=9.0, pelvis_tilt_amp=3.0, pelvis_drop=6.0, pelvis_turn=6.0, pelvis_sway=0.010,
    trunk_lean=9.0, thorax_turn=16.0,
    shoulder_mean=-10.0, shoulder_amp=30.0, elbow_mean=84.0, elbow_amp=16.0, arm_out=10.0,
)


# --------------------------------------------------------------------------

def knee_distance(body, knee_deg):
    """Hip-to-ankle distance at a knee flexion (law of cosines)."""
    k = math.radians(knee_deg)
    t, s = body.thigh, body.shank
    return math.sqrt(t * t + s * s + 2 * t * s * math.cos(k))


def mirror(v, side):
    return v if side == 'l' else (v[0], -v[1], v[2])


def pelvis_rotation(g, phase):
    """Tilt, obliquity, turn (radians) of the pelvis at a phase of the stride.

    Obliquity: the swing side drops in early stance (left stance at phase 0,
    so the right side drops: a negative roll). Turn: the swing-side hip comes
    forward, largest at mid swing of that leg.
    """
    w = TAU * phase
    tilt = math.radians(g.pelvis_tilt + g.pelvis_tilt_amp * math.cos(2 * w - TAU * 0.25))
    drop = -math.radians(g.pelvis_drop) * math.sin(TAU * phase / 1 + TAU * 0.07)
    turn = -math.radians(g.pelvis_turn) * math.sin(w + TAU * 0.05)
    return tilt, drop, turn


def rotate_pelvis(v, tilt, drop, turn):
    """Apply tilt (front down), then obliquity, then turn, to a pelvis-relative vector."""
    return rot_z(rot_x(rot_y(v, tilt), drop), turn)


def hip_position(g, body, phase, side, pelvis_z):
    tilt, drop, turn = pelvis_rotation(g, phase)
    offset = mirror(sub(body.hip, body.pelvis_head), side)
    centre = (0.0, pelvis_sway(g, phase), pelvis_z)
    return add(centre, rotate_pelvis(offset, tilt, drop, turn))


def pelvis_sway(g, phase):
    # Toward the stance foot: left (+y) around left mid-stance.
    return g.pelvis_sway * math.cos(TAU * (phase - g.duty * 0.45))


# ---- stance ---------------------------------------------------------------

def foot_point(body, point, pitch):
    """A foot point relative to the ankle, with the foot at a REST-relative pitch."""
    return rot_y((point[0], 0.0, point[2]), -pitch)


def toe_tip(body, leg):
    """The front sole point of the shoe for a solved leg (gait.py coordinates)."""
    mtp = add(leg.ankle, foot_point(body, body.mtp, leg.pitch))
    return add(mtp, foot_point(body, body.toe_tip, leg.pitch + leg.toe))


def stance_foot(g, body, s, roll=0.0):
    """Ankle position, rest-relative foot pitch and toe extension at stance progress s.

    Pitches here are relative to the FLOOR (+ toes up) until the return, which
    adds the rest offset. The heel lands on the floor and the foot rolls down
    onto it; the whole sole is then flat; then the foot turns about the
    ball-of-foot joint by `roll` (negative: heel up), with the toes left flat
    on the floor. `Cycle` solves the roll from the stance knee.
    """
    flat = body.flat_pitch
    heel_ic = g.lead * g.stance_travel
    shift = -g.stance_travel * s
    heel_x = heel_ic + shift
    if s < g.heel_rise_at:
        if s < g.foot_flat_at:
            roll = math.radians(g.foot_ic_pitch) * (1 - ease(s / g.foot_flat_at))
        else:
            roll = 0.0
        ankle = sub((heel_x, 0.0, 0.0), foot_point(body, body.heel, flat + roll))
        return ankle, flat + roll, 0.0
    # The ball-of-foot joint stays where it was when the heel began to rise.
    heel_rise_x = heel_ic - g.stance_travel * g.heel_rise_at
    flat_ankle = sub((heel_rise_x, 0.0, 0.0), foot_point(body, body.heel, flat))
    mtp = add(flat_ankle, foot_point(body, body.mtp, flat))
    mtp = (mtp[0] + heel_x - heel_rise_x, 0.0, mtp[2])
    ankle = sub(mtp, foot_point(body, body.mtp, flat + roll))
    return ankle, flat + roll, -roll


GRAVITY = 9.81
SWING_KNEE_LIMIT_DEG = 3.0
TOE_RELEASE = 0.25
PLANTAR_OVERRUN_DEG = 4.0


def flight_seconds(g):
    return (0.5 - g.duty) * g.stride_seconds


def flight_speeds(g):
    """Vertical pelvis speed at take-off and at landing, for a ballistic flight."""
    tf = flight_seconds(g)
    up = g.toe_off_drop / tf + GRAVITY * tf / 2
    return up, up - GRAVITY * tf


def stance_pelvis_offset(g, s):
    """Pelvis height in stance relative to its height at contact.

    The pelvis meets the floor with the landing speed of the flight, sinks to
    `bounce` below the contact height, and leaves `toe_off_drop` below it with
    the take-off speed.
    """
    up, down = flight_speeds(g)
    per_s = g.duty * g.stride_seconds          # seconds per unit of stance progress
    knots = [0.0, g.bounce_at, 1.0]
    values = [0.0, -g.bounce, -g.toe_off_drop]
    slopes = [down * per_s, 0.0, up * per_s]
    return spline(knots, values, slopes, s)


def flight_pelvis_offset(g, half):
    t = (half - g.duty) * g.stride_seconds
    up, _ = flight_speeds(g)
    return -g.toe_off_drop + up * t - GRAVITY * t * t / 2


# ---- leg solve ------------------------------------------------------------

def solve_knee(body, hip, ankle, pole):
    """Two-bone solve: knee position for hip and ankle, bending toward `pole`."""
    t, s = body.thigh, body.shank
    axis = sub(ankle, hip)
    d = norm(axis)
    reach = (t + s) * 0.9995
    if d > reach:
        raise ValueError(f'ankle out of reach by {d - reach:.4f} m')
    u = mul(axis, 1 / d)
    a = (t * t - s * s + d * d) / (2 * d)
    h = math.sqrt(max(0.0, t * t - a * a))
    p = sub(pole, mul(u, dot(pole, u)))
    p = unit(p)
    return add(hip, add(mul(u, a), mul(p, h)))


def sagittal(v):
    """Angle of a downward-ish vector from straight down, + forward."""
    return math.atan2(v[0], -v[2])


def knee_angle(hip, knee, ankle):
    a, b = sub(knee, hip), sub(ankle, knee)
    c = max(-1.0, min(1.0, dot(a, b) / (norm(a) * norm(b))))
    return math.acos(c)


# ---- the cycle ------------------------------------------------------------

@dataclass
class Leg:
    hip: tuple
    knee: tuple
    ankle: tuple
    pitch: float          # foot pitch relative to the rest pose, radians, + toes up
    toe: float            # toe extension, radians
    contact: bool
    ankle_angle: float    # radians, anatomical, + dorsiflexion


@dataclass
class Frame:
    phase: float
    pelvis: tuple                 # pelvis bone head position
    tilt: float
    drop: float
    turn: float
    legs: dict = field(default_factory=dict)
    spine: list = field(default_factory=list)   # (lean, turn) per spine bone, world
    head: tuple = (0.0, 0.0)
    arms: dict = field(default_factory=dict)    # side -> (shoulder, elbow, out), radians


class Cycle:
    """Precomputes the parts of the cycle that need numeric slopes."""

    def __init__(self, g: Gait, body: Body = Body()):
        self.g, self.body = g, body
        joint = foot_point(body, body.mtp, body.flat_pitch)
        # Past this roll the ankle stands straight over the ball of the foot,
        # and more heel lift LOWERS it again.
        self.roll_limit = -(math.pi / 2 - math.atan2(-joint[2], joint[0]))
        self.z_contact = self._solve_contact_height()
        h = 1e-5
        hr = g.heel_rise_at
        self.knee_heel_rise = self._knee_for(hr * g.duty, 'l', hr, 0.0)
        self.knee_heel_rise_rate = (self.knee_heel_rise - self._knee_for((hr - h) * g.duty, 'l', hr - h, 0.0)) / h
        self.to_pitch = self._roll(g.duty - 1e-9, 'l', 1.0)
        self.to_pitch_rate = (self.to_pitch - self._roll((1 - h) * g.duty, 'l', 1 - h)) / h   # per unit s
        self._swing = {side: self._swing_path(side) for side in ('l', 'r')}

    # Local phase of a leg: 0 at its own initial contact.
    def local(self, phase, side):
        return (phase - (0.0 if side == 'l' else 0.5)) % 1.0

    def _stance_leg(self, phase, side, s, roll=None):
        g, body = self.g, self.body
        if roll is None:
            roll = self._roll(phase, side, s)
        ankle, pitch, toe = stance_foot(g, body, s, roll)
        ankle = (ankle[0], (1 if side == 'l' else -1) * g.step_half_width, ankle[2])
        return ankle, pitch, toe

    def _knee_for(self, phase, side, s, roll):
        """Knee flexion (radians) the leg needs for a stance foot at this roll."""
        body = self.body
        ankle, _, _ = self._stance_leg(phase, side, s, roll)
        hip = hip_position(self.g, body, phase, side, self.pelvis_z(phase))
        d = norm(sub(ankle, hip))
        t, k = body.thigh, body.shank
        if d >= t + k:
            return 0.0
        return math.pi - math.acos(max(-1.0, min(1.0, (t * t + k * k - d * d) / (2 * t * k))))

    def knee_target(self, s):
        """Stance knee from heel rise to toe-off.

        It extends to its minimum `knee_to` in late stance (`knee_min_at`) and
        is flexing again by toe-off, as the knee of a runner does. A fixed
        heel-lift curve gave 830 deg/s of knee extension at toe-off; a knee
        that stopped exactly at toe-off made the heel lift at 1570 deg/s and
        pointed the foot to -46 degrees after toe-off.
        """
        g = self.g
        low = math.radians(g.knee_to)
        if s <= g.knee_min_at:
            span = g.knee_min_at - g.heel_rise_at
            u = (s - g.heel_rise_at) / span
            return hermite(self.knee_heel_rise, self.knee_heel_rise_rate, low, 0.0, u, span)
        span = 1 - g.knee_min_at
        u = (s - g.knee_min_at) / span
        rise = math.radians(g.knee_to_rise)
        return low + rise * u * u

    def _roll(self, phase, side, s):
        """Heel lift (radians, negative) that gives the target knee, by bisection."""
        g = self.g
        if s < g.heel_rise_at:
            return 0.0
        # The knee is the larger of the flat-foot knee and the target. A hard
        # maximum left a velocity corner where the heel starts to lift, so the
        # two join through a smooth maximum up to 2 degrees wide. Its width
        # grows from zero at heel rise, where the two curves are equal, so it
        # adds no step there.
        flat = self._knee_for(phase, side, s, 0.0)
        width = math.radians(2.0) * ease((s - g.heel_rise_at) / 0.1)
        target = self.knee_target(s)
        top = max(flat, target)
        if width > 1e-9:
            target = top + width * math.log(math.exp((flat - top) / width) + math.exp((target - top) / width))
        else:
            target = top
        lo, hi = self.roll_limit, 0.0
        if flat >= target:
            return 0.0
        if self._knee_for(phase, side, s, lo) <= target:
            return lo
        for _ in range(40):
            mid = (lo + hi) / 2
            if self._knee_for(phase, side, s, mid) > target:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    def _ankle_angle(self, knee, ankle, pitch):
        """Anatomical ankle angle: 0 with the sole flat under a vertical shank.

        + is dorsiflexion. `pitch` is the rest-relative foot pitch.
        """
        return pitch - self.body.flat_pitch - sagittal(sub(ankle, knee))

    def _solve_contact_height(self):
        """Pelvis height at initial contact that gives the prescribed contact knee."""
        g, body = self.g, self.body
        ankle, _, _ = self._stance_leg(0.0, 'l', 0.0, 0.0)
        d = knee_distance(body, g.knee_ic)
        z = body.pelvis_head[2]
        for _ in range(8):
            hip = hip_position(g, body, 0.0, 'l', z)
            horizontal = math.hypot(hip[0] - ankle[0], hip[1] - ankle[1])
            if horizontal >= d:
                raise ValueError(f'{g.name}: contact foot out of reach')
            z += ankle[2] + math.sqrt(d * d - horizontal * horizontal) - hip[2]
        return z

    def _pole(self, phase, side):
        _, _, turn = pelvis_rotation(self.g, phase)
        return rot_z((1.0, 0.0, 0.0), 0.5 * turn)

    def pelvis_z(self, phase):
        g = self.g
        half = phase % 0.5
        if half <= g.duty:
            return self.z_contact + stance_pelvis_offset(g, half / g.duty)
        return self.z_contact + flight_pelvis_offset(g, half)

    def _stance_state(self, phase, side):
        """Ankle, its phase velocity, and the ankle angle and its velocity, in stance."""
        g, body = self.g, self.body
        lp = self.local(phase, side)
        s = lp / g.duty
        ankle, pitch, toe = self._stance_leg(phase, side, s)
        z = self.pelvis_z(phase)
        hip = hip_position(g, body, phase, side, z)
        knee = solve_knee(body, hip, ankle, self._pole(phase, side))
        return ankle, pitch, toe, self._ankle_angle(knee, ankle, pitch), hip

    def _leg_angles(self, phase, side):
        """Leg direction, knee flexion and lateral ankle offset of a stance leg.

        These three are the exact inverse of the swing reconstruction below,
        so the swing joins stance with equal value and equal slope. A thigh
        angle is not: the leg is adducted, and the solve puts the knee in the
        plane of the pole, so a sagittal thigh angle left a corner at toe-off.
        """
        ankle, pitch, toe, angle, hip = self._stance_state(phase, side)
        knee = solve_knee(self.body, hip, ankle, self._pole(phase, side))
        return (sagittal(sub(ankle, hip)), knee_angle(hip, knee, ankle), ankle[1] - hip[1], angle)

    def _leg_direction(self, thigh_deg, knee_deg):
        """Sagittal hip-to-ankle direction of a via pose given as thigh and knee angles."""
        body = self.body
        th = math.radians(thigh_deg)
        sh = th - math.radians(knee_deg)
        dx = body.thigh * math.sin(th) + body.shank * math.sin(sh)
        dz = -(body.thigh * math.cos(th) + body.shank * math.cos(sh))
        return math.atan2(dx, -dz)

    def _swing_path(self, side):
        """Joint-space splines for the swing: thigh angle, knee flexion, lateral offset.

        The swing is built in JOINT space so that it can never ask for more
        reach than the leg has. A position spline for the ankle continued the
        backward stance velocity after toe-off and straightened the knee.
        """
        g = self.g
        start = 0.0 if side == 'l' else 0.5
        h = 1e-5
        to = (start + g.duty) % 1.0
        ic = (start + 1.0) % 1.0
        t0, k0, y0, ang0 = self._leg_angles(to - h, side)
        t0b, k0b, y0b, ang0b = self._leg_angles(to - 2 * h, side)
        t1, k1, y1, ang1 = self._leg_angles(ic, side)
        t1b, k1b, y1b, _ = self._leg_angles(ic + h, side)
        # Just after toe-off the thigh reaches its peak extension: the stance
        # velocity carries on into a short turn-round (`turn` of the stride).
        # The knee is already flexing at toe-off and needs no turn-round.
        turn = 0.045
        rt, rk = (t0 - t0b) / h, (k0 - k0b) / h
        tk = [g.duty, g.duty + turn, g.swing_knee_at, g.swing_hip_at, 1.0]
        thigh = [t0, t0 + rt * turn * 0.4, self._leg_direction(g.swing_knee_thigh, g.swing_knee),
                 self._leg_direction(g.swing_hip_thigh, g.swing_hip_knee), t1]
        thigh_slopes = interior_slopes(tk, thigh, rt, (t1b - t1) / h)
        thigh_slopes[1] = thigh_slopes[3] = 0.0
        # The knee also turns round just BEFORE contact: it extends to a
        # minimum, then flexes on into stance with the stance velocity.
        rk1 = (k1b - k1) / h
        # The drop to that minimum is the least that keeps the last segment
        # free of overshoot (Fritsch-Carlson: a slope at most 3x its secant).
        late = 0.03
        kk = [g.duty, g.swing_knee_at, g.swing_hip_at, 1.0 - late, 1.0]
        knee = [k0, math.radians(g.swing_knee), math.radians(g.swing_hip_knee),
                k1 - max(0.0, rk1) * late / 3, k1]
        knee_slopes = interior_slopes(kk, knee, rk, rk1)
        knee_slopes[1] = knee_slopes[3] = 0.0
        thigh_slopes = limit_slopes(tk, thigh, thigh_slopes)
        knee_slopes = limit_slopes(kk, knee, knee_slopes)
        knots = (tk, kk)
        lateral = ([g.duty, 1.0], [y0, y1], [(y0 - y0b) / h, (y1b - y1) / h])
        w0 = (ang0 - ang0b) / h
        # Ankle angle in early swing: it carries on plantarflexing for a short
        # time after toe-off, to a peak `PLANTAR_OVERRUN_DEG` past its toe-off
        # value, then dorsiflexes to clear the floor by mid swing. The time to
        # that peak is the least that keeps the segment from overshooting
        # (Fritsch-Carlson), so the peak is the real cycle minimum.
        overrun = math.radians(PLANTAR_OVERRUN_DEG)
        peak_at = g.duty + max(0.01, 3 * overrun / max(1e-9, -w0))
        ankle = ([g.duty, peak_at, g.swing_knee_at], [ang0, ang0 - overrun, math.radians(g.ankle_swing)], [w0, 0.0, 0.0])
        return (knots, thigh, thigh_slopes, knee, knee_slopes), lateral, ankle, None

    def leg(self, phase, side):
        g, body = self.g, self.body
        lp = self.local(phase, side)
        if lp < g.duty:
            ankle, pitch, toe, angle, hip = self._stance_state(phase, side)
            knee = solve_knee(body, hip, ankle, self._pole(phase, side))
            return Leg(hip, knee, ankle, pitch, toe, True, angle)
        (knots, thigh, ts, kn, ks), lateral, ankle_spline, _ = self._swing[side]
        hip = hip_position(g, body, phase, side, self.pelvis_z(phase))
        direction = spline(knots[0], thigh, ts, lp)
        k = max(math.radians(SWING_KNEE_LIMIT_DEG), spline(knots[1], kn, ks, lp))
        d = knee_distance(body, math.degrees(k))
        dy = spline(*lateral, lp)
        r = math.sqrt(max(1e-12, d * d - dy * dy))
        ankle = add(hip, (r * math.sin(direction), dy, -r * math.cos(direction)))
        knee = solve_knee(body, hip, ankle, self._pole(phase, side))
        shank = sagittal(sub(ankle, knee))
        angle = spline(*ankle_spline, min(lp, g.swing_knee_at))
        pitch = angle + shank + body.flat_pitch
        if lp > g.swing_knee_at:
            # Late swing: cross-fade from the held ankle angle to the contact
            # foot pitch, arriving with zero pitch velocity, as stance begins.
            w = ease((lp - g.swing_knee_at) / (1 - g.swing_knee_at))
            contact = body.flat_pitch + math.radians(g.foot_ic_pitch)
            pitch = (1 - w) * pitch + w * contact
            angle = pitch - body.flat_pitch - shank
        # After toe-off the toes stay level with the floor, as they were in
        # push-off, and are released smoothly by `TOE_RELEASE` of the stride.
        # Releasing them at once folded the toe tip into the floor while the
        # foot still hung near vertical (2.4 cm, measured on the shoe mesh).
        u = (lp - g.duty) / TOE_RELEASE
        toe = -(pitch - body.flat_pitch) * (1 - ease(u)) if u < 1 else 0.0
        return Leg(hip, knee, ankle, pitch, toe, False, angle)

    def frame(self, phase):
        g = self.g
        phase %= 1.0
        tilt, drop, turn = pelvis_rotation(g, phase)
        f = Frame(phase, (0.0, pelvis_sway(g, phase), self.pelvis_z(phase)), tilt, drop, turn)
        f.legs = {s: self.leg(phase, s) for s in ('l', 'r')}
        w = TAU * phase
        # Thorax counter-rotates against the pelvis; spread over three spine bones.
        thorax = math.radians(g.thorax_turn) * math.sin(w + TAU * 0.05)
        lean = math.radians(g.trunk_lean)
        f.spine = [(lean * k / 3, turn + (thorax - turn) * k / 3) for k in (1, 2, 3)]
        f.head = (math.radians(2.0), 0.0)  # level gaze; head faces forward
        for side in ('l', 'r'):
            # Each arm swings forward with the OPPOSITE leg: left arm forward
            # while the right thigh is forward (late right swing, phase ~0.37).
            shift = 0.0 if side == 'l' else 0.5
            c = math.cos(TAU * (phase - shift - (g.swing_hip_at - 0.5) - g.arm_lead))
            f.arms[side] = (math.radians(g.shoulder_mean + g.shoulder_amp * c),
                            math.radians(g.elbow_mean + g.elbow_amp * c),
                            math.radians(g.arm_out))
        return f

    def frames(self):
        return [self.frame(i / self.g.frames) for i in range(self.g.frames)]


def with_body(g: Gait, body: Body):
    return Cycle(g, body)


__all__ = ['Body', 'Gait', 'JOG', 'RUN', 'Cycle', 'Frame', 'Leg', 'replace']
