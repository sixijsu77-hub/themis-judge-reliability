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
from orderings import ALL, FIXED_DISTRACTORS, PILOT, SLOT_BALANCED

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


def fixed_relative_order(i):
    """The three distractors read left to right are R1, R2, R3, not a rotation of them."""
    return distractor_cycle(i) == (1, 2, 3)


def clean_pairs(indices):
    """Slot pairs whose two arrangements hold the three distractors in the same order.

    A paired accuracy difference between two named slots is clean when both arrangements
    present the distractors identically, because then the only difference between them is
    where the correct answer sits.
    """
    out = []
    for i in indices:
        for j in indices:
            si, sj = "ABCD"[list(ALL[i]).index(0)], "ABCD"[list(ALL[j]).index(0)]
            if si < sj and distractor_cycle(i) == distractor_cycle(j):
                out.append((si, sj))
    return sorted(out)


def section5():
    print("\n" + "=" * 78)
    print("5. Can one set of four be clean on both counts at once?")
    print("=" * 78)
    strict = [i for i in range(24) if fixed_relative_order(i)]
    print(f"  Arrangements whose distractors read R1, R2, R3 in slot order: {strict}")
    print(f"  That is {len(strict)} of 24, so the only four-element set with the property is")
    print(f"  that set itself, and it is {'' if is_latin(strict) else 'not '}a Latin set.")
    print("  **No set of four is clean on both counts.** The two requirements each pin four")
    print("  arrangements and the two quadruples are different ones.")

    print("\n" + "=" * 78)
    print("6. What a reduced P2 could measure, per set")
    print("=" * 78)
    print(f"  {'statistic':34s} {'FIXED_DISTRACTORS':>22s} {'SLOT_BALANCED':>18s}")
    rows = [
        ("V, accuracy spread over 4 slots", "clean", "confounded"),
        ("W, spread over distractor orders", "not available", "not available"),
        ("paired difference, named slots", "clean, all pairs", "clean, some pairs"),
        ("E*_A, conditional error share", "confounded", "clean"),
        ("f_A, S, letter frequencies", "confounded", "clean"),
    ]
    for name, a_, b_ in rows:
        print(f"  {name:34s} {a_:>22s} {b_:>18s}")
    for label, S in (("FIXED_DISTRACTORS", FIXED_DISTRACTORS),
                     ("SLOT_BALANCED", SLOT_BALANCED)):
        print(f"\n  {label}: slot pairs whose arrangements present the distractors alike")
        print(f"    {clean_pairs(S)}")
    print("""
  W needs six arrangements at one position of the correct answer and neither set has more
  than one, so H4 cannot be tested on either. That is what section 7 already says happens
  when H3 fails.""")


def section7():
    """What the two sets already measured, on the same judge and the same items."""
    import glob
    import json
    print("\n" + "=" * 78)
    print("7. The same statistic on two arrangement sets, same judge, same items")
    print("=" * 78)
    pilot = {}
    for lv in (3, 2, 1, 0):
        tot = at = 0
        for d in PILOT:
            slot = "ABCD"[list(ALL[d]).index(0)]
            if slot == "A":
                continue
            for line in open(f"results/validation/graded/o{lv}_original_{d}.jsonl"):
                o = json.loads(line)
                if o.get("_record") == "metadata":
                    continue
                L = o["parsed_letter"]
                if L in "ABCD" and L != slot:
                    tot += 1
                    at += L == "A"
        pilot[lv] = (at / tot if tot else float("nan"), tot)
    new = {}
    for path in sorted(glob.glob("results/exp01/P1a_Qwen__*.jsonl")):
        with open(path) as f:
            meta = json.loads(f.readline())
            if meta["chosen_at_slot"] == "A":
                continue
            tot, at = new.get(meta["obvious"], (0, 0))
            for line in f:
                L = json.loads(line)["parsed_letter"]
                if L in "ABCD" and L != meta["chosen_at_slot"]:
                    tot += 1
                    at += L == "A"
            new[meta["obvious"]] = (tot, at)
    print("  E*_A for Qwen2.5-7B-Instruct, the same 150 items under two sets of four\n")
    print(f"  {'obvious':>7s} {'pilot set':>22s} {'P1a set':>22s}")
    for lv in (3, 2, 1, 0):
        t, a_ = new[lv]
        print(f"  {lv:7d} {pilot[lv][0]:14.4f} (n={pilot[lv][1]:3d}) "
              f"{a_/t if t else float('nan'):14.4f} (n={t:3d})")
    print("""
  They agree at --obvious 0 and disagree by two orders of magnitude at 2 and 1. The pilot
  set holds each candidate at slot A exactly once; the P1a set holds the first distractor
  there every time. At --obvious 0 all three distractors are the item's own rejected
  responses, so which one sits at A hardly matters and the sets agree. At 2 and 1 the first
  distractor is off-topic, nobody picks it, and the P1a set reads almost zero while the
  pilot set -- which offers a plausible candidate at A two thirds of the time at --obvious 1
  -- reads high.

  SLOT_BALANCED has the property the pilot set has at slot A, and has it at every slot. So
  the re-run should reproduce the pilot's shape, not P1a's. That is the prediction, and it
  is in section 6 of the pre-registration with what it implies for each hypothesis.""")


if __name__ == "__main__":
    main()
    section5()
    section7()
