"""A Blender job for ONE drill with its elbow pole angle overridden, beside the shipped job.

Coach-morning item 2 asks Erin to compare two renders of one drill, at the
shipped pole angle and at a previewed one. The pair must differ in that one
parameter, and each job must SAY which value it was solved with.

WHY NOT `preview_variants.applied`. That context patches
`contact_solve.ELBOW_POLE_ANGLE_DEGREES`, which changes the solve. But
`export_blender_job` imports the constant BY VALUE, so `solve_parameters` still
records the shipped 31.3, and `check_solve_parameters` compares against that same
stale value and passes. The job would be solved at 37.3 and say 31.3. That is the
failure `solve_parameters` exists to prevent, arriving from a path it cannot see.

WHAT THIS DOES INSTEAD. The per-drill override `elbowAngleDegrees`
(`technique.read_elbow_angle_degrees`) is read by the solve AND recorded by
`solve_parameters`. This replaces the drill's technique with a copy carrying the
override, for the duration of one build, in the three modules that load it by
name. No file under `movements/` is edited: the override exists only in memory
and in the job's `solveParameters`.

Both jobs are built in ONE process from ONE tree, so every other parameter is
equal between them, which is what `render_receipt.refuse_unverifiable_pair`
assumes and cannot check.

    cd spikes
    pixi run --frozen python export_override_job.py netball_deflect_high 37.3 <out-dir>

Writes <out-dir>/shipped/<drill>.job.json and <out-dir>/elbow-<angle>/<drill>.job.json.
"""

from __future__ import annotations

import contextlib
import dataclasses
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

SPIKE_DIR = Path(__file__).resolve().parent
if str(SPIKE_DIR) not in sys.path:
    sys.path.insert(0, str(SPIKE_DIR))

import contact_solve  # noqa: E402
import export_blender_job  # noqa: E402
import possession_solve  # noqa: E402
import technique  # noqa: E402
from movement_engine import load_character  # noqa: E402

# Every module that loads a technique BY NAME on the build path. A module added to
# this path later and missing here would solve with the shipped technique while
# the job recorded the override; `overridden` refuses that case by reading back.
LOADERS = (possession_solve, export_blender_job, contact_solve)


@contextlib.contextmanager
def overridden(movement_id: str, degrees: float):
    """Load `movement_id`'s technique with `elbow_angle_degrees` set, then restore."""
    original = technique.load_technique
    target = technique.technique_path(movement_id)

    def load(path):
        method = original(path)
        if Path(path).resolve() == Path(target).resolve():
            method = dataclasses.replace(method, elbow_angle_degrees=float(degrees))
        return method

    saved = {module: module.load_technique for module in LOADERS}
    for module in LOADERS:
        module.load_technique = load
    try:
        yield
    finally:
        for module, loader in saved.items():
            module.load_technique = loader


def contact_width_cm(character, movement_id: str) -> float:
    """The elbow separation at the contact frame, as `measure_elbow_width` reads it."""
    result = possession_solve.solve_movement(character, movement_id)
    index = {name: n for n, name in enumerate(character.skeleton.joint_names)}
    points = result["points"][result["possession"].contact_frame]
    return float(np.linalg.norm(points[index["l_lowarm"]] - points[index["r_lowarm"]]))


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(__doc__)
        return 2
    movement_id, degrees, out = argv[1], float(argv[2]), Path(argv[3])
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=SPIKE_DIR, capture_output=True, text=True
    ).stdout.strip()
    character = load_character()

    shipped_job = export_blender_job.build(character, movement_id)
    shipped_width = contact_width_cm(character, movement_id)
    with overridden(movement_id, degrees):
        override_job = export_blender_job.build(character, movement_id)
        override_width = contact_width_cm(character, movement_id)
    restored_width = contact_width_cm(character, movement_id)

    recorded = override_job["solveParameters"]["ELBOW_POLE_ANGLE_DEGREES"]
    problems = []
    if recorded != degrees:
        problems.append(f"the override job records {recorded}, not {degrees}")
    if abs(override_width - shipped_width) < 1e-6:
        problems.append("the override did not change the solve (inert)")
    if abs(restored_width - shipped_width) > 1e-9:
        problems.append("the override leaked past the context")
    if shipped_job["solveParameters"] == override_job["solveParameters"]:
        problems.append("the two jobs record the same solveParameters")

    label = f"elbow-{degrees:g}"
    # A REFUSED PAIR WRITES NOTHING. A job left on disk after a refusal looks
    # exactly like a good one, under a label that claims the overridden angle,
    # and whoever renders the folder next cannot tell. That is the mislabelled
    # pair this script exists to prevent.
    if not problems:
        for name, job in (("shipped", shipped_job), (label, override_job)):
            folder = out / name
            folder.mkdir(parents=True, exist_ok=True)
            (folder / f"{movement_id}.job.json").write_text(
                json.dumps(job, indent=2), encoding="utf-8"
            )

    print(f"HEAD {head}")
    print(f"shipped   records {shipped_job['solveParameters']}  contact width {shipped_width:.2f} cm")
    print(f"{label:9} records {override_job['solveParameters']}  contact width {override_width:.2f} cm")
    print(f"restored after the context: contact width {restored_width:.2f} cm")
    for problem in problems:
        print(f"REFUSED: {problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
