#!/usr/bin/env python3
"""Decide J1 and J2 of exp01c on logs that were already committed.

Both ask whether the sign of a judge's conditional first-slot error share is a property of
the judge. J1 splits the 1,763 items in half; J2 compares the two difficulty levels that
were run at full size. Neither needs a new pass, and both were registered in
PREREGISTRATION-exp01c.md before this file computed anything.

The sign is read only where the 95% interval excludes 1/3. A half or a level whose interval
contains the null agrees with neither sign and counts against the prediction, which is the
rule exp01b arrived at after H3: a measurement that could not fire is not a measurement that
passed.

  python scripts/sign_stability.py
"""
import glob
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

NULL = 1 / 3
MIN_N_ERR = 40
NEEDED = 4
BOOT = 10000
SEED = 0
RNG = np.random.default_rng(SEED)


def load(phase, obvious=None):
    """{model: {(subset, id): [(chosen slot, letter), ...]}} for one phase.

    `obvious` filters to one difficulty. Without it a phase that ran several -- P1c ran four
    -- pools them, which silently turns a comparison at one difficulty into a comparison
    across all of them. That happened once and the error counts gave it away.

    The filter reads each file's own metadata rather than narrowing the glob, which is what
    the three sibling loaders do. A glob that stops matching returns nothing, and nothing is
    indistinguishable from zero errors and from "not evaluated" -- and this repository has
    extended its filename convention six times.
    """
    out = defaultdict(lambda: defaultdict(list))
    for path in sorted(glob.glob(f"results/exp01/{phase}_*.jsonl")):
        with open(path) as f:
            meta = json.loads(f.readline())
            if obvious is not None and meta["obvious"] != obvious:
                continue
            slot = meta["chosen_at_slot"]
            for line in f:
                r = json.loads(line)
                out[meta["model"]][(r["subset"], r["id"])].append((slot, r["parsed_letter"]))
    return out


def share(items, keys):
    """(E*_A, lo, hi, n) over the given item keys, bootstrapped over items."""
    num, den = [], []
    for k in keys:
        rows = [r for r in items.get(k, []) if r[1] in "ABCD" and r[0] != "A"]
        wrong = [r for r in rows if r[1] != r[0]]
        num.append(sum(1 for r in wrong if r[1] == "A"))
        den.append(len(wrong))
    num, den = np.array(num, float), np.array(den, float)
    if den.sum() < MIN_N_ERR:
        return float("nan"), float("nan"), float("nan"), int(den.sum())
    idx = RNG.integers(0, len(keys), (BOOT, len(keys)))
    a, b = num[idx].sum(1), den[idx].sum(1)
    d = np.divide(a, b, out=np.full_like(a, np.nan), where=b > 0)
    d = d[~np.isnan(d)]
    return (float(num.sum() / den.sum()), float(np.percentile(d, 2.5)),
            float(np.percentile(d, 97.5)), int(den.sum()))


def sign_of(pt, lo, hi, n):
    if n < MIN_N_ERR:
        return "not evaluated"
    if lo > NULL:
        return "above"
    if hi < NULL:
        return "below"
    return "contains"


def report(title, blocks, note):
    """blocks: {model: [(label, (pt, lo, hi, n)), ...]} with exactly two entries each."""
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)
    print(note + "\n")
    lab = [b[0] for b in next(iter(blocks.values()))]
    print(f"  {'judge':30s} " + " ".join(f"{l:>28s}" for l in lab) + "  agree?")
    agree = 0
    for m, rows in blocks.items():
        cells, signs = [], []
        for _, (pt, lo, hi, n) in rows:  # noqa: B007
            s = sign_of(pt, lo, hi, n)
            signs.append(s)
            cells.append(f"{pt:.4f} [{lo:+.3f},{hi:+.3f}] n={n}" if n >= MIN_N_ERR
                         else f"{'not evaluated, n=' + str(n):>28s}")
        ok = signs[0] == signs[1] and signs[0] in ("above", "below")
        agree += ok
        print(f"  {m.split('/')[-1]:30s} " + " ".join(f"{c:>28s}" for c in cells)
              + f"  {'yes' if ok else 'no — ' + ' / '.join(signs)}")
    print(f"\n  {agree} of {len(blocks)} agree with a sign read at both; the rule needs "
          f"{NEEDED}.")
    print(f"  ==> {'HOLDS' if agree >= NEEDED else 'FALSIFIED'}")
    return agree


