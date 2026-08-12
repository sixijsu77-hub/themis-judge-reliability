#!/usr/bin/env python3
"""Audit the published RewardBench 2 result files for things that affect how the
numbers can be read. Findings came out of validating this repository's harness against
them; this script exists so anyone can reproduce them without taking our word for it.

  python scripts/audit_published_results.py            # all three checks, full census
  python scripts/audit_published_results.py --limit 20 # quick sample instead

Check 1 - per-item id integrity
    eval-set-scores/<model>.json stores parallel arrays; joining on (subset, id) is the
    only way to line an item up with anything else. In many files the first ten
    Factuality ids are wrong, so ten items join to the wrong row with no error raised.

Check 2 - which protocol produced a generative score
    scripts/run_generative_v2.py can score either by four-way ranking (default) or by
    pointwise ratings (--score_w_ratings). The saved results record model, model_type and
    chat_template, but not which of the two ran. The two are not comparable, and the only
    way to tell them apart afterwards is the arithmetic of the per-item values: ranking
    yields {0, 1, 0.25}, ratings yields (0 in winners)/len(winners), so 0.5 and 1/3 appear.

Check 3 - credit for unparseable verdicts
    process_judgement returns "error" when no [[X]] marker is found, and process_shuffled
    maps that to 0.25 - chance, under a four-way choice. In ranking mode 0.25 can only
    arise that way, so its frequency is exactly the parse-failure rate.
"""
import argparse
import json
from collections import Counter

from huggingface_hub import HfApi, hf_hub_download

REPO = "allenai/reward-bench-2-results"
SUBSETS = ["Factuality", "Focus", "Math", "Precise IF", "Safety", "Ties"]
# With four candidates, ranking yields {0, 1, 0.25}; ratings yields
# (0 in winners)/len(winners) in {0, 1/4, 1/3, 1/2, 1}. Only 1/2 and 1/3 separate them,
# because 1/4 is also what a parse failure scores under ranking.
RATING_FINGERPRINTS = (0.5, 1 / 3)
MODE_KEYS = {"score_w_ratings", "scoring_mode", "mode", "protocol", "ratings"}


def get(path):
    return json.load(open(hf_hub_download(REPO, path, repo_type="dataset")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="audit only the first N files")
    args = ap.parse_args()

    api = HfApi()
    files = api.list_repo_files(REPO, repo_type="dataset")
    scored = sorted(f for f in files if f.startswith("eval-set-scores/") and f.endswith(".json"))
    total = len(scored)
    if args.limit:
        scored = scored[: args.limit]

    print(f"repo    : {REPO}")
    print(f"auditing: {len(scored)} of {total} per-item files"
          f"{' (SAMPLE, not a census)' if args.limit else ' (census)'}\n")

    dup_files, clean_files, unreadable = [], [], []
    generative = []

    for f in scored:
        name = f[len("eval-set-scores/"):-len(".json")]
        try:
            d = get(f)
        except Exception as e:  # noqa: BLE001
            unreadable.append((name, type(e).__name__))
            continue

        # ---- check 1
        counts = Counter(zip(d["subset"], d["id"]))
        dups = sorted(k for k, v in counts.items() if v > 1)
        fact = [i for i, s in zip(d["id"], d["subset"]) if s == "Factuality"]
        if dups:
            dup_files.append((name, len(dups), fact[:10]))
        else:
            clean_files.append(name)

        # ---- checks 2 and 3
        if "Generative" in str(d.get("model_type", "")):
            vals = [x for x in d["results"] if x is not None]
            hist = Counter(vals)
            is_ratings = any(
                any(abs(v - fp) < 1e-9 for fp in RATING_FINGERPRINTS) for v in hist
            )
            generative.append({
                "model": name,
                "mode_inferred": "ratings" if is_ratings else "ranking",
                # Exact key names only. Substring matching gives a false positive here:
                # "mode" is inside "model", which every file has.
                "mode_recorded": bool(MODE_KEYS & set(d)),
                "frac_quarter": hist.get(0.25, 0) / len(vals),
                "n": len(vals),
                "score": sum(vals) / len(vals),
            })

    print("=" * 78)
    print("CHECK 1 - per-item id integrity")
    print("=" * 78)
    print(f"  files with duplicate (subset, id) keys : {len(dup_files)}")
    print(f"  files clean                            : {len(clean_files)}")
    print(f"  files unreadable                       : {len(unreadable)}")
    if dup_files:
        shapes = Counter(tuple(f[2]) for f in dup_files)
        print(f"\n  distinct shapes of the first ten Factuality ids among affected files: {len(shapes)}")
        for shape, n in shapes.most_common(5):
            print(f"    x{n:<4d} {list(shape)}")
        print(f"\n  expected (from the dataset itself): "
              f"['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']")
        print(f"\n  affected, first 15 by name:")
        for name, nd, _ in dup_files[:15]:
            print(f"    {nd:3d} dup keys  {name}")
        if clean_files:
            print(f"\n  unaffected, first 10 by name:")
            for name in clean_files[:10]:
                print(f"                {name}")

    print()
    print("=" * 78)
    print("CHECKS 2 and 3 - generative entries: protocol, and credit for parse failures")
    print("=" * 78)
    if not generative:
        print("  no generative entries in this slice")
    else:
        print(f"  {'model':44s} {'inferred':>9s} {'recorded':>9s} {'0.25 rate':>10s} {'score':>7s}")
        for g in sorted(generative, key=lambda g: g["model"]):
            print(f"  {g['model']:44s} {g['mode_inferred']:>9s} "
                  f"{str(g['mode_recorded']):>9s} {g['frac_quarter']:9.1%} {g['score']:7.3f}")
        modes = Counter(g["mode_inferred"] for g in generative)
        print(f"\n  inferred protocol split: {dict(modes)}")
        print(f"  entries that record which protocol ran: "
              f"{sum(1 for g in generative if g['mode_recorded'])} of {len(generative)}")
        rank = [g for g in generative if g["mode_inferred"] == "ranking"]
        if rank:
            worst = max(rank, key=lambda g: g["frac_quarter"])
            print(f"\n  In ranking mode 0.25 arises only from an unparseable verdict.")
            print(f"  Highest such rate: {worst['frac_quarter']:.1%} "
                  f"({round(worst['frac_quarter']*worst['n'])} of {worst['n']} items) "
                  f"for {worst['model']},")
            print(f"  contributing {0.25*worst['frac_quarter']:.4f} of its "
                  f"{worst['score']:.4f} non-Ties score.")


if __name__ == "__main__":
    main()
