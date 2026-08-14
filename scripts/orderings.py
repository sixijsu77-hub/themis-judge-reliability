"""The candidate arrangements, derived once so no caller retypes them.

`run_generative_v2.py --ordering N` selects the Nth permutation of the four candidates,
where the first element of the permutation is the chosen response and the rest are the
distractors in dataset order. Two subsets of the 24 matter and they are not the same set,
which is the mistake this module exists to prevent.
"""
import itertools

ALL = list(itertools.permutations(range(4)))

# The four that move the correct answer through every slot while leaving the three
# distractors in one relative order. Only these separate a position effect from a
# distractor-arrangement effect.
FIXED_DISTRACTORS = [i for i, p in enumerate(ALL) if [x for x in p if x != 0] == [1, 2, 3]]

# What the pilot behind exp01b actually ran. It visits all four slots, so letter
# frequencies from it are sound, but two of its four also permute the distractors, so any
# accuracy spread computed on it mixes the two factors. Kept so the pilot's summaries stay
# faithful to the data that produced them.
PILOT = [0, 6, 14, 21]

SLOT_OF = {i: "ABCD"[ALL[i].index(0)] for i in range(len(ALL))}

assert len(ALL) == 24
assert len(FIXED_DISTRACTORS) == 4
assert sorted(SLOT_OF[i] for i in FIXED_DISTRACTORS) == list("ABCD")
assert sorted(SLOT_OF[i] for i in PILOT) == list("ABCD")
assert FIXED_DISTRACTORS != PILOT
