#!/usr/bin/env python3
"""Measure position while holding the candidate fixed, which the letter counts cannot do.

Two things move together in this design and had to be separated.

First, the control set orders its distractors. `build_control_set.py` writes
`[foreign] * obvious + [own rejected] * (3 - obvious)`, so at `--obvious 2` the single
plausible distractor is always last in the list, at `--obvious 1` the two plausible ones are
last, and only at `--obvious 3` and `--obvious 0` is the list homogeneous. Second, the four
arrangements P1 uses hold that list in one relative order, so a fixed place in the list is a
fixed slot. Put together, a judge that simply prefers the hardest distractor produces a
letter distribution that reads as a slot preference, and the preferred slot moves between
difficulty levels because the hard distractor moves.

The fix needs no new run. Each distractor visits two slots across the four arrangements --
the first visits A and B, the second B and C, the third C and D -- so asking how often *the
same candidate* is named in one slot versus the other holds its content fixed and varies
only where it sits. A ratio of 1 is a judge that does not care where a candidate is.

  python scripts/within_candidate.py
"""
import glob
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orderings import ALL

BOOT = 10000
RNG = np.random.default_rng(0)
LEVELS = [3, 2, 1, 0]
NAME = {1: "first rejected", 2: "second rejected", 3: "third rejected"}


def load():
    """{(model, obvious, candidate, slot): {item id: 1 if named, else 0}}"""
    out = defaultdict(dict)
    for path in sorted(glob.glob("results/exp01/P1a_*.jsonl")):
        with open(path) as f:
            meta = json.loads(f.readline())
            perm = ALL[meta["ordering"]]
            slot_of = {c: "ABCD"[list(perm).index(c)] for c in (1, 2, 3)}
            for line in f:
                r = json.loads(line)
                if r["parsed_letter"] not in "ABCD":
                    continue
                for c in (1, 2, 3):
                    key = (meta["model"], meta["obvious"], c, slot_of[c])
                    out[key][r["id"]] = int(r["parsed_letter"] == slot_of[c])
    return out


def ratio_ci(a, b):
    """Bootstrap the ratio of two rates over the items they share, unpaired."""
    ka, kb = np.array(list(a.values()), float), np.array(list(b.values()), float)
    ia = RNG.integers(0, len(ka), (BOOT, len(ka)))
    ib = RNG.integers(0, len(kb), (BOOT, len(kb)))
    num, den = ka[ia].mean(1), kb[ib].mean(1)
    r = np.divide(num, den, out=np.full_like(num, np.nan), where=den > 0)
    r = r[~np.isnan(r)]
    pt = ka.mean() / kb.mean() if kb.mean() > 0 else float("nan")
    if not len(r):
        return pt, float("nan"), float("nan")
    return pt, float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5))


def main():
    data = load()
    models = sorted({k[0] for k in data})
    print("how often the same candidate is named, by the slot it happens to occupy\n")
    print("Each row holds the candidate's content fixed and moves only its position. The")
    print("earlier slot is listed first, so a ratio above 1 means the judge is pulled")
    print("towards the front. A judge indifferent to position gives 1.\n")
    print(f"  {'judge':30s} {'obv':>3s} {'candidate':>16s} {'slots':>7s} "
          f"{'named early':>12s} {'named late':>11s} {'ratio':>7s} {'95% CI':>16s}")
    for m in models:
        for lv in LEVELS:
            for c in (1, 2, 3):
                slots = sorted({k[3] for k in data if k[:3] == (m, lv, c)})
                if len(slots) != 2:
                    continue
                early, late = data[(m, lv, c, slots[0])], data[(m, lv, c, slots[1])]
                pt, lo, hi = ratio_ci(early, late)
                ea = np.mean(list(early.values()))
                la = np.mean(list(late.values()))
                sep = "" if np.isnan(lo) else ("  " if lo <= 1 <= hi else " *")
                print(f"  {m.split('/')[-1]:30s} {lv:3d} {NAME[c]:>16s} "
                      f"{slots[0]+' vs '+slots[1]:>7s} "
                      f"{ea:12.4f} {la:11.4f} {pt:7.2f} [{lo:5.2f}, {hi:5.2f}]{sep}")
            print()
    print("  * marks an interval that excludes 1. Rates are over the 150 items of that level")
    print("  at one arrangement each, so the two rates are not paired and the interval is")
    print("  wider than a paired one would be.")
    print("\n  This is the only position statistic in P1 that does not depend on which")
    print("  candidate sits where. The letter frequencies, the slot skew and the conditional")
    print("  error share all do, for the reason in this file's header.")


if __name__ == "__main__":
    main()
