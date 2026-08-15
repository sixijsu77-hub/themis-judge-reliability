#!/usr/bin/env python3
"""How much of a published four-way score is the arrangement it happened to draw.

This repository's opening question was whether a judge's position sensitivity "differs
enough between judges to distort a leaderboard". Everything since has been about
establishing that the sensitivity exists, is stable per judge, and points in different
directions. This closes that back onto the score.

The mechanism is not hypothetical. `run_generative_v2.py` draws the candidate arrangement
per item from an unseeded `np.random.randint(0, 4)` (allenai/reward-bench#272), so a
published generative score is one sample from a distribution over arrangements. What this
prints is the width of that distribution per judge, and what the induced ranking does when
the arrangement is held fixed instead.

Read from the reduced P2 runs: five judges, the 1,763 unmodified benchmark items, the
slot-balanced arrangements, so each column is the same items with only the correct answer's
position changed.

  python scripts/leaderboard_exposure.py
"""
import glob
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BOOT = 10000
RNG = np.random.default_rng(0)


def per_position(phase="P2b"):
    """{model: {slot: [per-item credit]}} at --obvious 0."""
    out = defaultdict(dict)
    for path in sorted(glob.glob(f"results/exp01/{phase}_*_o0_*.jsonl")):
        with open(path) as f:
            meta = json.loads(f.readline())
            rows = [json.loads(l) for l in f]
        out[meta["model"]][meta["chosen_at_slot"]] = np.array(
            [float(r["parsed_letter"] == meta["chosen_at_slot"]) for r in rows])
    return out


def main():
    print((__doc__ or "").split("  python")[0].strip())
    data = per_position()
    models = sorted(data, key=lambda m: -np.mean([data[m][s].mean() for s in "ABCD"]))

    print("\n" + "=" * 96)
    print("1. Accuracy by where the correct answer sits, on identical items")
    print("=" * 96)
    print(f"  {'judge':30s} " + " ".join(f"{'at ' + s:>9s}" for s in "ABCD")
          + f" {'mean':>9s} {'spread':>9s} {'95% CI on spread':>20s}")
    for m in models:
        v = np.stack([data[m][s] for s in "ABCD"])
        idx = RNG.integers(0, v.shape[1], (BOOT, v.shape[1]))
        b = v[:, idx].mean(2)
        sp = b.max(0) - b.min(0)
        lo, hi = float(np.percentile(sp, 2.5)), float(np.percentile(sp, 97.5))
        means = v.mean(1)
        print(f"  {m.split('/')[-1]:30s} " + " ".join(f"{x:9.4f}" for x in means)
              + f" {means.mean():9.4f} {means.max() - means.min():9.4f} "
              f"[{lo:8.4f},{hi:8.4f}]")
    print("\n  The spread is how much a judge's score moves when nothing changes but where")
    print("  the correct answer was placed. It is not a property of the benchmark; it")
    print("  differs by an order of magnitude between judges on the same items.")

    print("\n" + "=" * 96)
    print("2. The ranking those scores induce, by arrangement")
    print("=" * 96)
    order = {}
    for s in "ABCD":
        order[s] = sorted(models, key=lambda m: -data[m][s].mean())
    order["mean"] = sorted(models, key=lambda m: -np.mean([data[m][x].mean() for x in "ABCD"]))
    for k in ("mean", "A", "B", "C", "D"):
        label = ("averaged over the four" if k == "mean" else f"answer always at {k}")
        print(f"  {label:24s} " + " > ".join(m.split("/")[-1] for m in order[k]))
    firsts = {order[s][0] for s in "ABCD"}
    lasts = {order[s][-1] for s in "ABCD"}
    print(f"\n  {len(firsts)} different judges rank first depending on the arrangement, and")
    print(f"  {len(lasts)} rank last. A judge that is first at one position is last at"
          " another.")

    print("\n" + "=" * 96)
    print("3. What this does and does not say about the published numbers")
    print("=" * 96)
    print("""
  Does say. A four-way score is a sample over arrangements, the sampling is unseeded, and
  the width of that sample differs by an order of magnitude between judges. Two judges whose
  averaged scores are close can be far apart at any particular arrangement, and the order
  between them is not a property of the judges alone.

  Does not say. These are five open-weight judges we screened, not the leaderboard's
  entries, and none of them has a published score -- no open-weight generative judge that
  fits on a 24 GB card does, which is the limitation this repository has carried from the
  start. Upstream's draw also reaches only 4 of the 24 arrangements and not the four here,
  so the "averaged over the four" row is the estimand of a uniform draw rather than of
  upstream's. The mechanism is the published one; the magnitudes are ours.""")


if __name__ == "__main__":
    main()
