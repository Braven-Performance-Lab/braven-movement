"""Coach-morning item 2: the elbow width at contact, at the shipped and previewed angle.

The guard in `test_elbow_pole.py` pins the two-handed mean to half a centimetre,
so a green test is not a reading. This prints every drill at both angles with
the test's own population rules: a catch only, both hands on the ball at the
contact frame for the two-handed group.

The previewed angle is applied through `preview_variants.applied`, the same
context the coach-pack exporter uses, and undone afterwards. If the patch did not
reach the solve, the two columns are equal, and this prints that as a failure.

    cd spikes
    pixi run --frozen python measure_elbow_width.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np

SPIKE_DIR = Path(__file__).resolve().parent
if str(SPIKE_DIR) not in sys.path:
    sys.path.insert(0, str(SPIKE_DIR))

from ball_track import has_ball  # noqa: E402
from movement_engine import library, load_character  # noqa: E402
from possession_solve import solve_movement  # noqa: E402
from preview_variants import VARIANTS, applied  # noqa: E402
from technique import has_technique, load_technique, technique_path  # noqa: E402

REFERENCE_CM = 38.6
VARIANT = "pole-37.3"


def contact_widths(character) -> dict[str, tuple[str, float]]:
    """Each catching drill's elbow separation at contact, in cm, with its group."""
    index = {name: n for n, name in enumerate(character.skeleton.joint_names)}
    out: dict[str, tuple[str, float]] = {}
    for movement_id in library():
        if not (has_ball(movement_id) and has_technique(movement_id)):
            continue
        if not load_technique(technique_path(movement_id)).possession_ready:
            continue
        result = solve_movement(character, movement_id)
        contact = result["possession"].contact_frame
        points = result["points"][contact]
        width = float(np.linalg.norm(points[index["l_lowarm"]] - points[index["r_lowarm"]]))
        states = [frame["ballState"] for frame in result["measurements"]]
        if "flight" not in states[:contact]:
            continue
        sides = set(result["possession"].frames[contact].sides)
        out[movement_id] = ("two" if sides == {"l", "r"} else "one", width)
    return out


def main() -> int:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=SPIKE_DIR, capture_output=True, text=True
    ).stdout.strip()
    character = load_character()
    shipped = contact_widths(character)
    with applied(VARIANT):
        previewed = contact_widths(character)
    after = contact_widths(character)

    found = VARIANTS[VARIANT]
    print(f"HEAD {head}")
    print(f"angle shipped {found['shipped']}  previewed {found['previewed']}  manual {REFERENCE_CM} cm")
    print(f"{'drill':44} {'hands':5} {'shipped':>8} {'preview':>8} {'moved':>7}")
    for movement_id in sorted(shipped):
        group, a = shipped[movement_id]
        b = previewed[movement_id][1]
        print(f"{movement_id:44} {group:5} {a:8.2f} {b:8.2f} {b - a:7.2f}")
    for group in ("two", "one"):
        a = [w for g, w in shipped.values() if g == group]
        b = [previewed[m][1] for m, (g, _) in shipped.items() if g == group]
        if a:
            print(
                f"mean {group}-handed ({len(a)}): shipped {np.mean(a):.2f} "
                f"[{min(a):.2f}..{max(a):.2f}]  previewed {np.mean(b):.2f} "
                f"[{min(b):.2f}..{max(b):.2f}]"
            )
    leaked = any(abs(after[m][1] - shipped[m][1]) > 1e-9 for m in shipped)
    inert = all(abs(previewed[m][1] - shipped[m][1]) < 1e-9 for m in shipped)
    print(f"patch leaked after the context: {leaked}")
    print(f"patch inert (preview equals shipped): {inert}")
    return 1 if (leaked or inert) else 0


if __name__ == "__main__":
    raise SystemExit(main())
