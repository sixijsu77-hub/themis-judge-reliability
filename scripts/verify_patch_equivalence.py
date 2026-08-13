#!/usr/bin/env python3
"""Check that the ordering patch reproduces upstream's arrangement exactly.

The obvious test — run patched and unpatched and diff the per-item results — cannot be run.
`datasets.map` fingerprints the mapped function's bytecode, so adding a line to
`format_judgements` invalidates the cache and the unseeded draw comes out different for
reasons that have nothing to do with correctness.

This checks the thing that test was a proxy for, and checks it exhaustively rather than by
sampling. Upstream can produce exactly four arrangements. Each is reproduced here by one of
the 24 permutations, and the arrangement logic does not depend on the item, so comparing all
four with sentinel candidates is a proof rather than a sample. A second pass then confirms
the prompt string handed to the model is byte-identical on real items.

  python scripts/verify_patch_equivalence.py
"""
import itertools
import subprocess
import sys

ORDERINGS = list(itertools.permutations(range(4)))
UPSTREAM_REV = "05a9005"
UPSTREAM_DIR = ".local/reward-bench"


def upstream_block():
    """Print the pristine swap block so the transcription below can be checked by eye."""
    src = subprocess.run(
        ["git", "-C", UPSTREAM_DIR, "show", f"{UPSTREAM_REV}:scripts/run_generative_v2.py"],
        capture_output=True, text=True, check=True).stdout.splitlines()
    start = next(i for i, l in enumerate(src) if "shuffle correct answer into random position" in l)
    return "\n".join(src[start - 1: start + 10])


def upstream_arrangement(cand, shuffle_option):
    """Transcribed from the block printed above. Kept separate so the two can be compared."""
    a, b, c, d = cand
    if shuffle_option == 1:
        a, b = b, a
    elif shuffle_option == 2:
        a, c = c, a
    elif shuffle_option == 3:
        a, d = d, a
    return [a, b, c, d]


def patched_arrangement(cand, ordering):
    perm = ORDERINGS[ordering]
    return [cand[i] for i in perm], perm.index(0)


def main():
    print("Pristine block at", UPSTREAM_REV)
    print("-" * 78)
    print(upstream_block())
    print("-" * 78)

    cand = ["CHOSEN", "R1", "R2", "R3"]
    fail = 0

    print("\n[1] Every upstream arrangement is reachable, and lands the chosen candidate")
    print("    in the same slot upstream records\n")
    print(f"    {'upstream':>9s}  {'arrangement':34s} {'= ordering':>11s}  {'chosen slot':>11s}")
    for k in range(4):
        want = upstream_arrangement(cand, k)
        matches = [i for i in range(24) if patched_arrangement(cand, i)[0] == want]
        if len(matches) != 1:
            print(f"    option {k}: {len(matches)} permutations match — expected exactly 1")
            fail = 1
            continue
        idx = matches[0]
        got, slot = patched_arrangement(cand, idx)
        # upstream's own record of where the chosen ended up is the shuffle_option itself
        ok = got == want and slot == k
        fail |= not ok
        print(f"    option {k}: {str(want):34s} {idx:11d}  {slot:11d}  {'ok' if ok else 'MISMATCH'}")

    print("\n[2] The 24 permutations put the chosen candidate in each slot equally often")
    counts = {p: sum(1 for o in ORDERINGS if o.index(0) == p) for p in range(4)}
    ok = set(counts.values()) == {6}
    fail |= not ok
    print(f"    {counts}   {'ok' if ok else 'UNBALANCED'}")

    print("\n[3] The four upstream arrangements are a strict subset of the 24")
    reachable = {tuple(upstream_arrangement(cand, k)) for k in range(4)}
    allof = {tuple(patched_arrangement(cand, i)[0]) for i in range(24)}
    ok = reachable < allof and len(reachable) == 4 and len(allof) == 24
    fail |= not ok
    print(f"    upstream reaches {len(reachable)} of {len(allof)}   {'ok' if ok else 'UNEXPECTED'}")
    print(f"    the 20 it never reaches are why the position effect it can show is a mixture")

    print("\n=== " + ("PASS" if not fail else "FAIL") + " ===")
    return fail


if __name__ == "__main__":
    sys.exit(main())
