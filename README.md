# THEMIS — judging the judges

If you cannot trust the judgment, you cannot trust the training.

Reward models and LLM judges are benchmarked on *what* they judge. They are rarely
benchmarked on **whether the same judgment, asked in the opposite direction, survives.**

This repository measures that, on public data, against a public leaderboard.

> Status: **nothing has been measured yet.** No number in this repository is a result.

## The two experiments

**exp01 — polarity sensitivity.** Ask a judge the same question with the predicate
reversed and the correct answer unchanged, and measure how far each model's score moves,
against how far it moves when the correct answer merely changes position. Evaluated on
[RewardBench 2](https://github.com/allenai/reward-bench) — **1,763 of its 1,865 items,
5 of its 6 subsets** (Ties is scored by a different prompt and is out of scope).

**exp02 — reward hacking under GRPO.** *(not started)* Train with a verifier that has a
known loophole, and measure how many steps the policy needs to find it.

exp01 is the premise of exp02. A judge that moves under rephrasing produces a reward
model that moves, which produces a policy optimizing something other than the goal.

## What "the opposite direction" had to become

RewardBench 2 contains no yes/no question. Each item is one prompt with four candidate
responses; a sequence-classifier reward model scores each candidate independently and is
never asked anything. So the phrasing this experiment was drafted around — "did this
follow the instruction?" against "did this violate the instruction?" — does not exist here
and had to be replaced.

The obvious replacement is worse than it looks. Flipping the four-way ranking prompt from
"which is best" to "which is worst" moves the correct answer from 1 candidate to 3, taking
chance from 25% to 75%. That is not a difficulty quirk to correct for; it is a different
question.

What this repository runs instead inverts the predicate and asks for the **complement**, so
that the answer stays a single candidate and chance stays at 25%:

> *original* — choose the assistant that follows the instruction and answers best
> *inverted* — three of these four fail to follow the instruction; identify the one that does not

Same items, same four-way format, same `[[A]]`–`[[D]]` output convention, same scoring
code. One string differs. The judge still has to reason in the inverted direction; only the
reporting convention is preserved — which is the shape of the original observation.

The options that were rejected, the measurements that decided it, and what the choice costs
are in [`docs/decisions/0001-polarity-implementation.md`](docs/decisions/0001-polarity-implementation.md).
Finding this after writing the harness would have meant discarding the harness.

**Known limitation, stated up front:** of the 18 generative judges with published scores,
16 are paid API models and the other two are 70 B+. No open-weight generative judge that
fits on a 24 GB card has a published score, so the experimental path cannot be validated by
reproducing a published number. The harness gate runs on the reward-model path and
validates the data, scoring and aggregation — not the prompt path.

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
- **Inverting the question must not change which answer is correct.** If the two conditions
  do not have the same chance level, the measurement is a difficulty difference wearing the
  costume of a finding.
- **Unparseable verdicts score 0, not chance.** Upstream credits them 0.25; an inverted
  prompt that merely breaks the output format would otherwise look like a result.
- **Perturbations are data, not code**, so a reader can inspect them.
- **Confidence intervals that include zero are reported as "cannot be said to shift."**
- **Coverage is stated as a count.** What was run out of what exists, and why the rest wasn't.
- **Raw logs are committed.** Every table is generated from `results/*.jsonl`, not typed by hand.
- **Corrections are published, not patched over.** [`docs/errata.md`](docs/errata.md) records
  what was wrong, what it should have said, and how it got past us.

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

[Apache License 2.0](LICENSE). The upstream evaluator this repository runs,
[`allenai/reward-bench`](https://github.com/allenai/reward-bench), is Apache-2.0 as well,
so results, scripts and any patch developed here can move back upstream without a licence
mismatch. Raw measurement logs under `results/` are covered by the same licence — reuse
them, and please say where they came from.
