#!/usr/bin/env python3
"""exp01f stage 1: four polarity conditions at four difficulties, one judge, 1,763 items.

Registered in PREREGISTRATION-exp01f.md and committed before the run. This reports the gate
that decides whether the remaining four judges are run; it does not decide H-f1, H-f2 or H-f3,
which need at least four evaluable judges and have one.

Detectors come from scripts/summarize_graded.py rather than being restated, because a rate is
read off whatever its detector matched and two copies of a regex are two detectors.

  python scripts/summarize_f1.py
"""
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from summarize_graded import CONCLUSION, CONCLUSION_NAME, COVERAGE_FACTOR, contra_cell

LEVELS = [3, 2, 1, 0]
CONDITIONS = ["original", "paraphrase", "inverted", "inverted_fixed"]
BOOT = 10000
RNG = np.random.default_rng(0)
NULL_CONDITIONS = ("original", "paraphrase")


def load(level, cond):
    """The one F1 pass for this cell, or None if it was not run."""
    suffix = "" if cond == "original" else f"_{cond}"
    hits = glob.glob(f"results/exp01/F1_*_o{level}_0{suffix}.jsonl")
    hits = [h for h in hits if h.endswith(f"_o{level}_0{suffix}.jsonl")]
    if len(hits) != 1:
        return None
    with open(hits[0]) as f:
        f.readline()
        return [json.loads(l) for l in f]


def cell(rows, cond):
    """(contradictions, matched conclusions, total verdicts, per-item contradiction flags)."""
    flags, matched = [], 0
    for r in rows:
        m = CONCLUSION[cond].search(r["judgement_text"])
        if not m:
            continue
        matched += 1
        flags.append(float(m.group(1).upper() != r["parsed_letter"]))
    return int(sum(flags)), matched, len(rows), np.array(flags)


