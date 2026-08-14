#!/usr/bin/env python3
"""Run P1 — the arrangement gradient — as the pre-registration specifies it.

Every pass is one invocation of the patched upstream runner. The arrangements come from
`scripts/orderings.py` and are asserted to be the fixed-distractor set before anything
starts: the four that move the correct answer through all four slots while leaving the three
distractors in one relative order. A pilot run used a different four, which visits every slot
but permutes distractors in two of them, so its accuracy spread confounded the two factors.
That is the mistake this file makes structurally impossible to repeat -- the set is imported,
never typed here.

  python scripts/run_p1.py --dry-run                          # print the plan and stop
  REWARD_BENCH=path/to/reward-bench python scripts/run_p1.py  # run it

The patched evaluator is not vendored here; harness/README.md says how to make one.

P1a is the four-difficulty gradient on 150 items and decides H1, H2 and H5. P1b is
`--obvious 3` on all 1,763 items and decides H3, which cannot be decided on 150 because the
judge is right on nearly all of them and the statistic reads only the errors.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orderings import ALL, FIXED_DISTRACTORS, SLOT_OF

# The five that passed the pre-registered screen (PREREGISTRATION-exp01b.md section 4).
# Written here rather than re-derived so a rerun cannot silently change the judge set;
# scripts/summarize_screen.py is what decides membership and it is committed.
JUDGES = [
    "Skywork/Skywork-Critic-Llama-3.1-8B",
    "Qwen/Qwen2.5-7B-Instruct",
    "ZiyiYe/Con-J-Qwen2-7B",
    "R-I-S-E/RISE-Judge-Qwen2.5-7B",
    "NCSOFT/Llama-3-OffsetBias-8B",
]
RUNNER = os.path.join(os.environ.get("REWARD_BENCH", "reward-bench"),
                      "scripts", "run_generative_v2.py")
PROMPT = "prompts/polarity_original.txt"
OUT = "results/exp01"
MAX_MODEL_LEN = 16384
P1A_LEVELS = [3, 2, 1, 0]
P1B_N = 1763


def plan():
    """Every pass, as (phase, judge, obvious level, dataset dir, ordering index)."""
    rows = []
    for m in JUDGES:
        for lv in P1A_LEVELS:
            for o in FIXED_DISTRACTORS:
                rows.append(("P1a", m, lv, f"data/control_o{lv}", o))
    for m in JUDGES:
        for o in FIXED_DISTRACTORS:
            rows.append(("P1b", m, 3, f"data/p1b_o3", o))
    return rows


def tag(phase, model, lv, o):
    return f"{phase}_{model.replace('/', '__')}_o{lv}_{o}"


def build_p1b():
    """The 1,763-item obvious=3 set H3 needs. Same builder, same seed, larger n."""
    if os.path.isfile("data/p1b_o3/test.jsonl"):
        return
    subprocess.run([sys.executable, "scripts/build_control_set.py", "--obvious", "3",
                    "--n", str(P1B_N), "--seed", "0", "--out", "data/p1b_o3",
                    "--manifest", "results/validation/control_manifest_p1b_o3.json"], check=True)


def run_one(phase, model, lv, dataset, o):
    out = f"{OUT}/{tag(phase, model, lv, o)}.jsonl"
    if os.path.isfile(out):
        print(f"  exists, skipping: {out}")
        return
    shutil.rmtree("results/eval-set-scores", ignore_errors=True)
    t0 = time.time()
    subprocess.run([sys.executable, RUNNER, "--model", model, "--dataset", dataset,
                    "--ordering", str(o), "--system_prompt_file", PROMPT,
                    "--skip_ties", "--max_model_len", str(MAX_MODEL_LEN),
                    # do_not_save keeps results off the hub; disable_beaker_save keeps the
                    # runner from writing to /output, which only exists inside AI2's cluster
                    "--do_not_save", "--disable_beaker_save"], check=True)
    src = [os.path.join(r, f) for r, _, fs in os.walk("results/eval-set-scores")
           for f in fs if f.endswith(".json")]
    if len(src) != 1:
        raise RuntimeError(f"expected one score file, found {src}")
    d = json.load(open(src[0]))
    meta = {"_record": "metadata", "phase": phase, "model": model, "ordering": o,
            "chosen_at_slot": SLOT_OF[o], "permutation": list(ALL[o]), "obvious": lv,
            "dataset": dataset, "prompt": f"{PROMPT} (upstream verbatim)",
            "evaluator": "allenai/reward-bench@05a9005 + harness/run_generative_v2.patch",
            "max_model_len": MAX_MODEL_LEN, "n_items": len(d["results"]),
            "seconds": round(time.time() - t0, 1),
            "note": "PREREGISTRATION-exp01b.md section 3."}
    keys = [k for k in ("id", "subset", "results", "parsed_letter", "judgement_text") if k in d]
    os.makedirs(OUT, exist_ok=True)
    with open(out, "w") as f:
        f.write(json.dumps(meta) + "\n")
        for i in range(len(d["results"])):
            f.write(json.dumps({k: d[k][i] for k in keys}) + "\n")
    print(f"  wrote {out}  ({meta['n_items']} items, {meta['seconds']}s)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--phase", choices=["P1a", "P1b"], default=None)
    args = ap.parse_args()

    assert FIXED_DISTRACTORS == [i for i in range(24)
                                 if [x for x in ALL[i] if x != 0] == [1, 2, 3]]
    assert sorted(SLOT_OF[i] for i in FIXED_DISTRACTORS) == list("ABCD")
    print("arrangements, from scripts/orderings.py:")
    for i in FIXED_DISTRACTORS:
        print(f"  index {i:2d}  permutation {ALL[i]}  correct answer at {SLOT_OF[i]}")
    print("  each moves the correct answer to a different slot; distractors stay in one order\n")

    rows = [r for r in plan() if args.phase is None or r[0] == args.phase]
    for phase in ("P1a", "P1b"):
        n = sum(1 for r in rows if r[0] == phase)
        if n:
            print(f"{phase}: {n} passes")
    if args.dry_run:
        for r in rows:
            print("  " + tag(r[0], r[1], r[2], r[4]))
        return
    if not os.path.isfile(RUNNER):
        sys.exit(f"no patched evaluator at {RUNNER}; set REWARD_BENCH (see harness/README.md)")
    if any(r[0] == "P1b" for r in rows):
        build_p1b()
    for phase, model, lv, dataset, o in rows:
        print(f"\n[{phase}] {model}  obvious={lv}  ordering={o} (correct at {SLOT_OF[o]})")
        run_one(phase, model, lv, dataset, o)


if __name__ == "__main__":
    main()
