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

N_ITEMS, N_ARR = 150, 4          # the P1a design: 150 items at four arrangements
N_JUDGES, NEEDED = 5, 4          # five judges passed the screen; the threshold stays at four
RNG = np.random.default_rng(0)

# Per-slot accuracy measured in the pilot, by difficulty. Used to bound what the slot skew
# can reach when the judge is nearly always right, which is the regime H3 is asked in.
PILOT_ACC = {3: [.9933, .9933, .9933, .9867], 2: [.9400, .9467, .9467, .4133],
             1: [.9067, .9267, .4800, .3000], 0: [.8533, .5333, .3933, .3000]}
# Measured within-item correlation of the "answered A" indicator, same pilot.
PILOT_ICC = {3: 0.0000, 2: 0.0000, 1: 0.0000, 0: 0.1227}

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


def s_ceiling(acc):
    """Largest slot skew reachable given the four per-slot accuracies in `acc`.

    `acc` is a vector, one entry per slot the correct answer can occupy -- not a single
    accuracy. The ceiling depends on how accuracy is distributed across slots and not only
    on its mean, so a number from this function is conditional on the pattern passed in and
    is not a general bound at that mean. Section 3c shows how far apart three patterns of
    the same mean come out.

    The correct answer sits in each slot for one of the four arrangements, so correct
    verdicts contribute equally to every letter and only errors can move S. Send every
    error to one slot `t`; the errors made on `t`'s own arrangement cannot go to `t`, so
    park them on the highest-accuracy other slot, leaving the lowest one as the minimum.
    """
    best = 0.0
    for t in range(4):
        others = [L for L in range(4) if L != t]
        top = 0.25 * (acc[t] + sum(1 - acc[p] for p in others))
        best = max(best, top - 0.25 * min(acc[L] for L in others))
    return best


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
    print("3. S against its own null: the second draft, and why it also cannot decide")
    print("=" * 78)
    cut = np.percentile(null, 95)
    print(f"  {'letter distribution':22s} {'true S':>7s} {'S <= null 95th':>15s} {'>= 4 of 5':>11s}")
    for name, p in SKEWS.items():
        ok = np.mean([one_judge(p)[0] <= cut for _ in range(1000)])
        print(f"  {name:22s} {max(p)-min(p):7.3f} {ok:14.1%} {at_least(ok):10.1%}")
    print(f"\n  null 95th percentile at this n = {cut:.4f}")
    print("  Read on its own that separates the four rows. It is still the wrong rule,")
    print("  because S has a ceiling this design imposes and the ceiling depends on")
    print("  accuracy. The correct answer visits all four slots equally, so correct")
    print("  verdicts land on every letter equally and only errors can move S. The most")
    print("  hostile arrangement of a given error budget is computed by s_ceiling().\n")
    print(f"  {'obvious':>7s} {'accuracy':>9s} {'errors':>7s} {'S ceiling':>10s} "
          f"{'null 95th':>10s}   can the rule fire?")
    for d in (3, 2, 1, 0):
        acc = PILOT_ACC[d]
        n_err = round(N_ITEMS * N_ARR * (1 - float(np.mean(acc))))
        ceil = s_ceiling(acc)
        print(f"  {d:7d} {float(np.mean(acc)):9.4f} {n_err:7d} {ceil:10.4f} {cut:10.4f}   "
              f"{'no -- ceiling is under the threshold' if ceil < cut else 'yes'}")
    print("\n" + "=" * 78)
    print("3c. The ceiling depends on the pattern of per-slot accuracy, not just its mean")
    print("=" * 78)
    print(f"  {'obvious':>7s} {'mean acc':>9s} {'equal':>8s} {'one slot':>9s} {'measured':>9s}")
    for d in (3, 2, 1, 0):
        acc = PILOT_ACC[d]
        m = float(np.mean(acc))
        n_err_total = 4 * (1 - m)
        # All the error on one slot: that slot's accuracy is 1 - 4(1-m), the rest are perfect.
        one = [max(0.0, 1 - n_err_total)] + [1.0, 1.0, 1.0]
        print(f"  {d:7d} {m:9.4f} {s_ceiling([m] * 4):8.4f} {s_ceiling(one):9.4f} "
              f"{s_ceiling(acc):9.4f}")
    print("\n  Same mean accuracy, three arrangements of it, ceilings that differ by a factor")
    print("  of two or more. The figure quoted in the pre-registration is the 'measured'")
    print("  column -- conditional on the pilot's per-slot pattern, not a bound at that mean.")
    print("  The conclusion holds under all three: at obvious=3 every ceiling is under 0.0750.")

    print("\n  H3 is asked at obvious=3. There the rule cannot fail: the same defect as the")
    print("  first draft with the sign reversed. A statistic diluted by 99% correct verdicts")
    print("  is the wrong place to look. Condition on the errors instead -- section 3b.")

    print("\n" + "=" * 78)
    print("3b. The rule that replaces it: conditional error share at A, null exactly 1/3")
    print("=" * 78)
    print("  A first draft of this used the share over ALL wrong verdicts, with a null of")
    print("  0.25 = (3/4) x (1/3). That 3/4 assumes the error mass is spread evenly over the")
    print("  four arrangements, and on the pilot it is not -- see")
    print("  results/validation/decomposition.txt section 4, where the real null runs to")
    print("  0.31, above 0.25 and in the hypothesis's own direction. Dropping the")
    print("  arrangement whose answer is at A leaves a weighted average of three quantities")
    print("  that are each 1/3 under the null, so the null is 1/3 at any per-slot accuracy.")
    print(f"\n  {'n_err*':>6s} " + " ".join(f"{f'true {t:.2f}':>11s}"
                                             for t in (1/3, 0.45, 0.60, 0.80)))
    for n_err in (5, 20, 40, 47, 120):
        cells = []
        for t in (1/3, 0.45, 0.60, 0.80):
            draws = RNG.binomial(n_err, t, size=4000) / n_err
            b = RNG.binomial(n_err, draws[:, None], size=(4000, 400)) / n_err
            cells.append(np.mean(np.percentile(b, 2.5, axis=1) > 1/3))
        print(f"  {n_err:6d} " + " ".join(f"{c:10.1%} " for c in cells))
    print("\n  First column is the false-positive rate; the rest are power. Below about 40")
    print("  usable errors nothing fires. 150 items at obvious=3 give the pilot judge 4,")
    print("  which is why H3 runs at all 1,763 items (about 47 for that judge): enough for a")
    print("  strong preference, not enough for a moderate one, and the pre-registration says")
    print("  so before the run. A judge more accurate than the pilot may not reach 40 even")
    print("  there, and is then reported as not evaluated rather than as passing.")

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
            # Arrangements of one item share a per-item offset sized to the measured ICC,
            # so the four draws are correlated the way the pilot's verdicts are.
            per_item = []
            for lvl, f in enumerate(fs):
                icc = PILOT_ICC[3 - lvl]
                u = RNG.normal(0, np.sqrt(icc), (N_ITEMS, 1)) if icc > 0 else 0.0
                q = np.clip(f + u * np.sqrt(f * (1 - f)), 1e-6, 1 - 1e-6)
                per_item.append(RNG.binomial(1, q * np.ones((N_ITEMS, N_ARR))).mean(1))
            per_item = np.stack(per_item)
            idx = RNG.integers(0, N_ITEMS, (600, N_ITEMS))
            y = per_item[:, idx].mean(2)
            slopes = (dc[:, None] * (y - y.mean(0))).sum(0) / (dc**2).sum()
            hits += np.percentile(slopes, 2.5) > 0
        sl = hits / 800
        print(f"  {name:22s} {mono:9.1%} {at_least(mono):9.1%} {sl:10.1%} {at_least(sl):9.1%}")
    print("\n  Both reject the flat world. On a shallow real trend the slope keeps it and")
    print("  monotonicity throws it away, which is the case P1 exists to resolve.")
    print(f"  Arrangements within an item are drawn correlated at the measured ICC "
          f"{PILOT_ICC}, so the")
    print("  slope's interval is not assuming independence it does not have.")

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
