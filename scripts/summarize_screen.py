#!/usr/bin/env python3
"""Apply the pre-registered judge screen and print the result for every candidate.

The screen is in `PREREGISTRATION-exp01b.md` §4: a judge enters the measurement if its
unparseable-verdict rate is at most 10% and its accuracy is above 0.30. Both thresholds were
fixed before any candidate ran. Candidates that fail are printed with their numbers rather
than dropped silently, and a candidate that could not be run at all is listed with the
reason.

  python scripts/summarize_screen.py
"""
import glob
import json
import os

import numpy as np

MAX_UNPARSED = 0.10
MIN_ACCURACY = 0.30
BOOT = 10000
SEED = 0
# Candidates that never produced a result, with why. Kept here so the count of candidates
# stays honest: six were tried, not five.
DID_NOT_RUN = {
    "AtlaAI/Selene-1-Mini-Llama-3.1-8B":
        "upstream's Atla branch calls LLM.generate(prompt_token_ids=...), which vllm 0.13.0 "
        "does not accept",
}


def load(path):
    meta, rows = {}, []
    for line in open(path):
        o = json.loads(line)
        (meta.update(o) if o.get("_record") == "metadata" else rows.append(o))
    return meta, rows


def rescore():
    """Apply the screen's own thresholds at each position of the correct answer.

    The screen ran one arrangement, and reading its metadata says which: permutation
    (0, 1, 2, 3), the correct answer at slot A on all 150 items. Its accuracy is therefore
    the rate of answering [[A]], which is the axis this experiment exists to measure. The
    same 150 items at the other three positions are in the P1c --obvious 0 runs, so the
    screen can be re-scored where it was never run, without running anything.
    """
    pos = {}
    for path in sorted(glob.glob("results/exp01/P1c_*_o0_*.jsonl")):
        with open(path) as f:
            meta = json.loads(f.readline())
            rows = [json.loads(l) for l in f]
        acc = sum(1 for r in rows if r["parsed_letter"] == meta["chosen_at_slot"]) / len(rows)
        up = sum(1 for r in rows if r["parsed_letter"] not in "ABCD") / len(rows)
        pos.setdefault(meta["model"], {})[meta["chosen_at_slot"]] = (acc, up)
    if not pos:
        return
    print("\n\nthe same screen, scored at each position of the correct answer\n")
    print("The screen ran at one arrangement: the correct answer at slot A, every item. Its")
    print("accuracy is the rate of answering [[A]]. The other three columns are the same 150")
    print("items from the P1c --obvious 0 runs, so nothing new was run to produce them.\n")
    print(f"  {'candidate':32s} {'screen':>8s} " + " ".join(f"{'ans@' + s:>8s}" for s in "ABCD")
          + "   passes at A B C D")
    for m in sorted(pos, key=lambda x: -pos[x]["A"][0]):
        p = pos[m]
        flags = "".join(" Y" if p[s][0] > MIN_ACCURACY and p[s][1] <= MAX_UNPARSED else " n"
                        for s in "ABCD")
        meta, items = load(f"results/validation/screen/{m.replace('/', '__')}.jsonl")
        sc = sum(x["results"] for x in items) / len(items)
        print(f"  {m.split('/')[-1]:32s} {sc:8.4f} "
              + " ".join(f"{p[s][0]:8.4f}" for s in "ABCD") + f"   {flags}")
    print("\n  rank by accuracy, at each position:")
    for s in "ABCD":
        order = sorted(pos, key=lambda m: -pos[m][s][0])
        print(f"    {s}: " + " > ".join(m.split("/")[-1] for m in order))
    print("\n  The screen selected on the same axis the experiment measures, so which judges")
    print("  entered it is not independent of what it found. Section 11 records that.")


