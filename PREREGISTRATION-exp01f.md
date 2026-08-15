# Pre-registration — the polarity axis, rewritten

**Status: not run. Nothing has been computed against these hypotheses.** They are written and
committed for a decision; the run they name has not started and will not until that decision is
made. The git timestamp on this file, against the first result file the run produces, is the
evidence.

## Why the old hypotheses are not repaired in place

`PREREGISTRATION.md` §5 records H1–H5 and `PREREGISTRATION.md` §"Verdict on the polarity axis"
records them as **mis-specified**:

> H1–H5 were written assuming one `Δ(s)` per subset. S1b shows `Δ` is a function of item
> difficulty that changes sign, so the quantity the hypotheses name is not a single number and
> no result can decide them as written … They are not rewritten to fit.

That is a defect in the writing and not a report of what the data said, so repairing it is
legitimate — but only in one direction. **Rewritten hypotheses judged on a new run is a repair.
Rewritten hypotheses scored against the data that came back weak is choosing the rule after
seeing the result**, and it would cost exp01 rather than save it. Everything below is judged on
a run that has not happened.

H1–H5 and their verdicts stay where they are, marked mis-specified. Nothing here replaces them
in that file, and this document does not renumber them: its hypotheses are H-f1 to H-f3 so that
a reader cannot mistake one for the other.

## What survived, and what it is

Two things came out of S1b. The first is that the accuracy effect of inverting the predicate
falls with difficulty, loses its interval at `--obvious 1`, and **reverses sign** on the
unmodified item. That is the finding that makes a single `Δ(s)` meaningless, and it is reported
as such.

The second is the one this repository is named for:

```
  obvious                  original                paraphrase                  inverted
        3        0 of 93   =   0.0%        0 of 227  =   0.0%       23 of 103  =  22.3%
        2        0 of 96   =   0.0%        0 of 186  =   0.0%       32 of 192  =  16.7%
        1        0 of 64   =   0.0%        0 of 171  =   0.0%       22 of 159  =  13.8%
        0        0 of 46   =   0.0%        0 of 118  =   0.0%        7 of 120  =   5.8%
```

**Zero contradictions between a verdict and its own stated reasoning in 1,001 control
observations, and between 5.8% and 22.3% under inversion at every difficulty.** A judge that
explains why one candidate is the answer and then names a different one is the failure this
repository exists to measure, and unlike the accuracy shift it does not change sign.

## The defect that makes those numbers unusable, and its fix

`prompts/polarity_inverted.txt` says:

> Three of the four assistants follow the user's instructions and answer the user's question
> less well than one of the others does; you should identify **the remaining assistant**.

*Remaining after what.* The judge reads it as the one left among the failures in 1.6% to 6.4%
of the sentences that use the phrase — found by reading the judge's output, not by inspecting
the wording. The contradiction count above is therefore **not a clean measure**, and the
contamination cannot be subtracted from it.

The corrected wording names the target by its relation to the three rather than by remainder,
and changes nothing else:

> Three of the four assistants follow the user's instructions and answer the user's question
> less well than the fourth does; you should identify **the one assistant that is not among
> those three**.

with the verdict lines correspondingly *"[[A]] if assistant A is the one that is not among those
three"*. The inversion is untouched: the judge still has to reason about which three are worse,
the answer is still a single candidate, and chance is still 25%.

**The old wording is kept and run as a fourth condition**, because "we could not subtract the
contamination" is a statement that can be turned into a measurement rather than left standing.

## The run these are judged on

Four difficulty levels × four conditions, at 1,763 items each.

| | |
|---|---|
| levels | `--obvious` 3, 2, 1, 0 — all four now exist at 1,763 items |
| conditions | original, paraphrase, inverted **corrected**, inverted **as it was** |
| arrangement | one, `SLOT_BALANCED[0]`, so position cannot vary between conditions |
| judges | the five screened in `results/validation/screen_summary.txt` |
| passes | 16 per judge, 80 in total |

