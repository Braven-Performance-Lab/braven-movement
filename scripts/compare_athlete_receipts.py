"""What moved when the figures changed body: two sets of render receipts, phase by phase.

A pixel comparison cannot answer this, because a different body moves almost
every pixel. The receipts measure what a figure must get right, on the posed
body that was drawn, so this reads them and nothing else:

- `girdle.ballAnchorErrorMm`: how far the ball is from where the solve put
  it, because the ball is placed from this rig's shoulders;
- `girdle.verdict`: whether this rig followed the transmitted girdle;
- the nearest digit to the ball surface on each hand that HOLDS it
  (`hands.<side>.surfaceClearanceMm.<digit>.nearestOnBone`). Which hand holds
  is read from the job (`phases[].grip`, one key per holding hand), because
  the receipt does not say; the free hand of a one-hand hold, 219 to 980 mm
  from the ball, is never counted (review round 1);
- `bodyClearanceMm`: whether any part of the body is inside the ball.

Both sides must come from the same jobs, and the job files given must be
those jobs: each receipt's `jobSha256` is compared with the other side's and
with the SHA-256 of the job file. A phase on one side only, or one that holds
the ball on one side only, is refused, never dropped.

    python scripts/compare_athlete_receipts.py --before out/step5-render-rig --after out/step5-shared --jobs spikes/poc-output --out out/step5-moved.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from pathlib import Path

DIGITS = ("thumb", "index", "middle", "ring", "pinky")


def receipts(directory: Path) -> dict:
    return {path.name.removesuffix(".render.json"): json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(directory.glob("*.render.json"))}


def nearest_digit(phase: dict, side: str, holding_sides):
    hand = (phase.get("hands") or {}).get(side)
    if not phase.get("holding") or not hand or side not in holding_sides:
        return None
    return min(hand["surfaceClearanceMm"][digit]["nearestOnBone"] for digit in DIGITS)


def phase_row(drill: str, before: dict, after: dict, holding_sides) -> dict:
    row = {"drill": drill, "phase": before["name"], "holding": before["holding"],
           "holdingHands": sorted(holding_sides)}
    if after["holding"] != before["holding"]:
        raise SystemExit(f"{drill}.{before['name']}: holds the ball on one side only")
    for label, phase in (("before", before), ("after", after)):
        girdle, body = phase["girdle"], phase.get("bodyClearanceMm") or {}
        row[label] = {
            "girdle": girdle["verdict"],
            "ballAnchorErrorMm": girdle["ballAnchorErrorMm"],
            "nearestDigitMm": {side: nearest_digit(phase, side, holding_sides) for side in ("l", "r")},
            "bodyDeepestMm": body.get("deepestMm"),
            "bodyVerticesInside": body.get("verticesInside"),
        }
    return row


def job_grips(jobs_dir: Path, drill: str, job_sha256: str) -> dict:
    """The hands that hold the ball in each phase, from the job the receipts name."""
    path = jobs_dir / f"{drill}.job.json"
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != job_sha256:
        raise SystemExit(f"{drill}: {path} is not the job these receipts were drawn from")
    job = json.loads(path.read_text(encoding="utf-8"))
    return {phase["name"]: set(phase.get("grip") or {}) for phase in job["phases"]}


def compare(before_dir: Path, after_dir: Path, jobs_dir: Path) -> dict:
    before_all, after_all = receipts(before_dir), receipts(after_dir)
    if set(before_all) != set(after_all):
        raise SystemExit(f"the two sides render different drills: {sorted(set(before_all) ^ set(after_all))}")
    rows, failed = [], {}
    for drill in sorted(before_all):
        b, a = before_all[drill], after_all[drill]
        if b["jobSha256"] != a["jobSha256"]:
            raise SystemExit(f"{drill}: the two sides were rendered from different jobs")
        failed[drill] = {"before": b["failedPhases"], "after": a["failedPhases"]}
        grips = job_grips(jobs_dir, drill, b["jobSha256"])
        after_by_name = {p["name"]: p for p in a["phases"]}
        unpaired = {p["name"] for p in b["phases"]} ^ set(after_by_name)
        if unpaired:
            raise SystemExit(f"{drill}: phases on one side only: {sorted(unpaired)}")
        for phase in b["phases"]:
            rows.append(phase_row(drill, phase, after_by_name[phase["name"]],
                                  grips.get(phase["name"], set())))
    return {"before": {"dir": str(before_dir), "athlete": next(iter(before_all.values())).get("athlete")},
            "after": {"dir": str(after_dir), "athlete": next(iter(after_all.values())).get("athlete")},
            "failedPhases": failed, "rows": rows, "summary": summary(rows)}


def summary(rows: list) -> dict:
    def median(label, key):
        return round(statistics.median(r[label][key] for r in rows), 2)

    def digits(label):
        return [v for r in rows for v in r[label]["nearestDigitMm"].values() if v is not None]

    deeper = [f"{r['drill']}.{r['phase']}" for r in rows
              if (r["after"]["bodyDeepestMm"] or 0) < (r["before"]["bodyDeepestMm"] or 0) - 1.0]
    shallower = [f"{r['drill']}.{r['phase']}" for r in rows
                 if (r["after"]["bodyDeepestMm"] or 0) > (r["before"]["bodyDeepestMm"] or 0) + 1.0]
    return {
        "phases": len(rows),
        "ballAnchorErrorMedianMm": {"before": median("before", "ballAnchorErrorMm"),
                                    "after": median("after", "ballAnchorErrorMm")},
        "ballAnchorOver10Mm": {label: sum(r[label]["ballAnchorErrorMm"] > 10 for r in rows)
                               for label in ("before", "after")},
        "girdleVerdictChanged": [f"{r['drill']}.{r['phase']}: {r['before']['girdle']} -> {r['after']['girdle']}"
                                 for r in rows if r["before"]["girdle"] != r["after"]["girdle"]],
        "nearestDigitMedianMm": {label: round(statistics.median(digits(label)), 2)
                                 for label in ("before", "after")},
        "bodyInsideBallPhases": {label: sum((r[label]["bodyVerticesInside"] or 0) > 0 for r in rows)
                                 for label in ("before", "after")},
        "bodyDeeperByOver1Mm": deeper,
        "bodyShallowerByOver1Mm": shallower,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--before", required=True, type=Path)
    parser.add_argument("--after", required=True, type=Path)
    parser.add_argument("--jobs", required=True, type=Path,
                        help="the folder of the job files both sides were drawn from")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = compare(args.before, args.after, args.jobs)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
