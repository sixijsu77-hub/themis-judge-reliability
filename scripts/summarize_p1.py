#!/usr/bin/env python3
"""Decide H1, H2, H3 and H5 from the P1 runs, by the rules fixed in the pre-registration.

Nothing here chooses a threshold. Every threshold is read from PREREGISTRATION-exp01b.md §6,
which was committed before the first pass ran, and each hypothesis prints the number it was
compared against so the comparison can be checked rather than trusted.

  python scripts/summarize_p1.py

Difficulty is coded `d = 3 - obvious`, so d rises as the item gets harder and `--obvious 0`,
the unmodified benchmark item, is d = 3. H1 predicts a positive slope in that coding.

The statistic every hypothesis but H4 reads is `E*_A`: among the wrong verdicts on the three
arrangements whose correct answer is not at A, the share that name A. Its null is 1/3 and
does not move with the per-slot accuracies, which the first-slot rate's 0.25 does. Why that
matters is in scripts/decompose_f_a.py and PREREGISTRATION-exp01b.md section 5.

H1's gradient uses P1a only. P1b is a different item draw built for H3, so its `--obvious 3`
numbers are printed beside P1a's rather than pooled into a slope.
"""
import glob
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orderings import FIXED_DISTRACTORS, SLOT_OF

BOOT = 10000
SEED = 0
NEEDED = 4            # "at least 4 judges", against the 5 that passed the screen
N_JUDGES = 5          # the screen's survivors; a verdict needs data from all of them
NULL = 1 / 3          # the null of the conditional error share, at any per-slot accuracy
MIN_N_ERR = 40        # below this H3 cannot fire; registered before the run
LEVELS = [3, 2, 1, 0]
RNG = np.random.default_rng(SEED)


def load(phase):
    """{model: {obvious: {item_id: [(chosen_slot, letter, credited), ...]}}}"""
    out = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for path in sorted(glob.glob(f"results/exp01/{phase}_*.jsonl")):
        with open(path) as f:
            meta = json.loads(f.readline())
            if meta.get("_record") != "metadata":
                raise RuntimeError(f"{path} does not start with a metadata record")
            by_level = out[meta["model"]][meta["obvious"]]
            slot = meta["chosen_at_slot"]
            for line in f:
                o = json.loads(line)
                by_level[o["id"]].append((slot, o.get("parsed_letter"), o["results"]))
    return out


def verdict(passing, with_data):
    """Apply the registered clause, which counts an unevaluable judge against the hypothesis.

    The falsification clauses in section 6 read "fewer than 4 judges ... whether it excludes
    it upward, downward, or the judge could not be evaluated". So a judge that could not be
    evaluated is not neutral: it fails to support. The only thing this function refuses to
    call is a run that has not happened -- a missing judge is a missing measurement, not a
    measurement that came out unfavourably, and the two must not print the same word.
    """
    if with_data < N_JUDGES:
        return (f"RUN INCOMPLETE — {with_data} of {N_JUDGES} judges have data; "
                f"no verdict is recorded until all five do")
    return "HOLDS" if passing >= NEEDED else "FALSIFIED"


def counts_f(items, L):
    """Per item: (verdicts naming L, parsed verdicts). Resampling items resamples both."""
    ids = sorted(items)
    num = np.array([sum(1 for r in items[i] if r[1] == L) for i in ids], float)
    den = np.array([sum(1 for r in items[i] if r[1] in "ABCD") for i in ids], float)
    return num, den


def counts_err_A(items):
    """Per item: (wrong verdicts naming A, wrong verdicts where A was available).

    The arrangement whose correct answer is at A is dropped: an error there cannot name A,
    so including it makes the null depend on how much error that arrangement attracts. On
    the three that remain, an indifferent judge names A with probability 1/3 whatever its
    per-slot accuracies are, so the null is 1/3 by construction.
    """
    ids = sorted(items)
    wrong = [[r for r in items[i] if r[1] in "ABCD" and r[1] != r[0] and r[0] != "A"]
             for i in ids]
    num = np.array([sum(1 for r in w if r[1] == "A") for w in wrong], float)
    den = np.array([len(w) for w in wrong], float)
    return num, den


