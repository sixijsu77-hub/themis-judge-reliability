#!/usr/bin/env python3
"""Test whether the three distractors are exchangeable across their list positions.

A statistic that counts how often a judge names slot A is confounded with candidate identity
whenever the arrangement set ties the two together. Whether that matters depends on something
the arrangement set cannot decide: are the three distractors distinguishable at all?

The judge sees the question and four answer texts labelled A to D. It sees no index, no
provenance, and no name. So "the judge prefers the first distractor" is only a coherent
alternative if the first distractor differs from the other two in the text itself. Where
`build_control_set.py` draws all three the same way they cannot, and where it draws them
differently they can.

The test permutes the three position labels within each item, which is exactly the null that
position carries no information, and compares the observed spread of a per-position summary
against that null.

  python scripts/check_exchangeable.py
"""
import glob
import json
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

N_PERM = 20000
RNG = np.random.default_rng(0)
WORD = re.compile(r"\w+")
PROPERTIES = {
    "characters": len,
    "words": lambda t: len(WORD.findall(t)),
    "newlines": lambda t: t.count("\n"),
}


def load(path):
    """Per item, the three distractor texts in the order the file writes them."""
    out = []
    for line in open(path):
        r = json.loads(line)
        if len(r["rejected"]) == 3:
            out.append([x if isinstance(x, str) else x[0] for x in r["rejected"]])
    return out


def spread(values):
    """max - min over the three position means. Zero when position says nothing."""
    m = values.mean(0)
    return float(m.max() - m.min())


def test(items, prop):
    v = np.array([[prop(t) for t in row] for row in items], float)
    observed = spread(v)
    null = np.empty(N_PERM)
    for k in range(N_PERM):
        idx = np.argsort(RNG.random(v.shape), axis=1)
        null[k] = spread(np.take_along_axis(v, idx, axis=1))
    p = float((null >= observed).mean())
    return observed, v.mean(0), p


def main():
    print(__doc__.split("  python")[0].strip() if __doc__ else "")
    print("\n" + "=" * 92)
    print(f"permutation test, {N_PERM:,} shuffles of the three position labels within each item")
    print("=" * 92)
    print(f"  {'dataset':16s} {'n':>5s} {'property':>11s} "
          f"{'mean at R1':>11s} {'mean at R2':>11s} {'mean at R3':>11s} "
          f"{'spread':>9s} {'p':>7s}  exchangeable?")
    for path in sorted(glob.glob("data/*/test.jsonl")):
        name = path.split("/")[1]
        items = load(path)
        if not items:
            continue
        for label, prop in PROPERTIES.items():
            obs, means, p = test(items, prop)
            print(f"  {name:16s} {len(items):5d} {label:>11s} "
                  + " ".join(f"{m:11.1f}" for m in means)
                  + f" {obs:9.1f} {p:7.4f}  "
                  + ("yes" if p > 0.05 else "NO — position carries information"))
        print()
    print("  A large p means the three positions look alike on that property, which is what")
    print("  the construction implies where all three distractors are drawn the same way. A")
    print("  small p means the list position predicts something about the text, and then a")
    print("  judge could act on the text and produce what looks like a slot preference.")
    print("\n  This bounds one alternative. It does not show the judge is indifferent to")
    print("  content; it shows what content there is for it to be sensitive to.")


if __name__ == "__main__":
    main()
