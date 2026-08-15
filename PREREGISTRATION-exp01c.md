# Pre-registration — exp01c: is a judge's slot disposition a property of the judge?

**Draft. Nothing here has been run and this file does not authorise a run.** It is written
before the measurement so that the observation which prompted it stays an observation. The
git timestamp is the evidence, as in the two pre-registrations before it.

Status: **awaiting a decision on cost. No pass has been executed against it.**

---

## 1. Where this came from, and why that matters

exp01b registered that if H3 failed, what remained was a magnitude measurement on one
benchmark ([`PREREGISTRATION-exp01b.md`](PREREGISTRATION-exp01b.md) §7). H3 failed, and the
magnitude turned out not to be one magnitude: two of five judges excluded the null in
**opposite directions**, and the natural pooling reports the reverse of what both of them do.

**That was not predicted and it is not a finding yet.** It is one difficulty level of one
benchmark for five judges, and the pre-registration it came from did not ask the question it
raises. Turning it into a claim requires asking it of data that did not suggest it, which is
what this file is for. The dispersion is not re-tested on the sample that produced it.

## 2. Question

Is the direction of a judge's slot disposition a stable property of that judge, or a property
of the items it was measured on?

## 3. Design

**Judges.** The five that passed exp01b's screen. No new screen: adding or dropping a judge
between experiments on the strength of what the first one showed is the move that
pre-registration exists to stop.

**Held fixed from exp01b.** The prompt (upstream's `prompt_v2`, verbatim), the arrangement
set (`SLOT_BALANCED`, since every statistic here reads slots), the statistic `E*_A` and its
null of 1/3, the floor of 40 usable errors below which a judge is reported **not evaluated**.

**What varies — three axes, each a way the disposition could fail to be a property.**

| axis | how it is split | what a stable disposition predicts |
|---|---|---|
| items | the 1,763 benchmark items, split in half by the seed already committed | same sign in both halves |
| difficulty | `--obvious 3` against `--obvious 0`, both already run | same sign at both |
| benchmark | a second four-way set, not RewardBench 2 | same sign there |

The first two need no new run: exp01b's P1b and the reduced P2 already cover them, and the
split-half is a re-analysis of committed logs. **Only the third costs GPU time.**

## 4. Hypotheses

| ID | Prediction | Falsified by |
|---|---|---|
| J1 | For **at least 4** of the 5 judges, `E*_A` has the same sign relative to 1/3 in both halves of a seeded split of the 1,763 items, where sign is read only when the half's 95% CI excludes 1/3; a half whose interval contains 1/3 counts as agreeing with neither | Fewer than 4 — including judges not evaluated in a half for want of errors, and which of the two applies is reported per judge |
| J2 | For **at least 4** of the 5, the sign at `--obvious 3` and at `--obvious 0` agrees, read the same way | Fewer than 4 |
| J3 | For **at least 4** of the 5, the sign on a second four-way benchmark agrees with the sign on RewardBench 2 | Fewer than 4 |

Each falsification clause is the complement of its prediction, checked by asking whether a
result exists that satisfies neither. A judge that is not evaluated counts against the
prediction and is reported as its own outcome, never as a pass — the rule exp01b arrived at
after H3.

**J1 and J2 are decided on data already committed.** They are registered before being
computed, and the commit that carries this file precedes the commit that carries their
result.

**Both are falsified, and the two failures are not the same kind of failure**
([`results/validation/sign_stability.txt`](results/validation/sign_stability.txt)).

J1 fails for want of errors. Halving 1,763 items at `--obvious 3` leaves each half below the
registered floor of 40 for four of the five judges, so the test asks something the sample
cannot answer — the trap H3 already fell into, in a design that knew about it. That is a
defect in J1's power, written here rather than discovered afterwards, and it does not become
a claim about judges.

J2 fails for a defect in J2. Its two phases differ in the difficulty, **and** in the
arrangement set, **and** in whether the distractors are exchangeable at all. A sign that
flips between them cannot be told from a judge measured two different ways, and the one flip
observed is what the fixed-distractor confound predicts. The verdict stands as falsified and
carries almost no information. **Registering a comparison is not the same as registering one
that could have worked.**

A J2 that could work holds the arrangement set fixed. The obvious form — `--obvious 3` on
`SLOT_BALANCED` at full size — **carries J1's defect and was proposed without the check that
would have shown it**, which is the same minute of arithmetic J1's own entry two paragraphs
above says was skipped. Run now, in
[`results/validation/power_j2prime.txt`](results/validation/power_j2prime.txt):

| judge | usable errors at 150 | expected at 1,763 | P(clears the floor of 40) |
|---|---|---|---|
| `Llama-3-OffsetBias-8B` | 0 | 0 | 0.000 |
| `RISE-Judge-Qwen2.5-7B` | 3 | 35 | 0.232 |
| `Con-J-Qwen2-7B` | 4 | 47 | 0.864 |
| `Qwen2.5-7B-Instruct` | 5 | 59 | 0.996 |
| `Skywork-Critic-Llama-3.1-8B` | 38 | 447 | 1.000 |

**P(at least 4 of 5 readable) = 0.0100** at each judge's own `--obvious 0` share, 0.0117 with
every judge held at 0.45, and 0.1759 at 0.60. The threshold asks for more readable judges
than the difficulty can supply, and the item count is not the lever — 1,763 is the whole
benchmark. **So that form of J2′ is not proposed.**

The lever is the difficulty. At `--obvious 0` the same judges have between 1,423 and 3,239
usable errors each and every interval is narrow, which is where a comparison across
arrangement sets can actually be read.

## 5. What this cannot settle

The arrangement set makes `E*_A` a statistic about slots rather than candidates, but no set
of four arrangements separates position from candidate identity for a single candidate; that
needs the six distractor orderings within a position ([`exp01b`](PREREGISTRATION-exp01b.md)
§5). So a stable sign is a stable disposition toward a *slot on this arrangement set*, and
whether it is the slot or the candidate that the judge is drawn to remains open.

Nor does a stable sign explain itself. Training data, decoding order and attention are all
candidates and none is measured here.

## 6. Cost

| | what runs | passes | hours |
|---|---|---|---|
| J1, J2 | re-analysis of committed logs | 0 | 0 — done, both falsified |
| J2′ at `--obvious 3` | **withdrawn** — P(readable for 4 of 5) = 0.0100 | — | — |
| J2″ at `--obvious 0` | `FIXED_DISTRACTORS` at full size, against the reduced P2 already run | 20 | 2.6 |
| J3 | 5 judges × a second benchmark × 4 arrangements, **at that benchmark's own items**, the `--obvious 0` equivalent | 20 | 2.6 at a benchmark of this size |

**J3's difficulty is fixed here as the second benchmark's own items and not a control set
built on top of them.** At that level errors are ample and the power question does not
arise; at an `--obvious 3` equivalent it would be J2′ again. Stated before costing, not
after.

**J3 does not start on the strength of a judge's finding or an implementer's judgement.**
The hour cost is estimated and put to the CEO before anything runs.
