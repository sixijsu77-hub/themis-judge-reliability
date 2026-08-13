# 0002 — Making position, not polarity, the primary axis

Decided 2026-08-14, after the staged validation in `PREREGISTRATION.md` §6a and before the
full run it was gating. Supersedes nothing in
[0001](0001-polarity-implementation.md); that record still describes how polarity was
implemented and why.

## The decision

The polarity question keeps its answer and its data. It stops being the headline.

The measurement that goes to the full grid is the one in
[finding 0002](../findings/0002-position-fallback.md): a judge that is positionally unbiased
when the answer is obvious, and that falls back on position as the judgment gets harder.

## Why, and the part that is uncomfortable

**Changing what you measure after looking at data is the move that destroys a result.** It
is worth being precise about what is and is not being changed here, because the difference
is the whole defence.

The polarity hypotheses H1–H5 were pre-registered, the staged validation that would decide
whether to run them at full scale was pre-registered with its gates, and the gates were run.
What the gates returned is recorded in the pre-registration whatever it says. **No
hypothesis is being withdrawn, rewritten, or left unreported.** What changes is which of two
measured effects gets the remaining GPU time.

That is a resource decision, and the staged design existed to make exactly this kind of
decision cheaply. It cost about 3 GPU-hours instead of 46.

## What the polarity axis actually returned

Measured, and reported in full in the pre-registration:

- the effect on accuracy depends on how hard the item is — `+0.1667` where the answer is
  obvious, `+0.0317` with a confidence interval including zero one level down, and `−0.0667`
  on the unmodified item, where the inverted prompt scores *higher*
- the judge's stated conclusion contradicts its own emitted letter in the inverted condition
  at every level and in neither control condition, ever: 0 of 93 and 0 of 227 against 23 of
  103 at the easiest level
- but the inverted wording is ambiguous. "The remaining assistant" does not say remaining
  after what, and the judge reads it as the one left among the *failures* in 1.6% to 6.4% of
  the sentences that use it. That is our defect, found by reading the judge's output, and it
  contaminates the contradiction count by an amount we cannot cleanly subtract

The second of those is a real signal and it is not being thrown away. It is not strong
enough, on one judge with a wording we know to be flawed, to spend two days on.

## Four things went wrong, and three of them are structural

Written down because the next experiment inherits them.

**The phenomenon was imported from a setting that does not exist here.** The source
observation was a boolean judgment described against its schema. RewardBench 2 has no
boolean and no schema. [0001](0001-polarity-implementation.md) says as much and picks the least-bad construction; a least-bad
construction is still a construction.

**The treatment is a text we wrote, so the effect is partly a property of our writing.** Two
rounds of fixing ambiguity — a negation scope, then a referent — and a third remains. This
does not converge by fixing once more. Doing it properly needs several independent inverted
wordings, which multiplies the cost and invites the reply that we kept the ones that worked.

**The signal is smaller than a source of variance nobody was controlling.** Position moves
accuracy by 0.5533 on the same items. Polarity moves it by at most 0.1667, and by less than
that everywhere the items are realistic.

**H1–H5 are the wrong shape**, not merely unsupported. They assume one `Δ(s)` per subset.
The data says `Δ` is a function of item difficulty that changes sign. A hypothesis that
cannot be true or false because the quantity it names is not a single number is a
specification error, and it is ours.

## What this costs

**Position bias in LLM judges is not our discovery.** It is documented, and we make no
novelty claim about the phenomenon. What these runs add is its size on this benchmark, the
fact that it appears only as the judgment gets harder rather than being a standing
preference, and that it is measured under a prompt that instructs against it.

**The repository's stated question changes.** README and the pre-registration are edited to
say what is now being measured, with the polarity result kept and linked rather than
removed.

**One judge.** Everything here is one 7 B model. The claim does not leave that until the
grid runs.
