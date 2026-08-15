#!/usr/bin/env python3
"""Build J3's second benchmark from UltraFeedback, four-way as it already is.

exp01c's J3 asks whether a judge's slot disposition survives a change of benchmark. That
needs a four-way set that is not RewardBench 2, and UltraFeedback is one natively: every
instruction carries exactly four completions from four different models, each scored. So
nothing is constructed — no substituted distractors, and therefore none of the composition
defects that exp01b spent three rounds finding in its own control set.

Two things are decided here rather than inherited, and both are checked rather than assumed:

  the correct answer   the completion with the unique highest `overall_score`. Items where
                       two or more share the top score have no designated correct answer and
                       are dropped -- 18,468 of 63,966 at the time of writing
  the distractor order UltraFeedback's list position is not neutral: position 0 is
                       disproportionately one model and position 3 another, and the mean
                       score differs by position. Writing the three distractors in native
                       order would reproduce exactly the defect this repository found in
                       build_control_set.py, where a fixed place in the list carried a fixed
                       quality. They are shuffled per item under a committed seed

The ground truth is GPT-4's rating, so "correct" here means "top-rated by GPT-4". That does
not bias the statistic J3 reads: E*_A's null of 1/3 comes from the arrangement design, not
from the label being right, so a noisy label enlarges the error set without moving where
those errors land. It does mean errors are measured against a label that is itself a
judgement, and the results say so.

  python scripts/build_ultrafeedback.py --n 1763 --seed 0
"""
import argparse
import json
import os
import random

from datasets import load_dataset


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1763)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="data/uf_o0")
    ap.add_argument("--manifest", default="results/validation/uf_manifest.json")
    args = ap.parse_args()

    ds = load_dataset("openbmb/UltraFeedback", split="train")
    usable = []
    n_tied = 0
    for i, r in enumerate(ds):
        c = r["completions"]
        if len(c) != 4:
            continue
        sc = [x.get("overall_score") for x in c]
        if any(s is None for s in sc):
            continue
        top = max(sc)
        if sc.count(top) > 1:
            n_tied += 1
            continue
        usable.append((i, sc.index(top)))

    rng = random.Random(args.seed)
    picked = rng.sample(usable, args.n)
    os.makedirs(args.out, exist_ok=True)
    os.makedirs(os.path.dirname(args.manifest) or ".", exist_ok=True)
    drawn = []
    with open(os.path.join(args.out, "test.jsonl"), "w") as f:
        for idx, best in picked:
            r = ds[idx]
            c = r["completions"]
            others = [j for j in range(4) if j != best]
            rng.shuffle(others)
            drawn.append({"source_index": idx, "best_position": best,
                          "distractor_positions": others,
                          "models": [c[j]["model"] for j in [best] + others],
                          "scores": [c[j]["overall_score"] for j in [best] + others]})
            f.write(json.dumps({
                "id": str(idx),
                "subset": "UltraFeedback",
                "prompt": r["instruction"],
                "chosen": [c[best]["response"]],
                "rejected": [c[j]["response"] for j in others],
                "num_correct": 1,
                "num_incorrect": 3,
                "total_completions": 4,
                "models": [c[best]["model"]] + ["uf"] * 3,
            }) + "\n")
    json.dump({"dataset": "openbmb/UltraFeedback", "split": "train", "n": args.n,
               "seed": args.seed,
               "usable": len(usable), "total": len(ds),
               "note": "correct answer is the unique highest overall_score; ties at the top "
                       "dropped; the three distractors are shuffled per item under the seed "
                       "so that list position carries no quality ordering",
               "drawn": drawn}, open(args.manifest, "w"), indent=1)
    import numpy as np
    print("UltraFeedback as J3's second benchmark")
    print(f"  rows in the split                      : {len(ds):,}")
    print(f"  four completions with scores           : {len(usable) + n_tied:,}")
    print(f"  tied at the top, no correct answer     : {n_tied:,}")
    print(f"  usable, unique top score               : {len(usable):,}")
    print(f"  drawn at seed {args.seed}                        : {args.n:,}")
    print(f"  written to {args.out}/test.jsonl")

    sc = np.array([r["scores"] for r in drawn], float)
    dist = sc[:, 1:]
    obs = float(dist.mean(0).max() - dist.mean(0).min())
    rng2 = np.random.default_rng(0)
    null = [np.take_along_axis(dist, np.argsort(rng2.random(dist.shape), axis=1),
                               axis=1).mean(0) for _ in range(4000)]
    p_val = float(np.mean([n.max() - n.min() >= obs for n in null]))
    print("\n  did the shuffle remove the quality ordering the native list has?")
    print(f"    mean score by written position: correct {sc[:, 0].mean():.3f}, "
          + ", ".join(f"R{j} {dist[:, j-1].mean():.3f}" for j in (1, 2, 3)))
    print(f"    spread among the three distractors: {obs:.4f}")
    print(f"    permutation p over 4,000 shuffles : {p_val:.4f}  "
          + ("exchangeable" if p_val > 0.05 else "NOT exchangeable — do not run on this"))
    print("""
    build_control_set.py wrote its distractors in a fixed order and that order carried a
    fixed quality, which took three rounds to find and invalidated a headline result. The
    same check runs here before anything is measured rather than after.""")


if __name__ == "__main__":
    main()
