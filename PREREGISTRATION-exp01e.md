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

---

# Result

Written after the run. Everything above this line was committed as `430d7e0` and pushed at
`2026-08-15 17:14:24 UTC`, before `scripts/band_strata.py` existed. Full tables in
`results/validation/band_strata.txt`.

## H-e1 holds

```
B=3 -> 4/5    B=4 -> 4/5    B=5 -> 4/5
```

Four of five judges keep the same readable sign across difficulty, at every band count, so the
conjunction registered above is satisfied. At `B = 5`:

| judge | stratum | n_err* | E*_A | 95% CI | sign |
|---|---|---|---|---|---|
| Llama-3-OffsetBias-8B | easy | 534 | 0.0787 | [0.0498, 0.1113] | − |
| | hard | 2318 | 0.1389 | [0.1190, 0.1596] | − |
| Qwen2.5-7B-Instruct | easy | 2364 | 0.8316 | [0.8062, 0.8561] | + |
| | hard | 4135 | 0.7487 | [0.7273, 0.7697] | + |
| RISE-Judge-Qwen2.5-7B | easy | 653 | 0.3583 | [0.3061, 0.4121] | **null** |
| | hard | 3221 | 0.3592 | [0.3350, 0.3835] | + |
| Skywork-Critic-Llama-3.1-8B | easy | 1983 | 0.5265 | [0.4949, 0.5564] | + |
| | hard | 3750 | 0.5752 | [0.5517, 0.5982] | + |
| Con-J-Qwen2-7B | easy | 1394 | 0.5122 | [0.4716, 0.5527] | + |
| | hard | 3760 | 0.5082 | [0.4837, 0.5333] | + |

**The judge that counts against is the one that counted against `J2″`, for the same reason.**
`RISE-Judge-Qwen2.5-7B` has point estimates of 0.3583 and 0.3592 — the two strata agree with
each other about as closely as any pair in the table — and its easy interval contains 1/3, so
its sign is not readable there and it counts against the prediction. That is the registered
rule, and it is what a judge sitting on the null looks like rather than a disagreement.

Every judge has far fewer errors on the easy stratum than the hard one, which is what "easy"
means: items the other four judges get right are items this judge mostly gets right too. The
wider easy intervals follow from that and were not a surprise the design failed to anticipate.

## The two poolings agree

The unweighted mean of the per-band ratios is printed beside every primary figure and **no
judge's two poolings differ in sign at any band count**; the largest gap between them is
Qwen's easy stratum, 0.8316 weighted against 0.8038 unweighted. The clause registered above
for the case where they disagree is not exercised.

## The precondition held on re-run

`results/validation/band_power.txt` reports the matching check for every judge at every band
count: all five matched at `B` = 3, 4 and 5, every interval on the easy-minus-hard
heterogeneity difference containing zero. No band count is void.

## What changes, and what does not

`exp01c`'s stability table has an empty row — *every clean test of the difficulty axis is
missing, and the one look available disagrees*. **It is no longer empty.** The direction of a
judge's slot disposition survives a change of difficulty at the same threshold, and with the
same one judge falling short, as it survives a change of arrangement set.

It does **not** establish a difficulty effect: H-e1 is about the sign surviving, and three of
the four agreeing judges have visibly different `E*_A` on their two strata. It does not
rescore H1, H2, H3 or H5. And it matches on heterogeneity alone, which is the property a
simulation identified as moving this statistic without a change in the judge; a second property
with the same power would be invisible to this design.

## One number in the note that occasioned this did not reproduce

`026-judge.md` reported that at five bands the smallest cell holds 35 to 143 errors and that
two judges fall below the floor of 40. Measured here over `P2a` and `P2b` together, the
smallest cell at `B = 5` holds 78 and **no cell for any judge at any band count is below the
floor**. The cause is not established; the likely one is pass count, since this analysis uses
all forty passes of both arrangement sets, which is the source `scripts/slot_rates.py` uses
for its confirmatory table. It did not change the design — the band count was left unchosen
precisely so that a power argument would not have to carry it.
