#!/usr/bin/env python3
"""Take the conditional error share apart into the four slot rates it is built from.

On the slot-balanced arrangements every distractor visits every slot, so pooling the four
arrangements averages over candidate identity by construction. That gives, per slot, the rate
at which the judge names it when it does not hold the correct answer -- four numbers per
difficulty that owe nothing to which candidate happens to be there.

The conditional first-slot error share is one function of those four:

    E*_A  =  s_A / (s_A + s_B + s_C + s_D)      approximately

exactly if the four denominators were identical, and close enough on this data to read that
way. It is a **share**, so it rises either because the numerator rises or because the rest of
the denominator falls, and the two are not the same claim about a judge.

  python scripts/slot_rates.py
"""
import glob
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

LEVELS = [3, 2, 1, 0]
BOOT = 10000
RNG = np.random.default_rng(0)


def load(phase="P1c"):
    named = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    errs = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    per_item = defaultdict(lambda: defaultdict(dict))
    for path in sorted(glob.glob(f"results/exp01/{phase}_*.jsonl")):
        with open(path) as f:
            meta = json.loads(f.readline())
            chosen = meta["chosen_at_slot"]
            key = (meta["model"], meta["obvious"])
            rows = [(json.loads(l)["id"], json.loads(l)["parsed_letter"]) for l in
                    open(path).read().splitlines()[1:]]
            rows = [(i, L) for i, L in rows if L in "ABCD"]
            n_err = sum(1 for _, L in rows if L != chosen)
            for slot in "ABCD":
                if slot == chosen:
                    continue
                named[key][slot][0] += sum(1 for _, L in rows if L == slot)
                named[key][slot][1] += len(rows)
                errs[key][slot][0] += sum(1 for _, L in rows if L == slot)
                errs[key][slot][1] += n_err
                for i, L in rows:
                    per_item[key][slot][i] = per_item[key][slot].get(i, 0) + int(L == slot)
    return named, errs, per_item


def main():
    print((__doc__ or "").split("  python")[0].strip())
    named, errs, per_item = load()
    models = sorted({k[0] for k in named})

    print("\n" + "=" * 104)
    print("1. Identity-averaged rate of naming each slot, and what E*_A makes of them")
    print("=" * 104)
    print(f"  {'judge':30s} {'obv':>3s} " + " ".join(f"{'s_' + s:>8s}" for s in "ABCD")
          + f" {'E*_A':>8s} {'s_A/sum':>8s} {'s_A - s_D':>10s}")
    contrast = defaultdict(dict)
    for m in models:
        for lv in LEVELS:
            k = (m, lv)
            s = {sl: named[k][sl][0] / named[k][sl][1] for sl in "ABCD"}
            e = errs[k]["A"][0] / errs[k]["A"][1] if errs[k]["A"][1] else float("nan")
            tot = sum(s.values())
            contrast[m][lv] = s["A"] - s["D"]
            print(f"  {m.split('/')[-1]:30s} {lv:3d} "
                  + " ".join(f"{s[x]:8.4f}" for x in "ABCD")
                  + f" {e:8.4f} {s['A'] / tot if tot else float('nan'):8.4f} "
                  f"{s['A'] - s['D']:+10.4f}")
        print()

    print("=" * 104)
    print("2. What moves across difficulty: the numerator, the rest of the denominator, or both")
    print("=" * 104)
    print(f"  {'judge':30s} {'s_A obv2 -> obv0':>18s} {'s_B+s_C+s_D obv2 -> obv0':>26s}"
          f"  reading")
    for m in models:
        s2 = {sl: named[(m, 2)][sl][0] / named[(m, 2)][sl][1] for sl in "ABCD"}
        s0 = {sl: named[(m, 0)][sl][0] / named[(m, 0)][sl][1] for sl in "ABCD"}
        rest2 = sum(s2[x] for x in "BCD")
        rest0 = sum(s0[x] for x in "BCD")
        up = s0["A"] > s2["A"]
        down = rest0 < rest2
        reading = ("first slot rises and the rest falls" if up and down else
                   "first slot rises, the rest does not fall" if up else
                   "the rest falls, the first slot does not rise" if down else
                   "neither")
        print(f"  {m.split('/')[-1]:30s} {s2['A']:8.4f} ->{s0['A']:8.4f} "
              f"{rest2:12.4f} ->{rest0:12.4f}  {reading}")

    print("\n" + "=" * 104)
    print("3. H1 re-scored on the first-versus-last contrast instead of the share")
    print("=" * 104)
    print("  The contrast is a difference of two identity-averaged rates, not a share, so it")
    print("  does not rise when the middle slots empty. Same slope rule as H1: fitted over")
    print("  --obvious 2, 1 and 0, positive with a 95% interval excluding zero.\n")
    print(f"  {'judge':30s} " + " ".join(f"{'obv ' + str(l):>9s}" for l in LEVELS)
          + f" {'slope':>9s} {'95% CI':>20s} {'monotone':>9s}  verdict")
    passed = mono_n = 0
    for m in models:
        ids = sorted(set.intersection(*(set(per_item[(m, lv)]["A"]) for lv in LEVELS)))
        vals = []
        for lv in LEVELS:
            a = np.array([per_item[(m, lv)]["A"].get(i, 0) for i in ids], float)
            d = np.array([per_item[(m, lv)]["D"].get(i, 0) for i in ids], float)
            vals.append(a - d)
        v = np.stack(vals)[1:]                       # --obvious 2, 1, 0
        x = np.array([0.0, 1.0, 2.0])
        xc = x - x.mean()
        idx = RNG.integers(0, len(ids), (BOOT, len(ids)))
        draws = v[:, idx].mean(2).T
        slopes = (xc * (draws - draws.mean(1, keepdims=True))).sum(1) / (xc ** 2).sum()
        pts = [contrast[m][lv] for lv in LEVELS]
        point = float((xc * (v.mean(1) - v.mean())).sum() / (xc ** 2).sum())
        lo, hi = float(np.percentile(slopes, 2.5)), float(np.percentile(slopes, 97.5))
        mono = all(b > a for a, b in zip(pts, pts[1:]))
        mono_n += mono
        ok = lo > 0
        passed += ok
        print(f"  {m.split('/')[-1]:30s} " + " ".join(f"{p:+9.4f}" for p in pts)
              + f" {point:+9.4f} [{lo:+8.4f}, {hi:+8.4f}] {'yes' if mono else 'no':>9s}"
              f"  {'positive' if ok else 'not positive'}")
    print(f"\n  {passed} of {len(models)} have a positive slope excluding zero, and {mono_n} of "
          f"{len(models)} are monotone over all four levels.")
    print(f"  H1's threshold is 4. On this statistic H1 would be "
          f"{'held' if passed >= 4 else 'FALSIFIED'}; on the share it was held.")


