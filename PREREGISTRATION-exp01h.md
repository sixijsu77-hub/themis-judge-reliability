# Pre-registration — widening the judge pool, and the criterion before the candidates

**Status: not run, and no candidate is named in this file.** Amended once before any pass of it
existed, to add what criterion 3 does not guarantee; the git history of this file against the
first result file it produces is the evidence that the amendment preceded the data. That is the point of it. The
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

## Where the candidates come from, fixed before any is named

Criterion 2 below does not bound the pool, and I registered it believing it did. The evaluator's
`run_generative_v2.py` at the pinned commit assigns a `model_modifier` from the model name and
ends `else: model_modifier = None`, so **a model with no special handling runs on the default
path**. Two of the five judges already screened — `Qwen/Qwen2.5-7B-Instruct` and
`Skywork/Skywork-Critic-Llama-3.1-8B` — match no branch and ran that way. Every open-weight chat
model that fits satisfies criterion 2, which makes the candidate space unbounded and turns
"which candidates" into a choice rather than a lookup.

So the enumeration is registered here, before any candidate is named:

**The candidate list is the open-weight generative judges with a published RewardBench score —
v1 or v2 — that fit one 24 GB card, together with the seven already screened.** It is somebody
else's list and not one assembled here, which is the same reason this repository measures
against a public leaderboard at all. Models with no published score are outside it however
promising they look, and that exclusion is the price of the list being external.

**If that list is exhausted, the result is that it is exhausted.** Widening to general
instruct models with no published judge score would make the pool unbounded and every
subsequent choice mine, which is the failure this paragraph exists to prevent.

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

**What criterion 3 does not guarantee.** It is measured under the **upstream prompt** the screen
uses, and it gates a run whose four conditions include two inverted ones. Those are not the same
question, and the criterion's own property moves between them. On the one judge measured across
conditions, the share of verdicts carrying both reasoning and a parsed letter runs **0.9850 on
`original`, 0.9738 on `paraphrase` and 0.8325 on `inverted`** — a drop of about a sixth when the
predicate is inverted. A candidate sitting near the threshold on the screen can therefore fall
under it where the run happens.

*A larger-looking number is available and does not belong here.* Detector coverage across the
same conditions runs 0.1246, 0.2925 and 0.2392, which is a factor of 2.35 — but those are three
different regexes keyed to three different prompts, so the spread is between detectors and not a
single property changing, and two of the three are controls with the inverted arm between them.
The clause needs the criterion's own property, which is the first table and the smaller ratio.

That gap is covered by the `not evaluated` path rather than by a stronger screen: a level whose
corrected-arm coverage falls outside a factor of 2 of the old inverted arm's is `not evaluated`
and no null from it counts. **So criterion 3 is necessary for a candidate to be worth running and
not sufficient for it to produce a reading**, and a candidate that passes here and comes back
unreadable is reported as unreadable rather than as an absent effect. Screening under the
inverted prompt instead would mean running the experimental condition to decide who enters the
experiment, which is the larger error.

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
