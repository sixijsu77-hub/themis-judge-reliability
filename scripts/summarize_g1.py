#!/usr/bin/env python3
"""exp01g: the polarity axis on the two judges that state reasoning.

Registered in PREREGISTRATION-exp01g.md and committed before the run. That file fixes what is
confirmatory and what is exploratory, and this one does not decide it: Qwen carries H-g1 and
H-g2 because every prior observation of this phenomenon is Qwen's; RISE is a first look with no
hypothesis and no threshold, and cannot falsify anything.

Detectors, the coverage factor and the not-evaluated state come from scripts/summarize_graded.py
rather than being restated, because a rate is read off whatever its detector matched.

  python scripts/summarize_g1.py
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from summarize_graded import CONCLUSION, CONCLUSION_NAME, COVERAGE_FACTOR, contra_cell

LEVELS = [3, 2, 1, 0]
CONDITIONS = ["original", "paraphrase", "inverted", "inverted_fixed"]
CONTROLS = ("original", "paraphrase")
CONFIRMATORY = "Qwen/Qwen2.5-7B-Instruct"
EXPLORATORY = "R-I-S-E/RISE-Judge-Qwen2.5-7B"
BOOT = 10000
RNG = np.random.default_rng(0)
# A control rate above this is not near zero, and the exploratory arm then has a
# different shape from an arm whose controls sit at zero.
CONTROL_FLOOR = 0.05


def load(judge, level, cond):
    tag = judge.replace("/", "__")
    suffix = "" if cond == "original" else f"_{cond}"
    path = f"results/exp01/G1_{tag}_o{level}_0{suffix}.jsonl"
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        f.readline()
        return [json.loads(l) for l in f]


def cell(rows, cond):
    """(contradictions, matched conclusions, total verdicts, per-item flags)."""
    flags = []
    for r in rows:
        m = CONCLUSION[cond].search(r["judgement_text"])
        if m:
            flags.append(float(m.group(1).upper() != r["parsed_letter"]))
    a = np.array(flags)
    return int(a.sum()) if len(a) else 0, len(a), len(rows), a


def interval(a, b):
    if not len(a) or not len(b):
        return None
    d = (a[RNG.integers(0, len(a), (BOOT, len(a)))].mean(1)
         - b[RNG.integers(0, len(b), (BOOT, len(b)))].mean(1))
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def coverage(data, judge):
    """{level: (ratio of corrected to old inverted coverage, may the level be read)}."""
    out = {}
    for lv in LEVELS:
        cov = {}
        for c in CONDITIONS:
            _, matched, total, _ = cell(data[(judge, lv, c)], c)
            cov[c] = matched / total if total else 0.0
        r = cov["inverted_fixed"] / cov["inverted"] if cov["inverted"] else float("inf")
        out[lv] = (cov, r, 1 / COVERAGE_FACTOR <= r <= COVERAGE_FACTOR)
    return out


def judge_block(data, judge, cov):
    """Print one judge's cells and return {level: (interval, control used, readable)}."""
    print(f"\n  {judge}")
    print("  " + "-" * 104)
    print(f"  {'obvious':>7s}" + "".join(f"{c:>22s}" for c in CONDITIONS)
          + f"{'inv_fixed/inv':>15s}  gate")
    fired = {}
    for lv in LEVELS:
        cells, flags = [], {}
        for c in CONDITIONS:
            k, matched, _, f = cell(data[(judge, lv, c)], c)
            cells.append(contra_cell(k, matched))
            flags[c] = f
        _, ratio, ok = cov[lv]
        print(f"  {lv:7d}" + "".join(f"{x:>22s}" for x in cells)
              + f"{ratio:15.3f}  {'may read' if ok else 'NOT EVALUATED'}")
        best = max(CONTROLS, key=lambda c: flags[c].mean() if len(flags[c]) else 0.0)
        fired[lv] = (interval(flags["inverted_fixed"], flags[best]), best, ok, flags)
    print()
    print(f"  {'obvious':>7s} {'corrected - higher control':>28s} {'95% CI':>22s}  reading")
    for lv in LEVELS:
        ci, best, ok, _ = fired[lv]
        if ci is None:
            print(f"  {lv:7d} {'no matched conclusions':>28s} {'':>22s}  not evaluated")
        elif not ok:
            print(f"  {lv:7d} {f'against {best}':>28s} [{ci[0]:+9.4f},{ci[1]:+9.4f}]  "
                  f"not evaluated (coverage)")
        else:
            print(f"  {lv:7d} {f'against {best}':>28s} [{ci[0]:+9.4f},{ci[1]:+9.4f}]  "
                  + ("shows the effect" if ci[0] > 0 else "does not"))
    return fired


