# 0003 — judges hold slot dispositions that differ in direction, and a four-way score is a draw from them

Recorded 2026-08-15. Supersedes the reading in
[`0002-position-fallback.md`](0002-position-fallback.md), which is marked superseded in part
and left as written.

Five open-weight judges, 240 evaluator passes, two benchmarks, 1,763 items each. Every table
below is printed by a script from `results/*.jsonl`; none is retyped.

## The finding

**Each judge has a direction it falls toward when it is wrong, the direction differs between
judges, and it is stable.** On the unmodified RewardBench 2 item, the share of a judge's
errors landing on the first slot runs from 0.7876 to 0.1335 against a null of 1/3 — one judge
pushing errors onto the first slot, another pushing them away. That direction survives
changing the arrangement set (4 of 5 judges,
[`sign_stability.txt`](../../results/validation/sign_stability.txt) J2″) and changing the
benchmark entirely (5 of 5, on UltraFeedback, J3).

**A published four-way score is one sample from that.** With only the correct answer's
position changed on identical items, a judge's accuracy moves by up to 0.6205 and by as
little as 0.0686 — a ninefold difference in exposure between judges. Those two figures score
an unparseable verdict 0; the convention moves them, which is the next paragraph and is
stated wherever they appear. The ranking those scores
induce inverts: a judge that is first at one position is last at another
([`leaderboard_exposure.txt`](../../results/validation/leaderboard_exposure.txt) §1–2).
Upstream draws that position from an unseeded call
([#272](https://github.com/allenai/reward-bench/issues/272)), so which ordering a published
run reports is not fixed by the judges.

**The same issue's other half moves it too.** An unparseable verdict is credited 0.25
upstream and 0 here. First place changes on that convention alone, and the two judges that
swap are the two with parse failures (§3). **The row averaged over the four arrangements is
not a stable ordering to fall back on** — it is stable under neither axis.

## What was retracted on the way, and why it matters more than the finding

The first account of this said a judge *acquires* a first-slot preference as items get
harder, while being almost unbiased where the answer is obvious. Both halves are gone.

**The rise was arithmetic.** Writing `f_A` in terms of accuracy and error placement gives
`f_A = (1/4) a_A + E_A (1 - a)`, so at fixed placement `d f_A / d a = 1/4 - E_A`. Any judge
with `E_A > 1/4` shows a rising first-slot rate as it becomes less accurate **without its
behaviour changing at all** ([`decomposition.txt`](../../results/validation/decomposition.txt)).

**The "unbiased when obvious" reading rested on four usable errors.** At the difficulty where
the answer is not in dispute, the statistic had almost nothing to divide by.

**And the control set supplied most of the gradient.** `build_control_set.py` wrote its
off-topic substitutes first and the item's own rejected responses last, so a fixed place in
the distractor list carried a fixed quality; the four arrangements then mapped list position
to slot. A judge that merely prefers the hardest distractor produces a letter distribution
that reads as a slot preference, and the apparently preferred slot moves between difficulty
levels because the hard distractor moves
([`arrangement_sets.txt`](../../results/validation/arrangement_sets.txt)).

The arrangement set was rebuilt so that every slot holds every candidate equally often — 24
of the 10,626 four-element subsets do, three of those keep the distractors in one cyclic
order — and the grid was re-run on it. **H1 still holds on the corrected set.** It does not
mean what its name says: a judge whose slot weights are the same four numbers at every
difficulty reproduces the observed slopes, because difficulty changes how much the candidates
differ and a constant weight expresses itself more when they are alike
([`constant_preference.txt`](../../results/validation/constant_preference.txt)).

## The registered verdicts, as registered

| | | |
|---|---|---|
| H1 | slope of `E*_A` over difficulty is positive | **holds** by its rule; no judge clears its own constant-preference twin |
| H2 | `E*_A` at `--obvious 0` excludes 1/3 upward for ≥4 | **falsified**, 3 of 5 |
| H3 | `E*_A` at `--obvious 3` contains 1/3 for ≥4 | **falsified**, 2 of 5, and in opposite directions |
| H4 | `V > W` | **not evaluated** — §7 withdrew it when H3 failed |
| H5 | `E*_A` negatively rank-correlated with accuracy | **holds** directionally; the sign depends on which accuracy axis it is read against |
| J1 | same sign in both halves of the items | **not evaluated** — the sample cannot answer it |
| J2 | same sign at both difficulties | **falsified**, and carries little: its arms differ in three things |
| J2″ | same sign across arrangement sets | **holds**, 4 of 5 |
| J3 | same sign on a second benchmark | **holds**, 5 of 5 |

§7 of [`PREREGISTRATION-exp01b.md`](../../PREREGISTRATION-exp01b.md) registered that H3's
failure would leave "a magnitude measurement on one benchmark". It is reported that way and
per judge, because pooling inverts it: one judge carries 70.3% of the usable errors and the
natural weighting reports the reverse of what two of the five do.

## What this does not establish

**Five judges, all 7–8B open-weight, none with a published score.** No open-weight generative
judge that fits on a 24 GB card has one, which is why the leaderboard section says the
mechanism is upstream's and the magnitudes are ours.

**The difficulty axis has no clean test in this design.** Every version of it is unpowerable:
at `--obvious 3` two judges expect fewer errors than the floor, so P(a readable sign for 4 of
5) = 0.0100 ([`power_j2prime.txt`](../../results/validation/power_j2prime.txt)). The one
comparison available disagrees with the others, and it cannot be explained away — at
`--obvious 3` the distractors test as exchangeable, so that reading is a clean slot
measurement. **We do not have a design for this that survives its own power check.**

**Slot or candidate is not separated.** No set of four arrangements can move a candidate
without moving the correct answer; that needs the six distractor orderings within a position,
which only the full 24 provide.

**The stability results are not independent of each other.** J2″'s two arms had been compared
informally before the hypothesis was computed, which the pre-registration records.

## Reproducing

```bash
.venv/bin/python scripts/summarize_p1.py            # H1, H2, H3, H5, and the pooling table
.venv/bin/python scripts/sign_stability.py          # J1, J2, J2″, J3
.venv/bin/python scripts/leaderboard_exposure.py    # the exposure and the two conventions
.venv/bin/python scripts/constant_preference.py     # the calibrated null
.venv/bin/python scripts/decompose_f_a.py           # the identity behind the retraction
.venv/bin/python scripts/check_exp01_records.py --quiet
```
