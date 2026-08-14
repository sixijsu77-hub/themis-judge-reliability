#!/usr/bin/env python3
"""Ask what a judge whose slot preference never changes does to H1.

H1 reads the slope of the conditional first-slot error share across four difficulty levels
and calls a positive slope, with an interval excluding zero, evidence that a judge falls back
on position more as items get harder. This simulates a judge that cannot do that -- its slot
weights are the same number at every difficulty -- and asks what slope it produces anyway.

The model is the simplest one that can express both effects at once. Each candidate has an
attractiveness by kind (the correct answer, one of the item's own rejected responses, an
off-topic substitute) and each slot has a weight. The judge picks a slot with probability
proportional to the product. Difficulty enters only through the control set, which replaces
off-topic substitutes with the item's own rejected responses as it falls.

  python scripts/constant_preference.py
"""
import itertools
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orderings import ALL, FIXED_DISTRACTORS, PILOT, SLOT_BALANCED

LEVELS = [3, 2, 1, 0]
SETS = {"pilot": PILOT, "fixed": FIXED_DISTRACTORS, "balanced": SLOT_BALANCED}
FLAT = np.array([1.0, 1.0, 1.0, 1.0])
FRONT = np.array([1.6, 1.2, 0.9, 0.7])      # a front preference, identical at every level


def kinds(obvious):
    """Attractiveness kind of each candidate: index 0 is the correct answer.

    build_control_set.py writes the off-topic substitutes first and the item's own rejected
    responses last, so R1..R3 change kind as difficulty falls.
    """
    return ["correct"] + ["off"] * obvious + ["own"] * (3 - obvious)


def e_star(indices, weights, attract, obvious):
    """Exact conditional first-slot error share for one difficulty, no sampling.

    Returns (share, denominator mass). The denominator is error probability on the
    arrangements whose correct answer is not at A, which is what the statistic conditions on.
    """
    k = kinds(obvious)
    num = den = 0.0
    for i in indices:
        perm = ALL[i]
        p = np.array([attract[k[c]] * weights[j] for j, c in enumerate(perm)])
        p = p / p.sum()
        chosen_slot = list(perm).index(0)
        if chosen_slot == 0:                      # an error here cannot name A
            continue
        err = 1.0 - p[chosen_slot]
        den += err
        num += p[0]
    return (num / den if den else float("nan")), den


# H1 fits over the levels whose error count clears the floor. On this data that is
# --obvious 2, 1 and 0 for every judge, so the simulation fits the same three and not the
# four it could: a slope over a different set of points is not the slope H1 read.
FIT_LEVELS = [1, 2, 3]


def slope(shares):
    """Least-squares slope over FIT_LEVELS, with d rising as the item gets harder."""
    y = np.array([shares[i] for i in FIT_LEVELS], float)
    if np.isnan(y).any():
        return float("nan")
    d = np.array(FIT_LEVELS, float)
    d = d - d.mean()
    return float((d * (y - y.mean())).sum() / (d ** 2).sum())


def contrast(indices, weights, attract, obvious):
    """s_A - s_D, the identity-averaged rate of naming the first slot minus the last.

    Not a share: nothing here is divided by the other slots' rates, so it does not rise
    merely because the middle empties.
    """
    k = kinds(obvious)
    got = {"A": [0.0, 0], "D": [0.0, 0]}
    for i in indices:
        perm = ALL[i]
        p = np.array([attract[k[c]] * weights[j] for j, c in enumerate(perm)])
        p = p / p.sum()
        for slot, j in (("A", 0), ("D", 3)):
            if perm[j] == 0:
                continue
            got[slot][0] += p[j]
            got[slot][1] += 1
    a_ = got["A"][0] / got["A"][1] if got["A"][1] else float("nan")
    d_ = got["D"][0] / got["D"][1] if got["D"][1] else float("nan")
    return a_ - d_


def run(weights, attract):
    out = {}
    for name, idx in SETS.items():
        shares = [e_star(idx, weights, attract, lv)[0] for lv in LEVELS]
        cons = [contrast(idx, weights, attract, lv) for lv in LEVELS]
        out[name] = (shares, slope(shares), cons, slope(cons))
    return out