def ratio_ci(num, den, n=BOOT):
    """Bootstrap a ratio of two per-item totals over items. Returns (point, lo, hi).

    An item enters or leaves with both of its counts, which is what "bootstrap over items"
    has to mean when the four arrangements of one item are not independent.
    """
    idx = RNG.integers(0, len(num), (n, len(num)))
    a, b = num[idx].sum(1), den[idx].sum(1)
    draws = np.divide(a, b, out=np.full_like(a, np.nan), where=b > 0)
    draws = draws[~np.isnan(draws)]
    point = float(num.sum() / den.sum()) if den.sum() else float("nan")
    return point, float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def table(p1a):
    print("per judge and difficulty. letter fractions use parsed verdicts only.\n")
    hdr = (f"  {'judge':34s} {'obv':>3s} {'n':>5s} {'parsed':>7s} {'acc':>7s} "
           f"{'f_A':>7s} {'f_B':>7s} {'f_C':>7s} {'f_D':>7s} {'S':>7s} {'V':>7s}")
    print(hdr)
    for m in p1a:
        for lv in LEVELS:
            items = p1a[m].get(lv)
            if not items:
                continue
            rows = [r for i in items for r in items[i]]
            parsed = [r for r in rows if r[1] in "ABCD"]
            f = {L: sum(1 for r in parsed if r[1] == L) / len(parsed) for L in "ABCD"}
            acc_by_slot = {}
            for s in "ABCD":
                v = [r[2] for r in rows if r[0] == s]
                acc_by_slot[s] = sum(v) / len(v) if v else float("nan")
            print(f"  {m.split('/')[-1]:34s} {lv:3d} {len(items):5d} "
                  f"{len(parsed)/len(rows):7.1%} {sum(r[2] for r in rows)/len(rows):7.4f} "
                  + " ".join(f"{f[L]:7.4f}" for L in "ABCD")
                  + f" {max(f.values())-min(f.values()):7.4f}"
                  f" {max(acc_by_slot.values())-min(acc_by_slot.values()):7.4f}")
        print()
    print("  V is the accuracy spread over the four slots the correct answer occupies.")
    print("  It is position alone: these four arrangements hold the distractors in one order.")


def h1(p1a):
    print("\n" + "=" * 100)
    print("H1  slope of E*_A over difficulty (d = 3 - obvious) is positive, CI excluding 0")
    print("=" * 100)
    print("  Reads the conditional error share, not f_A. Identity [1] makes f_A's slope")
    print("  positive whenever E_A > 1/4 and accuracy falls, with placement unchanged, so")
    print("  the f_A slope is decomposed below rather than tested.\n")
    d = np.arange(4.0)
    dc = d - d.mean()
    print(f"  {'judge':34s} " + " ".join(f"{'d='+str(k):>8s}" for k in range(4))
          + f" {'slope':>9s} {'95% CI':>20s}  verdict")
    passed = []
    for m in p1a:
        if any(lv not in p1a[m] for lv in LEVELS):
            print(f"  {m.split('/')[-1]:34s}  incomplete, not evaluated")
            continue
        # The same items at every level, resampled together, so a bootstrap draw moves all
        # four points of the gradient at once and the slope's interval reflects that.
        common = sorted(set.intersection(*(set(p1a[m][lv]) for lv in LEVELS)))
        nums, dens = [], []
        for lv in LEVELS:                       # LEVELS is 3,2,1,0, so d = 0..3
            n_, d_ = counts_err_A({i: p1a[m][lv][i] for i in common})
            nums.append(n_)
            dens.append(d_)
        nums, dens = np.stack(nums), np.stack(dens)
        n_star = [int(x.sum()) for x in dens]
        pts = [float(n / d) if d else float("nan") for n, d in zip(nums.sum(1), dens.sum(1))]
        # Only levels with enough errors to give the statistic a denominator (section 3).
        keep = [k for k in range(4) if n_star[k] >= MIN_N_ERR]
        if len(keep) < 3:
            print(f"  {m.split('/')[-1]:34s} " + " ".join(f"{p:8.4f}" for p in pts)
                  + f"   NOT EVALUATED — only {len(keep)} level(s) with n_err* >= "
                    f"{MIN_N_ERR}   n_err*={n_star}")
            continue
        dk = np.array([float(k) for k in keep])
        dkc = dk - dk.mean()
        idx = RNG.integers(0, len(common), (BOOT, len(common)))
        draws = (nums[keep][:, idx].sum(2) / dens[keep][:, idx].sum(2)).T
        slopes = (dkc * (draws - draws.mean(1, keepdims=True))).sum(1) / (dkc ** 2).sum()
        yk = np.array([pts[k] for k in keep])
        point = float((dkc * (yk - yk.mean())).sum() / (dkc ** 2).sum())
        lo, hi = np.percentile(slopes, 2.5), np.percentile(slopes, 97.5)
        ok = bool(lo > 0)
        passed.append(ok)
        mono = all(b > a for a, b in zip(yk, yk[1:]))
        print(f"  {m.split('/')[-1]:34s} " + " ".join(f"{p:8.4f}" for p in pts)
              + f" {point:+9.4f} [{lo:+8.4f}, {hi:+8.4f}]  "
              + ("positive" if ok else "not positive")
              + f"   monotone={'yes' if mono else 'no'}   levels={keep}   n_err*={n_star}")
    print(f"\n  {sum(passed)} of {len(passed)} judges have a positive slope excluding zero; "
          f"H1 needs {NEEDED}.")
    print(f"  ==> H1 {verdict(sum(passed), len(p1a))}")
    print("  Strict monotonicity is printed but is not the criterion (§6). n_err* is the")
    print("  denominator at each level; a level with few errors carries little of the slope.")
    decompose(p1a)
    return sum(passed) >= NEEDED


