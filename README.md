# THEMIS — judging the judges

If you cannot trust the judgment, you cannot trust the training.

Reward models and LLM judges are benchmarked on *what* they judge. They are rarely
benchmarked on **whether the same judgment, asked in the opposite direction, survives.**

This repository measures that, on public data, against a public leaderboard.

> Status: **nothing has been measured yet.** No number in this repository is a result.
> The experiment design has one unresolved question, stated below rather than papered over.

## The two experiments

**exp01 — polarity sensitivity.** Ask a judge the same question with the polarity
reversed, invert the decision rule to match, and measure how far each model's score moves,
with confidence intervals. Evaluated on
[RewardBench 2](https://github.com/allenai/reward-bench) — 1,865 items, six subsets.

**exp02 — reward hacking under GRPO.** *(not started)* Train with a verifier that has a
known loophole, and measure how many steps the policy needs to find it.

exp01 is the premise of exp02. A judge that moves under rephrasing produces a reward
model that moves, which produces a policy optimizing something other than the goal.

## The unresolved question

RewardBench 2 has no yes/no question in it. Each item is one prompt with four candidate
responses, and a sequence-classifier reward model scores each candidate independently —
it is handed a (prompt, response) pair and returns a scalar. There is no "did this follow
the instruction?" to negate.

A generative judge *is* asked a question, so its question can be negated. But inverting
the four-way ranking prompt from "which is best" to "which is worst" changes the chance
level from 25% to 75%, and a shift measured across that change confounds polarity with
difficulty. And of the 18 generative judges with published scores, 16 are paid API models
and the other two are 70 B+ — none is runnable here.

How polarity gets implemented, and what the shift is compared against, are recorded as
open items in [`PREREGISTRATION.md`](PREREGISTRATION.md) §6. They are fixed in a commit of
their own before anything runs. Writing the harness first and discovering this later would
have meant discarding the harness.

## How it is kept honest

- **Pre-registration.** [`PREREGISTRATION.md`](PREREGISTRATION.md) records hypotheses and
  pass/fail criteria, committed before any experiment runs. The git timestamp is the evidence.
- **Falsification clauses are the exact complement of the prediction.** A hypothesis that
  some outcome cannot decide is a hypothesis that will produce no verdict.
- **Harness validation first.** No perturbation result is reported until published
  scores are reproduced within 0.02 — checked per item, not only on the aggregate.
- **The upstream evaluator is the evaluator.** `allenai/reward-bench` is pinned to a
  commit and run as-is. This repository does not reimplement the scoring it is checking.
- **Individual verdicts are retained, not just aggregates.** The failure mode this
  repository exists to measure is precisely one where the aggregate looks fine.
- **Inverting the question inverts the decision rule.** Otherwise the measurement is a
  scoring bug wearing the costume of a finding.
- **Perturbations are data, not code**, so a reader can inspect them.
- **Confidence intervals that include zero are reported as "cannot be said to shift."**
- **Coverage is stated as a count.** What was run out of what exists, and why the rest wasn't.
- **Raw logs are committed.** Every table is generated from `results/*.jsonl`, not typed by hand.

## Constraints

Open-weight models on local hardware only — RTX 4090 (24 GB), Python 3.10.12.
**No paid API.** A sibling project was abandoned because its call count grew
multiplicatively; any design that starts to look like that stops and gets redesigned.

One full pass over the benchmark's 8,977 candidate rows takes about 13 minutes for an 8 B
reward model on this hardware, measured rather than estimated.

## Reproducing

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt      # stage 1 only; see the comments in that file
```

Verify the GPU is actually being used before running anything — a silent fall back to CPU
does not fail, it just takes days:

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

## License

TBD
