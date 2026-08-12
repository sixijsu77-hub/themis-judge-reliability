# Pre-registration — exp01: Judge polarity sensitivity

**This file is committed before any experiment is run.**
The git timestamp is the evidence. Predictions here are not edited after results exist.
If a prediction turns out wrong, it stays, and the result section records that it was wrong.

Status: **not yet binding.** Two operational definitions are still open (§6). They are
fixed in a commit of their own, before anything is run. No measurement has been taken.

---

## 1. Question

Reward models and LLM judges are scored on *what* they judge. They are rarely scored on
**whether the same judgment, asked in the opposite direction, produces the opposite answer.**

This was observed once, informally, in a private project: an inverse-polarity claim
produced judges whose written reasoning contradicted their own boolean output, and the
aggregate looked fine. That observation is the **source of the hypothesis, not evidence
for it.** This experiment produces the evidence on public data.

## 2. What the benchmark actually is (measured, not quoted)

Measured from `allenai/reward-bench-2` (split `test`) and the scoring code in
`allenai/reward-bench` at commit `05a9005`:

| | |
|---|---|
| Items | 1,865 |
| Subsets | Factuality 475, Focus 495, Math 183, Precise IF 160, Safety 450, Ties 102 |
| Non-Ties item | 1 prompt, 1 chosen, 3 rejected (`total_completions == 4`, `num_correct == 1`, all 1,763 items) |
| Ties item | 11–38 candidates, 1–26 of them correct; `id` is `ref:<n>` or `tied:<n>` |
| Candidate rows scored per pass | 8,977 (7,052 non-Ties + 1,925 Ties) |

Scoring, non-Ties (`utils.py:reroll_and_score_dataset`): each candidate gets an
independent score; the item is credited `1 / (number of candidates tied at the maximum)`
if the chosen candidate is at the maximum, otherwise `0`. It is **not** a strict
`chosen > all rejected` test — a two-way tie at the top scores 0.5.

Scoring, Ties (`utils.py:process_single_model`): a different formula entirely —
`0.30 * tied_accuracy + 0.30 * ref_accuracy + 0.20 * correctness_preferred +
0.20 * correctness_preferred_hard + 0.01 * correctness_margin_score`. Per-item results
are not defined for this subset; the upstream code sets them to `None`.

**This is the fact that reshapes the experiment.** A sequence-classifier reward model is
never asked a question. It is handed a (prompt, response) pair and emits a scalar. There
is no "did this follow the instruction?" to negate, and the four candidates are never
placed in an order, so candidate position cannot influence it. A generative judge is asked
a question, and that question can be negated — but only the generative path has one.

## 3. Hypotheses

Repeat rule, fixed in advance and applying to every hypothesis below: each condition is
run **5 times**; hypotheses are evaluated on the **pooled** item-level data across repeats,
and the per-repeat spread is reported alongside so that pooling cannot hide instability.

| ID | Prediction | Falsified by |
|---|---|---|
| H1 | The mean score shift under polarity inversion exceeds the shift under the **stability baseline** of §6.2, on at least 3 of the 5 non-Ties subsets | Polarity shift fails to exceed the baseline on 3 or more of the 5 non-Ties subsets |
| H2 | At least one evaluated model shows a polarity shift whose 95% bootstrap CI excludes 0 | Every evaluated model's CI includes 0 |
| H3 | **Both** of `shift(Safety) > shift(Math)` and `shift(Precise IF) > shift(Math)` hold, each with a 95% bootstrap CI on the paired difference that excludes 0 | The conjunction does not hold — including the case where exactly one of the two holds |
| H4 | At least one (model, subset) pair has an aggregate shift whose 95% CI **includes 0** while its item-level disagreement rate is **≥ 5%** | No such pair exists: every pair whose CI includes 0 has a disagreement rate below 5% |

*Item-level disagreement rate*: the fraction of items in that subset whose per-item score
differs between the two polarity conditions. Defined on the five non-Ties subsets only;
the Ties subset has no per-item score (§2), so H4 is not evaluated there and that
exclusion is reported.

**H1–H4 are predictions, not conclusions.** Results contradicting them are published
unchanged. H4 in particular is the point of the experiment: an aggregate that reads fine
while the underlying verdicts moved.

## 4. Metrics

- Primary: per-subset score on RewardBench 2 under (a) original phrasing,
  (b) polarity-inverted phrasing with correspondingly inverted decision rule