def interval(a, b):
    """95% bootstrap interval on mean(a) - mean(b), resampling each independently."""
    if not len(a) or not len(b):
        return None
    d = (a[RNG.integers(0, len(a), (BOOT, len(a)))].mean(1)
         - b[RNG.integers(0, len(b), (BOOT, len(b)))].mean(1))
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def main():
    data = {(lv, c): load(lv, c) for lv in LEVELS for c in CONDITIONS}
    missing = [k for k, v in data.items() if v is None]
    if missing:
        print(f"  not run: {sorted(missing)}")
        return 1
    judge = os.path.basename(glob.glob("results/exp01/F1_*_o3_0.jsonl")[0])
    print(f"  {judge}\n  {len(data[(3, 'original')])} items per cell, "
          f"one arrangement, four conditions x four difficulties\n")

    print("  0. Which of the screened judges state reasoning at all")
    print("  " + "-" * 96)
    print("  A verdict can only contradict its own stated reasoning if there is any. Measured")
    print("  from committed P2b passes, which predate this registration: the criterion that")
    print("  picked stage 1's judge was its usable error count, and error count is not this.")
    print("  A long output counts only if it also parses to a verdict -- one judge's longest")
    print("  abandons the task and answers an unrelated question. Parse-failure separates them;")
    print("  a unique-word ratio below 0.2 removes eleven more rows in 35,260, so that part of")
    print("  the criterion is doing essentially nothing and is reported rather than relied on.")
    print("  The ratio counts distinct words case-folded over the untouched word count; without")
    print("  folding it removes ten rather than eleven, which is the whole of that difference.\n")
    from collections import defaultdict
    seen = defaultdict(list)
    for path in glob.glob("results/exp01/P2b_*_o0_*.jsonl"):
        with open(path) as f:
            model = json.loads(f.readline())["model"]
            for line in f:
                r = json.loads(line)
                seen[model].append((r["judgement_text"], r["parsed_letter"]))

    def unique_ratio(text):
        words = text.split()
        return len(set(w.lower() for w in words)) / max(len(words), 1)

    print(f"  {'judge':32s} {'n':>6s} {'len>5':>7s} {'parses':>7s} {'clean':>7s} "
          f"{'per level':>10s}  reads as")
    for model in sorted(seen, key=lambda k: -sum(len(t) > 5 for t, _ in seen[k])):
        rows = seen[model]
        long_out = [(t, L) for t, L in rows if len(t) > 5]
        parses = [(t, L) for t, L in long_out if L in "ABCD"]
        clean = [(t, L) for t, L in parses if unique_ratio(t) > 0.2]
        share = len(clean) / len(rows)
        reads = ("states reasoning" if share > 0.5 else
                 "cannot -- no output above the bare verdict" if not long_out else
                 "emits non-judgements too" if len(parses) < 0.9 * len(long_out) else
                 "can, and almost never does")
        print(f"  {model.split('/')[-1]:32s} {len(rows):6d} {len(long_out):7d} "
              f"{len(parses):7d} {len(clean):7d} {share * 1763:10.0f}  {reads}")
    n_ok = sum(1 for model in seen
               if sum(1 for t, L in seen[model] if len(t) > 5 and L in "ABCD")
               > 0.5 * len(seen[model]))
    print(f"\n  {n_ok} of {len(seen)} state reasoning, so a threshold of four judges is above")
    print("  what this screen can supply, whatever the run finds. The rest are below the")
    print("  smallest sample the registered reachability table covers, which is 120.\n")

    print("  1. Coverage — what each detector matched, and whether the gate may read a null")
    print("  " + "-" * 96)
    print(f"  {'obvious':>7s}" + "".join(f"{c:>20s}" for c in CONDITIONS)
          + f"{'inv_fixed/inv':>15s}  gate")
    gate_ok = {}
    for lv in LEVELS:
        cov, row = {}, []
        for c in CONDITIONS:
            _, matched, total, _ = cell(data[(lv, c)], c)
            cov[c] = matched / total if total else 0.0
            row.append(f"{matched:6d}/{total:<5d} {cov[c]:5.3f}")
        ratio = cov["inverted_fixed"] / cov["inverted"] if cov["inverted"] else float("inf")
        ok = 1 / COVERAGE_FACTOR <= ratio <= COVERAGE_FACTOR
        gate_ok[lv] = ok
        print(f"  {lv:7d}" + "".join(f"{x:>20s}" for x in row)
              + f"{ratio:15.3f}  {'may read' if ok else 'NOT EVALUATED'}")
    print(f"\n  Registered factor is {COVERAGE_FACTOR}; a level outside it is not evaluated and no")
    print("  null from it counts. Detectors, in order: "
          + ", ".join(CONCLUSION_NAME[c] for c in CONDITIONS) + ".\n")

    print("  2. Verdicts that contradict their own stated reasoning")
    print("  " + "-" * 96)
    print(f"  {'obvious':>7s}" + "".join(f"{c:>22s}" for c in CONDITIONS))
    fired = {}
    for lv in LEVELS:
        cells, flags = [], {}
        for c in CONDITIONS:
            k, matched, _, f = cell(data[(lv, c)], c)
            cells.append(contra_cell(k, matched))
            flags[c] = f
        print(f"  {lv:7d}" + "".join(f"{x:>22s}" for x in cells))
        best = max(NULL_CONDITIONS, key=lambda c: flags[c].mean() if len(flags[c]) else 0.0)
        ci = interval(flags["inverted_fixed"], flags[best])
        fired[lv] = (ci, best)
    print()
    print(f"  {'obvious':>7s} {'corrected - the higher control':>32s} {'95% CI':>22s}  reading")
    for lv in LEVELS:
        ci, best = fired[lv]
        if ci is None:
            print(f"  {lv:7d} {'no matched conclusions':>32s} {'':>22s}  not evaluated")
            continue
        lo, hi = ci
        shows = lo > 0
        print(f"  {lv:7d} {f'against {best}':>32s} [{lo:+9.4f},{hi:+9.4f}]  "
              + ("shows the effect" if shows
                 else "not evaluated (coverage)" if not gate_ok[lv] else "does not"))

    print("\n  3. Accuracy, for H-f3's shape")
    print("  " + "-" * 96)
    print(f"  {'obvious':>7s}" + "".join(f"{c:>20s}" for c in CONDITIONS)
          + f"{'orig - corrected':>18s}")
    for lv in LEVELS:
        acc = {c: float(np.mean([r["results"] for r in data[(lv, c)]])) for c in CONDITIONS}
        print(f"  {lv:7d}" + "".join(f"{acc[c]:20.4f}" for c in CONDITIONS)
              + f"{acc['original'] - acc['inverted_fixed']:18.4f}")

    print("\n  The staging gate. Stage 1 nulls out only if the corrected condition shows no")
    print("  contradiction at any level whose coverage the gate may read. This is one judge and")
    print("  decides no hypothesis: H-f1, H-f2 and H-f3 need at least four evaluable judges.")
    readable = [lv for lv in LEVELS if gate_ok[lv]]
    print(f"\n  levels the gate may read: {readable or 'none'}")
    if not readable:
        # No level is evaluable, so the gate has nothing to fire on. Reading that as a null
        # is the failure the not-evaluated state exists to prevent, and an earlier version of
        # this very function did exactly that.
        print("  **stage 1 is NOT EVALUATED** — no level's coverage the gate may read, so it")
        print("  cannot fire in either direction. This is not the effect failing to survive.")
        return 0
    any_shown = any(fired[lv][0] is not None and fired[lv][0][0] > 0 for lv in readable)
    print(f"  **stage 1 {'clears the gate' if any_shown else 'NULLS OUT'}** — "
          + ("the remaining four judges are run"
             if any_shown else "the remaining 64 passes are not run"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
