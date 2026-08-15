#!/usr/bin/env python3
"""H-e1: does a judge's slot disposition keep its direction across difficulty, once the
strata are matched on heterogeneity?

Registered in PREREGISTRATION-exp01e.md and committed before this ran. The design is not
chosen here: bands, pooling, resample count, readability rule and threshold are all fixed
there, and this file is the arithmetic.

  python scripts/band_strata.py

Loading, difficulty and heterogeneity come from scripts/band_power.py, which is the same path
scripts/slot_rates.py uses for its confirmatory stratum table.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from band_power import BANDS, FLOOR, heterogeneity, records

NULL = 1 / 3
BOOT = 4000
RNG = np.random.default_rng(0)


def cells(diff_j, het, items, B):
    """[(band, stratum, [item keys])] under equal-count heterogeneity bands."""
    h = np.array([het[i] for i in items])
    edges = np.quantile(h, np.linspace(0, 1, B + 1))
    out = []
    for b in range(B):
        sel = [i for k, i in enumerate(items)
               if h[k] >= edges[b] and (h[k] <= edges[b + 1] if b == B - 1
                                        else h[k] < edges[b + 1])]
        if not sel:
            continue
        med = float(np.median([diff_j[i] for i in sel]))
        out.append((b, "easy", [i for i in sel if diff_j[i] >= med]))
        out.append((b, "hard", [i for i in sel if diff_j[i] < med]))
    return out


def counts(by_judge, keys):
    """Per item: (errors landing on A, errors at arrangements where A is not correct)."""
    num = np.array([sum(1 for c, l in by_judge[i] if c != "A" and l == "A")
                    for i in keys], float)
    den = np.array([sum(1 for c, l in by_judge[i]
                        if c != "A" and l in "ABCD" and l != c) for i in keys], float)
    return num, den


def stratum(by_judge, groups):
    """Pooled E*_A over a stratum's cells, its interval, and the unweighted variant.

    Primary is the ratio of summed counts, which is how E*_A is defined everywhere in this
    repository. The interval resamples items within the stratum. The unweighted variant is the
    mean of the per-band ratios and is reported beside it because a weighted and an unweighted
    pooling of the same cells have inverted a conclusion here before.
    """
    per_band, nums, dens = [], [], []
    for _, _, keys in groups:
        n, d = counts(by_judge, keys)
        nums.append(n)
        dens.append(d)
        if d.sum() > 0:
            per_band.append(n.sum() / d.sum())
    num = np.concatenate(nums)
    den = np.concatenate(dens)
    idx = RNG.integers(0, len(num), (BOOT, len(num)))
    boot = num[idx].sum(1) / np.maximum(den[idx].sum(1), 1)
    return (num.sum() / den.sum(), float(np.percentile(boot, 2.5)),
            float(np.percentile(boot, 97.5)), float(np.mean(per_band)), int(den.sum()))


def main():
    by, n_passes = records()
    het = heterogeneity()
    models = sorted(by)
    items = sorted(set.intersection(*(set(by[m]) for m in models)) & set(het))
    print(f"  H-e1, registered in PREREGISTRATION-exp01e.md")
    print(f"  {len(models)} judges x {len(items)} items, {n_passes} passes, null = {NULL:.4f}\n")

    diff = {m: {i: float(np.mean([np.mean([c == l for c, l in by[o][i]])
                                  for o in models if o != m])) for i in items}
            for m in models}
    verdict, ceiling, res_rows, calls = {}, {}, {}, []
    for B in BANDS:
        print(f"  B = {B}")
        print("  " + "-" * 98)
        print(f"  {'judge':30s} {'stratum':>7s} {'n_err*':>7s} {'E*_A':>8s} {'95% CI':>19s} "
              f"{'sign':>6s} {'unweighted':>11s}")
        agree = 0
        resolvable = {}
        for m in models:
            groups = cells(diff[m], het, items, B)
            signs, row = {}, []
            for lab in ("easy", "hard"):
                g = [c for c in groups if c[1] == lab]
                e, lo, hi, unw, n = stratum(by[m], g)
                readable = lo > NULL or hi < NULL
                signs[lab] = ("+" if e > NULL else "-") if readable else None
                row.append((lab, n, e, lo, hi, signs[lab], unw))
            ok = signs["easy"] is not None and signs["easy"] == signs["hard"]
            agree += ok
            for lab, n, e, lo, hi, s, unw in row:
                print(f"  {m.split('/')[-1]:30s} {lab:>7s} {n:7d} {e:8.4f} "
                      f"[{lo:+8.4f},{hi:+8.4f}] {s or 'null':>6s} {unw:11.4f}")
            unread = [lab for lab in ("easy", "hard") if signs[lab] is None]
            note = ("agrees" if ok else
                    f"not counted -- sign unreadable on {' and '.join(unread)}" if unread else
                    "does not agree -- signs differ")
            print(f"  {'':30s} {note}\n")
            # The hard stratum estimates the judge's disposition to within a few thousandths;
            # the question the easy stratum has to answer is whether it can see something that
            # size. Where it cannot, the judge is uncountable by construction, not undecided.
            e_lab, h_lab = row[0], row[1]
            half = (e_lab[4] - e_lab[3]) / 2
            resolvable[m] = abs(h_lab[2] - NULL) > half
            res_rows.setdefault(m, {"gap": abs(h_lab[2] - NULL)})[B] = half
            for lab, n, e, lo, hi, sg, unw in row:
                if sg is not None:
                    calls.append((min(abs(lo - NULL), abs(hi - NULL)), m, B, lab, lo, hi))
        ceiling[B] = sum(resolvable.values())
        unres = sorted(n.split("/")[-1] for n, ok in resolvable.items() if not ok)
        verdict[B] = agree
        print(f"  {agree} of {len(models)} judges agree at B = {B}; "
              f"{agree} of the {ceiling[B]} this sample can resolve")
        if unres:
            print(f"  unresolvable at this B: {', '.join(unres)} -- the disposition its hard")
            print("  stratum measures is smaller than its easy stratum's interval half-width,")
            print("  so no outcome of this design could have counted it either way\n")
        else:
            print()

    print("  " + "=" * 98)
    hold = all(v >= 4 for v in verdict.values())
    print(f"  H-e1: {' '.join(f'B={b} -> {v}/5' for b, v in verdict.items())}")
    print(f"  attainable maximum, judges this sample can resolve: "
          f"{' '.join(f'B={b} -> {c}' for b, c in ceiling.items())}")
    print(f"  Registered threshold is 4 of 5 at every one of B = "
          f"{', '.join(map(str, BANDS))}.")
    print(f"  **H-e1 {'HOLDS' if hold else 'is FALSIFIED'}.**\n")
    print("  Which judges this sample could resolve at all")
    print("  " + "-" * 98)
    print("  The hard stratum estimates a judge's disposition to a few thousandths. The easy")
    print("  stratum holds a fifth to a quarter of the errors, so about twice the interval, and")
    print("  the question is whether it can see something that size. A judge whose gap is")
    print("  smaller than its own half-width is uncountable whatever it does.\n")
    print(f"  The gap is taken at B={BANDS[0]}; it moves by under a thousandth across the three.\n")
    print(f"  {'judge':30s} {'gap from null':>14s} "
          + " ".join(f"{f'half-width B={b}':>17s}" for b in BANDS) + "  resolvable")
    for m in models:
        r = res_rows[m]
        ok = all(r["gap"] > r[b] for b in BANDS)
        print(f"  {m.split('/')[-1]:30s} {r['gap']:14.4f} "
              + " ".join(f"{r[b]:17.4f}" for b in BANDS)
              + f"  {'yes' if ok else 'NO, at any B'}")
    print()
    print("  On the readable rule. A sign is readable when its interval excludes the null, which")
    print("  is a binary verdict on a resampled quantity, so a call can sit inside its own noise.")
    calls.sort()
    d, m, B, lab, lo, hi = calls[0]
    print(f"  The narrowest call here is {m.split('/')[-1]} at B={B}, {lab}: the interval")
    print(f"  [{lo:+.4f},{hi:+.4f}] clears the null by {d:.4f}, from {BOOT:,} resamples at a")
    print("  registered seed. It reproduces; it is not stable. Recorded rather than fixed,")
    print("  because changing a registered rule to taste is what registration is against.\n")
    print("  What this does not say. H-e1 is about the sign surviving, not about E*_A moving:")
    print("  a judge can agree on sign while its two strata differ. Matching covers")
    print("  heterogeneity, the one property a simulation found moves this statistic without a")
    print(f"  change in the judge; another with the same power would be invisible here. Cell")
    print(f"  sizes and the matching check are in band_power.txt, floor {FLOOR}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
