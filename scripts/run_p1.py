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
from orderings import ALL, FIXED_DISTRACTORS, SLOT_BALANCED, SLOT_OF

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
MAX_MODEL_LEN = 16384    # capped per model below; one judge declares less than this
GENERATION_CAP = 2048    # upstream's max_tokens for a four-way verdict
P1A_LEVELS = [3, 2, 1, 0]
P1B_N = 1763


# Which arrangements each phase uses. P1a and P1b ran on the fixed-distractor set and are
# kept; P1c repeats P1a's grid on the slot-balanced set, which is the one a statistic about
# slots needs. Section 3 of the pre-registration says why, and scripts/arrangement_sets.py
# shows that no set of four is clean on both counts.
PHASES = {
    "P1a": (FIXED_DISTRACTORS, P1A_LEVELS, lambda lv: f"data/control_o{lv}"),
    "P1b": (FIXED_DISTRACTORS, [3], lambda lv: "data/p1b_o3"),
    "P1c": (SLOT_BALANCED, P1A_LEVELS, lambda lv: f"data/control_o{lv}"),
    # Reduced P2, both four-arrangement sets on the unmodified benchmark item. Section 7
    # chose the reduced form when H3 failed and section 3 chose both sets, because no set of
    # four is clean on both counts.
    "P2a": (FIXED_DISTRACTORS, [0], lambda lv: "data/p2_o0"),
    "P2b": (SLOT_BALANCED, [0], lambda lv: "data/p2_o0"),
    # exp01c J3: the same judges on UltraFeedback's own items, which are four-way natively.
    # The set is built by scripts/build_ultrafeedback.py, which shuffles the distractors so
    # that list position carries no quality ordering.
    "J3": (SLOT_BALANCED, [0], lambda lv: "data/uf_o0"),
}


def plan():
    """Every pass, as (phase, judge, obvious level, dataset dir, ordering index)."""
    rows = []
    for phase, (orderings, levels, dataset) in PHASES.items():
        for m in JUDGES:
            for lv in levels:
                for o in orderings:
                    rows.append((phase, m, lv, dataset(lv), o))
    return rows


def longest_request(model, datasets):
    """The most tokens a request can need, measured with this judge's own tokenizer.

    Not a constant: a number copied here would be a number nobody re-derives when the
    prompt or the control set changes, and tokenizers disagree about the same text.
    """
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model)
    system = open(PROMPT).read()
    worst = 0
    for d in sorted(set(datasets)):
        for line in open(os.path.join(d, "test.jsonl")):
            r = json.loads(line)
            text = system + r["prompt"] + "".join(r["chosen"] + r["rejected"])
            worst = max(worst, len(tok(text, add_special_tokens=False)["input_ids"]))
    return worst + GENERATION_CAP


def context_cap(model, datasets):
    """The cap to pass for this judge: ours, or the model's own if it declares less.

    vLLM refuses a max_model_len above the model's declared context, and one of the five
    judges declares 8192. Capping is safe only because nothing truncates, which is measured
    here rather than assumed.
    """
    from transformers import AutoConfig
    cap = min(MAX_MODEL_LEN, int(AutoConfig.from_pretrained(model).max_position_embeddings))
    need = longest_request(model, datasets)
    if cap < need:
        raise RuntimeError(f"{model} allows {cap} tokens, below the {need} a request can "
                           f"need; results would be silently truncated")
    return cap


def tag(phase, model, lv, o):
    return f"{phase}_{model.replace('/', '__')}_o{lv}_{o}"


def build_set(obvious, out, manifest):
    """A full-size control set at one difficulty. Same builder, same seed, larger n."""
    if os.path.isfile(f"{out}/test.jsonl"):
        return
    subprocess.run([sys.executable, "scripts/build_control_set.py", "--obvious", str(obvious),
                    "--n", str(P1B_N), "--seed", "0", "--out", out,
                    "--manifest", manifest], check=True)


def run_one(phase, model, lv, dataset, o):
    out = f"{OUT}/{tag(phase, model, lv, o)}.jsonl"
    if os.path.isfile(out):
        print(f"  exists, skipping: {out}")
        return
    cap = context_cap(model, [dataset])
    shutil.rmtree("results/eval-set-scores", ignore_errors=True)
    t0 = time.time()
    subprocess.run([sys.executable, RUNNER, "--model", model, "--dataset", dataset,
                    "--ordering", str(o), "--system_prompt_file", PROMPT,
                    "--skip_ties", "--max_model_len", str(cap),
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
            "max_model_len": cap, "n_items": len(d["results"]),
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
    ap.add_argument("--phase", choices=list(PHASES), default=None)
    args = ap.parse_args()

    for phase in ([args.phase] if args.phase else PHASES):
        orderings = PHASES[phase][0]
        assert sorted(SLOT_OF[i] for i in orderings) == list("ABCD")
        if orderings is SLOT_BALANCED:
            assert all(sorted(ALL[i][j] for i in orderings) == [0, 1, 2, 3] for j in range(4))
        print(f"{phase} arrangements, from scripts/orderings.py:")
        for i in orderings:
            print(f"  index {i:2d}  permutation {ALL[i]}  correct answer at {SLOT_OF[i]}")
        print()

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
        build_set(3, "data/p1b_o3", "results/validation/control_manifest_p1b_o3.json")
    if any(r[0].startswith("P2") for r in rows):
        build_set(0, "data/p2_o0", "results/validation/control_manifest_p2_o0.json")
    if any(r[0] == "J3" for r in rows) and not os.path.isfile("data/uf_o0/test.jsonl"):
        subprocess.run([sys.executable, "scripts/build_ultrafeedback.py",
                        "--n", str(P1B_N), "--seed", "0"], check=True)
    for phase, model, lv, dataset, o in rows:
        print(f"\n[{phase}] {model}  obvious={lv}  ordering={o} (correct at {SLOT_OF[o]})")
        run_one(phase, model, lv, dataset, o)


if __name__ == "__main__":
    main()
