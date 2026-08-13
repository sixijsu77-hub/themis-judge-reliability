# Pre-registration — exp01b: When a judge stops judging and starts counting slots

**Committed before any of it is run.** The git timestamp is the evidence. Predictions here
are not edited after results exist; a wrong one stays, and the result section says it was
wrong.

Status: **binding as of this commit. Nothing below has been measured.**

The measurements that motivated this are in
[`docs/findings/0002-position-fallback.md`](docs/findings/0002-position-fallback.md), and
the decision to make it the primary axis — with what that decision costs — is in
[`docs/decisions/0002-changing-the-primary-axis.md`](docs/decisions/0002-changing-the-primary-axis.md).
The polarity experiment that came first keeps its own file,
[`PREREGISTRATION.md`](PREREGISTRATION.md), including the hypotheses it could not decide.

---

## 1. Question

A four-way judge that answers correctly regardless of where the correct answer sits is doing
the job. One that answers `[[A]]` more often as the question gets harder has stopped judging
and started guessing by slot, and its benchmark score is then partly a measure of that habit
rather than of its judgment.

The pilot behind this saw exactly that in one judge: uniform letter choice on items whose
answer is obvious, and 56.5% `[[A]]` against 8.8% `[[D]]` on unmodified benchmark items,
under a prompt that instructs it to avoid position bias. **Position sensitivity in LLM
judges is a documented phenomenon and we claim no discovery of it.** What is open is how
large it is on this benchmark, whether it is a standing preference or something that appears
under load, and whether it differs enough between judges to distort a leaderboard.

## 2. Why this axis and not the one before it

The experiment this repository started with perturbed the judge's *prompt*, which meant
every effect was partly a property of a sentence we wrote. Two rounds of fixing ambiguity
did not close it, and the residual is recorded in the previous pre-registration.

**Here the prompt never changes.** Every run uses upstream's `prompt_v2` verbatim
([`prompts/polarity_original.txt`](prompts/polarity_original.txt), extracted from the
evaluator by AST rather than retyped). What varies is where the candidates sit and how hard
the item is. Neither is authored by us: the arrangement is a permutation, and the difficulty
grading substitutes responses that already exist in the dataset.

That is the structural reason this axis is sounder, and it is worth more than the effect
being larger.

## 3. Design

**Prompt.** One condition. Upstream's four-way ranking prompt, unmodified.

**Arrangement.** All 24 orderings of the four candidates, via
[`harness/run_generative_v2.patch`](harness/run_generative_v2.patch). The 24 factor into 4
positions for the correct answer × 6 orderings of the three distractors, which separates
*where the correct answer sits* from *which distractor sits where*. Upstream's own sampler
reaches only 4 of the 24 and cannot separate them.

**Difficulty.** Four levels built by
[`scripts/build_control_set.py`](scripts/build_control_set.py) on the same 150 items:
`--obvious 3, 2, 1, 0` replaces three, two, one or none of the distractors with responses to
a different question. `--obvious 0` is the unmodified benchmark item. Seed 0; the drawn
indices are committed.

**Judges.** Six, screened by §4. The candidate pool is the open-weight judges that
RewardBench v1 published scores for and RewardBench 2 does not — the runner still carries a
`model_modifier` branch for each and all fit in 24 GB — plus general instruct models if
fewer than six survive the screen.

**Grid and cost**, at the measured 3.65 items/s and 46 s per model load:

| | what runs | passes | generations | hours |
|---|---|---|---|---|
| P0 | screen: 6 candidates × 150 items × 1 ordering | 6 | 900 | 0.1 |
| P1 | gradient: judges × 4 levels × 150 items × 4 orderings | 96 | 14,400 | 2.3 |
| P2 | main: judges × 1,763 items × 24 orderings | 144 | 253,872 | 21.2 |
| | | | | **23.6** |

P1 uses the 4 orderings that place the correct answer in each slot, because the gradient it
measures is over that position and six samples per position buy little there. P2 uses all 24
because separating position from distractor order is the point of it.

**Ties is excluded**: its scoring path is the pointwise ratings prompt, where no arrangement
exists. Coverage is 5 of 6 subsets, 1,763 of 1,865 items, stated as a count in the results.

## 4. Judge screen, fixed before it runs

A judge enters P1 and P2 if, on 150 items at one ordering under the unmodified prompt:

