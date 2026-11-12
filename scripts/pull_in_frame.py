"""The two-hand catch's pull-in checkpoints at 0.72 and at 0.76, and every
drill whose coaching phase and ball key share a name.

    cd spikes
    pixi run --frozen -- python -B ../scripts/pull_in_frame.py
    python -B scripts/pull_in_frame.py --pairs-only      (no solve, any Python)

WHY. Spec 1 decision 12.8: `netball_two_hand_catch_chest.json` grades its
`pull_in` phase at 0.72, and the ball key of the same name in
`netball_two_hand_catch_chest.technique.json` sits at 0.76. With 98 frames the
definition reads frame 70 and the key is at frame 74. Whether the graded frame
should move is the owner's decision under gate 4; this instrument gives him
the two readings and the population the name belongs to.

PART 1 SOLVES ONCE. `possession_solve.solve_movement` never reads the
definition, and `MovementDefinition.assess` reads the frame at
`round(at_phase * last)`. So both readings come from one solve, with the
definition moved in memory. Nothing under `spikes/movements/` is written.

PART 2 PAIRS BY NAME, which is a label, not a correspondence. It prints the
pairs and their gaps, so a person can judge which are by design; it cannot.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPIKES = ROOT / "spikes"
MOVEMENTS = SPIKES / "movements"
# Appended, not inserted first: the host test suite imports this module, and
# spikes/ placed first would hide tests/ modules of the same name.
if str(SPIKES) not in sys.path:
    sys.path.append(str(SPIKES))

DRILL = "netball_two_hand_catch_chest"
PHASE = "pull_in"
FRAMES_AT = (0.72, 0.76)
GAP = 1e-9


def frame_index(at_phase: float, frame_count: int) -> int:
    """The frame `MovementDefinition.assess` reads for a phase."""
    return round(at_phase * (frame_count - 1))


def moved_definition(definition, phase_name: str, at_phase: float):
    """The definition with one phase moved; every other field unchanged."""
    if phase_name not in {phase.name for phase in definition.phases}:
        raise SystemExit(f"REFUSED: {definition.movement_id} has no phase {phase_name!r}")
    phases = tuple(
        dataclasses.replace(phase, at_phase=at_phase) if phase.name == phase_name else phase
        for phase in definition.phases
    )
    return dataclasses.replace(definition, phases=phases)


def named_keys(document, path: str = "") -> list[tuple[str, str, float]]:
    """Every entry with both a name and an atPhase, at any depth."""
    found = []
    if isinstance(document, dict):
        if isinstance(document.get("name"), str) and "atPhase" in document:
            found.append((path, document["name"], float(document["atPhase"])))
        for key, value in document.items():
            found.extend(named_keys(value, f"{path}/{key}"))
    elif isinstance(document, list):
        for index, value in enumerate(document):
            found.extend(named_keys(value, f"{path}[{index}]"))
    return found


def pair(definition: dict, key_files: dict[str, dict]) -> list[dict]:
    """Each coaching phase paired with every ball or motion key of its name."""
    rows = []
    for phase in definition.get("phases", []):
        keys = [(file, path, at)
                for file, document in sorted(key_files.items())
                for path, name, at in named_keys(document) if name == phase["name"]]
        if not keys:
            continue
        at = float(phase["atPhase"])
        gap = max(abs(key_at - at) for _, _, key_at in keys)
        rows.append({"name": phase["name"], "atPhase": at, "keys": keys,
                     "gap": gap, "differs": gap > GAP})
    return rows


def library_pairs(movements: Path = MOVEMENTS) -> list[dict]:
    """Every drill definition with at least one key file beside it."""
    drills = []
    for path in sorted(movements.glob("*.json")):
        if path.name.count(".") != 1:
            continue
        definition = json.loads(path.read_text(encoding="utf-8"))
        if "phases" not in definition:
            continue
        key_files = {
            other.name: json.loads(other.read_text(encoding="utf-8"))
            for suffix in ("motion", "technique")
            for other in [path.with_name(f"{path.stem}.{suffix}.json")] if other.exists()
        }
        if key_files:
            drills.append({"drill": path.stem, "files": sorted(key_files),
                           "rows": pair(definition, key_files)})
    return drills


def print_pairs(drills: list[dict]) -> None:
    differ = [d for d in drills if any(r["differs"] for r in d["rows"])]
    agree = [d for d in drills if d["rows"] and not any(r["differs"] for r in d["rows"])]
    unpaired = [d for d in drills if not d["rows"]]
    print(f"PART 2: {len(drills)} drills have a definition and a key file; "
          f"{len(differ)} differ on a shared name, {len(agree)} agree, "
          f"{len(unpaired)} share no name.")
    for drill in drills:
        state = ("DIFFERS" if drill in differ else "agrees" if drill in agree else "no shared name")
        print(f"  {drill['drill']}  [{state}]  files: {', '.join(drill['files'])}")
        for row in drill["rows"]:
            keys = "; ".join(f"{file}{path} {at:.2f}" for file, path, at in row["keys"])
            mark = "  <- differs by %.2f" % row["gap"] if row["differs"] else ""
            print(f"      {row['name']:14s} phase {row['atPhase']:.2f}   key {keys}{mark}")
    print()


def measure_catch() -> int:
    from movement_definition import load
    from movement_engine import load_character
    from possession_solve import solve_movement

    definition = load(MOVEMENTS / f"{DRILL}.json")
    shipped = {phase.name: phase.at_phase for phase in definition.phases}[PHASE]
    technique = json.loads((MOVEMENTS / f"{DRILL}.technique.json").read_text(encoding="utf-8"))
    key = {name: at for _, name, at in named_keys(technique)}[PHASE]
    if (shipped, key) != FRAMES_AT:
        raise SystemExit(f"REFUSED: the files hold {shipped} and {key}, not {FRAMES_AT}")

    result = solve_movement(load_character(), DRILL)
    frames = result["measurements"]
    print(f"PART 1: {DRILL}, one possession solve, {len(frames)} frames.")
    readings = {}
    for at in FRAMES_AT:
        moved = moved_definition(definition, PHASE, at)
        readings[at] = moved.assess(frames).results[PHASE]
    control = definition.assess(frames).results[PHASE]
    if [r.measured for r in control] != [r.measured for r in readings[shipped]]:
        raise SystemExit("REFUSED: the moved definition at 0.72 does not reproduce the shipped one")
    print(f"  control: the shipped definition and the in-memory one at {shipped} read the same values.")
    for at in FRAMES_AT:
        label = "definition (shipped)" if at == shipped else "ball key"
        print(f"  {PHASE} at {at:.2f}, frame {frame_index(at, len(frames))}, the {label}:")
        for entry in readings[at]:
            band = f"{entry.checkpoint.minimum:.1f} to {entry.checkpoint.maximum:.1f}"
            print(f"      {entry.checkpoint.measure:26s} {entry.measured:9.2f}   band {band:14s} {entry.verdict}")
    first, last = (frame_index(at, len(frames)) for at in FRAMES_AT)
    print(f"  every frame from {first} to {last}:")
    for measure in (entry.checkpoint.measure for entry in readings[shipped]):
        series = "  ".join(f"{frames[i][measure]:.2f}" for i in range(first, last + 1))
        print(f"      {measure:26s} {series}")
    print()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs-only", action="store_true", help="skip the solve")
    arguments = parser.parse_args()
    if not arguments.pairs_only:
        measure_catch()
    print_pairs(library_pairs())
    return 0


if __name__ == "__main__":
    sys.exit(main())
