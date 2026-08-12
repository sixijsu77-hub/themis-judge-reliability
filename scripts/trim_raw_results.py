#!/usr/bin/env python3
"""Turn an upstream run's per-item output into a committable raw log.

`run_v2.py` writes results/eval-set-scores/<org>/<model>.json, which is ~16 MB because it
embeds the full prompt and all four candidate responses for every item. That text is a
verbatim copy of a pinned public dataset, so committing it would put a second copy of
`allenai/reward-bench-2` in this repository's history for no gain.

What must survive is the individual verdicts, because the whole point of this repository is
that aggregates can agree while items disagree. So this writes one JSON object per item —
id, subset, the raw per-candidate scores, and the credited result — as JSONL, which diffs
and greps by line.

Usage:  python scripts/trim_raw_results.py <model> [<model> ...]
"""
import json
import os
import sys

SRC = "results/eval-set-scores/{model}.json"
DST = "results/gate/{flat}.jsonl"
KEEP = ["id", "subset", "num_correct", "scores", "results"]


def trim(model):
    src = SRC.format(model=model)
    if not os.path.exists(src):
        print(f"  MISSING  {src}")
        return False
    d = json.load(open(src))
    n = len(d["id"])
    dst = DST.format(flat=model.replace("/", "__"))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w") as f:
        f.write(json.dumps({
            "_record": "metadata",
            "model": d.get("model", model),
            "model_type": d.get("model_type"),
            "chat_template": d.get("chat_template"),
            "n_items": n,
            "dataset": "allenai/reward-bench-2",
            "evaluator": "allenai/reward-bench@05a9005efb607249822c193590c8ecab87c77052",
            "note": ("Per-item scores from an unmodified upstream run. The 'text' field of "
                     "the upstream output is dropped here: it is a verbatim copy of the "
                     "pinned dataset and is regenerable with rewardbench.load_bon_dataset_v2. "
                     "'results' is None for the Ties subset because upstream does not define "
                     "a per-item result there."),
        }, ensure_ascii=False) + "\n")
        for i in range(n):
            f.write(json.dumps({k: d[k][i] for k in KEEP}, ensure_ascii=False) + "\n")
    print(f"  {src}  ({os.path.getsize(src)/1e6:.1f} MB)"
          f"  ->  {dst}  ({os.path.getsize(dst)/1e6:.2f} MB, {n} items)")
    return True


def load_trimmed(model):
    """Read a trimmed JSONL back into the column-wise dict the comparison script wants."""
    path = DST.format(flat=model.replace("/", "__"))
    rows, meta = [], {}
    with open(path) as f:
        for line in f:
            o = json.loads(line)
            (meta.update(o) if o.get("_record") == "metadata" else rows.append(o))
    out = {k: [r[k] for r in rows] for k in KEEP}
    out.update({k: v for k, v in meta.items() if k in ("model", "model_type", "chat_template")})
    return out


if __name__ == "__main__":
    ok = all([trim(m) for m in sys.argv[1:]])
    sys.exit(0 if ok else 1)
