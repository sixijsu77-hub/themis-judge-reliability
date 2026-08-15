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
    print("\n  With no slot preference the balanced set sits at one third at every level,")
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
    # Widened 2026-08-15 by a decade at each end after the first grid's maximum was quoted
    # as if it were a bound. It is not a bound; it is the largest value searched.
    grid_c = [1.2, 1.5, 3.0, 6.0, 12.0, 25.0, 60.0, 200.0, 600.0]
    grid_own = [1.0]
    grid_off = [0.0005, 0.005, 0.02, 0.05, 0.15, 0.4, 1.0, 2.5, 8.0]
    lv = [0.002, 0.02, 0.05, 0.15, 0.4, 0.7, 1.0, 2.0, 5.0, 50.0]
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
    print("\n  observed slopes on the balanced set, computed from the P1c runs:")
    hit, ea = observed()
    for m in sorted(hit):
        print(f"    {m.split('/')[-1]:32s} {observed_slope(ea, m):+.4f}")

    print("\n" + "=" * 92)
    print("3b. The same, on the first-versus-last contrast, which is not a share")
    print("=" * 92)
    print(f"  {'set':10s} {'max slope':>10s}   attained at")
    for name in SETS:
        sl, cfg = best_c[name]
        print(f"  {name:10s} {sl:+10.4f}   correct={cfg[0]}, off-topic={cfg[1]}, "
              f"weights={[round(float(x), 3) for x in cfg[2]]}")
        print(f"  {'':10s} {'':10s}   s_A - s_D " + " ".join(f"{v:+.4f}" for v in cfg[3]))
    print("\n  the observed contrast slopes are in results/validation/slot_rates.txt §3,")
    print("  computed there from the same runs and not restated here.")

    print("\n" + "=" * 92)
    print("4. What null does H1 test?")
    print("=" * 92)
    print("""
  The registered criterion is that the slope's interval excludes zero. A slope of zero is
  what a judge produces when the statistic does not move across difficulty -- not when the
  judge has no slot preference. Those are different nulls, and sections 3 and 3b show how
  far apart they are: the maxima printed there are reached by a judge whose slot weights are
  literally the same four numbers at every difficulty.

  **So the criterion does not separate the hypothesis from its negation on this design.**
  H1 as written tests "the statistic rises with difficulty". Section 1 claims "the judge's
  preference for the first slot strengthens with difficulty", and a judge that cannot do the
  second produces the first.

  The shapes agree too, which is the part that is hard to argue with. The row printed under
  each maximum in section 3 has the same form as the measured one: high where the answer is
  not in dispute, a trough in the middle, and a rise to the benchmark item. The measured rows
  are in results/exp01/p1_summary.txt, under H1.

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


def accuracy(indices, weights, attract, obvious):
    """Pooled accuracy over the four arrangements, under the same choice model."""
    k = kinds(obvious)
    tot = 0.0
    for i in indices:
        perm = ALL[i]
        p = np.array([attract[k[c]] * weights[j] for j, c in enumerate(perm)])
        p = p / p.sum()
        tot += p[list(perm).index(0)]
    return tot / len(indices)


def _structure(indices):
    """Per difficulty, the candidate kind at each slot and where the correct answer sits.

    Kinds are 0 correct, 1 the item's own rejected response, 2 off-topic. Building this once
    turns the fit's inner loop into one array operation over a whole batch of candidate
    parameter vectors, which is the difference between a fit that finishes and one that does
    not: the loop version evaluated the loss about seven million times and was still running
    after three hours.
    """
    KIND = {"correct": 0, "own": 1, "off": 2}
    per_level = {}
    for lv in LEVELS:
        k = [KIND[x] for x in kinds(lv)]
        idx = np.array([[k[ALL[i][j]] for j in range(4)] for i in indices])
        chosen = np.array([list(ALL[i]).index(0) for i in indices])
        per_level[lv] = (idx, chosen)
    return per_level


def _probs(struct_lv, att, w):
    """(batch, arrangement, slot) choice probabilities. att is (batch, 3), w is (batch, 4)."""
    idx, _ = struct_lv
    p = att[:, idx] * w[:, None, :]
    return p / p.sum(2, keepdims=True)


def _batch_targets(struct, att, w):
    """The five fitted quantities for a batch: four accuracies, then E*_A at --obvious 2."""
    out = []
    for lv in LEVELS:
        _, chosen = struct[lv]
        p = _probs(struct[lv], att, w)
        out.append(p[:, np.arange(len(chosen)), chosen].mean(1))
    _, chosen = struct[2]
    p = _probs(struct[2], att, w)
    keep = chosen != 0
    num = p[:, keep, 0].sum(1)
    den = (1 - p[:, np.arange(len(chosen)), chosen][:, keep]).sum(1)
    out.append(np.divide(num, den, out=np.full_like(num, np.nan), where=den > 0))
    return np.stack(out, axis=1)


def fit_judge(targets, indices, rounds=60, draws=4000, seed=0, start=None, span=None):
    """Fit c, off-topic attractiveness and three slot weights to one judge's own numbers.

    Five free parameters against five targets: pooled accuracy at each of the four
    difficulties and the conditional first-slot share at --obvious 2. A random search with
    shrinking radius, because the search space is small and there is no optimiser here.
    Returns (parameters, worst absolute deviation on the targets).
    """
    rng = np.random.default_rng(seed)
    lo = np.array([np.log(0.5), np.log(1e-4), *([np.log(1e-3)] * 3)])
    hi = np.array([np.log(2e3), np.log(20.0), *([np.log(2e2)] * 3)])
    # A bootstrap replicate differs from the point fit only by resampling noise, so it starts
    # from the point fit's solution and searches a small ball around it. Without that the
    # replicate's search budget has to rediscover the whole space, and a fit that fails
    # because the search was short is indistinguishable from a model that cannot fit.
    if start is not None:
        centre, radius = np.array(start, float), np.full(5, span if span else 0.6)
    else:
        centre, radius = (lo + hi) / 2, (hi - lo) / 2

    struct = _structure(indices)
    want = np.asarray(targets, float)
    best = (9e9, None, None)
    for _ in range(rounds):
        cand = np.clip(centre + radius * rng.uniform(-1, 1, (draws, 5)), lo, hi)
        e = np.exp(cand)
        att = np.stack([e[:, 0], np.ones(len(e)), e[:, 1]], axis=1)
        w = np.concatenate([np.ones((len(e), 1)), e[:, 2:]], axis=1)
        got = _batch_targets(struct, att, w)
        dev = np.nanmax(np.abs(got - want), axis=1)
        j = int(np.nanargmin(dev))
        if dev[j] < best[0]:
            best = (float(dev[j]), cand[j], list(got[j]))
        centre, radius = best[1], radius * 0.85
    return best


def observed(phase="P1c"):
    """Read each judge's own numbers from the run, per item so they can be resampled.

    Everything the fit consumes and everything it predicts comes from this one phase. The
    first version of this section used accuracies typed by hand from a different phase and
    an E*_A from this one; the two phases differ by up to 0.22 in pooled accuracy at
    --obvious 2, because their arrangement sets present the distractors differently.
    """
    import glob
    import json
    from collections import defaultdict
    hit = defaultdict(lambda: defaultdict(dict))     # model -> obvious -> id -> [correct...]
    ea = defaultdict(lambda: defaultdict(dict))      # model -> obvious -> id -> [num, den]
    for path in sorted(glob.glob(f"results/exp01/{phase}_*.jsonl")):
        with open(path) as f:
            meta = json.loads(f.readline())
            slot = meta["chosen_at_slot"]
            for line in f:
                r = json.loads(line)
                L = r["parsed_letter"]
                if L not in "ABCD":
                    continue
                hit[meta["model"]][meta["obvious"]].setdefault(r["id"], []).append(L == slot)
                if slot != "A":
                    c = ea[meta["model"]][meta["obvious"]].setdefault(r["id"], [0, 0])
                    c[0] += L == "A"
                    c[1] += L != slot
    return hit, ea


def targets_from(hit, ea, m, ids=None):
    """The five numbers the fit is pinned to: four accuracies and the --obvious 2 share."""
    accs = []
    for lv in LEVELS:
        d = hit[m][lv]
        keys = ids if ids is not None else list(d)
        num = sum(sum(d[i]) for i in keys if i in d)
        den = sum(len(d[i]) for i in keys if i in d)
        accs.append(num / den if den else float("nan"))
    d = ea[m][2]
    keys = ids if ids is not None else list(d)
    num = sum(d[i][0] for i in keys if i in d)
    den = sum(d[i][1] for i in keys if i in d)
    return accs + [num / den if den else float("nan")]


def observed_slope(ea, m, ids=None):
    """The E*_A slope over the levels H1 fits, from the same verdicts."""
    sh = []
    for lv in (2, 1, 0):
        d = ea[m][lv]
        keys = ids if ids is not None else list(d)
        num = sum(d[i][0] for i in keys if i in d)
        den = sum(d[i][1] for i in keys if i in d)
        sh.append(num / den if den else float("nan"))
    x = np.array([0.0, 1.0, 2.0])
    x = x - x.mean()
    y = np.array(sh)
    return float((x * (y - y.mean())).sum() / (x ** 2).sum())


def predict(targets, indices, seed=0, start=None):
    """Fit, then read the slope off the fitted twin. Returns (deviation, slope, parameters)."""
    if start is None:
        # Budget past the point where more search stops lowering the deviation, which was
        # measured rather than assumed: thirteen times this changes none of the five.
        dev, v, _ = fit_judge(targets, indices, rounds=200, draws=40000, seed=seed)
    else:
        dev, v, _ = fit_judge(targets, indices, rounds=30, draws=900, seed=seed, start=start)
    c, off, wb, wc, wd = np.exp(v)
    at = {"correct": c, "own": 1.0, "off": off}
    w = np.array([1.0, wb, wc, wd])
    return dev, slope([e_star(indices, w, at, lv)[0] for lv in LEVELS]), v


def section5(boot=400):
    """A null calibrated to each judge, with an interval, from one phase only."""
    print("\n" + "=" * 92)
    print("5. A null fitted to each judge, since the grid maximum is a property of the grid")
    print("=" * 92)
    print("""
  Sections 3 and 3b search a grid and print its maximum. Widening that grid by a decade at
  each end raised both maxima, which is what a grid maximum does. A number that moves when
  the search moves is not a bound, and "how many judges exceed it" is then a fact about the
  search rather than about the judges. So
  the null is fitted instead: five parameters -- the correct answer's attractiveness, the
  off-topic attractiveness, and three slot weights -- against five of that judge's own
  numbers, its pooled accuracy at each difficulty and its conditional share at --obvious 2.

  Five parameters against five targets leaves no residual freedom, so the predicted slope is
  a deterministic function of five sample quantities. Both it and the observed slope are
  therefore resampled over items, and both intervals are shown. A judge beats its twin only
  if the two intervals do not overlap.
""")
    hit, ea = observed()
    models = sorted(hit)
    rng = np.random.default_rng(0)
    print(f"  {'judge':28s} {'fit dev':>8s} {'twin slope':>26s} "
          f"{'observed slope':>26s}  verdict")
    beat = 0
    fits = {}
    for m in models:
        ids = sorted(hit[m][0])
        dev, pred, v0 = predict(targets_from(hit, ea, m), SLOT_BALANCED)
        fits[m] = dev
        obs_pt = observed_slope(ea, m)
        preds, obss = [], []
        for b in range(boot):
            samp = [ids[j] for j in rng.integers(0, len(ids), len(ids))]
            t = targets_from(hit, ea, m, samp)
            if any(x != x for x in t):
                continue
            d2, p2, _ = predict(t, SLOT_BALANCED, seed=b + 1, start=v0)
            if d2 <= 0.02:
                preds.append(p2)
            obss.append(observed_slope(ea, m, samp))
        if len(preds) < 20 or dev > 0.02:
            print(f"  {m.split('/')[-1]:28s} {dev:8.4f} {'model does not fit':>26s} "
                  f"{obs_pt:+26.4f}  no prediction")
            continue
        plo, phi = np.percentile(preds, [2.5, 97.5])
        olo, ohi = np.percentile(obss, [2.5, 97.5])
        won = olo > phi
        beat += won
        print(f"  {m.split('/')[-1]:28s} {dev:8.4f} "
              f"{pred:+9.4f} [{plo:+7.4f},{phi:+7.4f}] "
              f"{obs_pt:+9.4f} [{olo:+7.4f},{ohi:+7.4f}]  "
              + ("beats its twin" if won else "intervals overlap"))
    print(f"\n  {beat} of {len(models)} beat their own twin with non-overlapping intervals.")
    print("  H1's threshold is 4.")
    print("\n  fit deviation, sorted, against the 0.02 cutoff used above:")
    for m, d in sorted(fits.items(), key=lambda kv: kv[1]):
        print(f"    {m.split('/')[-1]:32s} {d:.4f}  {'fits' if d <= 0.02 else 'does not fit'}")
    ordered = sorted(fits.values())
    below = [d for d in ordered if d <= 0.02]
    above = [d for d in ordered if d > 0.02]
    gap = (above[0] - below[-1]) if below and above else float("nan")
    print(f"""
  That cutoff is a number chosen here and not registered, and the two judges either side of
  it are {gap:.4f} apart. Raising the search thirteenfold moves none of the five, so a judge
  above the line is one this model cannot represent rather than one the search missed -- but
  which side of the line it falls on is partly a property of where the line was drawn, and
  that deserves more caution than a count of judges conveys.""")


def section6():
    """Inside --obvious 0, which knob moves the statistic: item difficulty or heterogeneity."""
    print("\n" + "=" * 92)
    print("6. Two knobs that remain inside --obvious 0, at a fixed slot preference")
    print("=" * 92)
    w = np.array([1.6, 1.0, 0.8, 0.6])

    def share(A, rs):
        num = den = 0.0
        for i in SLOT_BALANCED:
            perm = ALL[i]
            att = [A] + list(rs)
            p = np.array([att[c] * w[j] for j, c in enumerate(perm)])
            p = p / p.sum()
            cs = list(perm).index(0)
            if cs == 0:
                continue
            den += 1 - p[cs]
            num += p[0]
        return num / den

    print("\n  A) item difficulty: the correct answer's margin over the distractors")
    print(f"  {'margin':>8s} {'E*_A':>8s}")
    a_vals = [share(A, [1.0, 1.0, 1.0]) for A in (8.0, 4.0, 2.0, 1.2, 0.8)]
    for A, v in zip((8.0, 4.0, 2.0, 1.2, 0.8), a_vals):
        print(f"  {A:8.1f} {v:8.4f}")
    print("\n  B) heterogeneity among the distractors, holding their mean fixed")
    print(f"  {'spread':>8s} {'E*_A':>8s}")
    b_vals = [share(2.0, [1 - sp, 1.0, 1 + sp]) for sp in (0.0, 0.3, 0.6, 0.9)]
    for sp, v in zip((0.0, 0.3, 0.6, 0.9), b_vals):
        print(f"  {sp:8.2f} {v:8.4f}")
    print(f"\n  range under A: {max(a_vals) - min(a_vals):.4f}   "
          f"range under B: {max(b_vals) - min(b_vals):.4f}")
    print("""
  Item difficulty barely moves the statistic; heterogeneity moves it twenty times more. So
  splitting --obvious 0 by how hard the item is gives a difficulty axis a constant preference
  does not respond to -- which is the axis section 6 says the --obvious ladder cannot be --
  provided the strata do not also differ in heterogeneity. That has to be checked, not
  assumed.""")


if __name__ == "__main__":
    main()
    section5()
    section6()
