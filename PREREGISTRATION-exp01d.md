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

---

# Result

Written after the run. Everything above this line was committed as `5c17249`, before the sets
were built. The sets are `data/control_o1_full` and `data/control_o2_full`, built at
`--n 1763 --seed 0`, under those names rather than `control_o1` and `control_o2` because the
150-item sets of those names are the input the committed
`results/validation/exchangeable.txt` reports on and overwriting them would make that artefact
unregenerable.

## H-d1 holds, on both of its clauses

From `results/validation/exchangeable_full_ladder.txt`:

| set | mean at R1 | R2 | R3 | spread | p | 95% CI | scale | reading |
|---|---|---|---|---|---|---|---|---|
| `control_o1_full` | 1602.4 | 1868.8 | 1972.6 | 370.2 | 0.0000 | [287.6, 453.5] | 120.5 | **differs** |
| `control_o2_full` | 1602.4 | 1624.0 | 1868.8 | 266.4 | 0.0000 | [197.1, 351.1] | 120.5 | **differs** |

Both return `differs` on characters, and both intervals lie entirely above 120.5 — the
stronger clause, which the script's own verdict does not test, since it reads `differs` off
`p ≤ 0.05` alone. Words agree; newlines are `undetermined` for both and are not part of H-d1.

**The position means are the ones the construction predicts, and they are not merely close to
the other full-size sets — they are the same numbers.** `control_o1_full`'s first position is
1602.4, which is `p1b_o3`'s first; its other two are 1868.8 and 1972.6, which are `p2_o0`'s
first two. The builder draws three candidate replacements for every item at every level and
uses the first `obvious` of them, so the same seed puts the same texts in the same places and
only the count changes. The ladder is one draw seen at four cut points.

## The ladder, complete

| `--obvious` | positions | characters at 1,763 |
|---|---|---|
| 0 | own, own, own | **differs** (`p2_o0`) |
| 1 | off-topic, own, own | **differs** (`control_o1_full`) |
| 2 | off-topic, off-topic, own | **differs** (`control_o2_full`) |
| 3 | off-topic ×3 | **undetermined** (`p1b_o3`) |

Only the level where every distractor is drawn the same way fails to reject, and it fails to
reject without reaching `alike` on characters. **Every mixed level differs, and it differs
because the builder writes the two kinds in a fixed order** — which is a fact about
`scripts/build_control_set.py:58`, not about difficulty and not about any judge. Nothing here
rescores H1, H2, H3 or H5.

## Two artefacts, and which is authoritative for what

`exchangeable.txt` is unchanged and stays that way. `exchangeable_full_ladder.txt` is a later
run of the same script on a tree that also holds the two new sets.

The rows they share carry **identical** position means and spreads, which are deterministic,
and **p-values and intervals that differ in the third and fourth decimal**. The module RNG is
seeded once and drawn inside the loop over `sorted(glob(...))`, so inserting two directories
shifts the draws of everything sorting after them. Across the 21 shared rows **no verdict
changes**; `p1b_o3` on characters reads 0.7490 in one and 0.7518 in the other, and both are
the same estimate of the same quantity.

The older file is kept because `PREREGISTRATION-exp01b.md` cites six of its p-values, and a
pre-registration is not edited to agree with a re-run. That is the whole reason there are two
files rather than one regenerated one, and it is a better reason than tidiness.

## What was tried and abandoned

A `--sets` flag, so the two new rungs could be tested without re-running everything. It was
written, it worked, and it is not in the commit: **the rejecting scale is the smallest spread
among the sets that reject, so restricting the run to the two new sets made them the scale.**
`control_o2_full` was then judged against its own spread of 266.4 instead of against 120.5,
and still read `differs`, because that verdict comes from `p` and not from the scale. A flag
that silently redefines the yardstick is worse than no flag. The reverted script reproduces
`exchangeable.txt` exactly, which was checked rather than assumed.

## What is deliberately not registered here

The second parked item — a difficulty axis controlled by banding — is a separate design and a
separate registration. Nothing in this file bears on it, and mixing the two would put a
registered prediction next to an unregistered one.
