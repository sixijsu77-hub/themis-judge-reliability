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
on almost everything, so the statistic H3 reads — the share of errors landing in slot A, on
the arrangements where an error *can* land there — has almost no errors to read. 150 items
give the pilot judge 5 errors, of which 4 are usable. Simulated at this design, the rule needs
about 40 usable errors before it can exclude 1/3 against a strong preference, and 1,763 items
would give that judge about 47. That is enough for a strong preference (91.1% at a true share
of 0.60) and not enough for a moderate one (30.7% at 0.45), so **a pass means no strong
preference, not no preference**, and the results will say it that way.

**A judge better than the pilot may have too few errors even at 1,763 items, and that is
recorded now rather than discovered later.** `n_err*` scales with `1 − a` at `--obvious 3`,
where every judge is near ceiling: the pilot judge's 0.9917 gives about 47 and an accuracy of
0.995 would give 26. P1b runs for all five judges regardless, each judge's `n_err*` is
printed, and the results table separates **"not evaluated — too few errors"** from
**"evaluated and failed"**. Neither is called a pass.

**H1's slope is fitted only over the levels where its statistic has a denominator.**
`E*_A` at `--obvious 3` rests on the handful of errors a near-perfect judge makes — 4 for the
pilot judge on 150 items — and a point estimate from four draws would swing the fit
arbitrarily. The slope is therefore fitted over the levels with `n_err* >= 40`, at least
three of which are required; a judge with fewer than three qualifying levels is **not
evaluated** for H1. The all-four-level fit is printed beside it and is not the criterion.
Fixed here because the qualifying set is a property of each judge's accuracy, not of its
slope, and waiting to see which choice helps would be a choice.

**`--obvious 3` is measured twice, and the two are not pooled.** P1a's 150 items are the same
items that carry the other three difficulty levels, which is what a paired slope needs; P1b's
1,763 are a different draw with different distractors, built for H3 alone. **H1's gradient
uses P1a only.** P1b's `--obvious 3` numbers are printed beside P1a's as a consistency check
and enter no slope. Fixed here so the choice cannot be made after seeing which pairing helps. Of the three ways out — accept "not evaluated", raise the item count,
or move H3 to an easier-to-decide difficulty — this takes the second. **The third was
rejected because every other difficulty is one where the pilot already shows the bias, so
moving H3 there is choosing the level at which it fails**, and the first leaves the claim in
§7 untestable. Fixed here, before anything runs.

**Amended 2026-08-15, after P1a and before it was re-run: the arrangement set is
`0, 9, 16, 18`.** The reason is not that P1a's numbers were unwelcome — H1 passed on them —
but that the statistic H1, H2 and H5 read was confounded with the control set's construction,
which two tables show and neither depends on any result. On the old set slot A holds the
first distractor in all three arrangements where an error at A is possible, and
`build_control_set.py` writes the off-topic substitutes first, so that distractor is
obviously wrong at `--obvious 3, 2, 1` and plausible at `0`. A statistic reading slot A
therefore steps when the control set changes what sits there, with the judge unchanged — and
that step is what H1's positive slope was. The requirement should have been that **every slot
holds every candidate equally often**, so that naming a slot says nothing about which
candidate was named. 24 of the 10,626 four-element subsets satisfy it and 3 of those also
keep the distractors in one cyclic order; `0, 9, 16, 18` is the first.
[`scripts/arrangement_sets.py`](scripts/arrangement_sets.py) enumerates all of it.

**What the new set costs.** The distractors are permuted between its arrangements, so an
accuracy spread over it mixes position with distractor arrangement — the objection that
produced the old set. The paired difference between two slots named in advance is unaffected,
because both arrangements hold the same four candidates, and it is what the results lead
with. Only P2's 24 arrangements are clean on both counts.

**P1a on the old set is kept and reported as a confounded measurement.** Two arrangement sets
disagreeing about the same statistic is itself a result, and deleting the first one would
throw it away.

**The old four are permutation indices 0, 6, 8, 9 — the only four that move the correct answer
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

**The screen ran at one arrangement, and it was the worst one it could have been.** Its
metadata records `ordering 0` — permutation `(0, 1, 2, 3)`, the correct answer at slot A on
all 150 items, for every candidate. So its accuracy is arithmetically the rate of answering
`[[A]]`: 0.9067 accuracy against 136 `A` verdicts for `Skywork-Critic`, 0.8533 against 128
for `Qwen2.5-7B-Instruct`, and so on, exact for the five that parse cleanly.
**Judges were selected by how often they say A, which is the axis this experiment measures.**

