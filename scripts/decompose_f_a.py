#!/usr/bin/env python3
"""Split the first-slot rate into an accuracy term and an error-placement term.

The pre-registration's H1 reads the first-slot rate `f_A` and calls a rise in it, as items
get harder, a judge falling back on position. This checks whether that reading survives, by
writing `f_A` in terms of quantities that separate the two things it mixes.

THE IDENTITY

Let `a_p` be the judge's accuracy on the arrangements where the correct answer sits at slot
`p`, `a` the accuracy pooled over the four, and `q_(p->A)` the probability it names A given
that it is wrong and the answer sits at `p`. A verdict naming A is either a correct one on
the arrangement whose answer is at A, or an error on one of the other three:

    f_A = (1/4) a_A + (1/4) SUM_{p != A} (1 - a_p) q_(p->A)

Writing `E_A` for the share of all wrong verdicts that name A, the second term is
`E_A (1 - a)`, because the total error mass is `4(1 - a)` in the same units. So

    f_A = (1/4) a_A + E_A (1 - a)                                        [1]

and if the per-slot accuracies are equal, `a_p = a`, this collapses to

    f_A - 1/4 = (1 - a) (E_A - 1/4)                                      [2]

ASSUMPTIONS. [1] needs only that the correct answer occupies each slot equally often -- the
design guarantees it -- and that `f_A`, `a` and `E_A` are all computed over parsed verdicts,
which is how the pre-registration defines the denominator. [2] needs the extra assumption
that accuracy does not depend on where the correct answer sits, which is the very thing the
position hypotheses doubt, so [2] is used for intuition and [1] for anything measured.

WHAT [2] SAYS. Differentiating at fixed `E_A` gives `d f_A / d a = 1/4 - E_A`. A judge whose
error placement never changes still shows a rising `f_A` as it gets less accurate, as long as
`E_A > 1/4`. Rising `f_A` is therefore not evidence that a judge is falling back on position
more; it is consistent with a fixed mild preference and nothing else moving.

  python scripts/decompose_f_a.py
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orderings import PILOT, SLOT_OF

LEVELS = [3, 2, 1, 0]
RNG = np.random.default_rng(0)
N_ITEMS = 150


def pilot(level):
    """[(chosen slot, parsed letter)] for the pilot's four arrangements at one difficulty."""
    rows = []
    for d in PILOT:
        path = f"results/validation/graded/o{level}_original_{d}.jsonl"
        for line in open(path):
            o = json.loads(line)
            if o.get("_record") == "metadata":
                continue
            rows.append((SLOT_OF[d], o["parsed_letter"]))
    return [r for r in rows if r[1] in "ABCD"]


def stats(rows):
    n = len(rows)
    a = sum(1 for s, l in rows if s == l) / n
    wrong = [(s, l) for s, l in rows if s != l]
    f_A = sum(1 for _, l in rows if l == "A") / n
    e_A = sum(1 for _, l in wrong if l == "A") / len(wrong) if wrong else float("nan")
    off = [(s, l) for s, l in wrong if s != "A"]
    e_A_cond = sum(1 for _, l in off if l == "A") / len(off) if off else float("nan")
    acc = {}
    err = {}
    for s in "ABCD":
        v = [l for t, l in rows if t == s]
        acc[s] = sum(1 for l in v if l == s) / len(v)
        err[s] = sum(1 for l in v if l != s)
    f = {L: sum(1 for _, l in rows if l == L) / n for L in "ABCD"}
    # f_A's own null: the value an indifferent judge would show given these per-slot
    # accuracies. It is 0.25 only when they are equal.
    f_A_null = 0.25 * acc["A"] + (1 / 12) * sum(1 - acc[s] for s in "BCD")
    return dict(n=n, a=a, f_A=f_A, f_A_null=f_A_null, E_A=e_A, E_A_cond=e_A_cond,
                n_err=len(wrong), n_err_cond=len(off),
                S=max(f.values()) - min(f.values())), acc, err


def simulate(a, e_A, uniform_errors=False):
    """One judge with accuracy `a` at every slot and a fixed error placement."""
    if uniform_errors:
        q = {p: {L: 1 / 3 for L in "ABCD" if L != p} for p in "ABCD"}
    else:
        # Errors go to A with probability e_A when A is available, the rest split evenly.
        # On the arrangement whose answer is at A the error cannot name A at all.
        q = {}
        for p in "ABCD":
            others = [L for L in "ABCD" if L != p]
            if p == "A":
                q[p] = {L: 1 / 3 for L in others}
            else:
                rest = [L for L in others if L != "A"]
                q[p] = {"A": e_A, **{L: (1 - e_A) / 2 for L in rest}}
    rows = []
    for p in "ABCD":
        for _ in range(N_ITEMS):
            if RNG.random() < a:
                rows.append((p, p))
            else:
                ks = list(q[p])
                rows.append((p, ks[int(RNG.choice(len(ks), p=[q[p][k] for k in ks]))]))
    return stats(rows)


