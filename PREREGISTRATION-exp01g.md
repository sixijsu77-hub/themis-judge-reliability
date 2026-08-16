# Pre-registration — the polarity axis on the two judges that can carry it

**Status: not run.** Committed before any pass of it exists. The git timestamp on this file,
against the first `G1_` result file, is the evidence.

This does not amend `PREREGISTRATION-exp01f.md`. H-f1 to H-f3 stay as registered and stage 1
stays `not evaluated`; what follows is a separate registration over a different population,
because the population is what changed.

## Why exp01f could not be run as written

The phenomenon is a verdict that contradicts its own stated reasoning, so it needs a judge that
states reasoning. Measured over 7,052 committed `P2b` verdicts each
(`results/validation/f1_stage1.txt` §0), the five screened judges divide:

| judge | verdicts carrying both reasoning and a parsed verdict | reads as |
|---|---|---|
| RISE-Judge-Qwen2.5-7B | 99.490% | states reasoning |
| Qwen2.5-7B-Instruct | 98.497% | states reasoning |
| Llama-3-OffsetBias-8B | 2.056%, and a third of its long outputs do not parse | emits non-judgements too |
| Con-J-Qwen2-7B | 0.482% | can, and almost never does |
| Skywork-Critic-Llama-3.1-8B | 0.000% in 7,052 | cannot |

H-f1's threshold of four judges is above what this screen can supply, and that was true before
it was registered. **Two judges can carry the measurement**, so this registers a design for two.

## The asymmetry this design has, stated before it runs

**All 48 files of the existing contradiction evidence are `Qwen/Qwen2.5-7B-Instruct`.** Every
observation of this phenomenon in this repository comes from one of the two judges available.
RISE has never been measured on this axis.

A conjunction over both judges would therefore report the likely outcome — Qwen replicating,
RISE not showing — as a single `falsified`, collapsing one replication and one first look into
one negative. **So there is no conjunction and no aggregate threshold.** The two judges are
registered as two different things, and the labels are fixed here rather than chosen when the
numbers arrive: this repository has once attached `(exploratory)` to a confirmatory block after
the fact, and the defect was the timing, not the word.

## The run

| | |
|---|---|
| judges | `R-I-S-E/RISE-Judge-Qwen2.5-7B`, `Qwen/Qwen2.5-7B-Instruct` |
| levels | `--obvious` 3, 2, 1, 0 at 1,763 items |
| conditions | original, paraphrase, inverted **corrected**, inverted **as it was** |
| arrangement | `SLOT_BALANCED[0]`, so position cannot vary between conditions |
| passes | 16 per judge, 32 in total |
| phase tag | `G1` |

Detectors, coverage rule and the `not evaluated` state are exp01f's unchanged: a condition the
detector never matched is `not evaluated` and not zero; a level whose corrected-arm coverage is
outside a factor of 2 of the old inverted arm's is `not evaluated` and no null from it counts.

## H-g1 — confirmatory: the contradiction effect replicates on Qwen with the corrected wording

For each level ℓ, `c(cond, ℓ)` is the fraction of verdicts whose conclusion the condition's
detector matched and whose matched conclusion names a different candidate than the verdict does.
Interval: bootstrap over items, 10,000 resamples, 95%.

**H-g1 holds when, for `Qwen2.5-7B-Instruct`, the interval on
`c(inverted-corrected, ℓ) − max(c(original, ℓ), c(paraphrase, ℓ))` excludes 0 at all four
levels.**

This is a replication and is labelled one. The same judge showed 5.8%–22.3% under inversion
against 0 of 1,001 control observations at 150 items on the contaminated wording; H-g1 asks
whether that survives a corrected prompt at 1,763 items.

**Falsification.** H-g1 is falsified when the interval fails to exclude 0 at one or more of the
four levels. Levels are four; "all four" and "fewer than four" partition every outcome.

**Not evaluated.** A level whose coverage is outside the registered factor, or whose pass did not
complete, is `not evaluated`; if any of the four is, H-g1 is `not evaluated` rather than
falsified — a level that could not be read is not evidence that the effect is absent.

**Reachability.** Against a control of zero, four contradictions clear the interval at every
sample this run produces; the smallest rate previously observed is 0.0583 against a detectable
0.0023 at 1,763 items. The risk is not power. It is that the corrected wording removes the
effect, which is what the fourth condition exists to measure.

## H-g2 — confirmatory: the wording defect does not account for it, on Qwen

**H-g2 holds when H-g1 holds and the drop from `inverted-as-was` to `inverted-corrected`, pooled
over levels, is less than half the old rate.**

The half is carried over from exp01f unchanged, and its justification is the disjointness
already measured: crossing contradictions against the misread phrase at the observation level
gives overlaps of 0, 0, 1, 1 across the four levels
(`results/validation/graded_summary.txt`). The defect explains none of the contradictions at the
two easy levels and at most one of seven at the hardest.

**Falsification.** H-g2 is falsified when H-g1 holds and the drop is half or more. When H-g1 is
falsified or `not evaluated`, H-g2 is `not evaluated` — it is a statement about an effect whose
presence H-g1 establishes, and it cannot be read without one.

## RISE — exploratory, and no hypothesis is registered on it

`RISE-Judge-Qwen2.5-7B` is run on the same 16 cells and **reported per level with intervals and
no threshold**. There is no prior observation of this phenomenon on this judge, so any outcome
is a first look. It is reported under a heading saying so.

**It cannot falsify anything registered here**, and a result on it is not evidence about judges
in general — it is one judge, chosen because it is one of two that can be measured at all.

## What a hold would and would not establish

It **would** say the phenomenon this repository is named for survives a corrected prompt at full
scale on the judge every prior observation came from.

It **would not** generalise. Two judges, one confirmatory and one exploratory, both Qwen-family
7B. The bound in `f1_stage1.txt` §0 says why there are not more, and it is a bound on the five
judges this screen admitted rather than on the size class.

It **would not** measure polarity sensitivity in general. One inversion of one prompt on one
benchmark is one point, and the accuracy half of that question is already reported as
mis-specified in `PREREGISTRATION.md`.

## What is deliberately not here

Any judge found by the widened screen registered in `PREREGISTRATION-exp01h.md`. That search
runs separately and **a judge it admits does not enter this registration** — adding one after
this run's numbers are visible would fix the denominator after the first result, which is the
reason there are two files and not one.
