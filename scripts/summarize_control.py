#!/usr/bin/env python3
"""Summarise the control-set runs (stage S1).

The control set has an indisputable correct answer per item, so a drop in accuracy cannot
be attributed to the items being hard. Three conditions run over it: the upstream prompt,
the same prompt with its polarity inverted, and a paraphrase that changes the same two
sentences by a comparable amount while leaving the polarity alone. The paraphrase is what
separates "rewording costs accuracy" from "inverting the predicate costs accuracy".

  python scripts/summarize_control.py results/validation/control
"""
import json
import re
import sys

# The concluding sentence each prompt invites, so the three are detected symmetrically.
CONCLUSION = {
    "original": re.compile(r"Assistant ([A-D])(?:'s response)?[^.]{0,60}?\bis (?:the )?best\b", re.I),
    "paraphrase": re.compile(r"Assistant ([A-D])(?:'s response)?[^.]{0,60}?\bis the leading\b", re.I),
    "inverted": re.compile(r"Assistant ([A-D])(?:'s response)?[^.]{0,60}?\bis the remaining\b", re.I),
}
GOLD_SLOT = {0: "A", 6: "B", 14: "C", 21: "D"}
CONDITIONS = ["original", "paraphrase", "inverted"]


def load(root, cond, ordering):
    meta, rows = {}, []
    for line in open(f"{root}/{cond}_{ordering}.jsonl"):
        o = json.loads(line)
        (meta.update(o) if o.get("_record") == "metadata" else rows.append(o))
    return meta, rows


def main(root):
    print("accuracy by condition and by where the correct candidate sits\n")
    print(f"  {'condition':11s} {'A':>8s} {'B':>8s} {'C':>8s} {'D':>8s} | {'all':>8s} {'spread':>8s}")
    for cond in CONDITIONS:
        accs, pooled = [], []
        for o in (0, 6, 14, 21):
            _, rows = load(root, cond, o)
            r = [x["results"] for x in rows]
            accs.append(sum(r) / len(r))
            pooled += r
        print(f"  {cond:11s} " + " ".join(f"{a:8.4f}" for a in accs) +
              f" | {sum(pooled)/len(pooled):8.4f} {max(accs)-min(accs):8.4f}")

    print("\nthe judge's stated conclusion against the letter it emitted\n")
    print(f"  {'condition':11s} {'items':>6s} {'wrong':>6s} {'unparsed':>9s} "
          f"{'stated':>7s} {'contradicts':>12s} {'named gold':>11s}")
    for cond in CONDITIONS:
        n = wrong = unparsed = stated = contra = named = 0
        wrong_stated = 0
        for o in (0, 6, 14, 21):
            _, rows = load(root, cond, o)
            gold = GOLD_SLOT[o]
            for x in rows:
                n += 1
                if x["results"] == 0:
                    wrong += 1
                if x["results"] == 0.25:
                    unparsed += 1
                m = CONCLUSION[cond].search(x["judgement_text"])
                if not m:
                    continue
                stated += 1
                said = m.group(1).upper()
                if said != x["parsed_letter"]:
                    contra += 1
                if x["results"] == 0:
                    wrong_stated += 1
                    if said == gold:
                        named += 1
        print(f"  {cond:11s} {n:6d} {wrong:6d} {unparsed:9d} {stated:7d} {contra:12d} {named:11d}")
        if cond == "inverted":
            print(f"  {'':11s} of the {wrong} wrong items, {wrong_stated} state a conclusion "
                  f"({wrong_stated/wrong:.1%}); the rest cannot be judged this way.")
            print(f"  {'':11s} 'named gold' is therefore a lower bound, not a total.")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "results/validation/control"))
