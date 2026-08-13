#!/usr/bin/env python3
"""Build a control set whose correct answer is not open to argument.

The point of the control is to catch a perturbation that inverted the meaning of the
question. That only works if the right answer is beyond dispute, which it is not on the real
benchmark — the rejected candidates there are often reasonable answers that happen to be
worse. So the distractors are replaced.

Nothing here is written by us. For each item we keep the real prompt and the real chosen
response, and take the three distractors from the *chosen* responses of three other items.
Those are well-written answers to a different question, so "follows the user's instructions
and answers the user's question" is false for them in a way no reader would dispute, while
length and register stay comparable so no length cue is introduced.

The output is a directory holding `test.jsonl`, which `load_dataset(dir, split="test")`
reads without any change to the runner. The manifest records the seed and every drawn index
so the set can be rebuilt exactly, and is committed while the set itself is not.

  python scripts/build_control_set.py --n 150 --seed 0
"""
import argparse
import json
import os
import random

from datasets import load_dataset


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=150)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--obvious", type=int, default=3, choices=[0, 1, 2, 3],
                    help="how many of the three distractors answer a different question; "
                         "3 is the easiest set and 0 is the real item")
    ap.add_argument("--out", default=None)
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--dataset", default="allenai/reward-bench-2")
    args = ap.parse_args()
    args.out = args.out or f"data/control_o{args.obvious}"
    args.manifest = args.manifest or f"results/validation/control_manifest_o{args.obvious}.json"

    ds = load_dataset(args.dataset, split="test")
    pool = [i for i, s in enumerate(ds["subset"]) if s != "Ties"]
    rng = random.Random(args.seed)
    picked = rng.sample(pool, args.n)

    os.makedirs(args.out, exist_ok=True)
    os.makedirs(os.path.dirname(args.manifest) or ".", exist_ok=True)
    drawn = []
    with open(os.path.join(args.out, "test.jsonl"), "w") as f:
        for idx in picked:
            row = ds[idx]
            # Draw three every time so the seed produces the same items at every level;
            # only how many of them are used changes.
            others = rng.sample([j for j in pool if j != idx], 3)
            others = others[: args.obvious]
            distractors = [ds[j]["chosen"][0] for j in others] + row["rejected"][: 3 - args.obvious]
            drawn.append({"id": row["id"], "subset": row["subset"], "source_index": idx,
                          "distractor_indices": others, "own_rejected_used": 3 - args.obvious})
            f.write(json.dumps({
                "id": row["id"],
                "subset": row["subset"],
                "source_index": idx,
                "distractor_indices": others,
                "prompt": row["prompt"],
                "chosen": [row["chosen"][0]],
                "rejected": distractors,
                "num_correct": 1,
                "num_incorrect": 3,
                "total_completions": 4,
                "models": row["models"][:1] + ["control"] * 3,
                "additional_metadata": None,
            }) + "\n")

    json.dump({
        "dataset": args.dataset, "n": args.n, "seed": args.seed, "obvious": args.obvious, "drawn": drawn,
        "note": (f"Prompt and chosen response are the item's own. {args.obvious} of the three "
                 f"distractors are the chosen responses of other items, so they answer a "
                 f"different question entirely; the remaining {3 - args.obvious} are the item's "
                 f"own rejected responses. Nothing here is authored by us."),
    }, open(args.manifest, "w"), indent=1)

    print(f"wrote {args.out}/test.jsonl: {args.n} items, seed {args.seed}")
    print(f"wrote {args.manifest}")
    rows = [json.loads(l) for l in open(os.path.join(args.out, "test.jsonl"))]
    lens_c = [len(r["chosen"][0]) for r in rows]
    lens_r = [len(x) for r in rows for x in r["rejected"]]
    print(f"  chosen response length   mean {sum(lens_c)/len(lens_c):8.1f} chars")
    print(f"  distractor length        mean {sum(lens_r)/len(lens_r):8.1f} chars")
    print(f"  overlap between a chosen and its own distractors: "
          f"{sum(1 for r in rows if r['source_index'] in r['distractor_indices'])}")
    from collections import Counter
    print("  subsets drawn from:", dict(Counter(r["subset"] for r in rows)))


if __name__ == "__main__":
    main()