The same 150 items at the other three positions are in the P1c `--obvious 0` runs, so the
screen can be re-scored where it never ran, at no cost
([`results/validation/screen_summary.txt`](results/validation/screen_summary.txt)):

| candidate | screen | ans@A | ans@B | ans@C | ans@D | passes at A B C D |
|---|---|---|---|---|---|---|
| `Skywork-Critic-Llama-3.1-8B` | 0.9067 | 0.9067 | 0.7867 | 0.3000 | 0.2867 | Y Y **n n** |
| `Qwen2.5-7B-Instruct` | 0.8533 | 0.8533 | 0.5467 | 0.4000 | 0.2533 | Y Y Y **n** |
| `Con-J-Qwen2-7B` | 0.7800 | 0.7800 | 0.5933 | 0.5067 | 0.5533 | Y Y Y Y |
| `RISE-Judge-Qwen2.5-7B` | 0.7400 | 0.7333 | 0.7000 | 0.6467 | 0.6333 | Y Y Y Y |
| `Llama-3-OffsetBias-8B` | 0.5500 | 0.5333 | 0.7000 | 0.7733 | 0.7800 | Y Y Y Y |

**Two of the five would not have passed §4's own threshold had it run at a different
position**, and the ranking inverts: the judge the screen placed last is first at C and at D,
and the judge it placed first is fourth at D. This is recorded in §11 as a limitation of the
experiment, not as a footnote to the screen, because the selection step and the measurement
sit on one axis.

## 5. Metrics

Let `f_L(m, d)` be the fraction of parsed verdicts on which judge `m` emits letter `L` at
difficulty `d`, pooled over arrangements, `a_p` its accuracy on the arrangements whose
correct answer sits at slot `p`, and `a` the accuracy pooled over the four.

### The identity these metrics have to respect

A verdict naming A is one of exactly two things: a correct verdict on the arrangement whose
answer is at A, or an error on one of the other three. Writing `E_A` for the share of wrong
verdicts that name A, and using that the total error mass is `4(1 − a)`,

    f_A = (1/4) a_A + E_A (1 − a)                                          [1]

and where the per-slot accuracies happen to be equal,

    f_A − 1/4 = (1 − a) (E_A − 1/4)                                        [2]

[1] assumes only that the correct answer occupies each slot equally often, which the design
guarantees, and that every term is computed over parsed verdicts. [2] additionally assumes
accuracy does not depend on where the answer sits — which is the thing under test — so [2] is
used for reading and [1] for measuring. Checked against the pilot to floating-point
in [`results/validation/decomposition.txt`](results/validation/decomposition.txt) §1.

**[1] is why the first draft of these metrics could not do its job.** At fixed `E_A`,
`d f_A / d a = 1/4 − E_A`, so any judge with `E_A > 1/4` shows a rising `f_A` as it gets less
accurate *without its error placement changing at all*. A rise in `f_A` with difficulty is
therefore not evidence of a judge falling back on position; it is what the identity produces
when accuracy falls. Simulated at three fixed placements in §2 of the same file.

### The metrics

- **First-slot rate** `f_A(m, d)` — **reported, not tested against 0.25.** Its null is
  `(1/4) a_A + (1/12) Σ_{p≠A} (1 − a_p)`, which is 0.25 only when the per-slot accuracies are
  equal. On the pilot that null runs 0.2506, 0.2928, 0.3344, 0.3611 across the four levels,
  so 0.25 is the right threshold at exactly one of them
- **Conditional first-slot error share** `E*_A(m, d)` — **the primary statistic.** Among the
  wrong verdicts on the three arrangements whose correct answer is *not* at A, the share that
  name A. **Its null is exactly 1/3 and does not move with the per-slot accuracies**
- **Error share at A** `E_A(m, d)` — reported for continuity with [1]; **not tested.** Its
  null is `(1/3) × (share of error mass on arrangements whose answer is not at A)`, which is
  `1/4` only under equal per-slot accuracy
- **Slot skew** `S(m, d) = max_L f_L − min_L f_L` — reported. Under equal per-slot accuracy
  `S = (1 − a) × (max_L E_L − min_L E_L)`, so it is an error-placement statistic scaled by the
  error rate, and it inherits the same confound
- **Accuracy spread** `V(m, d) = max_p acc(m, d, p) − min_p acc(m, d, p)` over the four
  positions `p` of the correct answer. **This one needs no null at all** — it compares a
  judge to itself on identical items — and it is the least assumption-laden thing here
- **Distractor-order spread** `W(m, d)` — the same statistic within a fixed position over its
  six distractor orderings, available from P2 only

