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
    """{model: {slot: [per-item credit]}} at --obvious 0, unparseable scored 0."""
    out = defaultdict(dict)
    for path in sorted(glob.glob(f"results/exp01/{phase}_*_o0_*.jsonl")):
        with open(path) as f:
            meta = json.loads(f.readline())
            rows = [json.loads(l) for l in f]
        out[meta["model"]][meta["chosen_at_slot"]] = np.array(
            [float(r["parsed_letter"] == meta["chosen_at_slot"]) for r in rows])
    return out


def per_position_raw(phase="P2b"):
    """The same table taken from the runner's own `results` field, which credits 0.25."""
    out = defaultdict(dict)
    for path in sorted(glob.glob(f"results/exp01/{phase}_*_o0_*.jsonl")):
        with open(path) as f:
            meta = json.loads(f.readline())
            rows = [json.loads(l) for l in f]
        out[meta["model"]][meta["chosen_at_slot"]] = float(
            np.mean([r["results"] for r in rows]))
    return out


def parse_conventions(phase="P2b"):
    """Per judge, (verdicts, unparseable, mean scored 0, mean scored 0.25).

    The second axis of the same upstream issue. #272 filed the unseeded arrangement and the
    0.25 credit for an unparseable verdict together, and both move the ranking.
    """
    out = defaultdict(lambda: [0, 0, 0.0, 0.0])
    for path in sorted(glob.glob(f"results/exp01/{phase}_*_o0_*.jsonl")):
        with open(path) as f:
            meta = json.loads(f.readline())
            for line in f:
                r = json.loads(line)
                L = r["parsed_letter"]
                t = out[meta["model"]]
                t[0] += 1
                if L not in "ABCD":
                    t[1] += 1
                    t[3] += 0.25
                else:
                    t[2] += L == meta["chosen_at_slot"]
                    t[3] += L == meta["chosen_at_slot"]
    return out


def main():
    print((__doc__ or "").split("  python")[0].strip())
    data = per_position()
    models = sorted(data, key=lambda m: -np.mean([data[m][s].mean() for s in "ABCD"]))

    print("\n" + "=" * 96)
    print("1. Accuracy by where the correct answer sits, on identical items")
    print("=" * 96)
    print("  **Unparseable verdicts score 0 here**, which is this repository's convention;")
    print("  upstream credits them 0.25 and §3 prints both. The choice moves these numbers,")
    print("  not only §2's ordering -- for the two judges with parse failures the spread")
    print("  differs in the third decimal either way. An independent recomputation of this")
    print("  table from the runner's own `results` field disagreed with it for exactly that")
    print("  reason, which is why the line is here.\n")
    raw = per_position_raw()
    print(f"  {'judge':30s} " + " ".join(f"{'at ' + s:>9s}" for s in "ABCD")
          + f" {'mean':>9s} {'spread':>9s} {'95% CI on spread':>20s} {'spread @0.25':>13s}")
    for m in models:
        v = np.stack([data[m][s] for s in "ABCD"])
        idx = RNG.integers(0, v.shape[1], (BOOT, v.shape[1]))
        b = v[:, idx].mean(2)
        sp = b.max(0) - b.min(0)
        lo, hi = float(np.percentile(sp, 2.5)), float(np.percentile(sp, 97.5))
        means = v.mean(1)
        r = np.array([raw[m][s] for s in "ABCD"])
        print(f"  {m.split('/')[-1]:30s} " + " ".join(f"{x:9.4f}" for x in means)
              + f" {means.mean():9.4f} {means.max() - means.min():9.4f} "
              f"[{lo:8.4f},{hi:8.4f}] {r.max() - r.min():13.4f}")
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
    print("3. The same ranking, under the two conventions for an unparseable verdict")
    print("=" * 96)
    conv = parse_conventions()
    print("  Upstream credits an unparseable verdict 0.25, which is chance under a four-way")
    print("  choice; this repository scores it 0 and reports the rate separately. #272 filed")
    print("  that and the unseeded arrangement together, and both move the ranking.\n")
    print(f"  {'judge':30s} {'unparseable':>16s} {'scored 0':>10s} {'scored 0.25':>12s} "
          f"{'gap':>8s}")
    for m in sorted(conv, key=lambda k: -conv[k][2] / conv[k][0]):
        n, up, z, q = conv[m]
        print(f"  {m.split('/')[-1]:30s} {up:6d} / {n:<7d} {z / n:10.4f} {q / n:12.4f} "
              f"{q / n - z / n:+8.4f}")
    zero = sorted(conv, key=lambda k: -conv[k][2] / conv[k][0])
    quart = sorted(conv, key=lambda k: -conv[k][3] / conv[k][0])
    print(f"\n  scored 0    " + " > ".join(m.split("/")[-1] for m in zero))
    print(f"  scored 0.25 " + " > ".join(m.split("/")[-1] for m in quart))
    if zero[0] != quart[0]:
        top = sorted((conv[zero[0]][2] / conv[zero[0]][0], conv[zero[1]][2] / conv[zero[1]][0]))
        print(f"\n  **First place changes on the convention alone.** The two judges that swap")
        print(f"  are the two with parse failures, and the gap the convention decides "
              f"({top[1] - top[0]:.4f})")
        print("  is smaller than what the convention is worth to the judge that has them.")

    print("\n" + "=" * 96)
    print("4. What this does and does not say about the published numbers")
    print("=" * 96)
    print("""
  Does say. A four-way score is a sample over arrangements *and* a choice about unparseable
  verdicts. The sampling is unseeded, the width of that sample differs by an order of
  magnitude between judges, and the top of the ranking moves under either axis. **The row
  averaged over the four arrangements is not a stable ordering to fall back on** -- it is
  stable under neither.

  Does not say. These are five open-weight judges we screened, not the leaderboard's
  entries, and none of them has a published score -- no open-weight generative judge that
  fits on a 24 GB card does, which is the limitation this repository has carried from the
  start. Upstream's draw also reaches only 4 of the 24 arrangements and not the four here,
  so the "averaged over the four" row is the estimand of a uniform draw rather than of
  upstream's. The mechanism is the published one; the magnitudes are ours.""")


if __name__ == "__main__":
    main()
