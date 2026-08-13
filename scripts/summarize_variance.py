#!/usr/bin/env python3
"""Summarise the repeated-run records in results/variance/.

Six runs of one command against one model at temperature 0. The only thing that differs
between them is where the correct candidate was placed among the four, drawn by an
unseeded RNG inside a cached datasets.map. Three runs reused the map cache; three had a
fresh one.

  python scripts/summarize_variance.py
"""
import glob
import itertools
import json
from collections import Counter

SUBSETS = ["Factuality", "Focus", "Math", "Precise IF", "Safety"]


def load(path):
    meta, rows = {}, []
    for line in open(path):
        o = json.loads(line)
        (meta.update(o) if o.get("_record") == "metadata" else rows.append(o))
    return meta, rows


def main():
    runs = {}
    for p in sorted(glob.glob("results/variance/*.jsonl")):
        meta, rows = load(p)
        runs[meta["run"]] = (meta, rows)
    if not runs:
        print("no records in results/variance/")
        return

    order = [r for r in ["run1", "run2", "run3", "cold1", "cold2", "cold3"] if r in runs]
    reused = [r for r in order if runs[r][0]["datasets_map_cache"] == "reused"]
    fresh = [r for r in order if runs[r][0]["datasets_map_cache"] == "fresh"]
    model = runs[order[0]][0]["model"]

    print(f"model    : {model}")
    print(f"evaluator: {runs[order[0]][0]['evaluator']}")
    print(f"command  : {runs[order[0]][0]['command']}")
    print(f"runs     : {len(reused)} reusing the datasets map cache, {len(fresh)} with a fresh one")
    print()

    def score(rows, s):
        v = [r["results"] for r in rows if r["subset"] == s and r["results"] is not None]
        return sum(v) / len(v)

    print("=== per-subset score ===")
    print(f"  {'subset':12s}" + "".join(f"{r:>9s}" for r in order) + f"{'spread':>9s}")
    worst = (0.0, "")
    for s in SUBSETS:
        vals = {r: score(runs[r][1], s) for r in order}
        spread = max(vals[r] for r in fresh) - min(vals[r] for r in fresh)
        worst = max(worst, (spread, s))
        print(f"  {s:12s}" + "".join(f"{vals[r]:9.4f}" for r in order) + f"{spread:9.4f}")
    print(f"\n  spread is over the {len(fresh)} fresh-cache runs only; the reused-cache runs are")
    print(f"  identical to each other by construction and are shown for contrast.")
    print(f"  largest spread: {worst[0]:.4f} on {worst[1]}")

    print("\n=== unparseable verdicts (credited 0.25 by the upstream scorer) ===")
    for r in order:
        c = Counter(x["results"] for x in runs[r][1] if x["subset"] != "Ties")
        n = sum(c.values())
        print(f"  {r:8s} {c.get(0.25, 0):4d} of {n}   value histogram {dict(sorted(c.items()))}")

    print("\n=== item-level disagreement between runs ===")
    def items(rows):
        return {(x["subset"], x["id"]): x["results"] for x in rows if x["subset"] != "Ties"}
    for group, label in ((reused, "reused cache"), (fresh, "fresh cache")):
        for a, b in itertools.combinations(group, 2):
            A, B = items(runs[a][1]), items(runs[b][1])
            k = set(A) & set(B)
            d = sum(1 for x in k if abs(A[x] - B[x]) > 1e-9)
            print(f"  {label:13s} {a:6s} vs {b:6s}: {d:4d} of {len(k)} = {d/len(k):6.1%}")


if __name__ == "__main__":
    main()
