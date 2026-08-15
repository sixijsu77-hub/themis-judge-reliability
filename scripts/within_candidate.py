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

Each distractor visits two slots across the four arrangements -- the first visits A and B,
the second B and C, the third C and D -- so asking how often *the same candidate* is named
in one slot versus the other holds its content fixed and varies only where it sits.

**That reasoning is wrong and this measure is confounded. Read the numbers with the
correction below, not as they were first reported.** With four arrangements the correct
answer must move whenever a candidate does: the first distractor sits at A only in the
arrangements whose correct answer is at B, C or D, and at B only in the one whose correct
answer is at A. The judge is far more accurate when the correct answer is first, so it names
the first distractor less often in exactly the arrangement where that distractor sits at B --
and the ratio comes out above 1 with no position preference required. It is not fixable by
choosing a different four: every four-element set pins the correct answer's position for each
candidate-slot pair. Holding the correct answer still while distractors move needs the six
arrangements per position that only P2 has.

The statistic that is clean in P1 is the paired difference between two slots named in
advance, in scripts/summarize_p1.py: both arrangements hold the same four candidates and only
the correct answer's position differs, so a preference for any candidate is present in both
and cancels. This file is kept because the comparison between a confounded measure and a
clean one is part of the record.

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

# The benchmark's `id` is not unique: 40 of the 1,763 non-Ties items share an id with
# another item, which is the corruption already filed upstream. Keying an analysis by it
# silently merges those pairs, so every item key here is (subset, id), which is unique at
# 1,763. The 150-item control sets are unaffected; the two full-size sets are not.
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
                    out[key][(r["subset"], r["id"])] = int(
                        r["parsed_letter"] == slot_of[c])
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
    print("\n  These ratios are confounded and are printed for comparison, not as a")
    print("  measurement of position. Moving a candidate between slots moves the correct")
    print("  answer too, and the judge is more accurate when it is first, so a ratio above 1")
    print("  needs no position preference to appear. See this file's header. The clean")
    print("  statistic is the paired first-versus-last difference in summarize_p1.py.")


if __name__ == "__main__":
    main()