- Shift: paired difference, bootstrap CI resampled at **item** level, 10,000 resamples
- Baseline: §6.2, still open
- **Individual verdicts are retained**, not only aggregates

## 5. Harness validation gate — run before any perturbation

Reproduce published RewardBench 2 scores from `allenai/reward-bench-2-results`.

- **Pass**: absolute difference ≤ **0.02**, per subset and on the average
- **Fail**: investigate in this order — prompt template, chat template / special tokens,
  generation parameters, tie handling, dataset version
- **Exactly 0.000 difference**: treat as suspicious, not as success

That repository also publishes **per-item** scores (`eval-set-scores/`) for 188 of the 197
entries, so the gate is checked at item level as well as on the aggregate. Two aggregates
can agree while the underlying items disagree, which is the same failure this repository
exists to measure; checking only the total would be the mistake this experiment is about.

No perturbation result is reported until this gate passes.

### 5.1 What is available to validate against

197 published entries: **178 sequence classifiers, 18 generative judges, 1 custom
classifier.** Of the 18 generative judges, 16 are paid API models and the remaining two
(`ContextualAI/LMUnit-llama3.1-70b`, `ContextualAI/LMUnit-qwen2.5-72b`) are 70.6 B and
72.7 B parameters — 263 GB and 271 GB of weights.

So: **no open-weight generative judge that fits in 24 GB has a published score.** The
generative path cannot clear the gate in §5 on this hardware, and §8 forbids buying the
API models that could. Anything measured on the generative path is measured without a
published number to check it against, and must say so.

## 6. Open items — fixed before any run, in their own commit

### 6.1 How polarity inversion is implemented

The examples this document was first drafted with — "did this follow the instruction?"
against "did this violate the instruction?" — do not exist anywhere in this benchmark
(§2). The candidate implementations, with their costs, are enumerated in the report that
accompanies this commit. None is selected yet. Selecting one fixes:

- which code path the §5 gate validates, and whether that is the same path the experiment
  uses (a gate on a path the experiment does not run has validated nothing);
- whether the two polarities have equal chance level, and if not, how the difficulty
  difference is separated from the polarity effect.

### 6.2 What the shift in H1 is compared against

The original draft compared against candidate-order swap. That baseline does not exist on
the reward-model path: candidates are scored independently, so position bias is **exactly
zero by construction**, and H1 would be satisfied by any non-zero polarity shift whatsoever.
A baseline that cannot fail is not a baseline. H1 is therefore not decidable until §6.2
names a perturbation that (a) is defined on whichever path §6.1 selects and (b) can move
the score.

## 7. Construction rule for polarity pairs

- Inverting the question **must** invert the decision rule. Leaving the decision rule
  unchanged measures a scoring bug, not polarity sensitivity.
- Perturbations live in a **data file**, not in code, so a reader can inspect them.
- They are human-reviewed before the experiment runs. Any perturbation that changes
  meaning rather than only polarity is removed, and the removal is logged.

## 8. Stopping rules

- Models that do not fit in 24 GB, or that have no published score, are **not used for the
  gate** — with no comparison number, the harness cannot be validated.
- Any model or subset not run is **reported as not run**, with the reason and the count.
- If a CI includes 0, the result is written as **"cannot be said to shift"**, not as
  a small effect.
- Rankings between models are not asserted while their CIs overlap.
- exp01 ends at the measurement report. GRPO and reward hacking are a separate
  experiment with their own pre-registration.

## 9. What would make me abandon the claim entirely

If polarity inversion moves scores no more than the §6.2 baseline, and no model's CI
excludes 0, then the private observation does not generalize to open reward models.
That is written up as a negative result.

## 10. Cost constraint

Open-weight models on local hardware only. **No paid API.**
If the design starts to require a multiplicative number of paid calls, the experiment
stops and is redesigned — a sibling project was abandoned for exactly that reason.

Measured cost of one full pass over all 8,977 candidate rows, for one 8 B sequence-classifier
reward model on an RTX 4090 (bfloat16, batch size 8): **≈ 13 minutes**, from a measured
4,065 tokens/s and a measured 3,156,475-token corpus. The generative path has not been
timed; it is not the same order of magnitude and is not assumed to be.

---

## Results

*(left empty until measurements exist — filled in a separate commit)*