def main():
    files = sorted(glob.glob("results/validation/screen/*.jsonl"))
    print(f"screen: unparsed <= {MAX_UNPARSED:.0%}, accuracy > {MIN_ACCURACY:.2f}")
    print("150 unmodified benchmark items, one arrangement, upstream's prompt\n")
    print(f"  {'candidate':40s} {'n':>4s} {'accuracy':>9s} {'unparsed':>9s} {'rate':>7s}  verdict")
    rows = []
    for f in files:
        meta, items = load(f)
        r = [x["results"] for x in items]
        unparsed = sum(1 for x in r if x == 0.25)
        acc = sum(r) / len(r)
        ok = unparsed / len(r) <= MAX_UNPARSED and acc > MIN_ACCURACY
        rows.append((meta["model"], len(r), acc, unparsed, ok))
    for m, n, acc, up, ok in sorted(rows, key=lambda x: -x[2]):
        print(f"  {m:40s} {n:4d} {acc:9.4f} {up:9d} {up/n:7.1%}  {'PASS' if ok else 'FAIL'}")
    for m, why in DID_NOT_RUN.items():
        print(f"  {m:40s} {'—':>4s} {'—':>9s} {'—':>9s} {'—':>7s}  DID NOT RUN")
        print(f"      {why}")
    print(f"\n  {sum(1 for r in rows if r[4])} of {len(rows) + len(DID_NOT_RUN)} candidates pass.")
    print("  The pre-registration said six; the shortfall is reported, not backfilled with")
    print("  judges chosen after seeing their scores.")

    rescore()

    print("\n\nis the ranking above separated, or is it noise\n")
    print("The screen ranks candidates by accuracy on one set of 150 items. Whether any")
    print("adjacent pair is actually separated is a different question from whether their")
    print("point estimates differ, and the ranking is not used for anything if it is not.")
    print("Paired over items -- the same items, the same arrangement, so each pair is")
    print(f"compared on its own {BOOT:,} bootstrap resamples of the item index.\n")
    scored = {}
    for f in files:
        meta, items = load(f)
        scored[meta["model"]] = {x["id"]: x["results"] for x in items}
    order = [m for m, *_ in sorted(rows, key=lambda x: -x[2])]
    rng = np.random.default_rng(SEED)
    print(f"  {'adjacent pair':58s} {'diff':>8s} {'95% CI':>20s} "
          f"{'A>B':>5s} {'B>A':>5s}  separated?")
    for hi, lo in zip(order, order[1:]):
        ids = sorted(set(scored[hi]) & set(scored[lo]))
        a = np.array([scored[hi][i] for i in ids])
        b = np.array([scored[lo][i] for i in ids])
        d = a - b
        idx = rng.integers(0, len(ids), (BOOT, len(ids)))
        bs = d[idx].mean(1)
        ci = (float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)))
        sep = ci[0] > 0 or ci[1] < 0
        name = f"{hi.split('/')[-1]} - {lo.split('/')[-1]}"
        print(f"  {name:58s} {d.mean():+8.4f} [{ci[0]:+7.4f}, {ci[1]:+7.4f}] "
              f"{int((d > 0).sum()):5d} {int((d < 0).sum()):5d}  "
              f"{'yes' if sep else 'no -- CI includes 0'}")
    print(f"\n  n = {len(ids)} items per pair. A>B and B>A count the items where exactly one")
    print("  of the two was credited; pairs whose interval includes zero are not ordered by")
    print("  this screen and are not described as ordered anywhere else.")

    print("\n\nwhy a context cap was needed\n")
    from transformers import AutoConfig, AutoTokenizer
    for m, *_ in sorted(rows, key=lambda x: -x[2]):
        try:
            n = AutoConfig.from_pretrained(m).max_position_embeddings
        except Exception:  # noqa: BLE001
            n = None
        print(f"  {m:40s} declares {n if n else '?':>7} tokens of context")
    items = [json.loads(l) for l in open("data/control_o0/test.jsonl")]
    sysp = open("prompts/polarity_original.txt").read()
    tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
    longest = max(len(tok(sysp + r["prompt"] + "".join(r["chosen"] + r["rejected"]),
                          add_special_tokens=False)["input_ids"]) for r in items)
    print(f"\n  longest four-way prompt in this set: {longest} tokens")
    print(f"  generation cap adds 2048, so {longest + 2048} is the most a request can need\n")
    # One cap per judge, read from that judge's own file. Quoting a single number here was
    # wrong: vLLM refuses a cap above the model's declared context, so the judge that
    # declares 8192 never ran at the 16384 the other five did.
    print(f"  {'candidate':40s} {'cap used':>9s} {'x the most a request needs':>27s}")
    for path in files:
        meta, _ = load(path)
        c = meta.get("max_model_len")
        print(f"  {meta['model']:40s} {c if c else '—':>9} "
              f"{c / (longest + 2048):27.1f}")


if __name__ == "__main__":
    main()