The cost unit is one pass over 1,763 items, the same unit as `P2a` and `P2b`. The committed
cost table plans 120 such passes at 17.6 hours; 80 passes is under that and it is local GPU
time, so the no-paid-API constraint is untouched.

**Staged, and the first stage is a gate.** `Skywork-Critic-Llama-3.1-8B`'s 16 passes run
first — named here rather than left open, in a document whose purpose is to close choices
before the data exists. It is the judge with the largest usable error count at `--obvious 0`
in the screen, so a null from it is the most informative null available.

**The gate cannot fire on a level whose detector under-covers it.** Registered here, before the
corrected prompt's coverage is known: the corrected condition's match rate at a level must be
within a **factor of 2** of the old inverted condition's at that same level, or the level is
`not evaluated` and no null from it counts. Without a number in this paragraph the previous
version was safe only against *total* non-match — a detector matching 30 of 1,763 would print
`0 of 30 = 0.0%`, a legitimate-looking null on a denominator twenty times smaller than the
controls', and the gate would fire on it.

**Why two.** The two inverted arms are the same items at the same level under the same judge,
differing in one clause of one prompt, so a coverage ratio past 2 means the two detectors are
selecting different populations and a rate difference between them stops being a wording
effect. For scale, the two patterns already committed differ by 26× on the same corpus —
`is the remaining` matches 574 of the 2,400 inverted judgements and `is the one` matches 22 —
which is what a condition with no number in it would have admitted.

Otherwise, if the corrected inverted condition produces **no** contradiction at any of the four
levels for that judge, the remaining 64 passes are not run and the result is reported as *the
effect did not survive the wording fix*, which is an answer. Otherwise all five judges are run and the hypotheses are
judged on all five. A single judge cannot carry them — generalising from one is a failure this
repository has already recorded.

## H-f1 — a verdict contradicts its own reasoning under inversion, and only under inversion

For each `--obvious` level ℓ and each judge, let `c(cond, ℓ)` be the fraction of **verdicts
whose conclusion sentence the detector for that condition matched** — not of parseable verdicts,
and not of items — whose matched conclusion names a different candidate than the verdict does.
The interval is a bootstrap over items, 10,000 resamples, 95%.

**That denominator is a selection and is reported beside every rate.** In the observations
already collected it runs from 46 to 227 out of 600 across conditions and levels, differing by
up to a factor of five, and what selects it is *did the judge phrase its conclusion in the
canonical way* — plausibly correlated with contradicting itself. A reader who pictures 1,763 is
picturing the wrong number, which is why the artefact prints `k of n` and never a bare rate.

**A condition the detector never matched is `not evaluated`, not zero.** The detector is a
per-condition regex keyed on that condition's own prompt wording, and the corrected inverted
prompt drops the word the old pattern is keyed on. Left alone it would have reported
`stated = 0, contra = 0` as `0.0%`, the staging gate above would have fired, and this repository
would have published that the phenomenon it is named for did not survive — on a detector never
pointed at the new prompt. A fourth pattern exists for the corrected wording and all four
directions are fixtures in `scripts/check_the_checks.py`.

A level **shows the effect** for a judge when the interval on
`c(inverted-corrected, ℓ) − max(c(original, ℓ), c(paraphrase, ℓ))` excludes 0.

**H-f1 holds when at least 4 of the evaluable judges show the effect at all four levels.**

The threshold of four is the one already registered for a five-judge count elsewhere in this
project (`J2″`, `J3`, `H-e1`) and is carried over so the rows are comparable.

**Evaluability, and it decides before the count does.** A judge is **evaluable** when, at every
one of the four levels, its run completed and the corrected condition's coverage is within the
registered factor of the old inverted condition's. Let `E` be the number of evaluable judges.

- **`E` < 4 → H-f1 is `not evaluated`**, the state `H4` and `J1` already carry in
  `PREREGISTRATION.md` — *the sample cannot answer it*.
