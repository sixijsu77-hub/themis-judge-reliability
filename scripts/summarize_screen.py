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

MAX_UNPARSED = 0.10
MIN_ACCURACY = 0.30
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
    _, first = load(files[0])
    cap = json.loads(open(files[0]).readline())["max_model_len"]
    print(f"\n  longest four-way prompt in this set: {longest} tokens")
    print(f"  generation cap adds 2048, so {longest + 2048} is the most a request can need")
    print(f"  cap used: {cap}, which is {cap / (longest + 2048):.1f}x that")


if __name__ == "__main__":
    main()
