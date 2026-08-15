# Pre-registration — the control-set exchangeability ladder at full size

Registered before the sets are built and before the test is run. The git timestamp on this
file, against the timestamp on `results/validation/exchangeable.txt`, is the evidence.

This is not a new experiment. It closes a question the existing artefact left open, on data
this repository already knows how to build, with no judge inference and no GPU.

## What is open, and what is not

`results/validation/exchangeable.txt` tests whether the three distractors in a control set are
exchangeable across their list positions — whether the position a distractor sits at predicts
anything about its text. Where it does, "the judge prefers the first distractor" is a live
alternative to "the judge prefers slot A"; where it does not, that alternative is unavailable.

At full size the ladder is half-built:

| `--obvious` | distractors | at 1,763 | verdict on characters |
|---|---|---|---|
| 0 | three of the item's own rejected | `p2_o0` | **differs** |
| 1 | one off-topic, two own rejected | *not built* | — |
| 2 | two off-topic, one own rejected | *not built* | — |
| 3 | three off-topic | `p1b_o3` | **undetermined** |

The 150-item sets settle nothing: the artefact's own equivalence test returns `undetermined`
for every level at that size, including levels whose permutation p rejects.

**The direction is not open.** `scripts/build_control_set.py:58` writes
`[off-topic] * obvious + [own rejected] * (3 - obvious)` with no shuffle, so at `--obvious` 1
and 2 the list position states which kind of distractor sits there, and the artefact says as
much in its own preamble. **What is open is whether the verdict is determinable**, which is a
question about spread against the rejecting scale, not about construction.

## H-d1 — the two missing rungs come back `differs` on characters

Built at `--n 1763 --seed 0`, `control_o1` and `control_o2` each return **`differs`** on the
characters property: the 95% interval on the spread lies entirely above the rejecting scale of
120.5 characters.

**Why this is a prediction and not arithmetic.** Full size does not confer determinacy.
`p1b_o3` is 1,763 items and still `undetermined` on characters, because its spread is 30.2 with
an interval of [10.3, 122.8] that reaches the scale. The prediction rests instead on the spread
being large at `--obvious` 1 and 2, and the basis for that is a between-set comparison rather
than a within-item one. In `results/validation/exchangeable.txt`, where every distractor is
off-topic the three position means are 1602.4, 1624.0 and 1632.6 characters (`p1b_o3`), and
where every distractor is the item's own rejected they are 1868.8, 1972.6 and 1852.1
(`p2_o0`) — two bands that do not overlap. A set that holds one kind at some positions and the
other kind at the rest should therefore span the gap between those bands, which is several
times the rejecting scale.

Those are different draws of different items, so the gap is an estimate and not a
measurement of what `control_o1` and `control_o2` will contain. If the within-item difference
is smaller than the between-set one, or if the per-item variance is wide enough, the interval
reaches the scale and the verdict is `undetermined` instead.

**Falsification.** H-d1 is falsified if either set returns anything other than `differs` on
characters — `alike`, or `undetermined`, or a build that does not complete. There is no third
outcome: the test emits exactly one of those three verdicts per row, and a level that is not
built is not evaluated and is reported as not evaluated.

**Aggregation.** One build per level at `--seed 0`, the seed every other control set in this
repository uses. The permutation test is 20,000 shuffles, the number already committed in the
artefact. Both levels must return `differs` for H-d1 to hold; one of two is a partial result
and is reported as one, not as a hold.

**Scope of the secondary properties.** Words and newlines are reported for every row and are
not part of H-d1. Characters is the property the rejecting scale was set on and the only one
this hypothesis is about; reading a hold out of whichever of the three happens to cooperate is
the failure this clause exists to prevent.

## What a hold would and would not establish

It **would** complete the ladder, and it would make explicit that the non-exchangeability at
`--obvious` 1 and 2 is a property of how this repository builds its control sets, not a
property of judges or of difficulty.

It **would not** change any verdict already recorded. H3 rests on `--obvious 3` at 1,763, which
is determinable and determined. H1, H2 and H5 are judged at their own levels and are not
rescored here. The artefact's existing sentence — that this decides nothing currently claimed —
survives a hold intact, and completing a ladder is worth doing on its own.

It **would not** license reading the `--obvious` 1 and 2 rows as evidence about difficulty. The
positions differ there because the builder concatenates two kinds of distractor in a fixed
order, and that is a fact about the builder.

## What is deliberately not registered here

The second parked item — a difficulty axis controlled by banding — is a separate design and a
separate registration. Nothing in this file bears on it, and mixing the two would put a
registered prediction next to an unregistered one.