def main():
    print((__doc__ or "").split("  python")[0].strip())

    print("\n" + "=" * 92)
    print("1. Slot weights all equal. Does the balanced set read the registered null of 1/3?")
    print("=" * 92)
    attract = {"correct": 6.0, "own": 1.0, "off": 0.15}
    res = run(FLAT, attract)
    print(f"  attractiveness: correct {attract['correct']}, own rejected {attract['own']}, "
          f"off-topic {attract['off']}\n")
    print(f"  {'set':10s} " + " ".join(f"{'obv '+str(l):>9s}" for l in LEVELS) + f" {'slope':>9s}")
    for name in SETS:
        sh, sl = res[name][:2]
        print(f"  {name:10s} " + " ".join(f"{v:9.4f}" for v in sh) + f" {sl:+9.4f}")
    print("\n  With no slot preference the balanced set sits at 1/3 = 0.3333 at every level,")
    print("  which is the null section 5 registers. The other two do not, and that is the")
    print("  confound: their slot A is not interchangeable with the others.")

    print("\n" + "=" * 92)
    print("2. A front preference, the same at every difficulty. What slope does it produce?")
    print("=" * 92)
    print(f"  slot weights {[float(x) for x in FRONT]}, identical at all four levels\n")
    res = run(FRONT, attract)
    print(f"  {'set':10s} " + " ".join(f"{'obv '+str(l):>9s}" for l in LEVELS) + f" {'slope':>9s}")
    for name in SETS:
        sh, sl = res[name][:2]
        print(f"  {name:10s} " + " ".join(f"{v:9.4f}" for v in sh) + f" {sl:+9.4f}")

    print("\n" + "=" * 92)
    print("3. The largest slope a constant preference can produce, over a grid")
    print("=" * 92)
    best = {}
    grid_c = [1.5, 3.0, 6.0, 12.0, 25.0, 60.0]
    grid_own = [1.0]
    grid_off = [0.005, 0.02, 0.05, 0.15, 0.4, 1.0, 2.5]
    lv = [0.02, 0.05, 0.15, 0.4, 0.7, 1.0, 2.0, 5.0]
    grid_w = [np.array(w) for w in itertools.product([1.0], lv, lv, lv)]
    best_c = {}
    for name in SETS:
        best[name] = (-9, None)
        best_c[name] = (-9, None)
    for c, own, off in itertools.product(grid_c, grid_own, grid_off):
        at = {"correct": c, "own": own, "off": off}
        for w in grid_w:
            r = run(w, at)
            for name in SETS:
                if r[name][1] == r[name][1] and r[name][1] > best[name][0]:
                    best[name] = (r[name][1], (c, off, tuple(w), r[name][0]))
                if r[name][3] == r[name][3] and r[name][3] > best_c[name][0]:
                    best_c[name] = (r[name][3], (c, off, tuple(w), r[name][2]))
    print(f"  fitted over --obvious 2, 1 and 0, the levels H1 fits\n")
    print(f"  {'set':10s} {'max slope':>10s}   attained at")
    for name in SETS:
        sl, cfg = best[name]
        print(f"  {name:10s} {sl:+10.4f}   correct={cfg[0]}, off-topic={cfg[1]}, "
              f"weights={[round(float(x), 3) for x in cfg[2]]}")
        print(f"  {'':10s} {'':10s}   E*_A " + " ".join(f"{v:.4f}" for v in cfg[3]))
    print("\n  observed slopes on the balanced set, from results/exp01/p1_summary.txt:")
    print("    Qwen2.5-7B-Instruct +0.2503, Skywork-Critic +0.1166, Con-J +0.0882,")
    print("    RISE-Judge +0.0676, Llama-3-OffsetBias -0.0163")

    print("\n" + "=" * 92)
    print("3b. The same, on the first-versus-last contrast, which is not a share")
    print("=" * 92)
    print(f"  {'set':10s} {'max slope':>10s}   attained at")
    for name in SETS:
        sl, cfg = best_c[name]
        print(f"  {name:10s} {sl:+10.4f}   correct={cfg[0]}, off-topic={cfg[1]}, "
              f"weights={[round(float(x), 3) for x in cfg[2]]}")
        print(f"  {'':10s} {'':10s}   s_A - s_D " + " ".join(f"{v:+.4f}" for v in cfg[3]))
    print("\n  observed, from results/validation/slot_rates.txt section 3:")
    print("    Qwen2.5-7B-Instruct +0.4567, Skywork-Critic +0.2267, Con-J +0.1133,")
    print("    RISE-Judge +0.1067, Llama-3-OffsetBias +0.0302")

    print("\n" + "=" * 92)
    print("4. What null does H1 test?")
    print("=" * 92)
    print("""
  The registered criterion is that the slope's interval excludes zero. A slope of zero is
  what a judge produces when the statistic does not move across difficulty -- not when the
  judge has no slot preference. Those are different nulls, and section 3 shows how far apart
  they are: a judge whose slot weights are literally the same four numbers at every
  difficulty reaches +0.2818 on the balanced set, above every slope observed there. The
  largest observed is +0.2503.

  **So the criterion does not separate the hypothesis from its negation on this design.**
  H1 as written tests "the statistic rises with difficulty". Section 1 claims "the judge's
  preference for the first slot strengthens with difficulty", and a judge that cannot do the
  second produces the first.

  The shapes agree too, which is the part that is hard to argue with. The configuration that
  maximises the slope gives 0.7089, 0.1501, 0.5086, 0.7137 across --obvious 3, 2, 1, 0: high
  where the answer is not in dispute, a trough in the middle, and a rise to the benchmark
  item. Qwen2.5-7B-Instruct measured 0.6000, 0.2697, 0.5188, 0.7704. The same form.

  Why a constant preference still produces a slope on the balanced set. Making every slot
  hold every candidate equally often removes one thing: which candidate sits where. It
  cannot remove the other thing difficulty changes, which is how much the candidates differ
  from each other. At --obvious 2 and 1 the distractors are a mixture of off-topic and
  plausible, so attractiveness dominates the choice and slot weight is swamped. At
  --obvious 0 they are all plausible, so the candidates are nearly interchangeable and slot
  weight is the only thing left to separate them. The same constant weights therefore
  express themselves more at the bottom of the difficulty range than in the middle, and the
  statistic rises.

  The balanced set equalises the assignment of candidates to slots. It does not, and cannot,
  equalise the contrast between candidates, and that contrast is what --obvious varies. No
  arrangement set can: the contrast is a property of the control set, not of the ordering.""")


if __name__ == "__main__":
    main()
