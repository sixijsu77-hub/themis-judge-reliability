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

---

# Result

Written after the run. Everything above this line was committed as `ef06e4b` and pushed at
`2026-08-16 00:06:59 UTC`, before `G1` existed as a phase. Full tables in
`results/validation/g1_polarity.txt`; 288 of 288 exp01 records pass the schema check.

## H-g1 is `not evaluated`, and H-g2 with it

Three of the four levels could be read and **all three show the effect**. The fourth could not
be read, and the registered rule says that makes the hypothesis `not evaluated` rather than
falsified — a level that could not be read is not evidence that the effect is absent.

| obvious | original | paraphrase | inverted (old) | inverted (corrected) | corrected − control | reading |
|---|---|---|---|---|---|---|
| 3 | 1 of 433 | 3 of 1083 | 100 of 339 | 57 of 1235 | [+0.0316, +0.0556] | not evaluated (coverage) |
| 2 | 2 of 318 | 1 of 778 | 162 of 838 | 100 of 1221 | [+0.0570, +0.0927] | **shows the effect** |
| 1 | 1 of 285 | 2 of 582 | 66 of 678 | 84 of 987 | [+0.0629, +0.1003] | **shows the effect** |
| 0 | 0 of 143 | 0 of 325 | 17 of 416 | 57 of 732 | [+0.0587, +0.0984] | **shows the effect** |

Controls run 0.0% to 0.6% throughout. H-g2 is `not evaluated` by its own clause, which makes it
conditional on H-g1.

## The registered coverage rule is mis-scoped, and this run is what showed it

**The rule is not being changed and the verdict stands.** What follows is a defect in the
registration, found by running it, recorded rather than repaired.

The rule gates a level on the ratio between the **two inverted arms** — corrected against
as-was. Its stated reason is that a ratio past 2 means the two detectors select different
populations, *so a rate difference between them stops being a wording effect.* That reason is
about subtracting one inverted arm from the other, which is **H-g2's comparison**. H-g1 does not
subtract the arms: it compares the corrected arm against the two controls.

So the condition that blocked level 3 bears on H-g2 and was applied to H-g1.

**And it fired in the direction it was not written for.** It exists to stop a null being read off
an under-covered arm. At level 3 the corrected arm covers 1,235 of 1,763 against the old arm's
339 — the corrected detector covers **more**, not less, and the symmetric form of the rule trips
on that too. A rule written to prevent a false negative blocked a positive reading.

**It is mis-scoped twice, and the second half is in the exploratory arm.** The rule is a ratio
against the old inverted condition, and that arm can itself be unreadable. The old detector
matches 149, 83, 58 and 45 of `RISE-Judge-Qwen2.5-7B`'s 1,763 rows, because that is not how it
phrases a conclusion — so at every level the gate divides by a baseline that is under-covered,
and all four ratios are large for a reason that has nothing to do with the corrected arm. A
rule that references an arm which can fail on its own terms fails with it.

So: **symmetric where the threat is one-sided, and referenced to an arm that can itself be
unreadable.** Whether to re-register with the condition scoped to H-g2, made one-sided, and
referenced to something that cannot be empty is not decided here, and **this data cannot be
re-scored under a changed rule** — that is choosing the rule after seeing the result, which is
the thing this file exists to prevent.

## The exploratory judge

`RISE-Judge-Qwen2.5-7B` is `not evaluated` at **all four** levels, for the same coverage rule:
the old inverted detector matches 45 to 149 of its 1,763 verdicts, because it does not phrase
its conclusions the way that detector expects. Its ratios run 2.36 to 5.82.

No hypothesis was registered on it and none is decided. Its cells are in the artefact.

**And it is not the same shape as the confirmatory judge.** Its controls do not sit near zero:
the highest control rate is 0.1565 against Qwen's 0.0063. It contradicts its own reasoning
under `original` and `paraphrase` as well, so inversion there raises an effect that is already
present rather than creating one. The intervals are read against the higher control and are
arithmetically right; a reader placing them beside the confirmatory judge's would see one
phenomenon where there are two. The artefact says so where the table is printed.

## What is worth saying that no hypothesis carries

The phenomenon **survives the corrected wording** on the confirmatory judge, at every level that
could be read, against controls that sit at or near zero. At the two hardest levels the
corrected rate is *higher* than the old wording's — 8.5% against 9.7% at `--obvious 1` and 7.8%
against 4.1% at `--obvious 0` — so the ambiguous phrase was not inflating the effect there.

That is an observation and not a verdict. The registered verdict is `not evaluated`.

## One row is withheld from publication, and it is declared

`results/exp01/G1_R-I-S-E__RISE-Judge-Qwen2.5-7B_o1_0_inverted_fixed.jsonl` carries 1,762 of
the 1,763 rows its run produced. The metadata records `n_items` as 1,763 and `excluded` as 1
with its reason, and `scripts/check_exp01_records.py` fails any file where those do not add up,
so the withholding cannot become silent.

**Why.** The pre-push publication check matched one string in that row, inside a book title in
the judge's own generated text. The term list is not in this repository and the matched string
is not recorded anywhere, which is the point of both. Whether the match was incidental is a
judgement about material this repository does not contain, so it was not made here.

**What it costs the measurement: nothing that is reported.** The row's conclusion matched no
detector, so it entered no contradiction cell. Its removal moves one figure in the artefact —
the coverage ratio at `--obvious 1` for the exploratory judge, which rises by three
thousandths because that cell's denominator fell by one row in 1,763. The artefact holds the
value after the exclusion; the value before it is in no committed output and is not quoted
here for that reason. Every contradiction count, every rate and every
reading is unchanged, and that level was `not evaluated` before and after.

**Why withholding rather than relaxing the check.** The two costs are not comparable. A row
withheld and recorded costs a row and this paragraph whether the judgement was right or wrong.
A pattern narrowed to admit the string costs nothing if the judgement was right and, if it was
wrong, publishes to a history that this repository has previously had to delete and rebuild to
clear. The recoverable option was taken.

The exclusion is on a string in generated text and not on any property of a verdict, so it is
not selection on the measured axis.
