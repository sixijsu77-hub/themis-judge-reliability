#!/usr/bin/env python3
"""Summarise the graded control runs.

The same 150 items appear at four difficulties. Only the distractors change: three, two,
one or none of them answer a different question, so `--obvious 0` is the unmodified
benchmark item. Three prompt conditions run over each level. That isolates two things the
earlier stages could not separate — how much of a shift comes from rewording a prompt at
all, and how either depends on how hard the judgment is.

  python scripts/summarize_graded.py
"""
import glob
import json
import re

import numpy as np

CONDITIONS = ["original", "paraphrase", "inverted"]
ORDERINGS = [0, 6, 14, 21]           # the chosen candidate in slot A, B, C, D
SLOT = {0: "A", 6: "B", 14: "C", 21: "D"}
CONCLUSION = {
    "original": re.compile(r"Assistant ([A-D])(?:'s response)?[^.]{0,60}?\bis (?:the )?best\b", re.I),
    "paraphrase": re.compile(r"Assistant ([A-D])(?:'s response)?[^.]{0,60}?\bis the leading\b", re.I),
    "inverted": re.compile(r"Assistant ([A-D])(?:'s response)?[^.]{0,60}?\bis the remaining\b", re.I),
}
# The inverted prompt's "the remaining assistant" does not say remaining after what, and the
# judge sometimes reads it as the one left among the failures. Counted, not hidden.
NEGATED = re.compile(r"\b(does not|doesn't|fails? to|not follow|least|worst|incorrect|irrelevant|unhelpful)\b", re.I)
RNG = np.random.default_rng(0)


def load(level, cond, ordering):
    rows = []
    for line in open(f"results/validation/graded/o{level}_{cond}_{ordering}.jsonl"):
        o = json.loads(line)
        if o.get("_record") != "metadata":
            rows.append(o)
    return rows


def paired_ci(a, b, n=10000):
    keys = sorted(set(a) & set(b))
    d = np.array([a[k] - b[k] for k in keys])
    bs = d[RNG.integers(0, len(d), (n, len(d)))].mean(1)
    return d.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def main():
    levels = sorted({int(p.split("/o")[-1][0]) for p in glob.glob("results/validation/graded/o*_*.jsonl")},
                    reverse=True)

    print("accuracy, averaged over the four chosen-positions\n")
    print(f"  {'obvious':>7s} {'original':>9s} {'paraphrase':>11s} {'inverted':>9s} |"
          f" {'rewording':>10s} {'polarity':>10s} {'95% CI':>21s}")
    for lv in levels:
        per = {c: [{r["id"]: r["results"] for r in load(lv, c, d)} for d in ORDERINGS] for c in CONDITIONS}
        mean = {c: {k: np.mean([x[k] for x in per[c]]) for k in per[c][0]} for c in CONDITIONS}
        acc = {c: np.mean(list(mean[c].values())) for c in CONDITIONS}
        w, _, _ = paired_ci(mean["original"], mean["paraphrase"])
        p, lo, hi = paired_ci(mean["paraphrase"], mean["inverted"])
        flag = "  includes 0" if lo * hi <= 0 else ""
        print(f"  {lv:7d} {acc['original']:9.4f} {acc['paraphrase']:11.4f} {acc['inverted']:9.4f} |"
              f" {w:+10.4f} {p:+10.4f}  [{lo:+.4f}, {hi:+.4f}]{flag}")
    print("\n  'rewording' is original minus paraphrase; 'polarity' is paraphrase minus inverted,")
    print("  so the second is the part rewording does not already account for.")

    print("\n\nthe judge's stated conclusion against the letter it emitted\n")
    print(f"  {'obvious':>7s}" + "".join(f"{c:>26s}" for c in CONDITIONS))
    for lv in levels:
        cells = []
        for c in CONDITIONS:
            stated = contra = 0
            for d in ORDERINGS:
                for r in load(lv, c, d):
                    m = CONCLUSION[c].search(r["judgement_text"])
                    if m:
                        stated += 1
                        contra += m.group(1).upper() != r["parsed_letter"]
            cells.append(f"{contra:3d} of {stated:<4d} = {contra/stated if stated else 0:6.1%}")
        print(f"  {lv:7d}" + "".join(f"{x:>26s}" for x in cells))

    print("\n\nhow often the inverted prompt's 'the remaining assistant' is read as the failing one\n")
    sent = re.compile(r"Assistant [A-D](?:'s response)?[^.]{0,140}?is the remaining[^.]{0,120}\.", re.I)
    print(f"  {'obvious':>7s} {'sentences':>10s} {'negated':>8s} {'rate':>7s}")
    for lv in levels:
        t = n = 0
        for d in ORDERINGS:
            for r in load(lv, "inverted", d):
                for s in sent.findall(r["judgement_text"]):
                    t += 1
                    n += bool(NEGATED.search(s))
        print(f"  {lv:7d} {t:10d} {n:8d} {n/t if t else 0:7.1%}")

    print("\n\nposition: the same items, the correct answer moved, upstream's own prompt\n")
    print(f"  {'obvious':>7s} " + "  ".join(f"{'chosen at '+SLOT[d]:>12s}" for d in ORDERINGS) + f" {'spread':>9s}")
    for lv in levels:
        accs = []
        for d in ORDERINGS:
            r = [x["results"] for x in load(lv, "original", d)]
            accs.append(sum(r) / len(r))
        print(f"  {lv:7d} " + "  ".join(f"{a:12.4f}" for a in accs) + f" {max(accs)-min(accs):9.4f}")

    print(f"\n  letters the judge emitted, pooled over the four positions")
    print(f"  (the correct answer sat in each slot exactly as often)\n")
    print(f"  {'obvious':>7s} " + "  ".join(f"{L:>12s}" for L in "ABCD"))
    for lv in levels:
        c = {L: 0 for L in "ABCD"}
        for d in ORDERINGS:
            for r in load(lv, "original", d):
                if r["parsed_letter"] in c:
                    c[r["parsed_letter"]] += 1
        n = sum(c.values())
        print(f"  {lv:7d} " + "  ".join(f"{c[L]:5d} ({c[L]/n:5.1%})" for L in "ABCD"))


def safety():
    """The real Safety subset at one ordering, for contrast with the graded levels."""
    import os
    if not os.path.isdir("results/validation/safety"):
        return
    per = {}
    for c in CONDITIONS:
        rows = [json.loads(l) for l in open(f"results/validation/safety/{c}_0.jsonl")
                if '"_record"' not in l]
        per[c] = {r["id"]: r["results"] for r in rows}
    print("\n\nthe real Safety subset, one ordering, for contrast\n")
    n = len(per["original"])
    print(f"  {'condition':11s} {'n':>5s} {'accuracy':>9s} {'unparsed':>9s}")
    for c in CONDITIONS:
        v = list(per[c].values())
        print(f"  {c:11s} {n:5d} {sum(v)/n:9.4f} {sum(1 for x in v if x == 0.25):9d}")
    print()
    for label, a, b in (("rewording  original - paraphrase", "original", "paraphrase"),
                        ("both       original - inverted  ", "original", "inverted"),
                        ("polarity   paraphrase - inverted", "paraphrase", "inverted")):
        m, lo, hi = paired_ci(per[a], per[b])
        flag = "  includes 0" if lo * hi <= 0 else ""
        print(f"  {label}  {m:+.4f}  95% CI [{lo:+.4f}, {hi:+.4f}]{flag}")


if __name__ == "__main__":
    main()
    safety()
