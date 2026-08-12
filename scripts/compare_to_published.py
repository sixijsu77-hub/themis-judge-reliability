#!/usr/bin/env python3
"""Harness validation gate: compare a local RewardBench 2 run against the published scores.

Every number printed here is computed from raw per-item files. Nothing is transcribed by
hand, because a table typed by hand is a table with typos in it.

Three comparisons, in increasing strength:

  1. aggregate      our per-subset score vs the published per-subset score  (the 0.02 gate)
  2. per item       do the two runs credit the same items?
  3. raw score      how far apart are the underlying scalars the model emitted?

A self-check runs first: the published aggregate is recomputed from the published per-item
file. If that disagrees, the recomputation is wrong and no verdict below it means anything.

Usage:  python scripts/compare_to_published.py <model> [<model> ...]
"""
import json
import sys

import numpy as np
from datasets import Dataset
from huggingface_hub import hf_hub_download

from rewardbench.utils import process_single_model

RESULTS_REPO = "allenai/reward-bench-2-results"
SUBSETS = ["Factuality", "Focus", "Math", "Precise IF", "Safety", "Ties"]
GATE = 0.02


def flat(scores):
    """Per-candidate scores are stored as [[x], [y], ...]; flatten to [x, y, ...]."""
    return [s[0] if isinstance(s, list) else s for s in scores]


def item_result(scores):
    """The upstream non-Ties rule, reimplemented here only to verify the stored one."""
    s = np.asarray(flat(scores), dtype=float)
    mx = s.max()
    return float(1.0 / np.sum(s == mx)) if s[0] == mx else 0.0


def aggregate(per_item):
    """Recompute the six subset scores from a per-item file, the way run_v2.py does."""
    out = {}
    sub = np.asarray(per_item["subset"])
    for s in SUBSETS:
        idx = np.flatnonzero(sub == s)
        if len(idx) == 0:
            continue
        if s == "Ties":
            ds = Dataset.from_dict({
                "id": [per_item["id"][i] for i in idx],
                "scores": [per_item["scores"][i] for i in idx],
                "num_correct": [per_item["num_correct"][i] for i in idx],
            })
            _, out[s] = process_single_model(ds)
        else:
            out[s] = float(np.mean([per_item["results"][i] for i in idx]))
    return out


def load_published(model):
    agg = json.load(open(hf_hub_download(RESULTS_REPO, f"eval-set/{model}.json", repo_type="dataset")))
    itm = json.load(open(hf_hub_download(RESULTS_REPO, f"eval-set-scores/{model}.json", repo_type="dataset")))
    return agg, itm


def main(models):
    overall_fail = 0
    for model in models:
        print("=" * 78)
        print(model)
        print("=" * 78)
        try:
            ours = json.load(open(f"results/eval-set-scores/{model}.json"))
        except FileNotFoundError:
            print("  no local run found at results/eval-set-scores/%s.json -- SKIPPED\n" % model)
            overall_fail = 1
            continue
        pub_agg, pub_item = load_published(model)

        # ---- self-check: can we reproduce the published aggregate from published items?
        recomputed = aggregate(pub_item)
        worst = max(abs(recomputed[s] - pub_agg[s]) for s in SUBSETS)
        print(f"\n[self-check] published aggregate recomputed from published per-item file")
        print(f"             largest disagreement: {worst:.6f}", end="  ")
        if worst > 1e-6:
            print("<- RECOMPUTATION IS WRONG; everything below is void")
            for s in SUBSETS:
                print(f"               {s:12s} stored={pub_agg[s]:.6f} recomputed={recomputed[s]:.6f}")
            overall_fail = 1
            continue
        print("OK")

        # ---- also verify the stored per-item results follow the documented rule
        bad = sum(
            1 for i, s in enumerate(pub_item["subset"])
            if s != "Ties" and abs(item_result(pub_item["scores"][i]) - pub_item["results"][i]) > 1e-9
        )
        print(f"[self-check] per-item rule reimplemented: {bad} of "
              f"{sum(1 for s in pub_item['subset'] if s != 'Ties')} non-Ties items disagree")

        # ---- 1. aggregate gate
        mine = aggregate(ours)
        print(f"\n  {'subset':12s} {'ours':>9s} {'published':>10s} {'diff':>9s}   gate")
        diffs = []
        fail = False
        for s in SUBSETS:
            if s not in mine:
                print(f"  {s:12s} {'not run':>9s}")
                fail = True
                continue
            d = mine[s] - pub_agg[s]
            diffs.append(d)
            ok = abs(d) <= GATE
            fail |= not ok
            print(f"  {s:12s} {mine[s]:9.4f} {pub_agg[s]:10.4f} {d:+9.4f}   "
                  f"{'PASS' if ok else 'FAIL'}{'  <- exactly 0, verify' if d == 0 else ''}")
        avg_o = float(np.mean([mine[s] for s in SUBSETS if s in mine]))
        avg_p = float(np.mean([pub_agg[s] for s in SUBSETS]))
        ok = abs(avg_o - avg_p) <= GATE
        fail |= not ok
        print(f"  {'AVERAGE':12s} {avg_o:9.4f} {avg_p:10.4f} {avg_o - avg_p:+9.4f}   "
              f"{'PASS' if ok else 'FAIL'}")

        # ---- 2. per-item agreement
        key_p = {(s, i): n for n, (s, i) in enumerate(zip(pub_item["subset"], pub_item["id"]))}
        agree = tot = 0
        per_sub = {}
        for n, (s, i) in enumerate(zip(ours["subset"], ours["id"])):
            if s == "Ties" or (s, i) not in key_p:
                continue
            m = key_p[(s, i)]
            same = abs(ours["results"][n] - pub_item["results"][m]) < 1e-9
            agree += same
            tot += 1
            a, t = per_sub.get(s, (0, 0))
            per_sub[s] = (a + same, t + 1)
        print(f"\n  per-item agreement (non-Ties): {agree}/{tot} = {agree/tot:.4f}")
        for s in SUBSETS[:-1]:
            if s in per_sub:
                a, t = per_sub[s]
                print(f"    {s:12s} {a:5d}/{t:<5d} {a/t:.4f}")

        # ---- 3. raw score distance
        d_all = []
        for n, (s, i) in enumerate(zip(ours["subset"], ours["id"])):
            if (s, i) not in key_p:
                continue
            m = key_p[(s, i)]
            a, b = flat(ours["scores"][n]), flat(pub_item["scores"][m])
            if len(a) == len(b):
                d_all.extend(abs(np.asarray(a) - np.asarray(b)))
        d_all = np.asarray(d_all)
        print(f"\n  raw candidate scores: n={len(d_all)}  mean|diff|={d_all.mean():.6f}  "
              f"max|diff|={d_all.max():.6f}  identical={100*np.mean(d_all == 0):.1f}%")

        print(f"\n  ==> {'GATE PASS' if not fail else 'GATE FAIL'}\n")
        overall_fail |= fail
    return overall_fail


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
