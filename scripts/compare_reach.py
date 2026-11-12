"""Compare two runs of ball_hand_gap_render.py: shoulder miss, anchor error, and how far each drill moves.

    python scripts/compare_reach.py out/reach-main.json out/reach-optB.json
"""
import json,math,statistics as st,sys
A={(r['movementId'],r['phase']):r for r in json.load(open(sys.argv[1]))['rows'] if 'failed' not in r}
B={(r['movementId'],r['phase']):r for r in json.load(open(sys.argv[2]))['rows'] if 'failed' not in r}
def q(v): return f"median {st.median(v):6.2f} max {max(v):6.2f}"
for tag,D in (('now',A),('option',B)):
    off=[e['offsetMm'] for r in D.values() for e in r['shoulders'].values()]
    anc=[r['girdle']['ballAnchorErrorMm'] for r in D.values()]
    print(f"{tag:7s} shoulder miss {q(off)} | anchor {q(anc)}  >10mm {sum(a>10 for a in anc)}")
moves={}
for k in A:
    mv=max(max(math.dist(A[k]['boneHeadsM'][n],B[k]['boneHeadsM'][n]) for n in A[k]['boneHeadsM']),math.dist(A[k]['ballCentreM'],B[k]['ballCentreM']))*1000
    moves.setdefault(k[0][8:],[]).append((k[1],mv,A[k]['girdle']['ballAnchorErrorMm'],B[k]['girdle']['ballAnchorErrorMm']))
print("\nper drill: largest move of any bone or the ball (mm), anchor now -> option, worst phase")
for m,rows in moves.items():
    w=max(rows,key=lambda x:x[1])
    print(f"  {m:32s} max move {w[1]:6.1f} ({w[0]})  anchor median {st.median([x[2] for x in rows]):5.2f} -> {st.median([x[3] for x in rows]):5.2f}")