### Why `E_A` was replaced by `E*_A`

`E_A`'s null is 0.25 only if the error mass is spread evenly over the four arrangements. On
the pilot it is not, and it fails in the direction that matters: the judge is most accurate
when the answer is at A (0.9933, 0.9400, 0.9067, 0.8533 by level) and least when it is at D,
so little error lands on the one arrangement where an error *cannot* name A. That pushes
`E_A`'s null to 0.2667, 0.3068, 0.3109, 0.3079 — **above 0.25, the same direction as the
hypothesis.** Testing against 0.25 would score part of the position effect as if it were
evidence for the position effect.

`E*_A` drops that arrangement. It is a weighted average of `q_(p→A)` over the three
arrangements where an error can name A, and under the null every one of those is 1/3, so any
weighting gives 1/3. Measured on the pilot the null is 1/3 at all four levels, by
construction rather than by luck ([`decomposition.txt`](results/validation/decomposition.txt)
§4).

`V` and `W` are the same quantity computed over different factors, which is what makes the
comparison in H4 meaningful.

### What `E*_A` cannot separate on P1, recorded before the results

The four arrangements P1 uses hold the three distractors in one relative order, which is
what makes `V` clean. It has a cost on the other side. In every arrangement where an error
*can* name A — the three whose correct answer is elsewhere — the first distractor is the
thing sitting at A. **So on P1, "the judge sent its error to the first slot" and "the judge
sent its error to the first distractor" are the same count**, and `E*_A` cannot tell them
apart. The same holds at D for the third distractor; B and C are separable. Enumerated by
[`scripts/check_slot_confound.py`](scripts/check_slot_confound.py).

`V` is untouched by this: it compares the same items with the same distractors in the same
order, and only the correct answer moves. Separating position from candidate identity for
the *error placement* needs the six distractor orderings within a position, which is P2 and
only P2 — the same separation H4 is about.

**H1, H2, H3 and H5 are not changed for this.** They read what they read, and the results
say so. **The reservation is not the same at every difficulty, and lumping them would
understate the result as badly as overstating it would.**

The alternative reading — that the judge is picking a *candidate* rather than a *slot* —
requires the judge to be able to tell the first distractor from the other two. It sees the
question and four answer texts labelled A to D, with no index, no provenance and no name, so
the only thing it can act on is the text. Whether the text differs by list position is a
question about the control set and is measured by
[`scripts/check_exchangeable.py`](scripts/check_exchangeable.py), which permutes the three
position labels within each item — the exact null that position says nothing — over 20,000
shuffles:

| level | how the distractors are drawn | characters | words | exchangeable |
|---|---|---|---|---|
| `--obvious 3` (1,763 items, H3's set) | all three off-topic, drawn the same way | p = 0.7490 | p = 0.7071 | **yes** |
| `--obvious 3` (150 items) | as above | p = 0.3301 | p = 0.3256 | yes |
| `--obvious 2` | two off-topic, one own | p = 0.1073 | p = 0.1065 | not rejected |
| `--obvious 1` | one off-topic, two own | p = 0.0006 | p = 0.0001 | **no** |
| `--obvious 0` | all three the item's own | p = 0.0294 | p = 0.0163 | **no** |

**So the reservation is withdrawn at `--obvious 3` and kept at `--obvious 1` and `0`.** At
`--obvious 3` the three distractors are drawn identically and test as indistinguishable on
every property measured, so there is no first distractor for a judge to prefer, and **H3's
falsification is a statement about slots.** At `--obvious 0` and `1` the list position
predicts length — the off-topic substitutes are the shorter ones and they are written
first — so a judge acting on length alone would produce what looks like a slot preference,
and **H2's falsification and H5's correlation carry the reservation in full.** At
`--obvious 2` the test does not reject exchangeability and does not establish it either; it
is reported as undetermined.

### The control set orders its distractors, which confounds every letter-based statistic

Found on the fourth judge of P1a, recorded here before P1a finished.
[`scripts/build_control_set.py`](scripts/build_control_set.py) writes
`[foreign] * obvious + [own rejected] * (3 - obvious)`, so **the plausible distractors are
always at the end of the list**, and the four arrangements hold the list in one relative
order. A judge that prefers the hardest distractor therefore produces a letter distribution
that looks like a slot preference, and the apparently preferred slot moves between difficulty
levels because the hard distractor moves. Measured: at `--obvious 2`, three of the four
judges send 113, 151 and 162 errors to the third distractor and 0 to 3 to the first.

**What this reaches.** Everything counted by which letter the judge emitted — `f_A`, `S`,
`E_A`, `E*_A`, and therefore H1, H2, H3 and H5. The damage is worst for H1, whose whole
subject is a gradient across difficulty levels, because the distractor composition changes
across those levels by construction. H3 at `--obvious 3` is the least affected: there all
three distractors are foreign and the list is homogeneous.

**What it does not reach.** Anything counted by accuracy. `V`, the paired first-versus-last
difference, and H4 compare arrangements holding the same four candidates, so a
distractor-quality effect is present in both and cancels. It also does not reach the
within-candidate contrast below.

**No hypothesis is rewritten and no run is repeated.** H1, H2, H3 and H5 are decided as
registered and reported with this stated, because a rule rewritten after seeing four judges
is not a rule. What changes is which number the results lead with.

### Position, with the candidate held fixed

Each distractor visits two slots across the four arrangements — the first visits A and B, the
second B and C, the third C and D. Asking how often *the same candidate* is named in one slot
versus the other holds its content fixed and varies only where it sits, so neither the
ordering defect above nor the slot/candidate confound before it applies. The null is a ratio
of 1. [`scripts/within_candidate.py`](scripts/within_candidate.py) reports it at every level
for every judge, and it is the statistic the results lead with. **It decides no hypothesis:
none of H1–H5 reads it, and none is added for it.**

### `E*_A` reads one slot, and a judge can be biased toward another

Nothing in H1, H2, H3 or H5 would fire for a judge that sends its errors to the second slot
instead of the first: `E*_A` would sit at 1/3 while the error distribution was nowhere near
uniform. The A-specific form was chosen from a pilot whose bias was toward A, and that is a
choice made from one judge. The full conditional distribution of errors over the four slots
is therefore **reported at every level for every judge**, beside the hypothesis it does not
decide, so a judge of that shape is visible in the results rather than scored as unbiased.
No hypothesis is added for it: adding one after seeing a judge would be the move these
clauses exist to prevent, and the report is what an honest reading needs.
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
| H1 | The least-squares slope of `E*_A(m, d)` over the four difficulty levels, with `d` coded 0–3 so that `d` rises as the item gets harder and bootstrapped over items, is positive with a 95% CI excluding zero, for **at least 4** judges. The slope of `f_A` is reported beside it, decomposed into its accuracy and placement terms | Fewer than 4 judges have a positive `E*_A` slope whose CI excludes zero |
| H2 | At `--obvious 0`, the 95% CI on `E*_A(m)` excludes 1/3 upward for **at least 4** judges. `f_A` against its own per-judge null is reported beside it as the magnitude a published score would carry | Fewer than 4 exclude 1/3 upward |
| H3 | At `--obvious 3`, the 95% CI on `E*_A(m)`, bootstrapped over items, contains 1/3 for **at least 4** judges. `n_err*(m)` — wrong verdicts on the three arrangements whose answer is not at A — is reported beside it, and a judge with `n_err*(m) < 40` is **not evaluated** and cannot count toward the 4 | Fewer than 4 judges have a CI containing 1/3 — whether it excludes it upward, downward, or the judge could not be evaluated. Which of the three, and for whom, is reported |
| H4 | On P2, `V(m) > W(m)` for **at least 4** judges — where the correct answer sits matters more than how the distractors are ordered | `V(m) > W(m)` for fewer than 4 |
| H5 | Across the judges, `E*_A` at `--obvious 0` is negatively rank-correlated with accuracy at `--obvious 0` — weaker judges place a larger share of their errors on the first slot. **Direction only: no significance is claimed and none is tested** | The rank correlation is zero or positive |

H5 is the weakest of the five and is stated anyway. Six judges would be a poor sample for a
correlation, and five is worse; it is written here so the result cannot be presented as a
discovery afterwards.

### What changed in each hypothesis, and what died with it

Every one of these moved off `f_A` and onto `E*_A`. Saying only that would hide which
hypothesis lost what, so:

- **H1 lost its subject.** It asked whether a judge falls back on position *more* as items get
  harder. Identity [1] makes `f_A`'s slope positive whenever `E_A > 1/4` and accuracy falls,
  with the judge's placement of errors entirely unchanged, so the old H1 could be satisfied by
  a judge whose behaviour never varied. On `E*_A` it asks the intended question. The `f_A`
  slope is still reported, split into `(1/4)Δa_A`, `−E*_A(0)·Δa` and `(1 − a)·ΔE*_A`, because
  the first two are what a published score actually absorbs
- **H2 lost its threshold, not its subject.** `f_A ≠ 0.25` is a fact about letter frequencies
  and 0.25 is only its null under equal per-slot accuracy, which is false here. Restated on
  `E*_A` against 1/3, and `f_A` against its own per-judge null is reported as the magnitude,
  since that is the quantity a leaderboard carries
- **H3 lost its null.** 0.25 was derived assuming errors are spread evenly over the four
  arrangements. That assumption is false on the pilot and false in the hypothesis's own
  direction. 1/3 on the conditional share needs no such assumption. The denominator shrinks
  by about a quarter, so the `n_err` floor is restated on `n_err*`
- **H4 is unchanged.** `V` and `W` are accuracy spreads over identical items and neither needs
  a null
- **H5 was very nearly a tautology.** Under [2], `f_A = E_A + a(1/4 − E_A)`, so if every judge
  has `E_A > 1/4` then `f_A` *must* fall as accuracy rises, and a negative rank correlation
  between them would have come out of the algebra rather than out of the judges. On `E*_A` it
  asks whether a weaker judge has a stronger preference, which is the claim that was meant

### H5 keeps pooled accuracy as its axis

Decided 2026-08-15. H5 correlates `E*_A` with accuracy, and the accuracy it uses is pooled
over the four arrangements of the same `--obvious 0` verdicts that produced `E*_A`. There are
two candidate axes and they disagree in sign:

| axis | Spearman rho with `E*_A` |
|---|---|
| pooled accuracy over the four positions — **registered** | **−1.0000** |
| accuracy with the answer at A, which is the screen's axis | **+0.9000** |

The screen's axis is the contaminated one and §4 says why: answering `A` is scored correct
there, so a first-slot pull raises it by definition. Pooled accuracy is the least sensitive
of the axes available — simulated at fixed skill while only the slot weights move, it spans
0.0813 against 0.5059 for the screen's axis and 0.2078 for the average of B, C and D — and it
is **symmetric in direction**: a pull toward D lowers it exactly as much as a pull toward A,
while `E*_A` is directional. So the mechanism that would manufacture a correlation pushes the
wrong way, and `Llama-3-OffsetBias-8B` is the case that shows it — lowest `E*_A` and highest
pooled accuracy, which the mechanical account cannot produce.

**No axis in this design is free of the position pull**, because accuracy is "did it name the
slot holding the answer" and the pull is about slots. Pooled accuracy is chosen as the least
contaminated available, not as a clean one, and H5's verdict is reported with the screen
axis's opposite sign beside it.

### H1 keeps `E*_A`, and the verdict does not mean what H1's name says

Decided 2026-08-15, after P1c and before the reduced P2. §5 defines two statistics that could
carry H1 and the hypothesis reads one of them, so choosing between them after seeing results
would be a choice. **Nothing is switched: H1 keeps `E*_A`,** and the first-versus-last
contrast is reported beside it. That costs nothing here, because the two agree — 4 of 5
judges on each ([`results/validation/slot_rates.txt`](results/validation/slot_rates.txt) §3).

What the two agreeing does *not* settle is whether either supports §1's claim, and the answer
is that mostly neither does. A judge whose slot weights are the same four numbers at every
difficulty — one that by construction cannot fall back on position more as items get harder —
still produces a positive slope, because difficulty changes how much the candidates differ
from each other and a constant slot weight expresses itself more when they are alike. The
size of that is measured, not asserted, in
[`results/validation/constant_preference.txt`](results/validation/constant_preference.txt):

**A grid maximum is not a bound and was not used as one.** Widening the search by a decade at
each end raised both maxima, so "how many judges exceed the ceiling" is a fact about the
grid. The maxima are printed in
[`results/validation/constant_preference.txt`](results/validation/constant_preference.txt)
§3 and §3b and are not restated here, because a figure retyped into prose is a figure nobody
recomputes when the search behind it changes. The null is
fitted per judge instead: five parameters — the correct answer's attractiveness, the
off-topic attractiveness, three slot weights — against five of that judge's own numbers,
its pooled accuracy at each of the four difficulties and its conditional share at
`--obvious 2`. Nothing is left free, and the slope becomes a prediction.

**The first version of this table was wrong and the way it was wrong is worth more than the
table was.** Its five accuracy vectors were typed into the script as literals. Checked against
the runs afterwards, **not one of the five matched either phase**: they were closest to P1a,
with deviations from 0.0083 to 0.1867, while the shares and slopes they were compared against
came from P1c. The two phases are not interchangeable — at `--obvious 2` their pooled
accuracies differ by up to 0.22, because their arrangement sets present the distractors
differently and that is exactly the property one set has and the other lacks. So the fit was
pinned to one run and asked to predict another.

`Llama-3-OffsetBias-8B` was reported as the judge the model could not fit. Its literals
deviate from P1a by 0.1867 and from P1c by 0.1300, so **that conclusion was about the input,
not about the model**, and the sentence speculating that the misfit was connected to its
reversed pull is withdrawn. It was not evidence of anything.

Every number the fit consumes and every number it predicts now comes from the same phase and
is read from the result files, and the prediction carries an interval: five parameters against
five sample quantities leaves no residual freedom, so the predicted slope is a deterministic
function of five numbers that are themselves estimates. Both the prediction and the
observation are resampled over items, and a judge beats its twin only when the two intervals
do not overlap. The table is in
[`results/validation/constant_preference.txt`](results/validation/constant_preference.txt) §5,
generated rather than transcribed.

**No arrangement set fixes this.** The confound the balanced set removes is which candidate
sits at which slot. What remains is that `--obvious` varies how much the candidates differ,
and that is a property of the control set, not of the ordering. Separating them needs a
difficulty axis that does not change the contrast between candidates, which this experiment
does not have and did not set out to build.

### What is predicted for the re-run on `SLOT_BALANCED`, written before it starts

Committed 2026-08-15, before the first pass. The evidence is
[`results/validation/arrangement_sets.txt`](results/validation/arrangement_sets.txt) §7,
which puts `E*_A` for one judge on the same 150 items under both existing sets:

| `--obvious` | pilot set | P1a set |
|---|---|---|
| 3 | 0.5000 (n=4) | 1.0000 (n=4) |
| 2 | 0.8269 (n=104) | 0.0092 (n=109) |
| 1 | 0.8351 (n=194) | 0.0267 (n=187) |
| 0 | 0.7932 (n=266) | 0.7762 (n=277) |

The two agree at `--obvious 0` and differ by two orders of magnitude at `2` and `1`. The
pilot set holds each candidate at slot A exactly once; the P1a set holds the first distractor
there every time, and that distractor is off-topic at `2` and `1`. **`SLOT_BALANCED` has the
pilot set's property at slot A, and has it at every slot, so the re-run should reproduce the
pilot's shape and not P1a's.** Concretely:

- **`E*_A` will be high and flat across `--obvious 2, 1, 0`** — near 0.8 for
  `Qwen2.5-7B-Instruct` — rather than the near-zero-then-jump the P1a set produced. At
  `--obvious 3` it will rest on a handful of errors and say nothing.
- **H1 will be falsified.** Its slope was positive on the P1a set only because the statistic
  stepped when the control set changed what sat at A. On a flat, slightly decreasing shape
  the slope's interval will contain zero for most judges. This is a prediction that the
  headline result of the first run does not survive its own correction.
- **H2 will stay falsified,** at 3 of 5 or nearby, because the two sets already agree at
  `--obvious 0` and that is the level H2 reads.
- **H5 will hold,** for the same reason: its inputs are the `--obvious 0` values, which move
  least between sets.

If `E*_A` on the new set instead reproduces the P1a shape, the account above is wrong and the
divergence is caused by something other than slot-A occupancy. Either way the number that
decides it exists before the run.

**Outcome, 2026-08-15. Two of the four predictions were wrong, and the two that were wrong
share one mistake.** `E*_A` on the slot-balanced set is neither flat nor near zero: for
`Qwen2.5-7B-Instruct` it runs 0.2697, 0.5188, 0.7704 across `--obvious 2, 1, 0`, rising
monotonically, and four of five judges rise monotonically. H1 therefore **holds**, where the
prediction said it would be falsified. H2 was falsified at 3 of 5 and H5 held at
`rho = -1.0000`, both as predicted.

The mistake was reading slot A's occupancy and stopping there. `E*_A` divides by errors at
*every* slot, so what sits at B, C and D matters as much. Restricted to the arrangements
that can carry an error, the three sets are:

| set | slot A | slot B | slot C | slot D |
|---|---|---|---|---|
| pilot | R1, R2, R3 | R1 ×3 | R2 ×3 | R3 ×3 |
| `FIXED_DISTRACTORS` | R1 ×3 | R1, R2 ×2 | R2 ×2, R3 | R3 ×3 |
| `SLOT_BALANCED` | R1, R2, R3 | R1, R2, R3 | R1, R2, R3 | R1, R2, R3 |

The pilot's slot A is balanced, which is what the prediction rested on, but its B holds the
first distractor three times out of three. At `--obvious 1` that distractor is off-topic and
nobody picks it, so slot B absorbs almost no errors and A's share is inflated — which is why
the pilot read 0.83 and flat. `SLOT_BALANCED` has no slot loaded that way, so it reads
neither the pilot's number nor P1a's.

**On the only set where the statistic is not confounded, the share of a judge's errors landing
on the first slot rises with difficulty.** That is the claim §1 made and the claim the first
run appeared to establish for the wrong reason. It survives its own correction, which is not
what this section predicted.

The `A`-versus-`D` paired accuracy comparison uses arrangements 0 and 9, which both sets
contain, so those ten judge-arrangements were run twice hours apart. All ten reproduce to the
last item.

### What the pilot already says about revised H1, written before P1 decides it

**The pilot fails revised H1, and probably in the direction of a flat line rather than a
negative one.** On `Qwen2.5-7B-Instruct`, `E*_A` across `--obvious 2, 1, 0` is 0.8269, 0.8351,
0.7932 — level, with the hardest setting lowest. `--obvious 3` has 4 usable errors and says
nothing. Meanwhile `f_A` climbs 0.2517 → 0.3783 → 0.4967 → 0.5650, which is [1] doing its
work: the placement is constant and there is simply more error to place.

If P1 reproduces that on five judges, **H1 is falsified and the finding becomes a better one
than H1 described.** A preference that is already at 0.79–0.84 against a null of 1/3 on items
whose answer is not in dispute is not a fallback that appears under load; it is a standing
property that difficulty makes visible by giving it more error to act on. That is stated here,
in advance, so that neither outcome can be presented as the one expected.

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
version paired "contains the null for at least 4" with "excludes it upward for 2 or more",
which leaves a judge whose interval sits *below* the null — one that steers its errors away
from the first slot — satisfying neither clause. The falsification clause is now literally "not
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
is **0.0083 at `--obvious 3`**, below the null's own 95th percentile of 0.0750, **so at the
level where H3 is asked the rule cannot fail** — the same defect as before with the sign
reversed. Ceilings by level: 0.0083, 0.3083, 0.4850 and 0.5817, against 5, 113, 208 and 288
errors.

**Those figures are conditional on the pilot's per-slot accuracy pattern and are not bounds
at that mean accuracy.** The ceiling depends on how the accuracy is spread across slots, not
only on its average: at the same mean the equal-accuracy and one-slot patterns give the two other columns of
[`decision_rules.txt`](results/validation/decision_rules.txt) §3c. The
conclusion survives all three — at `--obvious 3` every one of them is under 0.0750 — but the
number should be quoted with the pattern it came from.

`E*_A` replaces it because errors are the only thing carrying signal here, so it conditions on
them instead of letting them be diluted by a near-perfect accuracy — and it conditions on the
right subset of them, for the reason §5 gives.

The simulated nulls draw the four arrangements of an item independently, and the slope
power no longer does. Measured on the pilot, the within-item correlation of the "answered A"
indicator is 0.0000 at `--obvious 3`, `2` and `1`, and 0.1227 at `--obvious 0`, where the
design effect is 1.368 and 600 verdicts behave like 439. H3 is evaluated at `--obvious 3`,
where the assumption holds. Where it does not, intervals are widened by the measured design
effect and that is stated with the result.

Strict monotonicity over four noisy points was the H1 criterion. On a shallow but real
trend one judge clears it 62.3% of the time and four of five clear it 37.7% — the rule
discards well over half of a true effect. A fitted slope on the same data, drawn with the
measured within-item correlation rather than assuming independence, clears it 93.8% and
96.6%. Both reject the flat world at about 3%. P1a exists because we do not know whether the
effect is as large as the pilot's, and the first rule only worked if it was.

## 7. What would make this claim collapse

If `E*_A(m, 3)` is already above 1/3 with an interval excluding it upward — the judges send their
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

**H3 failed on 2026-08-15, so the reduced P2 is what runs. Which four is now a question,
because there are two sets and the clause names one.** "The four fixed-distractor orderings"
was written when `FIXED_DISTRACTORS` was the only set in the file, so that is its literal
referent; `SLOT_BALANCED` did not exist and is a candidate only in the sense that the clause's
purpose — a magnitude measurement — could be served by either. Both are therefore candidates
and the choice is made here, before the re-run of P1a produces anything.

**No set of four is clean on both counts, and that is a fact about the 24 rather than a
choice.** Only four of the twenty-four arrangements read their distractors as R1, R2, R3 in
slot order, so the only four-element set with that property is that set itself, and it is not
one where each slot holds each candidate equally often.
[`scripts/arrangement_sets.py`](scripts/arrangement_sets.py) §5 shows it. What each set can
carry:

| statistic | `FIXED_DISTRACTORS` | `SLOT_BALANCED` |
|---|---|---|
| `V`, accuracy spread over four slots | clean | confounded |
| `W`, spread over distractor orders | not available | not available |
| paired difference between two named slots | clean, all six pairs | clean, `A` vs `D` only |
| `E*_A`, and all letter frequencies | confounded | clean |

**One exploratory test is registered on the reduced P2 before it runs, and it is exploratory
because it was first computed on P1c.** Inside `--obvious 0` the distractors are always the
item's own rejected responses, so their composition never changes with the item — which means
difficulty can be taken from the item rather than from the control set, and that is the axis
§6 says this design lacks. Simulated at a fixed slot preference, moving an item's difficulty
(the correct answer's margin) barely moves `E*_A` across a factor of ten in that margin,
while moving the distractors' heterogeneity at fixed mean moves it about twenty times as
much — the two ranges are printed side by side
([`results/validation/slot_rates.txt`](results/validation/slot_rates.txt) §5 and
[`constant_preference.txt`](results/validation/constant_preference.txt)). So a difference in
`E*_A` between difficulty strata is not something a constant preference produces, provided
the strata do not differ in heterogeneity, which is checked and reported.

Item difficulty is the mean accuracy of **the other four judges** on that item, leaving the
judge under test out of its own difficulty measure, split at the median. On P1c's 150 items
the mean 95% interval width is 0.1876; at 1,763 items it projects to 0.0547. Most of the
easy-hard differences seen on P1c are smaller than that, so **this test can find a large
effect and not a small one**, and it is registered with that stated rather than discovered
afterwards. It decides no hypothesis. P1c's numbers are the exploratory pass; the reduced P2
sample is the confirmatory one.

**Reduced P2 runs on both sets: 5 judges × 1,763 items × 8 arrangements, 40 passes, 4.5
hours** at the rate P1b measured. One set cannot carry the statistics the surviving
hypotheses read, and the pair costs 2.2 hours more than one. The full 24 would add only `W`,
and the clause above already says H4 is not evaluated when H3 fails, so buying 13.6 hours for
a hypothesis this section has withdrawn would be spending on scope that was ruled out before
the result existed. The `A`-versus-`D` paired difference is measurable on both sets, which
makes the two runs checkable against each other rather than merely complementary.

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

### What §7 registered would remain, reported as registered

§7 said that if H3 failed, the "falls back under load" framing was wrong and what remained
was **a magnitude measurement on one benchmark**. H3 failed. That sentence keeps its status
as the registered consequence and is not edited, softened or explained away here.

**The magnitude is reported per judge, because pooling it changes what it says.** The null
is 1/3; the statistic is `E*_A` at `--obvious 3` on all 1,763 items
([`results/exp01/p1_summary.txt`](results/exp01/p1_summary.txt), H3):

| pooling | value | reads as |
|---|---|---|
| unweighted mean of the four evaluated | 0.3771 | almost no preference |
| weighted by `n_err*` | 0.2710 | judges push errors *away* from the first slot |
| per judge | 0.6543 excluding 1/3 upward, 0.1866 excluding it downward | two judges, opposite signs |

The weighted pool inverts because one judge carries 70.3% of the usable errors —
`Skywork-Critic` makes 477 of the 679 among the four evaluated. **A single pooled number
here does not merely lose the split; at the natural weighting it reports the opposite of what
two of the five judges do.** Wherever a pooled figure appears, this table appears beside it.

### Not registered: the dispositions point in opposite directions

**This was not anticipated by the pre-registration and was found after H3 was decided.** It
is written here under its own heading so that nothing merges it with the block above, and it
claims nothing the intervals do not carry.

On items whose correct answer is not in dispute, the five judges' conditional first-slot
error shares are 0.6543, 0.3750, 0.3421, 0.2927 and 0.1866 against a null of 1/3. Two
exclude the null and they exclude it in **opposite directions**: `Qwen2.5-7B-Instruct`
upward, `Skywork-Critic-Llama-3.1-8B` downward. Two contain it. `RISE-Judge-Qwen2.5-7B` was
**not evaluated** — 38 usable errors against the floor of 40 registered before the run.

That is five judges, one benchmark, one difficulty level. **It is not a statement about
judges in general**, and the next section says what would have to be true for it to become
one.

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

**Every number in this section is at one arrangement with the correct answer at slot A**, and
§4 shows that ordering the judges by it orders them by how often they answer `A`. The
comparisons below stand as comparisons *at that arrangement* and none of them survives being
read as a ranking of judgment: at slot C and slot D the order is close to reversed.

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