def decompose(p1a):
    """Split the change in f_A from easiest to hardest into its three identity terms."""
    print("\n  the f_A slope, decomposed by identity [1]: f_A = (1/4) a_A + E*_A' (1 - a)")
    print("  where E*_A' is the unconditional share; the split below uses the measured")
    print("  E_A so the three terms add to the observed change exactly.\n")
    print(f"  {'judge':34s} {'f_A(easy)':>10s} {'f_A(hard)':>10s} {'change':>8s} | "
          f"{'a_A term':>9s} {'accuracy':>9s} {'placement':>10s}")
    for m in p1a:
        if any(lv not in p1a[m] for lv in LEVELS):
            continue
        common = sorted(set.intersection(*(set(p1a[m][lv]) for lv in LEVELS)))
        vals = {}
        for lv in (3, 0):
            rows = [r for i in common for r in p1a[m][lv][i] if r[1] in "ABCD"]
            wrong = [r for r in rows if r[1] != r[0]]
            at_A = [r for r in rows if r[0] == "A"]
            vals[lv] = dict(
                f_A=sum(1 for r in rows if r[1] == "A") / len(rows),
                a=sum(1 for r in rows if r[1] == r[0]) / len(rows),
                a_A=sum(1 for r in at_A if r[1] == r[0]) / len(at_A) if at_A else float("nan"),
                E_A=sum(1 for r in wrong if r[1] == "A") / len(wrong) if wrong else 0.0)
        e, h = vals[3], vals[0]
        t_aA = 0.25 * (h["a_A"] - e["a_A"])
        t_acc = e["E_A"] * ((1 - h["a"]) - (1 - e["a"]))
        t_pl = (1 - h["a"]) * (h["E_A"] - e["E_A"])
        print(f"  {m.split('/')[-1]:34s} {e['f_A']:10.4f} {h['f_A']:10.4f} "
              f"{h['f_A']-e['f_A']:+8.4f} | {t_aA:+9.4f} {t_acc:+9.4f} {t_pl:+10.4f}")
    print("\n  'accuracy' is what the same placement produces once there is more error to")
    print("  place; 'placement' is the part the judge's behaviour actually changed. The")
    print("  three sum to the observed change by construction.")


def h2(p1a):
    print("\n" + "=" * 100)
    print(f"H2  at --obvious 0 the CI on E*_A excludes {NULL:.4f} upward")
    print("=" * 100)
    print(f"  {'judge':34s} {'n_err*':>7s} {'E*_A':>8s} {'95% CI':>22s}  verdict")
    passed = []
    for m in p1a:
        items = p1a[m].get(0)
        if not items:
            print(f"  {m.split('/')[-1]:34s}  not run at --obvious 0")
            continue
        num, den = counts_err_A(items)
        pt, lo, hi = ratio_ci(num, den)
        ok = lo > NULL
        passed.append(ok)
        print(f"  {m.split('/')[-1]:34s} {int(den.sum()):7d} {pt:8.4f} "
              f"[{lo:+9.4f}, {hi:+9.4f}]  "
              + ("excludes upward" if ok else
                 "excludes downward" if hi < NULL else "includes 1/3"))
    print(f"\n  {sum(passed)} of {len(passed)} exclude {NULL:.4f} upward; H2 needs {NEEDED}.")
    print(f"  ==> H2 {verdict(sum(passed), len(p1a))}")

    print("\n  f_A beside it, against its own null rather than 0.25. This is the magnitude a")
    print("  published score carries, and its null moves with the per-slot accuracies.\n")
    print(f"  {'judge':34s} {'f_A':>8s} {'null of f_A':>12s} {'excess':>8s}")
    for m in p1a:
        items = p1a[m].get(0)
        if not items:
            continue
        rows = [r for i in items for r in items[i] if r[1] in "ABCD"]
        acc = {}
        for sl in "ABCD":
            v = [r for r in rows if r[0] == sl]
            acc[sl] = sum(1 for r in v if r[1] == sl) / len(v) if v else float("nan")
        f_A = sum(1 for r in rows if r[1] == "A") / len(rows)
        null = 0.25 * acc["A"] + (1 / 12) * sum(1 - acc[sl] for sl in "BCD")
        print(f"  {m.split('/')[-1]:34s} {f_A:8.4f} {null:12.4f} {f_A-null:+8.4f}")
    return sum(passed) >= NEEDED


