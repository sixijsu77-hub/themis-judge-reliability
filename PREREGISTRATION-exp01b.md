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

**Judges.** This section asked for six. Seven candidates were screened by §4 and **five
passed**, so five is the number every count below uses; the shortfall is recorded in §11 and
is not backfilled with a judge chosen after seeing scores. The candidate pool is the
open-weight judges that RewardBench v1 published scores for and RewardBench 2 does not — the
runner still carries a `model_modifier` branch for each and all fit in 24 GB.

**Grid and cost**, at the measured 3.65 items/s and 46 s per model load:

| | what runs | passes | generations | hours |
|---|---|---|---|---|
| P0 | screen: 7 candidates × 150 items × 1 ordering | 7 | 1,050 | 0.2 |
| P1a | gradient: 5 judges × 4 levels × 150 items × 4 orderings | 80 | 12,000 | 1.9 |
| P1b | H3 only: 5 judges × 1,763 items × 4 orderings at `--obvious 3` | 20 | 35,260 | 2.9 |
| P2 | main: 5 judges × 1,763 items × 24 orderings | 120 | 211,560 | 17.6 |
| | | | | **22.7** |

P1a and P1b use the 4 orderings that place the correct answer in each slot; P2 uses all 24,
because separating position from distractor arrangement is the point of it.

**P1b exists because H3 cannot be decided on 150 items.** At `--obvious 3` the judge is right
on almost everything, so the statistic H3 reads — the share of *errors* landing in slot A —
has almost no errors to read. 150 items yield about 5. Simulated at this design, the rule
needs about 40 errors before it can exclude 0.25 against a strong bias, and 1,763 items yield
about 59. That is enough for a strong slot preference (98.0% at a true share of 0.50) and not
enough for a moderate one (40.1% at 0.35), so **a pass means no strong preference, not no
preference**, and the results will say it that way. Of the three ways out — accept "not evaluated", raise the item count,
or move H3 to an easier-to-decide difficulty — this takes the second. **The third was
rejected because every other difficulty is one where the pilot already shows the bias, so
moving H3 there is choosing the level at which it fails**, and the first leaves the claim in
§7 untestable. Fixed here, before anything runs.

**The four used by P1a and P1b are permutation indices 0, 6, 8, 9 — the only four that move the correct answer
through all four slots while holding the three distractors in one relative order**, and [`scripts/run_p1.py`](scripts/run_p1.py) imports
them from [`scripts/orderings.py`](scripts/orderings.py) rather than restating them, so the
set cannot drift from the one this section names. `V`
measured on any other four confounds where the correct answer sits with how the distractors
are arranged. The set used in the pilot behind this document was 0, 6, 14, 21, which does
not have that property; its `f_A` and `S` are unaffected, since those need only the correct
answer to visit each slot equally often, but its `V` mixes the two factors and is reported
as such. Enumerated by
[`scripts/check_decision_rules.py`](scripts/check_decision_rules.py) §5, and asserted again
at the top of every P1 run.

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
- **Error share at A** `E_A(m, d)` — among the verdicts judge `m` gets wrong at difficulty
  `d`, the fraction that name slot A

`E_A` has a null of **0.25**, and it comes from the construction, the same place `f_L`'s
0.25 does. The correct answer occupies slot A in exactly one of the four arrangements. In
that arrangement no error can land on A. In each of the other three, a judge with no slot
preference spreads its error over the three slots not holding the correct answer, so it hits
A with probability 1/3. With errors equally likely across arrangements the share is
`(3/4) x (1/3) = 0.25`.

`V` and `W` are the same quantity computed over different factors, which is what makes the
comparison in H4 meaningful.

- **The denominator of `f_L` is parsed verdicts only.** Unparseable ones are excluded from
  the letter frequencies and the parse rate is reported next to `f_L` at every difficulty.
  Counting them in would let a parse rate that rises with difficulty manufacture the very
  trend H1 tests, and one screened judge already produced unparseable verdicts
- Confidence intervals: bootstrap over **items**, 10,000 resamples, 95%
- Unparseable verdicts score 0 in the primary analysis and are reported separately; upstream
  credits them 0.25, which is chance under a four-way choice and would mask exactly this
  effect
- The judge's response text and parsed letter are retained per item

## 6. Hypotheses

| ID | Prediction | Falsified by |
|---|---|---|
| H1 | The least-squares slope of `f_A(m, d)` over the four difficulty levels, with `d` coded 0–3 and bootstrapped over items, is positive with a 95% CI excluding zero, for **at least 4** judges. Strict monotonicity of the four point estimates is reported alongside but is not the criterion | Fewer than 4 judges have a positive slope whose CI excludes zero |
| H2 | At `--obvious 0`, the 95% CI on `f_A(m)` excludes 0.25 for **at least 4** judges | Fewer than 4 exclude it |
| H3 | At `--obvious 3`, among the verdicts the judge got **wrong**, the share landing in slot A has a 95% CI, bootstrapped over items, containing 0.25, for **at least 4** judges. `n_err(m)` is reported beside it, and a judge whose `n_err(m)` is below 40 is **not evaluated** and cannot count toward the 4 | Fewer than 4 judges have a CI containing 0.25 — whether it excludes it upward, downward, or the judge could not be evaluated. Which of the three, and for whom, is reported |
| H4 | On P2, `V(m) > W(m)` for **at least 4** judges — where the correct answer sits matters more than how the distractors are ordered | `V(m) > W(m)` for fewer than 4 |
| H5 | Across the judges, `f_A` at `--obvious 0` is negatively rank-correlated with accuracy at `--obvious 0` — weaker judges fall back on slots more. **Direction only: no significance is claimed and none is tested** | The rank correlation is zero or positive |