- **`E` ≥ 4 → H-f1 holds** when at least 4 of the evaluable judges show the effect at all four
  levels, and is **falsified** otherwise.

Those three partition every outcome: `E` is an integer in 0…5 and the count of judges showing
the effect is another, and every pair falls in exactly one branch.

**Why a level that could not be measured must not count against.** The earlier version said a
judge whose run did not complete "counts as not qualifying", and said nothing about coverage at
all. Both push in one direction only: a detector that under-covers, or a pass that crashes,
moves H-f1 toward falsification and never toward holding. The sentence that would then be
published is *judges do not contradict their own reasoning under inversion* — a claim about the
world produced by a measurement that did not happen. The safeguard that stops a false null at
the staging gate would have opened a path to a false falsification here.

**And a coverage ratio past 2 is not a corner case.** Two detectors already in use, both
accepted, differ by 2.35× on the same corpus — `paraphrase` matches 0.2925 of its arm and
`original` 0.1246. The two inverted arms are keyed on different phrases by construction, which
is more reason to expect a spread rather than less.

**If `E` = 4 the threshold equals the ceiling.** Four evaluable judges against a threshold of
four means a hold is *every judge this run could measure*, not four out of five, and it is
reported in those words — the distinction `H-e1` had to be corrected for after the fact.

**Reachability.** The control rate is 0 of 1,001 in the observations already collected. Against
a control of zero, the interval on the difference clears 0 at **four contradictions** at every
sample size this run produces — computed at n = 120, 150, 300, 600 and 1,763, where the
smallest detectable rates are 0.0333, 0.0267, 0.0133, 0.0067 and 0.0023. The smallest rate
observed under inversion is 0.0583, twenty-five times the detectable rate at 1,763 items. **The
threshold is far inside what the statistic can reach**, and the risk in this hypothesis is not
power — it is that the corrected wording removes the effect.

## H-f2 — the wording defect does not account for the effect

For each judge and level, the interval on `c(inverted-corrected, ℓ) − c(inverted-as-was, ℓ)`.

**H-f2 holds when, for at least 4 of the evaluable judges, the corrected condition's contradiction rate
remains above both controls at all four levels** — that is, when H-f1's condition holds for that
judge — **and** the drop from the old wording to the corrected one, pooled over levels, is less
than half the old rate.

**Evaluability.** H-f2 uses H-f1's rule unchanged: a judge not evaluable there is not evaluable
here, and if fewer than 4 remain, H-f2 is `not evaluated` rather than falsified.

**Falsification.** H-f2 is falsified when fewer than 4 of the evaluable judges meet both clauses. Every
judge either meets both, or fails one, or fails both; the count is an integer in 0…`E` and the two
statements partition it. A judge that qualifies under H-f1 but whose rate more than halves falls
in the second, and is the outcome that says the phrase carried most of the effect.

**Why a half, and it is not the reasoning this clause first carried.** The first version argued
from the size of the contamination channel against the size of the effect — hand-written
reasoning about magnitudes, which has been wrong three times in this project in one week. It is
computable instead, from data already committed, by crossing the two **at the observation
level** rather than comparing their totals:

| obvious | contradictions | negated-phrase | overlap |
|---|---|---|---|
| 3 | 23 | 3 | 0 |
| 2 | 32 | 3 | 0 |
| 1 | 22 | 10 | 1 |
| 0 | 7 | 7 | 1 |

**They are nearly disjoint.** The defect explains none of the contradictions at the two easy
levels and at most one of seven at the hardest, so the matching totals at `--obvious 0` are a
coincidence. A halving is therefore a large drop against what the defect can account for, and
that is why the threshold sits there. `NEGATED` is a keyword regex and under-detects, which
moves this the other way — a fuller detector could only raise the overlap. Printed in
`results/validation/graded_summary.txt`.

