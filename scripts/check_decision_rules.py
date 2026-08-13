#!/usr/bin/env python3
"""Check that the decision rules in PREREGISTRATION-exp01b.md can decide anything.

A hypothesis names a statistic and a threshold. Whether that pair can distinguish the world
where the hypothesis is true from the world where it is false is a property of the
statistic's behaviour under noise, and picking a threshold without drawing that distribution
first is how a rule ends up unable to fire. Three of the rules in the first draft were
written that way. This is the check that catches it, and it runs before the measurement.

  python scripts/check_decision_rules.py

Everything here is simulation. No benchmark data is read.
"""
import itertools
from math import comb

import numpy as np

N_ITEMS, N_ARR = 150, 4          # the P1 design: 150 items at four arrangements
N_JUDGES, NEEDED = 5, 4          # five judges passed the screen; the threshold stays at four
RNG = np.random.default_rng(0)

# Letter distributions spanning no bias to the bias actually observed in the pilot.
SKEWS = {
    "unbiased":       [.25, .25, .25, .25],
    "weak":           [.30, .25, .23, .22],
    "moderate":       [.40, .25, .20, .15],
    "as observed":    [.565, .20, .147, .088],
}
# First-slot rates across the four difficulty levels, from flat to the observed gradient.
TRENDS = {
    "no effect":      [.25, .25, .25, .25],
    "shallow":        [.25, .28, .31, .34],
    "moderate":       [.25, .318, .385, .45],
    "as piloted":     [.25, .355, .46, .565],
}


def skew(counts):
    f = counts / counts.sum(-1, keepdims=True)
    return f.max(-1) - f.min(-1)


def one_judge(p, boot=1000):
    """Return (point estimate of S, CI on S) for one simulated judge."""
    letters = RNG.choice(4, size=(N_ITEMS, N_ARR), p=p)
    per_item = np.stack([(letters == k).sum(1) for k in range(4)], axis=1)
    idx = RNG.integers(0, N_ITEMS, (boot, N_ITEMS))
    s = skew(per_item[idx].sum(1))
    return skew(per_item.sum(0)), np.percentile(s, 2.5), np.percentile(s, 97.5)


def at_least(p_one):
    return sum(comb(N_JUDGES, k) * p_one**k * (1 - p_one)**(N_JUDGES - k)
               for k in range(NEEDED, N_JUDGES + 1))


def null_of_S(sims=20000):
    out = np.empty(sims)
    for i in range(sims):
        letters = RNG.choice(4, size=(N_ITEMS, N_ARR), p=[.25] * 4)
        out[i] = skew(np.bincount(letters.ravel(), minlength=4))
    return out


def main():
    print("=" * 78)
    print("1. The null distribution of the slot-skew S, and the fixed threshold 0.05")
    print("=" * 78)
    null = null_of_S()
    for q in (50, 95, 99):
        print(f"  {q:2d}th percentile of S under uniform letters : {np.percentile(null, q):.4f}")
    below = (null < 0.05).mean()
    print(f"\n  0.05 sits at the {100*below:.1f}th percentile of that distribution.")
    print(f"  An unbiased judge exceeds it {100*(1-below):.1f}% of the time.")
    print("  A threshold inside the noise cannot separate no bias from some bias.")

    print("\n" + "=" * 78)
    print("2. Both readings of 'the CI on S includes 0.05 or less'")
    print("=" * 78)
    print(f"  {'letter distribution':22s} {'true S':>7s} {'CI low <= .05':>14s} {'CI high <= .05':>15s}")
    for name, p in SKEWS.items():
        lows, highs = [], []
        for _ in range(1000):
            _, lo, hi = one_judge(p)
            lows.append(lo <= 0.05)
            highs.append(hi <= 0.05)
        print(f"  {name:22s} {max(p)-min(p):7.3f} {np.mean(lows):13.1%} {np.mean(highs):14.1%}")
    print("\n  Loose: unbiased and weakly biased judges both pass, so it cannot tell them apart.")
    print("  Strict: even a perfectly unbiased judge never passes.")

    print("\n" + "=" * 78)
    print("3. S against its own null, the replacement rule")
    print("=" * 78)
    cut = np.percentile(null, 95)
    print(f"  {'letter distribution':22s} {'true S':>7s} {'S <= null 95th':>15s} {'>= 4 of 5':>11s}")
    for name, p in SKEWS.items():
        ok = np.mean([one_judge(p)[0] <= cut for _ in range(1000)])
        print(f"  {name:22s} {max(p)-min(p):7.3f} {ok:14.1%} {at_least(ok):10.1%}")
    print(f"\n  null 95th percentile at this n = {cut:.4f}")

    print("\n" + "=" * 78)
    print("4. Strict monotonicity of four noisy points, against a fitted slope")
    print("=" * 78)
    d = np.arange(4.0)
    dc = d - d.mean()
    print(f"  {'true first-slot rates':22s} {'monotone':>10s} {'>=4 of 5':>10s} "
          f"{'slope CI>0':>11s} {'>=4 of 5':>10s}")
    for name, fs in TRENDS.items():
        draws = RNG.binomial(N_ITEMS * N_ARR, fs, size=(20000, 4)) / (N_ITEMS * N_ARR)
        mono = np.all(np.diff(draws, axis=1) > 0, axis=1).mean()
        hits = 0
        for _ in range(800):
            per_item = np.stack([RNG.binomial(1, f, size=(N_ITEMS, N_ARR)).mean(1) for f in fs])
            idx = RNG.integers(0, N_ITEMS, (600, N_ITEMS))
            y = per_item[:, idx].mean(2)
            slopes = (dc[:, None] * (y - y.mean(0))).sum(0) / (dc**2).sum()
            hits += np.percentile(slopes, 2.5) > 0
        sl = hits / 800
        print(f"  {name:22s} {mono:9.1%} {at_least(mono):9.1%} {sl:10.1%} {at_least(sl):9.1%}")
    print("\n  Both reject the flat world. On a shallow real trend the slope keeps it and")
    print("  monotonicity throws it away, which is the case P1 exists to resolve.")

    print("\n" + "=" * 78)
    print("5. Which four arrangements hold the distractors in a fixed relative order")
    print("=" * 78)
    perms = list(itertools.permutations(range(4)))
    name = {0: "chosen", 1: "R1", 2: "R2", 3: "R3"}
    keep = [i for i, p in enumerate(perms) if [x for x in p if x != 0] == [1, 2, 3]]
    for label, group in (("in use before this check", [0, 6, 14, 21]), ("fixed order", keep)):
        print(f"\n  {label}:")
        for i in group:
            p = perms[i]
            distractors = "-".join(name[x] for x in p if x != 0)
            print(f"    {i:2d}  " + " ".join(f"{name[x]:>6s}" for x in p)
                  + f"   chosen at {'ABCD'[p.index(0)]}   distractors {distractors}")
    print(f"\n  Only {keep} moves the correct answer through every slot while leaving the")
    print("  three distractors in one order. Any other four confounds the two.")


if __name__ == "__main__":
    main()