def main():
    print((__doc__ or "").split("  python")[0].strip())

    print("\n" + "=" * 96)
    print("1. The identity checked against the pilot, per difficulty")
    print("=" * 96)
    print(f"  {'obvious':>7s} {'a':>7s} {'a_A':>7s} {'E_A':>7s} {'f_A':>8s} "
          f"{'(1/4)a_A + E_A(1-a)':>21s} {'residual':>10s}")
    for lv in LEVELS:
        st, acc, _ = stats(pilot(lv))
        a_A = acc["A"]
        rhs = 0.25 * a_A + st["E_A"] * (1 - st["a"])
        print(f"  {lv:7d} {st['a']:7.4f} {a_A:7.4f} {st['E_A']:7.4f} {st['f_A']:8.4f} "
              f"{rhs:21.4f} {st['f_A'] - rhs:10.2e}")
    print("\n  Residual is float noise, so [1] is an identity on this data, not a model.")

    print("\n" + "=" * 96)
    print("2. Simulation: hold the error placement fixed, drop accuracy, watch f_A")
    print("=" * 96)
    for label, e_A, uni in (("errors go to A with p = 0.565", 0.565, False),
                            ("errors go to A with p = 0.35 ", 0.35, False),
                            ("errors spread evenly         ", None, True)):
        print(f"\n  {label}")
        print(f"    {'accuracy':>9s} {'n_err':>6s} {'f_A':>8s} {'E_A':>8s} "
              f"{'E_A cond':>9s} {'S':>8s}")
        for a in (0.99, 0.90, 0.75, 0.55):
            st, _, _ = simulate(a, e_A, uniform_errors=uni)
            print(f"    {a:9.2f} {st['n_err']:6d} {st['f_A']:8.4f} {st['E_A']:8.4f} "
                  f"{st['E_A_cond']:9.4f} {st['S']:8.4f}")
    print("\n  Nothing about the judge's placement of errors changes down any column. f_A")
    print("  still climbs, because there is simply more error to place. With errors spread")
    print("  evenly f_A stays at 0.25 whatever the accuracy, which is [2] at E_A = 1/4.")

    print("\n" + "=" * 96)
    print("3. The pilot: which of the two moves with difficulty")
    print("=" * 96)
    print(f"  {'obvious':>7s} {'a':>7s} {'f_A':>8s} {'f_A null':>9s} {'E_A':>8s} "
          f"{'E_A|not at A':>13s} {'n_err':>6s} {'n_err cond':>11s}")
    for lv in LEVELS:
        st, _, _ = stats(pilot(lv))
        print(f"  {lv:7d} {st['a']:7.4f} {st['f_A']:8.4f} {st['f_A_null']:9.4f} "
              f"{st['E_A']:8.4f} {st['E_A_cond']:13.4f} {st['n_err']:6d} "
              f"{st['n_err_cond']:11d}")
    print("\n  'f_A null' is what an indifferent judge would show at these per-slot")
    print("  accuracies. f_A is compared against that, not against 0.25, for the same")
    print("  reason E_A is compared against 1/3 in its conditional form.")

    print("\n" + "=" * 96)
    print("4. Is the null of E_A really 0.25? Per-slot accuracy decides that")
    print("=" * 96)
    print("  E_A's null is 1/3 x (share of the error mass sitting on arrangements whose")
    print("  answer is not at A). That share is 3/4 only when every slot has the same")
    print("  accuracy. The conditional form drops the arrangement whose answer is at A and")
    print("  has null exactly 1/3 whatever the per-slot accuracies are.\n")
    print(f"  {'obvious':>7s} " + " ".join(f"{'acc@'+s:>8s}" for s in "ABCD")
          + " " + " ".join(f"{'err@'+s:>7s}" for s in "ABCD")
          + f" {'null of E_A':>12s} {'null cond':>10s}")
    for lv in LEVELS:
        _, acc, err = stats(pilot(lv))
        errs = [err[s] for s in "ABCD"]
        null = (1 / 3) * (sum(errs) - errs[0]) / sum(errs) if sum(errs) else float("nan")
        print(f"  {lv:7d} " + " ".join(f"{acc[s]:8.4f}" for s in "ABCD")
              + " " + " ".join(f"{e:7d}" for e in errs)
              + f" {null:12.4f} {1/3:10.4f}")
    print("\n  The null sits above 0.25 at every level, and it does so because the judge is")
    print("  most accurate when the answer is at A -- so little error mass lands on the one")
    print("  arrangement where an error cannot name A. That is the position effect inflating")
    print("  the null of the statistic meant to detect it, and it moves in the same direction")
    print("  as the hypothesis. Testing against 0.25 would credit some of it as preference.")

    print("\n" + "=" * 96)
    print("5. What the conditional denominator costs, and the threshold on it")
    print("=" * 96)
    print(f"  {'n_err cond':>11s} " + " ".join(f"{'true '+f'{t:.2f}':>11s}"
                                               for t in (1/3, 0.45, 0.60, 0.80)))
    for n in (20, 40, 60, 80, 120):
        cells = []
        for t in (1 / 3, 0.45, 0.60, 0.80):
            draws = RNG.binomial(n, t, size=4000) / n
            b = RNG.binomial(n, draws[:, None], size=(4000, 400)) / n
            cells.append(float(np.mean(np.percentile(b, 2.5, axis=1) > 1 / 3)))
        print(f"  {n:11d} " + " ".join(f"{c:10.1%} " for c in cells))
    print("\n  First column is the false-positive rate against the null of 1/3; the rest are")
    print("  power. 0.45 is the conditional equivalent of the old 0.35 and 0.60 of the old")
    print("  0.50, since dropping one arrangement raises every share by about a third.")


if __name__ == "__main__":
    main()
