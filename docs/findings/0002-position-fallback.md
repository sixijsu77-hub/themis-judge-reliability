# 0002 — A judge that is positionally unbiased on easy items falls back on position as they get harder

Recorded 2026-08-14. This came out of a control built for a different purpose, which is
worth saying at the top: we were not looking for it.

> **Superseded in part, 2026-08-14, later the same day.** The letter-frequency reading below
> — that the judge *acquires* a first-slot preference as items get harder — does not survive
> two things found afterwards: an identity that makes the first-slot rate climb whenever
> accuracy falls, and an ordering defect in the control set that makes the hardest distractor
> sit at a fixed place in the list. Both are set out in
> [`docs/errata.md`](../errata.md). The accuracy tables and the position effect itself stand;
> a confound-free measurement across four judges is in
> [`results/validation/within_candidate.txt`](../../results/validation/within_candidate.txt).
> The text below is left as it was written.

## What we ran

The same 150 benchmark items at four difficulties. Only the distractors change — three, two,
one or none of them are responses to a *different* question, so `obvious = 0` is the
unmodified benchmark item and `obvious = 3` is one whose answer is not in dispute. Every
level runs at four candidate arrangements, placing the correct answer in each slot in turn.
The prompt is upstream's, verbatim.

`Qwen/Qwen2.5-7B-Instruct` through vLLM, `temperature=0`, evaluator pinned at `05a9005`
plus [the ordering patch](../../harness/run_generative_v2.patch). Raw per-item logs
including the judge's own text: [`results/validation/graded/`](../../results/validation/graded).
Every table below is printed by
[`scripts/summarize_graded.py`](../../scripts/summarize_graded.py).

## What we got

```
position: the same items, the correct answer moved, upstream's own prompt

  obvious  chosen at A   chosen at B   chosen at C   chosen at D    spread
        3       0.9933        0.9933        0.9933        0.9867    0.0067
        2       0.9400        0.9467        0.9467        0.4133    0.5333
        1       0.9067        0.9267        0.4800        0.3000    0.6267
        0       0.8533        0.5333        0.3933        0.3000    0.5533
```

```
  letters the judge emitted, pooled over the four positions
  (the correct answer sat in each slot exactly as often)

  obvious            A             B             C             D
        3   151 (25.2%)    152 (25.3%)    149 (24.8%)    148 (24.7%)
        2   227 (37.8%)    148 (24.7%)    142 (23.7%)     83 (13.8%)
        1   298 (49.7%)    141 (23.5%)    102 (17.0%)     59 ( 9.8%)
        0   339 (56.5%)    127 (21.2%)     81 (13.5%)     53 ( 8.8%)
```

**On items whose answer is obvious the judge is as close to unbiased as 600 draws can show:
25.2, 25.3, 24.8, 24.7.** It is not that the judge has a standing preference for the first
slot. It acquires one as the judgment gets harder, and on the unmodified benchmark item it
answers `[[A]]` 339 times against `[[D]]` 53 — while the correct answer sat in each slot
exactly as often.

Accuracy follows: identical items score 0.8533 with the answer first and 0.3000 with it
last. Every arrangement was scored by the same code on the same 150 items; the only thing
that changed is which slot the correct answer occupies.

The prompt this was measured under is upstream's own, and it contains the sentence:

> Avoid any position biases and ensure that the order in which the responses were presented
> does not influence your decision.

## Why this matters for a published score

`run_generative_v2.py` draws the arrangement per item from an unseeded
`np.random.randint(0, 4)` ([allenai/reward-bench#272](https://github.com/allenai/reward-bench/issues/272)).
That draw averages the bias out *within* a run — the four-position mean at `obvious = 0` is
0.5200, and a run with random placement lands near it. But the number a judge earns is then
a mixture of how well it judges and how strongly it falls back on position, and the two are
not separable from the published score. Two judges of equal skill and unequal position
sensitivity do not score the same.

The bias also has a direction, which the earlier per-run variance measurement could not
show: it is toward the first slot, and it strengthens monotonically as the item gets harder.

## What we have not established

**One judge.** Everything above is `Qwen2.5-7B-Instruct`. Whether the pattern holds for
purpose-built judges, or for larger models, is unmeasured. It is the obvious next thing to
run and the reason the ordering patch exists.

**Cause.** We can say the judge falls back on position and by how much. We cannot say why,
and nothing here distinguishes a decoding-order artefact from something about how the
candidates are attended to.

**The distractors are ordered, and that was not noticed until four judges had run.** The
control set writes the foreign distractors first and the item's own rejected responses last,
so "the hardest candidate" and "a fixed position in the list" are the same thing. With the
arrangement set holding the list in one relative order, that is enough to manufacture the
letter distribution above. See the errata entry; it is the reason this finding is marked
superseded in part.

**Four arrangements, and not the right four.** These runs place the correct answer in each
slot, which is all the letter frequencies need. They do **not** hold the three distractors
in a fixed relative order: two of the four arrangements used also permute the distractors.
So the accuracy spread reported above mixes where the correct answer sits with how the
distractors are arranged, and cannot be read as position alone. Only permutation indices
0, 6, 8, 9 have that property, and the measurement that follows this one uses them —
enumerated by [`scripts/check_decision_rules.py`](../../scripts/check_decision_rules.py).
The letter-frequency table is unaffected.

**The 0.9933 row is a ceiling.** At `obvious = 3` there is no room for position to matter,
so "no bias when easy" is partly a statement about the measurement, not only about the
judge. `obvious = 2` at 0.9400–0.9467 has room and still shows almost no bias in three of
four slots, which is the stronger version of the claim; the fourth slot already drops to
0.4133.

## Where this leaves the experiment this repository was built for

exp01 asked whether a judge's verdict survives having the question asked in the opposite
direction. That question now has a partial answer, recorded in
[`PREREGISTRATION.md`](../../PREREGISTRATION.md), and it is weak: on accuracy the effect is
large only where the answer is obvious, indistinguishable from zero at `obvious = 1`, and
reversed at `obvious = 0`. The polarity effect is also entangled with a defect in the
inverted wording that we found by reading the judge's output, and both are reported.

Position is the larger and cleaner effect, and it does not depend on any prompt we wrote.
The decision to make it the primary axis, and what that decision costs, is in
[`docs/decisions/0002-changing-the-primary-axis.md`](../decisions/0002-changing-the-primary-axis.md).
