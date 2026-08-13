# 0001 — How polarity inversion is implemented

Decided 2026-08-13. Decided **before** any experiment was run; see `git log`.
Superseding this decision requires a new record, not an edit to this one.

## The problem

This repository set out to measure whether a judge's verdict survives being asked in the
opposite direction. The design was drafted around a yes/no pair:

> "did this response follow the instruction?" against "did this response violate the instruction?"

**No such question exists in RewardBench 2.** Measured from the dataset and the scoring
code in `allenai/reward-bench` at commit `05a9005`:

- Each item is one prompt with four candidates: 1 chosen, 3 rejected. All 1,763 non-Ties
  items have `total_completions == 4` and `num_correct == 1`.
- A sequence-classifier reward model is never asked anything. It receives a
  (prompt, response) pair and returns a scalar. There is no question to negate, and the
  four candidates are never placed in an order, so candidate position cannot affect it.
- A generative judge *is* asked a question — either a four-way ranking ("which of these
  four is best", answer `[[A]]`–`[[D]]`) or a pointwise rating (1–10 per candidate).

So the phrasing the design assumed has to be replaced by something that exists.

## What constrains the choice

**No open-weight generative judge that fits on a 24 GB card has a published score.**
Of 197 published entries, 178 are sequence classifiers, 18 are generative judges, and 1 is
a custom classifier. Of the 18 generative judges, 16 are paid API models, which this
repository does not use; the remaining two are 70.55 B and 72.71 B parameters — 35 GB even at
4-bit.

The consequence is unavoidable and is stated here rather than discovered later: **the
generative path cannot be validated by reproducing a published number on this hardware.**
Every option below inherits that. What the options differ on is everything else.

Two further facts, both measured from the published per-item scores rather than assumed:

**The published "Generative RM" column is not one protocol.** The ranking path yields
per-item scores in `{0, 1, 0.25}`; the ratings path yields `(0 in winners)/len(winners)`,
so `0.5` and `0.333` appear. Sorting the 14 entries that publish per-item scores by that
fingerprint gives 2 ranking-mode entries and 12 ratings-mode entries. The mode is not
recorded in the results files.

**A parse failure earns 0.25, not 0.** `process_judgement` returns `"error"` when it finds
no `[[X]]` marker, and `process_shuffled` maps that to 0.25 — chance credit under a
four-way choice. One published ranking-mode entry has 20.0% of its items at 0.25
(352 of 1,763), which is 0.05 of its score. This matters below: any polarity effect that
also changes how often the output format holds will be partly a format effect.

## Options considered

| | Implementation | Chance level | Gate path vs experiment path |
|---|---|---|---|
| (a) | Invert the ranking prompt: "which is best" → "which is worst" | 25% → **75%** | same code |
| (b) | Reduce to pairwise: chosen + one rejected, "which is better" ↔ "which is worse" | 50% ↔ 50% | **different** |
| (c) | Invert the rating prompt: "rate the quality 1–10" → "rate the deficiency 1–10", argmax → argmin | unchanged | one flag apart |
| (d) | Invert the framing of the ranking prompt while asking for the complement: "choose the one that follows the instruction best" ↔ "three of these four fail to follow the instruction; identify the one that does not" | 25% ↔ 25% | **one string apart** |
| (e) | Abandon the generative path and measure something else | — | — |

## Decision: (d)

### (a) inverts the predicate *and* the answer cardinality; (d) inverts only the predicate

This is the reason (a) was rejected and it is worth stating precisely, because (d) reads
at first like a weaker version of (a) and is in fact the stricter one.

Under (a), the correct answer changes from 1 candidate to 3. That is where 25% → 75% comes
from: it is not an incidental difficulty difference, it is a change in what is being asked.
A score computed across that change cannot separate polarity from cardinality.

Under (d), the predicate is inverted (*follows* becomes *fails to follow*) and the question
asks for the **complement** of the inverted answer set. Since
`argmax(quality) = complement(argmax(deficiency) over three)`, the answer is the same single
candidate, and the chance level is unchanged. (d) is (a) composed with set complementation —
the same inversion with the confound removed.

The judge must still reason in the inverted direction: it has to establish which three
fail. Only the reporting convention is preserved. That is the shape of the phenomenon this
repository exists to measure — a description written against the direction of the output
schema — so preserving the convention is the point, not a compromise.

### (d) is the only option where the gate validates the code the experiment runs

Since no published number can gate the generative path (above), the only remaining way to
keep the gate honest is to make the gated path and the experimental path the same code.
Under (d) they differ by one system-prompt string; dataset loading, candidate placement,
`[[X]]` parsing, and scoring are byte-identical. Under (b) they differ completely: the gate
would validate best-of-4 scoring that the experiment never executes.

### (d) supplies its own comparison baseline

`run_generative_v2.py` already places the chosen candidate at one of four positions
(`shuffle_option`, three call sites, **none of them seeded**). Seeding it and sweeping all
four placements measures position sensitivity on the identical format, the identical items,
and the identical chance level as the polarity measurement. The two shifts are then
commensurable, which is what makes the primary hypothesis decidable at all.

Option (c) cannot supply this: a pointwise rating sees one candidate at a time, so position
does not exist for it.

### (c) does not fit in the cost budget

`_get_vllm_rating` calls `model.generate([prompt])` with a single prompt, wrapped in a
Python loop — one generation per candidate, 8,977 per pass, unbatched. The ranking path
submits all 1,763 prompts to a single `generate()` call. Batching the ratings loop would
fix this, but then the run is no longer unmodified upstream code, which was (c)'s main
attraction over (b).

## What this costs, stated plainly

1. **The published framing of this repository was wrong and is now corrected.** The yes/no
   example in the first draft of the pre-registration and README does not exist in this
   benchmark. It has been replaced, not quietly reinterpreted.

2. **The Ties subset is out of scope for the polarity measurement.** Its scoring path is
   the ratings prompt, which (d) does not modify. Coverage is therefore **5 of 6 subsets,
   1,763 of 1,865 items**, and results say so rather than reporting an overall average that
   implies six.

3. **No published number validates the experimental path.** The gate is run on the
   reward-model path, and what it validates is the dataset, the scoring, and the
   aggregation — not the prompt path. Results must say this in those words.

4. **A framing inversion is arguable in a way a logical negation is not.** The two
   wordings must be reviewed by a person and stored as inspectable data before the run
   (`prompts/`, tracked). If review concludes the two wordings do not share a single
   correct answer, the fallback is (b), and that reversal gets its own decision record.

5. **Format fragility contaminates the measurement if unmeasured.** Because parse failures
   earn 0.25, the inverted framing could raise the score by breaking the output format.
   Parse-failure rate is therefore recorded per condition, and a sensitivity analysis
   scoring failures as 0 is reported alongside the primary result.

## Consequences for the pre-registration

`PREREGISTRATION.md` §6.1 and §6.2 are closed by this record: §6.1 by (d) above, §6.2 by
the four-placement position sweep. H1 is restated against that baseline. The coverage
statement and the parse-failure reporting rule are added before anything runs.