def main():
    print((__doc__ or "").split("  python")[0].strip())
    p1b, p2 = load("P1b"), load("P2b")

    # J1: split the items in half. The seed is the one already committed for the control
    # sets, so which item lands in which half is fixed by a decision made before this ran.
    keys = sorted(set(p1b[next(iter(p1b))]))
    order = RNG.permutation(len(keys))
    half = {0: [keys[i] for i in order[: len(keys) // 2]],
            1: [keys[i] for i in order[len(keys) // 2:]]}
    j1 = {m: [(f"half {h} ({len(half[h])} items)", share(p1b[m], half[h])) for h in (0, 1)]
          for m in sorted(p1b)}
    report("J1 — the same sign in both halves of the items, at --obvious 3", j1,
           "  Both halves are the same judge on the same difficulty; only the items differ.")

    # J2: the two difficulties that were run at full size, on the same arrangement set.
    common = sorted(set(p1b[next(iter(p1b))]) & set(p2[next(iter(p2))]))
    j2 = {m: [("--obvious 3", share(p1b[m], common)),
              ("--obvious 0", share(p2[m], common))] for m in sorted(p1b)}
    report("J2 — the same sign at both difficulties", j2,
           f"  The {len(common)} items both phases ran. P1b uses the fixed-distractor set\n"
           "  and P2b the slot-balanced one, so a disagreement here is also a disagreement\n"
           "  between arrangement sets and this test cannot separate the two.")

    # J2 double prime: the comparison J2 should have been. Difficulty held at --obvious 0,
    # where errors are ample, and only the arrangement set differs. Both arms are the reduced
    # P2 and neither needed a pass; this was billed at 2.6 hours until a reviewer read the
    # filenames. Registered in exp01c before being computed, and reported with the
    # disclosure that its arms had already been compared informally.
    p2a = load("P2a")
    common2 = sorted(set(p2a[next(iter(p2a))]) & set(p2[next(iter(p2))]))
    j2pp = {m: [("FIXED_DISTRACTORS", share(p2a[m], common2)),
                ("SLOT_BALANCED", share(p2[m], common2))] for m in sorted(p2a)}
    report("J2-double-prime — the same sign across arrangement sets at --obvious 0", j2pp,
           f"  The {len(common2)} items both sets ran, same judges, same difficulty. Only the\n"
           "  arrangement changes, which is the one thing J2 could not hold still.")

    # J3: the same judges on a second benchmark, at its own items. UltraFeedback is four-way
    # natively, so nothing is constructed and the composition defects the --obvious ladder
    # carries cannot arise. Both arms use SLOT_BALANCED and the same statistic; only the
    # benchmark changes.
    j3 = load("J3")
    if j3:
        rb = {m: share(p2[m], sorted(p2[m])) for m in sorted(p2)}
        uf = {m: share(j3[m], sorted(j3[m])) for m in sorted(j3)}
        blocks = {m: [("RewardBench 2", rb[m]), ("UltraFeedback", uf[m])]
                  for m in sorted(set(rb) & set(uf))}
        report("J3 — the same sign on a second benchmark", blocks,
               "  Same judges, same arrangement set, same statistic. The benchmark changes,\n"
               "  and UltraFeedback is four-way natively so neither side is constructed.")

    # The only look available at the difficulty axis: the same difficulty on the two
    # arrangement sets. P1c is 150 items and its intervals are wide, which is the point.
    p1c = load("P1c", obvious=3)
    if p1c:
        both = sorted(set(p1b) & set(p1c))
        print("\n" + "=" * 100)
        print("The difficulty axis has no clean test; this is the closest reading available")
        print("=" * 100)
        print("  Both columns are --obvious 3. Only the arrangement set differs, and the")
        print("  slot-balanced column is 150 items where the other is 1,763.\n")
        print(f"  {'judge':30s} {'FIXED_DISTRACTORS, 1,763':>30s} "
              f"{'SLOT_BALANCED, 150':>30s}")
        for m in both:
            a_ = share(p1b[m], sorted(p1b[m]))
            c_ = share(p1c[m], sorted(p1c[m]))
            def cell(t):
                return (f"{t[0]:.4f} [{t[1]:+.3f},{t[2]:+.3f}] n={t[3]}"
                        if t[3] >= MIN_N_ERR else f"not evaluated, n={t[3]}")
            print(f"  {m.split('/')[-1]:30s} {cell(a_):>30s} {cell(c_):>30s}")

    print("\n" + "=" * 100)
    print("What the verdicts mean, which is not the same thing for each")
    print("=" * 100)
    print("""
  J1 fails mostly for want of errors, not for want of agreement. Halving 1,763 items at
  --obvious 3 leaves each half with fifteen to forty-seven usable errors, and the floor
  registered before the run is forty. Four of the five judges are not evaluated in at least
  one half, so the test asks a question the sample cannot answer -- the same trap H3 fell
  into, in a design that already knew about it. The one judge with errors to spare agrees
  with itself.

  J2 fails for a defect in J2: its two phases differ in the difficulty and in the arrangement
  set at the same time, so a sign that moves between them cannot be attributed to either.
  The verdict stands as falsified and carries little. Registering a comparison is not the
  same as registering one that could have worked.

  **An earlier version of this file blamed Skywork-Critic's flip on the fixed-distractor
  confound, and that was asserted rather than shown. It is wrong.** The confound is that
  slot A always holds the first distractor on that set, so naming A and naming that candidate
  are one count -- which matters only if the candidate carries something. At --obvious 3 the
  three distractors test as exchangeable (results/validation/exchangeable.txt, the 1,763-item
  row), so the first distractor carries nothing there and the --obvious 3 reading is a clean
  measurement of a slot. **The flip is real at that end and this design cannot explain it
  away.**

  What would decide whether it is the difficulty or the arrangement set is a clean reading at
  --obvious 3 on the slot-balanced set. P1c is that reading at 150 items and the table above
  shows it: **not one of the five judges is evaluable there**, at 0 to 38 usable errors
  against a floor of 40. At full size it would be J2', which cannot be powered either. So
  the difficulty axis has no clean reading in this design at any size, and the sentence
  "the sign is a property of the judge" has to carry that.

  So stability is established on two axes and untested on a third. The arrangement set holds
  at 4 of 5 and the benchmark at 5 of 5; the difficulty axis has J1 unpowered, J2 confounded
  and J2' unpowerable, and the one dirty look available disagrees -- Skywork-Critic sits
  below the null at --obvious 3 and above it at --obvious 0. Any sentence saying the sign is
  a property of the judge has to carry that.

  J2-double-prime is that comparison and it needed no pass: both arms were already on disk.
  It is reported with a disclosure -- its two arms had been compared informally before this
  computed them, so it is not an independent confirmation. What it does establish is narrow
  and real: whether the sign survives changing the one factor J2 confounded with two others.

  J3 is the only one of the four that looks outside RewardBench 2. Its arms are not
  symmetric in one respect worth stating: RewardBench 2's correct answer is curated, and
  UltraFeedback's is the completion GPT-4 scored highest, so a judge's errors on the second
  are measured against a label that is itself a judgement. That enlarges the error set
  without moving where those errors land -- the null of 1/3 comes from the arrangement, not
  from the label -- but a judge that happens to agree with GPT-4 will look more accurate
  there and no part of this design separates the two.""")


if __name__ == "__main__":
    main()
