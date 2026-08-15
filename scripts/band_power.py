#!/usr/bin/env python3
"""Whether a difficulty contrast can be read inside heterogeneity bands, before reading one.

The difficulty axis is void as registered. `results/validation/slot_rates.txt` says why: the
strata differ in distractor heterogeneity for four of five judges, and heterogeneity is the one
property that moves `E*_A` without any change in the judge -- so the split by other judges'
accuracy is a split by heterogeneity wearing a difficulty label.

Banding is the obvious repair: compare easy against hard *within* a heterogeneity band, so the
two strata are matched on the confound. Whether that repair is available is a question about
the data and not about the judges, and it has to be answered before a hypothesis is written or
the hypothesis is written to fit an answer already seen.

**This script cannot compute the outcome.** `E*_A` is a ratio of two counts: errors landing on
A over errors at arrangements where A is not correct. Nothing here forms the numerator. It
reports denominators, which is the power calculation, and heterogeneity, which is the
precondition, and it is written this way so that "the outcome was not computed before
registration" is a property of the code rather than an assurance.

  python scripts/band_power.py

Reads the same records and uses the same definitions as scripts/slot_rates.py: item difficulty
is the mean accuracy of the other four judges on that item, and heterogeneity is the
coefficient of variation of the three distractor lengths.
"""
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PHASES = ("P2a", "P2b")
BANDS = (3, 4, 5)
FLOOR = 40          # the error count below which slot_rates.py declines to read a cell
BOOT = 4000
RNG = np.random.default_rng(0)


def records():
    """{judge: {(subset, id): [(chosen_slot, parsed_letter), ...]}} over both arrangement sets."""
    import glob
    by = defaultdict(lambda: defaultdict(list))
    n = 0
    for phase in PHASES:
        for path in sorted(glob.glob(f"results/exp01/{phase}_*.jsonl")):
            with open(path) as f:
                meta = json.loads(f.readline())
                for line in f:
                    r = json.loads(line)
                    by[meta["model"]][(r["subset"], r["id"])].append(
                        (meta["chosen_at_slot"], r["parsed_letter"]))
            n += 1
    return by, n


def heterogeneity():
    """{(subset, id): sd/mean of the three distractor lengths}."""
    out = {}
    for src in ("data/p2_o0/test.jsonl", "data/control_o0/test.jsonl"):
        if not os.path.isfile(src):
            continue
        for line in open(src):
            r = json.loads(line)
            L = [len(x if isinstance(x, str) else x[0]) for x in r["rejected"]]
            out.setdefault((r["subset"], r["id"]), float(np.std(L) / max(np.mean(L), 1)))
    return out


def errors_at(by_judge, keys):
    """n_err* for one judge over these items: errors at arrangements where A is not correct.

    This is E*_A's denominator. The numerator -- which of those errors land on A -- is the
    outcome and is deliberately not computed anywhere in this file.
    """
    return int(sum(1 for i in keys for c, l in by_judge[i]
                   if c != "A" and l in "ABCD" and l != c))