def h5_axes():
    """How much each candidate accuracy axis moves when only the position pull changes."""
    print("\n" + "=" * 104)
    print("4. H5's axis: which accuracy measure is least moved by a pure position pull")
    print("=" * 104)
    print("  Skill fixed, only the slot weights vary. A judge picks a slot with probability")
    print("  proportional to its weight times the attractiveness of the candidate there.\n")
    def acc_by_pos(A, w):
        w = np.array(w, float)
        return np.array([w[p] * A / (w[p] * A + (w.sum() - w[p])) for p in range(4)])
    names = ("ans@A", "pooled", "mean B C D", "ans@D")
    print(f"  {'weights':26s} " + " ".join(f"{n:>11s}" for n in names))
    rows = []
    for w in ([1, 1, 1, 1], [1.5, 1, 1, 1], [2.5, 1, 1, 1], [5, 1, 1, 1],
              [1, 1, 1, 2.5], [1, 1, 1, 5]):
        a_ = acc_by_pos(4.0, w)
        v = (a_[0], a_.mean(), a_[1:].mean(), a_[3])
        rows.append(v)
        print(f"  {str(w):26s} " + " ".join(f"{x:11.4f}" for x in v))
    print(f"\n  {'spread at identical skill':26s} "
          + " ".join(f"{max(r[i] for r in rows) - min(r[i] for r in rows):11.4f}"
                     for i in range(4)))
    print("\n  Pooled accuracy moves least, and it is symmetric: a pull toward D costs it")
    print("  exactly what a pull toward A costs. E*_A is directional, so the mechanism that")
    print("  would manufacture their correlation pushes the wrong way.")


