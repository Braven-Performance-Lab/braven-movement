"""Side-by-side table of the shoulder-reach options against the current render.

Every option file is a run of `ball_hand_gap_render.py` or
`girdle_option_probe.py`. "worse" counts phases whose anchor error rises by
more than 0.5 mm; the moves are measured against the first file.

    python scripts/compare_options.py out/reach-main.json A=out/reach-optA.json B=out/reach-optB.json C=out/reach-optC.json
"""
import json
import math
import statistics as st
import sys


def load(path):
    return {(r["movementId"], r["phase"]): r for r in json.load(open(path))["rows"] if "failed" not in r}


now = load(sys.argv[1])
runs = [("now", sys.argv[1])] + [tuple(a.split("=", 1)) for a in sys.argv[2:]]
print(f"{'':5s} {'miss med':>8s} {'miss max':>8s} {'anch med':>8s} {'anch max':>8s} {'>10':>4s} "
      f"{'worse':>5s} {'ball med':>8s} {'ball max':>8s} {'bone max':>8s}")
for tag, path in runs:
    run = load(path)
    if set(run) != set(now):
        print(f"{tag}: phases differ: {sorted(set(now) ^ set(run))}")
        continue
    miss = [e["offsetMm"] for r in run.values() for e in r["shoulders"].values()]
    anchor = [r["girdle"]["ballAnchorErrorMm"] for r in run.values()]
    worse = [k for k in now if run[k]["girdle"]["ballAnchorErrorMm"] > now[k]["girdle"]["ballAnchorErrorMm"] + 0.5]
    ball = [math.dist(now[k]["ballCentreM"], run[k]["ballCentreM"]) * 1000 for k in now]
    bone = [max(math.dist(now[k]["boneHeadsM"][n], run[k]["boneHeadsM"][n]) for n in now[k]["boneHeadsM"]) * 1000
            for k in now]
    print(f"{tag:5s} {st.median(miss):8.2f} {max(miss):8.2f} {st.median(anchor):8.2f} {max(anchor):8.2f} "
          f"{sum(a > 10 for a in anchor):4d} {len(worse):5d} {st.median(ball):8.1f} {max(ball):8.1f} {max(bone):8.1f}")
    for k in worse:
        print(f"      worse: {k[0][8:]}/{k[1]} {now[k]['girdle']['ballAnchorErrorMm']:.2f} -> "
              f"{run[k]['girdle']['ballAnchorErrorMm']:.2f} mm")
    for k, r in run.items():
        if r["girdle"]["ballAnchorErrorMm"] > 10:
            print(f"      over 10 mm: {k[0][8:]}/{k[1]} {r['girdle']['ballAnchorErrorMm']:.2f} mm")
