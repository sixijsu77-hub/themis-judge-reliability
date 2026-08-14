#!/usr/bin/env python3
"""Work out which four arrangements can carry a statistic about slots.

P1a used four arrangements chosen so the three distractors keep one relative order. That
makes the accuracy spread clean, and it turned out to make every statistic about *which
letter the judge emitted* meaningless, because with the distractors in a fixed order a slot
and a candidate are the same thing. This enumerates what the requirement should have been
and which sets of four satisfy it.

  python scripts/arrangement_sets.py
"""
import itertools
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orderings import ALL, FIXED_DISTRACTORS, PILOT

NAME = {0: "chosen", 1: "R1", 2: "R2", 3: "R3"}
# How build_control_set.py assembles the list: the off-topic substitutes first, then as many
# of the item's own rejected responses as are needed to reach three.
COMPOSITION = {d: ["off-topic"] * d + ["own rejected"] * (3 - d) for d in (3, 2, 1, 0)}


def occupancy(indices):
    """{slot: Counter(candidate -> times it sits there)} over a set of arrangements."""
    return {s: Counter(NAME[ALL[i]["ABCD".index(s)]] for i in indices) for s in "ABCD"}


def print_occupancy(label, indices):
    occ = occupancy(indices)
    print(f"\n  {label}: {indices}")
    print(f"    {'slot':>5s}  " + "".join(f"{NAME[c]:>10s}" for c in (0, 1, 2, 3)))
    for s in "ABCD":
        print(f"    {s:>5s}  " + "".join(f"{occ[s][NAME[c]]:>10d}" for c in (0, 1, 2, 3)))
    return occ


def is_latin(indices):
    """Every slot holds every candidate exactly once across the four arrangements."""
    return all(set(ALL[i][j] for i in indices) == {0, 1, 2, 3} for j in range(4))


def distractor_cycle(i):
    """The three distractors in slot order, as a tuple."""
    return tuple(c for c in ALL[i] if c != 0)


def cyclic_rotations(t):
    return {t[k:] + t[:k] for k in range(len(t))}


def main():
    print(__doc__.split("  python")[0].strip() if __doc__ else "")

    print("\n" + "=" * 78)
    print("1. What sits in each slot, and what the control set puts in the list")
    print("=" * 78)
    print_occupancy("the set P1a used (FIXED_DISTRACTORS)", FIXED_DISTRACTORS)
    print("\n    Slot A holds R1 three times and the chosen answer once. An error can only")
    print("    happen when the chosen answer is elsewhere, so on every arrangement where an")
    print("    error at A is possible, the thing at A is R1. Slot D is the same with R3.")

    print("\n  what the distractor list contains, by difficulty "
          "(build_control_set.py line 58)")
    print(f"    {'obvious':>7s}  " + "".join(f"{r:>16s}" for r in ("R1", "R2", "R3")))
    for d in (3, 2, 1, 0):
        print(f"    {d:7d}  " + "".join(f"{c:>16s}" for c in COMPOSITION[d]))
    print("\n    The off-topic substitutes are written first, so the item's own rejected")
    print("    responses -- the plausible ones -- are always at the end of the list.")

    print("\n  overlaying the two:")
    print("""
    E*_A counts how often an error names slot A. On this set slot A holds R1 whenever an
    error there is possible, and R1 is off-topic at --obvious 3, 2 and 1 and only becomes a
    plausible response at --obvious 0. So E*_A counts how often the judge picks the first
    entry of the distractor list, and that entry changes from an obviously wrong answer to a
    genuinely competitive one as difficulty rises. It is a measure of the control set's
    construction, not of the judge's feeling about position.""")

    print("\n" + "=" * 78)
    print("2. The pilot set, and what the requirement should have been")
    print("=" * 78)
    print_occupancy("the pilot set (PILOT)", PILOT)
    print("\n    Slot A holds R1 twice and R2 once, so at --obvious 1 -- where R1 is")
    print("    off-topic and R2 is a real rejected response -- one of the three arrangements")
    print("    contributing to E*_A offers a plausible candidate at A and two do not. The")
    print("    mixture is why the pilot's E*_A was flat across difficulty while P1a's, which")
    print("    offers the same candidate at A every time, stepped when that candidate")
    print("    changed character.")
    print("""
    The requirement was never "hold the distractors in a fixed relative order". That fixes
    the accuracy spread and breaks everything else. What a statistic about slots needs is
    that a slot not be a candidate: each slot must hold each of the four candidates equally
    often across the set, so that naming a slot says nothing about which candidate was
    named. Neither set has that. FIXED_DISTRACTORS is the worse of the two because it is
    perfectly confounded; PILOT is partly confounded, which is harder to reason about.""")

    print("\n" + "=" * 78)
    print("3. The sets of four where every slot holds every candidate exactly once")
    print("=" * 78)
    latin = [c for c in itertools.combinations(range(24), 4) if is_latin(c)]
    total = len(list(itertools.combinations(range(24), 4)))
    print(f"  {len(latin)} sets of four out of the {total:,} possible satisfy it.")
    keep = [c for c in latin
            if len({distractor_cycle(i) for i in c}) == 1 or
            all(distractor_cycle(i) in cyclic_rotations((1, 2, 3)) for i in c)]
    print(f"  {len(keep)} of those also keep the three distractors in one cyclic order.\n")
    for c in keep:
        rows = []
        for i in c:
            rows.append(f"{i:2d} " + " ".join(f"{NAME[x]:>6s}" for x in ALL[i]))
        print("    " + "  |  ".join(rows[:2]))
        print("    " + "  |  ".join(rows[2:]))
        print()
    chosen = keep[0] if keep else latin[0]
    print(f"  taking {list(chosen)}:")
    print_occupancy("proposed set", chosen)
    print("\n    Every slot holds every candidate once, so an error naming a slot is not an")
    print("    error naming a candidate, and the cyclic order of the distractors is kept so")
    print("    the correct answer still moves through all four positions.")

    print("\n" + "=" * 78)
    print("4. Does the accuracy spread survive the change?")
    print("=" * 78)
    print("""
  V compares accuracy across the four positions of the correct answer. On P1a's set the
  three distractors sit in one relative order in every arrangement, so the comparison holds
  their arrangement fixed. On a Latin set the distractors are permuted between arrangements
  as well, so V mixes the two factors -- which is exactly the objection that produced
  FIXED_DISTRACTORS in the first place.

  The paired first-versus-last difference is not affected the same way. It names two slots
  in advance and compares accuracy on the same items with the same four candidates present;
  a distractor-arrangement effect is a property of both arrangements being compared and does
  not favour either. That is the statistic to lead with on the new set, and it is the same
  discipline as naming the two slots in advance rather than taking a maximum.

  So the two sets answer different questions and neither dominates:
    FIXED_DISTRACTORS  clean V, meaningless letter statistics
    a Latin set        meaningful letter statistics, V confounded with distractor order
  P2's 24 arrangements are both at once, which is the reason P2 exists.""")


if __name__ == "__main__":
    main()