def main():
    by, n_passes = records()
    het = heterogeneity()
    models = sorted(by)
    items = sorted(set.intersection(*(set(by[m]) for m in models)) & set(het))
    print(f"  {len(models)} judges x {len(items)} items, {n_passes} passes "
          f"over {' and '.join(PHASES)}\n")

    diff = {}
    for m in models:
        others = [o for o in models if o != m]
        diff[m] = {i: float(np.mean([np.mean([c == l for c, l in by[o][i]]) for o in others]))
                   for i in items}

    print("  1. How far apart the two axes are")
    print("  " + "-" * 90)
    print(f"  {'judge':30s} {'corr(difficulty, heterogeneity)':>32s}   "
          f"{'difficulty span within a band':>30s}")
    for m in models:
        d = np.array([diff[m][i] for i in items])
        h = np.array([het[i] for i in items])
        r = float(np.corrcoef(d, h)[0, 1])
        edges = np.quantile(h, np.linspace(0, 1, 6))
        spans = []
        for b in range(5):
            sel = (h >= edges[b]) & (h <= edges[b + 1] if b == 4 else h < edges[b + 1])
            if sel.sum() > 10:
                spans.append(np.quantile(d[sel], [0.10, 0.90]))
        lo = min(s[0] for s in spans)
        hi = max(s[1] for s in spans)
        print(f"  {m.split('/')[-1]:30s} {r:+32.4f}   "
              f"{f'{lo:.2f} to {hi:.2f}':>30s}")
    print("\n  A correlation near zero with difficulty still spanning most of its range inside")
    print("  each band is what makes the repair possible: the two axes overlap, and banding")
    print("  removes the overlap without removing the contrast.\n")

    print("  2. What the cells hold, per band count")
    print("  " + "-" * 90)
    print(f"  {'bands':>6s} {'judge':30s} {'cells':>6s} {'min n_err*':>11s} "
          f"{'median':>8s} {'max':>8s} {f'below {FLOOR}':>10s}")
    for B in BANDS:
        for m in models:
            h = np.array([het[i] for i in items])
            edges = np.quantile(h, np.linspace(0, 1, B + 1))
            counts = []
            for b in range(B):
                sel = [i for k, i in enumerate(items)
                       if (h[k] >= edges[b] and (h[k] <= edges[b + 1] if b == B - 1
                                                 else h[k] < edges[b + 1]))]
                if not sel:
                    continue
                med = float(np.median([diff[m][i] for i in sel]))
                for keep in ([i for i in sel if diff[m][i] >= med],
                             [i for i in sel if diff[m][i] < med]):
                    counts.append(errors_at(by[m], keep))
            counts = np.array(counts)
            print(f"  {B:6d} {m.split('/')[-1]:30s} {len(counts):6d} {counts.min():11d} "
                  f"{int(np.median(counts)):8d} {counts.max():8d} "
                  f"{int((counts < FLOOR).sum()):10d}")
        print()

    print("  3. The registered condition, inside bands")
    print("  " + "-" * 90)
    print("  Does the easy stratum still differ from the hard one in heterogeneity once the")
    print("  comparison is made within a band? Pooled over bands, weighted by cell size.\n")
    print(f"  {'bands':>6s} {'judge':30s} {'easy':>8s} {'hard':>8s} {'diff':>9s} "
          f"{'95% CI':>21s}  reading")
    for B in BANDS:
        for m in models:
            h = np.array([het[i] for i in items])
            edges = np.quantile(h, np.linspace(0, 1, B + 1))
            e_all, h_all = [], []
            for b in range(B):
                sel = [i for k, i in enumerate(items)
                       if (h[k] >= edges[b] and (h[k] <= edges[b + 1] if b == B - 1
                                                 else h[k] < edges[b + 1]))]
                if not sel:
                    continue
                med = float(np.median([diff[m][i] for i in sel]))
                e_all += [het[i] for i in sel if diff[m][i] >= med]
                h_all += [het[i] for i in sel if diff[m][i] < med]
            e_all, h_all = np.array(e_all), np.array(h_all)
            ie = RNG.integers(0, len(e_all), (BOOT, len(e_all)))
            ih = RNG.integers(0, len(h_all), (BOOT, len(h_all)))
            d = e_all[ie].mean(1) - h_all[ih].mean(1)
            lo, hi = float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))
            print(f"  {B:6d} {m.split('/')[-1]:30s} {e_all.mean():8.4f} {h_all.mean():8.4f} "
                  f"{e_all.mean() - h_all.mean():+9.4f} [{lo:+9.4f},{hi:+9.4f}]  "
                  + ("DIFFERS" if lo > 0 or hi < 0 else "matched"))
        print()

    print("  What this does not settle. Whether the strata are matched on heterogeneity is not")
    print("  whether a difficulty effect exists, and nothing here has looked. It also does not")
    print("  cover any other property that moves E*_A -- heterogeneity is the one the")
    print("  simulation identified, and it is the one that was checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