H5 is the weakest of the five and is stated anyway. Six judges would be a poor sample for a
correlation, and five is worse; it is written here so the result cannot be presented as a
discovery afterwards.

**The denominator is five, not six, and the threshold stays at four.** The screen (§4)
passed five candidates, so "at least 4 of the 6" is read as "at least 4", which against five
judges is a stricter bar than the two-thirds it was written as — 80% rather than 67%. Taking
the stricter reading is deliberate: the alternative is to lower the threshold after seeing
how many judges survived, which is the move these clauses exist to prevent. Fixed here,
before P1 runs. H5's correlation is over five points.

**H1, H2 and H5 are decided by P1a; H3 by P1b; H4 needs P2.** P1a and P1b are one batch and
report together, so no hypothesis can be held back and produced later depending on which way
it came out.

**H3's two clauses are complements by construction, and that took a second pass.** The first
version paired "contains 0.25 for at least 4" with "excludes 0.25 upward for 2 or more",
which leaves a judge whose interval sits *below* 0.25 — one that steers its errors away from
the first slot — satisfying neither clause. The falsification clause is now literally "not
the prediction", and the direction of every exclusion is reported so the two-sided case is
still visible.

**H1–H5 are predictions, not conclusions.** Any of them coming out wrong is published
unchanged. H3 is the one this repository would most like to be true and is therefore the one
to distrust.

### Why these rules and not the ones drafted first

Three of the five were rewritten before anything ran, because simulating them showed they
could not decide anything. The simulations are in
[`scripts/check_decision_rules.py`](scripts/check_decision_rules.py) and their output in
[`results/validation/decision_rules.txt`](results/validation/decision_rules.txt).

`S` was abandoned twice, in opposite directions, and the second time is the instructive one.
It is a maximum minus a minimum over four proportions, so it is positive even for an
unbiased judge: at this design's item count its null median is 0.0400 and its 95th
percentile 0.0750, which puts the first draft's fixed threshold of 0.05 at the 69th
percentile of the noise. Read loosely that rule passed an unbiased judge 99.3% of the time
and a weakly biased one 55.6%; read strictly it passed the unbiased judge 0.0%.

Comparing `S` to its own null looked like the fix — 95.6% for an unbiased judge against
30.7% for a weakly biased one. It is not, because `S` has a ceiling this design imposes.
The correct answer visits all four slots equally, so correct verdicts contribute equally to
every letter and only errors can move `S`. Send every error to one slot and the largest `S` reachable
from the accuracies actually observed is **0.0083 at `--obvious 3`**. That is below the
null's own 95th percentile of 0.0750, **so at the level where H3 is asked the rule cannot
fail** — the same defect as before with the sign reversed. Ceilings by level: 0.0083,
0.3084, 0.4850 and 0.5817, against 5, 113, 208 and 288 errors.

`E_A` replaces it because errors are the only thing carrying signal here, so it conditions
on them instead of letting them be diluted by a near-perfect accuracy.

The simulated nulls draw the four arrangements of an item independently, and the slope
power no longer does. Measured on the pilot, the within-item correlation of the "answered A"
indicator is 0.0000 at `--obvious 3`, `2` and `1`, and 0.1227 at `--obvious 0`, where the
design effect is 1.368 and 600 verdicts behave like 439. H3 is evaluated at `--obvious 3`,
where the assumption holds. Where it does not, intervals are widened by the measured design
effect and that is stated with the result.

Strict monotonicity over four noisy points was the H1 criterion. On a shallow but real
trend one judge clears it 61.8% of the time and four of five clear it 36.9% — the rule
discards well over half of a true effect. A fitted slope on the same data, drawn with the
measured within-item correlation rather than assuming independence, clears it 93.0% and
95.8%. Both reject the flat world at about 4%. P1a exists because we do not know whether the
effect is as large as the pilot's, and the first rule only worked if it was.

## 7. What would make this claim collapse

If `E_A(m, 3)` is already above 0.25 with an interval excluding it upward — the judges send their
errors to the first slot even where the answer is obvious — then this is a standing
preference, already documented elsewhere, and the "falls back under load" framing is wrong.
The finding would reduce to a magnitude measurement on one benchmark, which is worth
publishing and is a much smaller thing.

If `V(m)` at `--obvious 0` is under 0.10 for most judges, the pilot's 0.5533 was one model's
quirk and the leaderboard implication does not hold.

