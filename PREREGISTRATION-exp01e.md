# Pre-registration — the difficulty axis, with heterogeneity matched

Registered before `E*_A` is computed on any stratum of this design. The git timestamp on this
file, against the one on the result it is judged by, is the evidence.

`exp01c` reports the stability of a judge's slot disposition on four axes and leaves one of
them empty: **every clean test of the difficulty axis is missing, and the one look available
disagrees.** This is a clean test of that axis, and it exists because the reason the previous
one was void turns out to be removable.

## Why the previous test was void, and what removes it

`results/validation/slot_rates.txt` states it:

> The condition fails for 4 of 5 judges. The strata differ in the one property that moves this
> statistic without any change in the judge … the difficulty axis and the heterogeneity axis
> are the same axis here. This test is void, and that is its result.

Item difficulty is the mean accuracy of the **other four** judges on that item, split at the
median. Distractor heterogeneity is the coefficient of variation of the three distractor
lengths. Items whose distractors vary more in length are items other judges get right more
often, so splitting on difficulty splits on heterogeneity too — and a simulation at a fixed
slot preference moves `E*_A` about twenty times as much with heterogeneity as with difficulty.

**The two axes overlap; they are not the same axis.** Measured per judge over the 1,763 items
of `P2a` and `P2b`, `corr(difficulty, heterogeneity)` runs from +0.1209 to +0.1593. So the
easy and hard strata can be matched on heterogeneity by comparing them **within** bands of it,
and the difficulty contrast survives that, because difficulty still spans most of its range
inside every band.

`scripts/band_power.py` reports the correlations, the cell sizes and the matching. It computes
`E*_A`'s denominator and never its numerator, so that the claim *the outcome was not computed
before this file was committed* is a property of the code and not an assurance.

## Design

**Source.** `results/exp01/P2a_*` and `P2b_*`, forty passes, 1,763 items, five judges — the
same records and the same loading path `scripts/slot_rates.py` uses for its confirmatory
stratum table, so the gate that validated that path validates this one.

**Bands.** Items are cut into `B` equal-count bands on heterogeneity. Within each band,
difficulty is split at **that band's** median, so both strata are present in every band.

**`B` is not chosen.** The analysis is run at **B = 3, 4 and 5** and all three are reported.
Power does not force the choice — at every one of the three, and for every judge, the smallest
cell holds at least 78 errors against a floor of 40 — and choosing `B` after seeing which
value matched best would be selecting a design on its own precondition. Closing the candidate
set at {3, 4, 5} is registered here so it cannot be widened later.

**Pooling within a `B`.** Primary: numerators and denominators summed across bands within a
stratum, which is how `E*_A` is defined everywhere else in this repository — a ratio of counts,
so the pooling is error-weighted. Secondary, reported beside it: the unweighted mean of the
per-band `E*_A`. **If the two disagree in sign for any judge, that is reported explicitly**,
because a weighted and an unweighted pooling of the same cells have inverted a conclusion in
this repository before. The verdict is on the primary.

**Intervals.** Bootstrap over items within each stratum, 4,000 resamples, seed 0 — the resample
count and seed `slot_rates.py` already uses for stratum intervals.

## H-e1 — the direction of a judge's slot disposition survives a change of difficulty

For each judge and each `B`, a stratum's sign is **readable** when its 95% interval on `E*_A`
excludes 1/3. A judge **agrees** when both strata are readable and their signs match.

**H-e1 holds when at least 4 of the 5 judges agree, at all three of B = 3, 4 and 5.**

The threshold of four is the one already registered for the same question on the other two
axes — J2″ across arrangement sets and J3 across benchmarks — and is carried over unchanged so
that the difficulty row is comparable with the rows beside it. A judge whose sign is not
readable on one or both strata counts **against** the prediction, which is the rule J2″ was
judged by when `RISE-Judge-Qwen2.5-7B` sat on the null.

**Falsification.** H-e1 is falsified when fewer than 4 of 5 judges agree at any one of the
three band counts. That is the exact complement: for each `B` the count is an integer in
0…5, "at least 4 at all three" and "fewer than 4 at at least one" partition every possible
outcome, and a judge that is unreadable, or readable with opposite signs, falls in the second.
A `B` at which the analysis cannot be run at all is reported as not evaluated and counts as
falsifying, since the conjunction is over all three.

**The precondition, and what happens if it fails.** The strata must be matched on
heterogeneity for the contrast to be about difficulty. Matched means the 95% interval on
(mean heterogeneity of easy − mean heterogeneity of hard) contains zero, for every judge, at
that `B`. Measured before registration and reported in `band_power.py`: matched for all five
judges at all three band counts. **If a re-run finds it broken at some `B`, that `B` is void
and reported as void rather than dropped**, exactly as the unbanded test was.

## What a hold would and would not establish

It **would** fill the empty row of `exp01c`'s stability table with a test that is clean rather
than confounded, and it would say that a judge's direction is a property of the judge across
difficulty as well as across arrangement set and across benchmark.

It **would not** establish a difficulty *effect*. H-e1 is about the sign surviving, not about
`E*_A` moving, and a judge can agree on sign while its `E*_A` differs between strata.

It **would not** cover confounds other than heterogeneity. That is the one a simulation
identified as moving this statistic without a change in the judge, and it is the one matched
here. Another property with the same power would be invisible to this design, and nothing in
the result should be read as ruling one out.

**Registered limit on size.** `PREREGISTRATION-exp01b.md` projects a mean 95% interval width
of 0.0547 for a stratum at 1,763 items. Banding does not widen the pooled intervals, since
pooling recovers the full error mass, but this design can find a large difference and not a
small one — stated here rather than discovered afterwards.