1. its unparseable-verdict rate is ≤ 10%, and
2. its accuracy is above 0.30.

The second criterion is new and needs its reason: a judge at chance has no judgment for
position to displace, so it cannot inform the question. 0.30 is 5 points above the 0.25
chance level and is fixed here rather than after seeing the six numbers.

Every candidate's screen numbers are reported, including those that fail. If fewer than six
survive, the count is reported and the shortfall is not backfilled with judges chosen for
their scores.

## 5. Metrics

Let `f_L(m, d)` be the fraction of items on which judge `m` emits letter `L` at difficulty
`d`, pooled over arrangements. The correct answer sits in each slot equally often by
construction, so an unbiased judge gives `f_L = 0.25` for every `L`.

- **First-slot rate** `f_A(m, d)`
- **Slot skew** `S(m, d) = max_L f_L − min_L f_L`, zero for an unbiased judge
- **Accuracy spread** `V(m, d) = max_p acc(m, d, p) − min_p acc(m, d, p)` over the four
  positions `p` of the correct answer
- **Distractor-order spread** `W(m, d)` — the same statistic computed within a fixed
  position over its six distractor orderings, available from P2 only

`V` and `W` are the same quantity computed over different factors, which is what makes the
comparison in H4 meaningful.

- Confidence intervals: bootstrap over **items**, 10,000 resamples, 95%
- Unparseable verdicts score 0 in the primary analysis and are reported separately; upstream
  credits them 0.25, which is chance under a four-way choice and would mask exactly this
  effect
- The judge's response text and parsed letter are retained per item

## 6. Hypotheses

| ID | Prediction | Falsified by |
|---|---|---|
| H1 | `f_A(m, d)` rises monotonically as difficulty rises from `--obvious 3` to `--obvious 0`, for **at least 4 of the 6** judges | It fails to rise monotonically for 3 or more of the 6 |
| H2 | At `--obvious 0`, the 95% CI on `f_A(m)` excludes 0.25 for **at least 4 of the 6** judges | Fewer than 4 exclude it |
| H3 | At `--obvious 3`, the 95% CI on `S(m)` includes 0.05 or less for **at least 4 of the 6** judges — the bias is not a standing preference | Fewer than 4 |
| H4 | On P2, `V(m) > W(m)` for **at least 4 of the 6** judges — where the correct answer sits matters more than how the distractors are ordered | `V(m) > W(m)` for fewer than 4 |
| H5 | Across the six judges, `f_A` at `--obvious 0` is negatively rank-correlated with accuracy at `--obvious 0` — weaker judges fall back on slots more | The rank correlation is zero or positive |

H5 is the weakest of the five and is stated anyway. Six judges is a poor sample for a
correlation, and it is written here so the result cannot be presented as a discovery
afterwards.

**H1–H5 are predictions, not conclusions.** Any of them coming out wrong is published
unchanged. H3 is the one this repository would most like to be true and is therefore the one
to distrust.

## 7. What would make this claim collapse

If `S(m, 3)` is already large — the judges prefer the first slot even where the answer is
obvious — then this is a standing preference, already documented elsewhere, and the "falls
back under load" framing is wrong. The finding would reduce to a magnitude measurement on
one benchmark, which is worth publishing and is a much smaller thing.

If `V(m)` at `--obvious 0` is under 0.10 for most judges, the pilot's 0.5533 was one model's
quirk and the leaderboard implication does not hold.

## 8. Stopping rules

- No judge is added or dropped after P0 except by §4's criteria, and every candidate's
  numbers are reported
- A CI including the null value is written as **"cannot be said to differ"**, never as a
  small effect
- Rankings between judges are not asserted while their intervals overlap
- If P1 contradicts the pilot — no gradient, or a gradient in the other direction — P2 does
  not run until that is understood, and the contradiction is reported either way
- **No further control set is built.** The four difficulty levels are the ones in the
  previous pre-registration, unchanged, and searching for a difficulty at which an effect
  appears is the failure this clause exists to prevent

## 9. Cost constraint

Open weights on local hardware. **No paid API.** 23.6 GPU-hours at the measured rate. If a
judge turns out to run more than twice as slowly as the pilot, its P2 is cut to the 4
position-orderings and the reduction is reported rather than absorbed.

---

## Results

*(empty until measurements exist — filled in a separate commit)*
