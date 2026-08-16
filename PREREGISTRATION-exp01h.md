# Pre-registration — widening the judge pool, and the criterion before the candidates

**Status: not run, and no candidate is named in this file.** That is the point of it. The
criterion is fixed here; candidates are found afterwards and put through it. Naming a candidate
first and writing the criterion around it is the failure this document exists to prevent, and it
is one step from the failure the screen already refused.

## Why widening is a registration act and not a search

`PREREGISTRATION-exp01b.md` §4 defines the candidate pool as the open-weight judges RewardBench
v1 scored that RewardBench 2 does not, with a `model_modifier` branch in the evaluator, fitting
24 GB. **Seven were screened and there is no eighth inside it.** So any new judge is outside the
registered pool, and admitting one changes the population a later threshold is taken over.

`results/validation/screen_summary.txt` closes with the neighbouring prohibition:

> The pre-registration said six; the shortfall is reported, **not backfilled with judges chosen
> after seeing their scores.**

**Widening on *does it state reasoning at all* is not that.** Stating reasoning is a prerequisite
for a verdict to contradict its reasoning — it is what makes the measurement possible, not what
the measurement asks. Selecting on who **can** exhibit a phenomenon differs from selecting on who
**does**. Widening because a candidate looked likely to pass would be the prohibited move, and
this registration is what stops that being decided later.

## The criterion, in the order it is applied

A candidate enters the measurement when it meets all five. Each is checkable before any
experimental pass runs.

**1. Open weights, and it fits.** Weights publicly downloadable, and the model runs on one
RTX 4090 at 24 GB under the pinned evaluator — 7–14 B at FP16, or larger quantised. No paid API,
which is this repository's cost constraint and not a preference.

**2. It runs under the pinned evaluator without a patch we author.** `allenai/reward-bench` at
the pinned commit, with the harness patch already committed here. A candidate that needs new
inference code is **excluded and reported as excluded with the reason**, as
`AtlaAI/Selene-1-Mini-Llama-3.1-8B` already is. This is not a judgement about the model.

**3. It states reasoning, and reaches a verdict while doing so.** At least **half** of its
screen verdicts must carry text beyond the bare verdict *and* parse to a letter. Both halves are
required: reasoning with no verdict cannot be compared against a verdict, and a verdict with no
reasoning has nothing to contradict. Measured on the same 150 items and the same upstream prompt
the original screen used, by the same counting `results/validation/f1_stage1.txt` §0 applies to
the five already screened.

*The threshold is not doing the work and that is stated rather than discovered.* On those five
the shares are 99.490%, 98.497%, 2.056%, 0.482% and 0.000%, so any threshold between about 3%
and 98% produces the same partition. Fifty is the midpoint of a gap nothing sits in, and a
candidate landing near it would be reported as landing near it rather than rounded past it.

**4. The original screen's parse gate.** Unparseable-verdict rate at most 10%, unchanged from
`PREREGISTRATION-exp01b.md` §4.

**5. The original screen's accuracy gate, under this repository's convention.** Accuracy above
0.30 **with an unparseable verdict scored 0**, not credited 0.25.

The convention changes and the reason is that everything else here already uses it — `E*_A`
drops unparsed from the denominator outright, and `docs/errata.md` carries the account of a
figure that turned on this choice. **No judge's status changes.** The five that passed score
0.9067, 0.8533, 0.7800, 0.7400 and 0.5333 under the strict convention and all clear 0.30. One
candidate differs — `prometheus-eval/prometheus-7b-v2.0` passes at 0.3617 under upstream's
convention and fails at 0.2000 under this one — and it is already excluded by criterion 3's
sibling: it writes reasoning every time and emits a verdict in 53 of 150, so **44.7% of its
credit is for verdicts it did not produce.** That is measured in
`results/validation/screen_summary.txt`, which now prints both columns.

## What is reported, whatever the outcome

Every candidate considered, with which criterion it failed and its numbers — not only those that
pass. A candidate that could not be run at all is listed with the reason, as Selene is.

**The count of candidates searched is reported.** If the search finds none, that is the result
and is published as *the widened pool is empty under this criterion*, which is a stronger version
of the bound already in `f1_stage1.txt` §0.

## What a judge admitted here may and may not be used for

It **may** carry a new hypothesis, registered after it is admitted and before it runs.

It **may not** enter `PREREGISTRATION-exp01g.md`. That run's population is fixed at two judges
and its numbers may be visible by the time this search finishes; adding a judge to it afterwards
would fix a denominator after a result is in view. **This is the whole reason there are two
registrations rather than one.**

## What this does not fix

The pool is still open-weight judges that fit one 24 GB card. RewardBench 2's own generative
entries are 16 paid-API models and two at 70 B+, so the population this repository can measure is
not the population the leaderboard reports, and widening it by one or two judges does not change
that. It is stated in `README.md` as a known limitation and stays stated.
