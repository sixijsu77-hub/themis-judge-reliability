# THEMIS — judging the judges

If you cannot trust the judgment, you cannot trust the training.

Reward models and LLM judges are benchmarked on *what* they judge. They are rarely
benchmarked on **whether the same judgment, asked in the opposite direction, survives.**

This repository measures that, on public data, against a public leaderboard.

> **Status.** The harness gate has passed — three reward models reproduced their published
> RewardBench 2 scores within 0.0094, checked per item as well as on the aggregate. Five
> defects found in the published results along the way are
> [filed upstream](#what-turned-up-on-the-way), and two more found by running the evaluator
> rather than reading its numbers — one as a pull request, one as an issue. The polarity
> experiment this repository is named for returned a weak, difficulty-dependent answer and
> its hypotheses are recorded as mis-specified in [`PREREGISTRATION.md`](PREREGISTRATION.md).
> **The position experiment has run at full scale** — 240 passes over five judges, two
> benchmarks and 1,763 items each — and its four hypotheses are decided, two of them against
> the framing this repository started with.

## The two experiments

**exp01 — polarity sensitivity.** Ask a judge the same question with the predicate
reversed and the correct answer unchanged, and measure how far each model's score moves,
against how far it moves when the correct answer merely changes position. Evaluated on
[RewardBench 2](https://github.com/allenai/reward-bench) — **1,763 of its 1,865 items,
5 of its 6 subsets** (Ties is scored by a different prompt and is out of scope).

Its answer so far: on items whose correct answer is obvious the inverted phrasing costs the
judge 17 points, and a same-polarity paraphrase of the same magnitude costs it nothing — but
as the items get realistic the polarity effect falls to zero and then reverses, while the
paraphrase accounts for most of what is left. One thing survives at every difficulty: the
judge contradicts its own stated conclusion only under inversion, never in either control.
Both results, and a defect in our own inverted wording that partly contaminates the second,
are in [`PREREGISTRATION.md`](PREREGISTRATION.md).

**exp01b — where a judge's errors go.** The same runs found something larger, and the first
account of it was wrong in a way worth reading. It looked as though a judge acquired a
first-slot preference as items got harder while being unbiased where the answer was obvious.
Both halves of that dissolved: the rise follows from an identity once accuracy falls, the
"unbiased when obvious" reading rested on four usable errors, and the control set's own
construction supplied most of the apparent gradient. What survives is in
[`PREREGISTRATION-exp01b.md`](PREREGISTRATION-exp01b.md), which keeps every hypothesis as
registered and reports each against what it can actually carry.

Decided: **H1 holds by its rule and not by its name** — no judge's slope clears what a
constant preference fitted to its own behaviour produces. **H2 and H3 are falsified.** H5
holds directionally, and its sign depends on which accuracy axis it is read against, which
the results say rather than pick.

What is left is not one effect with an unknown size. **Judges of comparable accuracy differ
in which slot they fall toward, and two of the five exclude the null in opposite
directions** — reported under a heading saying the pre-registration did not anticipate it,
beside the sentence it did register, with neither merged into the other.

**And it reaches the score.** On identical items with only the correct answer's position
changed, a judge's accuracy moves by up to 0.6205 and by as little as 0.0686, and the
ranking those scores induce inverts — a judge first at one position is last at another.
Upstream draws that position unseeded, and credits an unparseable verdict 0.25; first place
changes on that convention alone. Written up in
[`docs/findings/0003-slot-dispositions.md`](docs/findings/0003-slot-dispositions.md),
including what was retracted on the way and what this does not establish.

**exp01c — is that a property of the judge?** Registered before it was computed, in
[`PREREGISTRATION-exp01c.md`](PREREGISTRATION-exp01c.md). The direction of a judge's slot
disposition **survives a change of arrangement set** (4 of 5) and **a change of benchmark**
(5 of 5, on [UltraFeedback](https://huggingface.co/datasets/openbmb/UltraFeedback), which is
four-way natively so neither side is constructed). It is **not established across
difficulty**: every clean test of that axis is unpowerable here, and the one dirty look
available disagrees. That sentence is in the pre-registration rather than left implied.

**exp02 — reward hacking under GRPO.** *(not started)* Train with a verifier that has a
known loophole, and measure how many steps the policy needs to find it. Its original premise
was that exp01 would show judges to be unreliable; exp01 did not show that cleanly, so the
premise is rewritten before exp02 opens.

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

## What turned up on the way

Reproducing published numbers meant reading the published numbers closely, and running the
evaluator meant reading its source. Seven things came out of that, all filed upstream and all
reproducible from
[`results/`](results) with the scripts in [`scripts/`](scripts):

| | | |
|---|---|---|
| Generative scores are not reproducible run to run: the candidate arrangement is unseeded, and the draw is frozen by the `datasets` cache | up to **0.0929** between runs of one model on itself, ~30% of items changing | [#272](https://github.com/allenai/reward-bench/issues/272) |
| An unparseable verdict is credited 0.25, which is chance under a four-way choice | **20.0%** of one published entry's items | [#272](https://github.com/allenai/reward-bench/issues/272) |
| The published per-item files carry wrong ids in the first ten Factuality entries | **179 of 188** files | [#273](https://github.com/allenai/reward-bench/issues/273) |
| Generative results do not record which of two scoring protocols produced them | **0 of 14** record it | [#273](https://github.com/allenai/reward-bench/issues/273) |
| The documented install for local models cannot import the local script | two packages, never called | [#274](https://github.com/allenai/reward-bench/issues/274) |
| The flag that caps vLLM's context is commented out in both generative runners, so a judge declaring a long context cannot start on a 24 GB card | **2 of 7** judges screened here | [#275](https://github.com/allenai/reward-bench/pull/275) |
| The `Atla` inference branch passes an argument the pinned vLLM does not accept, so every model routed through it raises after the weights load | **1 of 7** judges screened here | [#276](https://github.com/allenai/reward-bench/issues/276) |

Full write-up: [`docs/findings/0001-published-results-reproducibility.md`](docs/findings/0001-published-results-reproducibility.md).

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
- **A check is tested against the accident it was built for.**
  [`scripts/check_the_checks.py`](scripts/check_the_checks.py) replays each mistake this
  repository has made at the check meant to catch it. The first version of one check passed
  the exact defect it was named for; a check that has not been fed its own accident is a
  claim, not a guard.
- **A number that came out of a run does not live in code.** Measurements copied into a
  script are measurements nobody re-derives when the run behind them changes, and one such
  copy inverted a whole section's conclusion. Both faces are checked — literals a script
  consumes, and literals it prints into `results/` where the prose gate would then accept
  them as evidence.
- **Before a hypothesis is committed, the thing it needs is shown to exist.** Three in a row
  were registered without it: one needed errors that were not there, one needed a second
  four-way benchmark whose obvious candidate turned out to be pairwise, one asked a question
  its own sample could not answer. The check that settles it goes in the same commit.
- **Failing to reject is not establishing.** A permutation test that returns a large p leaves
  "alike" and "could not tell" together, and separating them changed which of this
  repository's own claims are supported.

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
