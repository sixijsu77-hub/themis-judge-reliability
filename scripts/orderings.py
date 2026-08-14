"""The candidate arrangements, derived once so no caller retypes them.

`run_generative_v2.py --ordering N` selects the Nth permutation of the four candidates,
where the first element of the permutation is the chosen response and the rest are the
distractors in dataset order. Two subsets of the 24 matter and they are not the same set,
which is the mistake this module exists to prevent.
"""
import itertools

ALL = list(itertools.permutations(range(4)))

# The four that move the correct answer through every slot while leaving the three
# distractors in one relative order. This separates a position effect from a
# distractor-arrangement effect in the *accuracy*, and P1a used it for that.
#
# It cannot carry a statistic about which letter the judge emitted, and this is kept rather
# than deleted because that is the record. Slot A holds R1 in all three arrangements where
# an error at A is possible, so "the judge named A" and "the judge named the first
# distractor" are one count. build_control_set.py writes the off-topic substitutes first, so
# the first distractor is obviously wrong at --obvious 3, 2 and 1 and plausible at 0; a
# statistic reading slot A therefore steps when the control set changes what sits there,
# with the judge unchanged. Measured and tabulated by scripts/arrangement_sets.py.
FIXED_DISTRACTORS = [i for i, p in enumerate(ALL) if [x for x in p if x != 0] == [1, 2, 3]]

# The property a statistic about slots actually needs: every slot holds every candidate
# exactly once across the set, so naming a slot says nothing about which candidate was
# named. 24 of the 10,626 four-element subsets have it and 3 of those also keep the
# distractors in one cyclic order; this is the first of the three.
#
# The cost is the mirror of the above: the distractors are permuted between arrangements, so
# an accuracy spread taken over this set mixes position with distractor arrangement. The
# paired difference between two slots named in advance does not, because both arrangements
# hold the same four candidates. Only P2's 24 arrangements are clean on both counts.
SLOT_BALANCED = [0, 9, 16, 18]

# What the pilot behind exp01b actually ran. It visits all four slots, so letter
# frequencies from it are sound, but two of its four also permute the distractors, so any
# accuracy spread computed on it mixes the two factors. Kept so the pilot's summaries stay
# faithful to the data that produced them.
PILOT = [0, 6, 14, 21]

SLOT_OF = {i: "ABCD"[ALL[i].index(0)] for i in range(len(ALL))}

assert len(ALL) == 24
assert len(FIXED_DISTRACTORS) == 4
assert len(SLOT_BALANCED) == 4
assert all(sorted(ALL[i][j] for i in SLOT_BALANCED) == [0, 1, 2, 3] for j in range(4))
assert sorted(SLOT_OF[i] for i in FIXED_DISTRACTORS) == list("ABCD")
assert sorted(SLOT_OF[i] for i in PILOT) == list("ABCD")
assert FIXED_DISTRACTORS != PILOT