def main():
    data = {(j, lv, c): load(j, lv, c)
            for j in (CONFIRMATORY, EXPLORATORY) for lv in LEVELS for c in CONDITIONS}
    missing = [k for k, v in data.items() if v is None]
    if missing:
        print(f"  not run: {sorted(missing)}")
        return 1
    # Row counts are per file and a withheld row can make one cell smaller than the rest, so
    # the header reports the range it finds rather than one cell's count generalised to all
    # sixteen. A single number here read as derived while contradicting a table below it.
    sizes = [len(v) for v in data.values() if v is not None]
    span = (f"{min(sizes)} items per cell" if min(sizes) == max(sizes)
            else f"{min(sizes)} to {max(sizes)} items per cell, the smaller being a cell with "
                 f"a row withheld from publication")
    print(f"  exp01g — {span}, one arrangement\n  detectors: "
          + ", ".join(f"{c} = {CONCLUSION_NAME[c]}" for c in CONDITIONS))
    print(f"  a level whose corrected-arm coverage is outside a factor of {COVERAGE_FACTOR} of "
          f"the old\n  inverted arm's is not evaluated, and no null from it counts")

    print("\n\n  CONFIRMATORY — H-g1 and H-g2, on the judge every prior observation came from")
    cov_q = coverage(data, CONFIRMATORY)
    q = judge_block(data, CONFIRMATORY, cov_q)

    readable = [lv for lv in LEVELS if q[lv][2] and q[lv][0] is not None]
    shows = [lv for lv in readable if q[lv][0][0] > 0]
    print("\n  " + "=" * 104)
    if len(readable) < len(LEVELS):
        verdict = "not evaluated"
        why = (f"{len(LEVELS) - len(readable)} of 4 levels could not be read; a level that "
               f"could not be read is not evidence that the effect is absent")
    elif len(shows) == len(LEVELS):
        verdict, why = "HOLDS", "the interval excludes 0 at all four levels"
    else:
        verdict = "FALSIFIED"
        why = f"the interval excludes 0 at {len(shows)} of 4 levels, and all four were required"
    print(f"  **H-g1 {verdict}** — {why}")

    # H-g2: the drop from the old wording to the corrected one, pooled over readable levels.
    if verdict == "HOLDS":
        old = np.concatenate([q[lv][3]["inverted"] for lv in readable])
        new = np.concatenate([q[lv][3]["inverted_fixed"] for lv in readable])
        drop = (old.mean() - new.mean()) / old.mean() if old.mean() else float("nan")
        print(f"\n  old wording {old.mean():.4f} over {len(old)} matched, "
              f"corrected {new.mean():.4f} over {len(new)}")
        print(f"  drop = {drop:+.4f} of the old rate; registered threshold is less than half")
        print(f"  **H-g2 {'HOLDS' if drop < 0.5 else 'FALSIFIED'}**")
    else:
        print(f"\n  **H-g2 not evaluated** — it is a statement about an effect H-g1 must first "
              f"establish")

    print("\n\n  EXPLORATORY — no hypothesis, no threshold, and it cannot falsify anything")
    print("  This judge has never been measured on this axis. Any pattern below is a first")
    print("  look, and a result on one judge is not evidence about judges in general.")
    cov_r = coverage(data, EXPLORATORY)
    judge_block(data, EXPLORATORY, cov_r)

    def worst_control(judge):
        return max(cell(data[(judge, lv, c)], c)[0] / max(cell(data[(judge, lv, c)], c)[1], 1)
                   for lv in LEVELS for c in CONTROLS)

    wc_e, wc_c = worst_control(EXPLORATORY), worst_control(CONFIRMATORY)
    print(f"\n  How much each judge contradicts itself with no inversion at all.")
    print(f"  Highest control rate: {CONFIRMATORY.split('/')[-1]} {wc_c:.4f}, "
          f"{EXPLORATORY.split('/')[-1]} {wc_e:.4f}.")
    # Absolute, not a ratio. A ratio needs a guard against a zero denominator, and that guard
    # made the warning loudest exactly when the confirmatory judge had no control
    # contradictions at all -- the case it should be quietest in. On this data any threshold
    # between about 0.01 and 0.15 reads the same, so CONTROL_FLOOR is not deciding anything.
    # Whether the two are the same shape is a comparison and is printed only when something
    # tests it. An earlier version asserted "not the same shape" unconditionally, which was
    # true of this data and false of data where both sit alike. Its replacement had an else
    # branch that said "both near zero" when only one of them was, and a third that read
    # "both elevated, so one shape and not two" -- which does not follow, since 0.051 and 0.90
    # both clear a floor of 0.05. Each repair carried one unearned comparative forward. A
    # branch may say what its own test established and no more; similarity is a comparison
    # nothing here makes.
    hot_e, hot_c = wc_e > CONTROL_FLOOR, wc_c > CONTROL_FLOOR
    if hot_e and not hot_c:
        print("  **The two are not the same shape and the tables should not be read as one.**")
        print("  The exploratory judge contradicts its own reasoning under the controls too, so")
        print("  inversion there raises an effect that is already present rather than creating")
        print("  one. The intervals above read against the higher control and are")
        print("  arithmetically right; a reader placing them beside the confirmatory judge's")
        print("  would see one phenomenon where there are two.")
    elif hot_e and hot_c:
        print("  Both judges contradict themselves under the controls, so neither column is a")
        print("  clean contrast against zero and both inversion effects sit on top of something")
        print("  already present. Whether the two are alike is not said: crossing one floor")
        print("  together is not similarity, and nothing here measures that.")
    elif hot_c and not hot_e:
        print("  **The two are not the same shape**, and the elevated one is the confirmatory")
        print("  judge. Its inversion effect is an increase on something already present, and")
        print("  the hypotheses above are read against the higher control accordingly.")
    else:
        print("  Both judges sit near zero under the controls, so an effect under inversion is")
        print("  a contrast against nothing rather than an increase on something.")

    print("\n  Why every exploratory level is not evaluated, which is not the same reason as")
    print("  the confirmatory one. The reference arm is the broken one:")
    # One shared denominator column was wrong the moment a row was withheld from one arm:
    # the two arms are separate files and can hold different row counts, so each carries its
    # own. A reader recomputing a ratio from a shared column got a figure the block above
    # contradicts.
    print(f"  {'obvious':>7s} {'old inverted':>21s} {'of':>6s} "
          f"{'corrected':>12s} {'of':>6s}")
    for lv in LEVELS:
        _, m_old, n_old, _ = cell(data[(EXPLORATORY, lv, "inverted")], "inverted")
        _, m_new, n_new, _ = cell(data[(EXPLORATORY, lv, "inverted_fixed")], "inverted_fixed")
        print(f"  {lv:7d} {m_old:21d} {n_old:6d} {m_new:12d} {n_new:6d}")
    print("  The old detector matches a small fraction of this judge's rows because that is not")
    print("  how it phrases a conclusion, so the gate divides by a baseline that is itself")
    print("  under-covered. Every ratio here is over-coverage of the corrected arm.")

    print("\n  " + "=" * 104)
    print("  What this does not establish. Two judges, both Qwen-family 7B, one confirmatory")
    print("  and one exploratory — not two independent grounds. The bound in f1_stage1.txt §0")
    print("  says why there are not more, and it is a bound on the five judges this screen")
    print("  admitted rather than on the size class.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
