#!/usr/bin/env python3
"""Write one subset of the benchmark to a local directory the runner can load.

The staged validation pilots on a single subset, and the runner has no way to select one.
`load_dataset(dir, split="test")` reads a directory holding `test.jsonl`, so a subset can be
handed to it without changing the runner at all. Items are copied verbatim.

  python scripts/build_subset.py --subset Safety
"""
import argparse
import json
import os

from datasets import load_dataset


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subset", required=True)
    ap.add_argument("--dataset", default="allenai/reward-bench-2")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out = args.out or f"data/{args.subset.lower().replace(' ', '_')}"

    ds = load_dataset(args.dataset, split="test")
    rows = [r for r in ds if r["subset"] == args.subset]
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "test.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {out}/test.jsonl: {len(rows)} items from {args.dataset} subset {args.subset!r}")


if __name__ == "__main__":
    main()