def strata(phases=("P1c",), label="P1c", expect_judges=5, expect_passes=None):
    """E*_A inside --obvious 0, split by how hard the other judges found each item.

    `phases` selects which runs supply the verdicts. P1c is the exploratory pass on 150
    items; the reduced P2 phases are the confirmatory one on 1,763, and both of its
    arrangement sets are pooled because the split is over items, not over arrangements.
    """
    print("\n" + "=" * 104)
    print("5. Difficulty taken from the item instead of the control set (exploratory)")
    print("=" * 104)
    print("  Inside --obvious 0 the distractors are always the item's own rejected responses,")
    print("  so the composition never changes. Item difficulty is the mean accuracy of the")
    print("  other four judges on that item, which leaves the judge under test out of its own")
    print("  difficulty measure. Split at the median.\n")
    rng = np.random.default_rng(0)
    by = defaultdict(lambda: defaultdict(list))
    paths = [p for ph in phases for p in sorted(glob.glob(f"results/exp01/{ph}_*_o0_*.jsonl"))]
    # A run still in flight produces a table that looks finished and is not. The last time
    # a partial artefact went unremarked it was committed at zero bytes.
    if not paths:
        print(f"\n  {label}: no runs found")
        return
    if expect_passes and len(paths) < expect_passes:
        print(f"\n  {label}: {len(paths)} of {expect_passes} passes present, still running "
              f"-- no table")
        return
    print(f"  source: {label}, {len(paths)} passes")
    for path in paths:
        with open(path) as f:
            meta = json.loads(f.readline())
            for line in f:
                r = json.loads(line)
                by[meta["model"]][r["id"]].append((meta["chosen_at_slot"], r["parsed_letter"]))
    models = sorted(by)
    if len(models) < expect_judges:
        print(f"  {label}: {len(models)} of {expect_judges} judges present -- no table")
        return
    items = sorted(set.intersection(*(set(by[m]) for m in models)))
    print(f"  {len(models)} judges x {len(items)} items\n")
    print(f"  {'judge':30s} {'stratum':>8s} {'n_err*':>7s} {'E*_A':>8s} {'95% CI':>18s} "
          f"{'width':>7s}")
    widths = []
    for m in models:
        others = [x for x in models if x != m]
        hard = {i: np.mean([np.mean([c == l for c, l in by[o][i]]) for o in others])
                for i in items}
        med = float(np.median(list(hard.values())))
        for label, keep in (("easy", [i for i in items if hard[i] >= med]),
                            ("hard", [i for i in items if hard[i] < med])):
            num = np.array([sum(1 for c, l in by[m][i] if c != "A" and l == "A")
                            for i in keep], float)
            den = np.array([sum(1 for c, l in by[m][i]
                                if c != "A" and l in "ABCD" and l != c) for i in keep], float)
            idx = rng.integers(0, len(keep), (4000, len(keep)))
            d = num[idx].sum(1) / np.maximum(den[idx].sum(1), 1)
            lo, hi = float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))
            widths.append(hi - lo)
            print(f"  {m.split('/')[-1]:30s} {label:>8s} {int(den.sum()):7d} "
                  f"{num.sum() / den.sum():8.4f} [{lo:+7.4f},{hi:+7.4f}] {hi - lo:7.4f}")
        print()
    # The registered condition. Difficulty barely moves E*_A for a constant-preference
    # judge; heterogeneity among the distractors moves it about twenty times as much. So the
    # strata are only readable as a difficulty contrast if they do not also differ in that.
    lens = {}
    for src in ("data/p2_o0/test.jsonl", "data/control_o0/test.jsonl"):
        if not os.path.isfile(src):
            continue
        for line in open(src):
            r = json.loads(line)
            lens.setdefault(r["id"],
                            [len(x if isinstance(x, str) else x[0]) for x in r["rejected"]])
    if lens:
        print("\n  registered condition: do the strata differ in distractor heterogeneity?")
        print(f"  {'judge':30s} {'easy':>9s} {'hard':>9s} {'diff':>9s} {'95% CI':>21s}")
        broken = 0
        for m in models:
            others = [x for x in models if x != m]
            h = {i: np.mean([np.mean([c == l for c, l in by[o][i]]) for o in others])
                 for i in items}
            med = float(np.median(list(h.values())))
            grp = {}
            for lab, keep in (("easy", [i for i in items if h[i] >= med]),
                              ("hard", [i for i in items if h[i] < med])):
                grp[lab] = np.array([np.std(lens[i]) / max(np.mean(lens[i]), 1)
                                     for i in keep if i in lens])
            if not len(grp["easy"]) or not len(grp["hard"]):
                continue
            ie = rng.integers(0, len(grp["easy"]), (4000, len(grp["easy"])))
            ih = rng.integers(0, len(grp["hard"]), (4000, len(grp["hard"])))
            bs = grp["easy"][ie].mean(1) - grp["hard"][ih].mean(1)
            lo, hi = float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
            ok = lo <= 0 <= hi
            broken += not ok
            print(f"  {m.split('/')[-1]:30s} {grp['easy'].mean():9.4f} "
                  f"{grp['hard'].mean():9.4f} "
                  f"{grp['easy'].mean() - grp['hard'].mean():+9.4f} "
                  f"[{lo:+9.4f},{hi:+9.4f}]" + ("" if ok else "  DIFFERS"))
        if broken:
            print(f"\n  **The condition fails for {broken} of {len(models)} judges.** The")
            print("  strata differ in the one property that moves this statistic without any")
            print("  change in the judge, so the table above cannot be read as a difficulty")
            print("  effect. The split is by other judges' accuracy, and items whose")
            print("  distractors vary more in length are items other judges get right more")
            print("  often -- so the difficulty axis and the heterogeneity axis are the same")
            print("  axis here. This test is void, and that is its result.")

    w = float(np.mean(widths))
    print(f"\n  mean interval width at 150 items: {w:.4f}")
    print(f"  projected at 1,763 items, scaling as one over the square root of n: "
          f"{w * np.sqrt(150 / 1763):.4f}")
    print("\n  The split was chosen after seeing P1c, so P1c's pass is exploratory and the")
    print("  reduced P2 sample is the confirmatory one. Both are printed when both exist.")


if __name__ == "__main__":
    main()
    h5_axes()
    strata(("P1c",), "P1c, exploratory")
    strata(("P2a", "P2b"), "reduced P2, confirmatory", expect_passes=40)
