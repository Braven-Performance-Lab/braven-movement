"""The renderer's run-to-run pixel band: two renders of the same jobs, compared.

`docs/COMPARING_TWO_RENDERS.md` section 2. Every pixel that differs AT ALL is
counted, with the largest step on any channel, because the band is about the
pixels a threshold would hide. `before_after_sheet.MOVED` (8 of 255) is the
right threshold for "did this figure change" and the wrong one here.

    python scripts/render_band.py out/band-a out/band-b > out/band.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def compare(first: Path, second: Path) -> dict:
    a = np.asarray(Image.open(first).convert("RGBA"), dtype=np.int16)
    b = np.asarray(Image.open(second).convert("RGBA"), dtype=np.int16)
    if a.shape != b.shape:
        return {"shapeDiffers": [list(a.shape), list(b.shape)]}
    step = np.abs(a - b).max(axis=2)
    return {
        "pixels": int(step.size),
        "differing": int((step > 0).sum()),
        "maxLevel": int(step.max()),
        "above8": int((step > 8).sum()),
    }


def main(argv: list[str]) -> int:
    first, second = Path(argv[1]), Path(argv[2])
    names = sorted(p.name for p in first.glob("*.png"))
    missing = sorted(set(names) ^ {p.name for p in second.glob("*.png")})
    rows = {name: compare(first / name, second / name) for name in names if (second / name).exists()}
    json.dump({"instrument": "scripts/render_band.py", "first": str(first), "second": str(second),
               "missing": missing, "views": rows}, sys.stdout, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
