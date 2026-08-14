#!/usr/bin/env python3
"""Ask what a statistic about slot A is actually a statistic about.

The four arrangements P1 uses hold the three distractors in one relative order, which is
what makes the accuracy spread `V` a clean measure of where the *correct answer* sits. This
checks the other half of the question, which the design was not chosen for: when a judge
answers wrongly and names a slot, is that slot identifiable by position, or does the same
candidate always occupy it?

  python scripts/check_slot_confound.py
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orderings import ALL, FIXED_DISTRACTORS, PILOT

NAME = {0: "chosen", 1: "R1", 2: "R2", 3: "R3"}


def occupants(indices, slot):
    """Which candidate sits at `slot` in each arrangement of the set."""
    j = "ABCD".index(slot)
    return [ALL[i][j] for i in indices]


def report(label, indices):
    print(f"\n{label}: arrangements {indices}")
    print(f"  {'slot':>5s}  " + "  ".join(f"{'idx '+str(i):>10s}" for i in indices)
          + "   distinct candidates")
    for slot in "ABCD":
        occ = occupants(indices, slot)
        print(f"  {slot:>5s}  " + "  ".join(f"{NAME[c]:>10s}" for c in occ)
              + f"   {len({NAME[c] for c in occ})}")
    print("\n  errors conditional on the correct answer not being at that slot:")
    for slot in "ABCD":
        j = "ABCD".index(slot)
        # The arrangements an error at `slot` can come from: those where the chosen is
        # elsewhere. What sits at `slot` in exactly those arrangements is what the
        # conditional error share is counting.
        occ = [ALL[i][j] for i in indices if ALL[i][j] != 0]
        c = Counter(NAME[x] for x in occ)
        distinct = len(c)
        verdict = ("position and candidate are the same thing here"
                   if distinct == 1 else f"{distinct} distinct candidates, separable")
        print(f"    an error naming {slot} always names "
              f"{', '.join(f'{k} x{v}' for k, v in sorted(c.items())):22s} — {verdict}")


def main():
    print(__doc__.split("  python")[0].strip() if __doc__ else "")
    report("the set P1 uses (fixed distractor order)", FIXED_DISTRACTORS)
    report("the pilot's set", PILOT)

    print("\n" + "=" * 78)
    print("What this means for the hypotheses")
    print("=" * 78)
    print("""
  V, the accuracy spread over the four positions of the correct answer, is unaffected: it
  compares the same items with the same distractors in the same relative order, and only
  the correct answer moves. It needs no null and stays sound.

  The conditional error share E*_A does not have that property on this set. Every
  arrangement in which an error can name A has the first distractor at A, so "the judge
  sent its error to the first slot" and "the judge sent its error to the first distractor"
  are the same count. Separating them needs the six distractor orderings within a position,
  which is P2 and only P2.

  Nothing here changes a decision rule. It is a limit on what a result can be said to mean,
  and it is recorded before the results exist.""")


if __name__ == "__main__":
    main()