def h3(p1b):
    print("\n" + "=" * 100)
    print(f"H3  at --obvious 3 the CI on E*_A contains {NULL:.4f}")
    print("=" * 100)
    print("  Null 1/3: on the three arrangements whose answer is not at A, an indifferent")
    print("  judge names A one time in three. Dropping the fourth arrangement is what makes")
    print("  the null independent of the per-slot accuracies.")
    print(f"  A judge with fewer than {MIN_N_ERR} usable errors is not evaluated and cannot")
    print(f"  count toward the {NEEDED}. That is reported as its own outcome, never as a pass.\n")
    print(f"  {'judge':34s} {'n_err*':>6s} {'E*_A':>8s} {'95% CI':>22s}  verdict")
    passed = n = 0
    for m in p1b:
        items = p1b[m].get(3)
        if not items:
            print(f"  {m.split('/')[-1]:34s}  not run")
            n += 1
            continue
        num, den = counts_err_A(items)
        n += 1
        if den.sum() < MIN_N_ERR:
            print(f"  {m.split('/')[-1]:34s} {int(den.sum()):6d} {'—':>8s} {'—':>22s}  "
                  f"NOT EVALUATED — too few errors (n_err* < {MIN_N_ERR})")
            continue
        pt, lo, hi = ratio_ci(num, den)
        ok = lo <= NULL <= hi
        passed += ok
        print(f"  {m.split('/')[-1]:34s} {int(den.sum()):6d} {pt:8.4f} "
              f"[{lo:+9.4f}, {hi:+9.4f}]  "
              + ("contains 1/3" if ok
                 else "EVALUATED AND FAILED — excludes 1/3 "
                      + ("upward" if lo > NULL else "downward")))
    print(f"\n  {passed} of {n} judges have a CI containing {NULL:.4f}; H3 needs {NEEDED}.")
    print(f"  ==> H3 {verdict(passed, len(p1b))}")
    print("  A pass means no strong slot preference. At about 47 usable errors the rule has")
    print("  96% power against a share of 0.60 and 40% against 0.45 (results/validation/")
    print("  decision_rules.txt §3b), so it cannot rule out a moderate one.")
    return passed >= NEEDED


def h5(p1a):
    print("\n" + "=" * 100)
    print("H5  across judges, E*_A at --obvious 0 is negatively rank-correlated with accuracy")
    print("=" * 100)
    print("  On f_A this would have been close to a tautology: identity [2] gives")
    print("  f_A = E_A + a(1/4 - E_A), so with every judge above 1/4 the correlation falls out")
    print("  of the algebra. E*_A asks whether a weaker judge has a stronger preference.\n")
    xs, ys, names = [], [], []
    for m in p1a:
        items = p1a[m].get(0)
        if not items:
            continue
        rows = [r for i in items for r in items[i]]
        parsed = [r for r in rows if r[1] in "ABCD"]
        num, den = counts_err_A(items)
        xs.append(float(num.sum() / den.sum()) if den.sum() else float("nan"))
        ys.append(sum(1 for r in parsed if r[1] == r[0]) / len(parsed))
        names.append(m.split("/")[-1])
    order_x = np.argsort(np.argsort(xs))
    order_y = np.argsort(np.argsort(ys))
    rho = float(np.corrcoef(order_x, order_y)[0, 1]) if len(xs) > 2 else float("nan")
    print(f"  {'judge':34s} {'E*_A':>8s} {'accuracy':>9s}")
    for nm, x, y in sorted(zip(names, xs, ys), key=lambda t: -t[1]):
        print(f"  {nm:34s} {x:8.4f} {y:9.4f}")
    print(f"\n  Spearman rho over {len(xs)} judges = {rho:+.4f}")
    if len(xs) < N_JUDGES:
        print(f"  ==> H5 RUN INCOMPLETE — {len(xs)} of {N_JUDGES} judges have data")
        return False
    print(f"  ==> H5 {'HOLDS' if rho < 0 else 'FALSIFIED'} (direction only; no significance "
          f"is claimed or tested)")
    return rho < 0


def main():
    p1a, p1b = load("P1a"), load("P1b")
    print(f"P1a: {sum(len(v) for v in p1a.values())} judge-levels over "
          f"{len(FIXED_DISTRACTORS)} arrangements "
          f"({', '.join(f'{i}->{SLOT_OF[i]}' for i in FIXED_DISTRACTORS)})")
    print(f"P1b: {sum(len(v) for v in p1b.values())} judge-levels\n")
    if p1a:
        table(p1a)
        h1(p1a)
        h2(p1a)
    if p1b:
        h3(p1b)
    if p1a:
        h5(p1a)


if __name__ == "__main__":
    main()