**H-f2 subtracts two detectors, so it carries the same coverage condition.**
`c(inverted-corrected)` is read with `is the one` and `c(inverted-as-was)` with
`is the remaining`, and those two select nearly disjoint subsets of the same texts — 574
against 22, overlapping in one judgement. A difference in coverage between the arms would
appear as a difference in contradiction rate, which is the quantity H-f2 exists to read. Both
arms' match rates are printed side by side, and **H-f2 is `not evaluated` at any level whose two
arms differ in coverage by more than the same factor of 2.**

One thing that is measured rather than assumed: the corrected pattern fires **0 times in 2,400
`original` judgements and 0 in 2,400 `paraphrase`**, whose prompts never use the phrase. It is
not picking up ordinary English, so the risk is under-coverage of the corrected arm and not
spurious matching of the controls.

**If `E` = 4 the threshold equals the ceiling here too.** A hold is then *every judge this run
could measure*, not four out of five, and is reported in those words.

**H-f2 contains H-f1.** A judge qualifies under H-f2 only if it already qualifies under H-f1, so
the two are not independent tests and "two of three held" would be double-counting. H-f2 adds
one clause to H-f1 and is reported that way.

## H-f3 — the accuracy effect is a function of difficulty and changes sign

This is the claim that replaces the mis-specified `Δ(s)`. It names the quantity as a function of
difficulty rather than as one number.

Let `Δ(ℓ) = acc(original, ℓ) − acc(inverted-corrected, ℓ)`, per judge, interval as above.

**H-f3 holds when, for at least 4 of the evaluable judges, `Δ(3)` is positive with an interval excluding
0 and `Δ(0)` is negative with an interval excluding 0.**

**Falsification.** Fewer than 4 of the evaluable judges. A judge with either interval containing 0, or with
both signs the same, does not qualify — those are measurements that came out, and they count.

**Evaluability, on the same rule as H-f1.** H-f3 reads accuracy rather than the detector, so
coverage does not bear on it, but an incomplete run does. A judge whose run did not complete at
all four levels is **not evaluable**; if fewer than 4 judges are evaluable, H-f3 is
`not evaluated` rather than falsified, for the reason given under H-f1 — a pass that crashed is
not evidence about a judge.

**If `E` = 4 the threshold equals the ceiling here too**, and a hold is reported as *every
judge this run could measure*.

**This is a replication and is labelled one.** S1b observed exactly this shape on one model at
150 items — `+0.1667` at `--obvious 3` and `−0.0667` at `--obvious 0`, intervals excluding 0 at
both — so H-f3 predicts what has already been seen once, on a corrected prompt, at a different
sample size, on five judges. It is not a discovery and the result should not be read as one.
What it can do is fail, and a failure would say the sign change was a property of one model or
of the contaminated wording.

**Reachability.** The intervals at 150 items were ±0.0375 and ±0.0358 around effects of 0.1667
and 0.0667. At 1,763 items an interval scales by roughly the square root of the ratio, so both
effects stay well outside their intervals if their sizes hold. If the effect at `--obvious 0` is
smaller than the 0.0667 already seen, this is the clause that will fail first, and it is the
weakest of the three.

## What a hold would and would not establish

It **would** put the phenomenon this repository is named for on a public benchmark with a clean
prompt: a judge whose stated reasoning and whose verdict disagree, under inversion and not under
two controls, across difficulty, on five open-weight judges.

It **would not** rescue H1–H5, which stay mis-specified. It would not establish that inverting
the predicate costs accuracy — H-f3 says the opposite at the hard end. And it would not measure
polarity sensitivity in general: one inversion of one prompt on one benchmark is one point.

**It would also not close the wording question.** H-f2 asks whether the defect accounts for the
effect, not whether the corrected prompt is free of others. A second referential ambiguity that
nobody has read for would be invisible to it, and the way this one was found — reading the
judge's output rather than inspecting the wording — is the only method that has worked.