**What P2 becomes if H3 fails, decided now.** P2 costs 17.6 hours and the only hypothesis it
adds is H4 — whether the correct answer's position matters more than the distractors'
arrangement. If H3 fails, the framing this repository would build on it is gone and what
remains is a magnitude measurement, which does not need six samples per position:

- **H3 holds** — P2 runs as specified: the five judges, 1,763 items, all 24 orderings.
  120 passes, 17.6 hours
- **H3 fails** — P2 runs at the four fixed-distractor orderings only, 1,763 items, same
  judges. 20 passes, 2.9 hours. H4 is then reported as **not evaluated**, with the reason,
  rather than tested on data that cannot separate its two factors
- **H3 not evaluated** — treated as failing for this purpose. A rule that could not fire is
  not a rule that passed

Written before P1 so the scope cannot be chosen to match the result.

## 8. Stopping rules

- No judge is added or dropped after P0 except by §4's criteria, and every candidate's
  numbers are reported
- A CI including the null value is written as **"cannot be said to differ"**, never as a
  small effect
- Rankings between judges are not asserted while their intervals overlap
- If P1a contradicts the pilot — no gradient, or a gradient in the other direction — P2 does
  not run until that is understood, and the contradiction is reported either way
- **No further control set is built.** The four difficulty levels are the ones in the
  previous pre-registration, unchanged, and searching for a difficulty at which an effect
  appears is the failure this clause exists to prevent

## 9. Cost constraint

Open weights on local hardware. **No paid API.** 22.7 GPU-hours at the measured rate. If a
judge turns out to run more than twice as slowly as the pilot, its P2 is cut to the 4
position-orderings and the reduction is reported rather than absorbed.

---

## Results

### P0 — judge screen: **five of seven candidates pass**

150 unmodified benchmark items, one arrangement, upstream's prompt. Raw per-item logs
including the judge's own text: [`results/validation/screen/`](results/validation/screen).
Table printed by [`scripts/summarize_screen.py`](scripts/summarize_screen.py) into
[`results/validation/screen_summary.txt`](results/validation/screen_summary.txt).

```
  candidate                                   n  accuracy  unparsed    rate  verdict
  Skywork/Skywork-Critic-Llama-3.1-8B       150    0.9067         0    0.0%  PASS
  Qwen/Qwen2.5-7B-Instruct                  150    0.8533         0    0.0%  PASS
  ZiyiYe/Con-J-Qwen2-7B                     150    0.7800         0    0.0%  PASS
  R-I-S-E/RISE-Judge-Qwen2.5-7B             150    0.7400         0    0.0%  PASS
  NCSOFT/Llama-3-OffsetBias-8B              150    0.5500        10    6.7%  PASS
  prometheus-eval/prometheus-7b-v2.0        150    0.3617        97   64.7%  FAIL
  AtlaAI/Selene-1-Mini-Llama-3.1-8B           —         —         —       —  DID NOT RUN
```

**§3 said six judges and five is what there is.** The shortfall is reported rather than
made up by adding a judge chosen after seeing scores.

`prometheus-7b-v2.0` fails on format, not on judgment: 97 of its 150 verdicts cannot be
parsed. Its 0.3617 is inflated by the 0.25 those failures are credited, and is not evidence
of anything. It is trained to rate one response at a time, not to pick among four.

`Selene-1-Mini` never produced a number. Upstream's own `model_modifier == "Atla"` branch
calls `LLM.generate(prompt_token_ids=...)`, an argument `vllm==0.13.0` — the version
upstream pins — does not accept. **This is a defect in the evaluator, not the judge**, and
belongs with the five already filed.

Two of the seven declare a 131072-token context. vLLM reserves KV cache for one request at
that length, 16 GiB of it, and that does not fit beside the weights on a 24 GB card, so the
engine refuses to start. Upstream's flag for this is commented out, so the patch adds
`--max_model_len`. It is set to 16384, which is 2.6x the most a request in this set can need
— the longest four-way prompt is 4294 tokens and generation is capped at 2048. The declared
lengths and the measurement are printed by the summary script.

**Not established, and one claim retracted.** These are one arrangement each on 150 items.
Paired bootstraps over the same items put every adjacent pair's interval across zero except
the last: `Skywork-Critic − Qwen2.5-7B-Instruct` is `+0.0533` with 95% CI
`[-0.0067, +0.1133]`, and only `RISE-Judge − OffsetBias` at `+0.1900 [+0.1050, +0.2750]`
excludes it. §8 forbids asserting a ranking while intervals overlap, and a verbal report of
these results asserted one anyway — that a judge RewardBench 2 dropped beats a general
instruct model. **It does not, at this sample size.** Retracted here.

The same selectivity applies to the leaderboard-gap argument. `prometheus-7b-v2.0`, from the
same pool of judges v1 published and v2 does not, fails on format with 97 of 150 verdicts
unparseable — which is a reason to leave it out, not an omission to complain about. Both
directions belong in that argument or neither does.

*(P1a onward filled in as they run)*
