#!/usr/bin/env python3
"""Can J2' clear its own threshold? Compute it before anyone is asked to pay for the pass.

J2' would re-run `--obvious 3` on the slot-balanced arrangements at full size and ask whether
at least 4 of 5 judges show the same sign as they do at `--obvious 0`. A sign is readable
only when the judge clears the floor of 40 usable errors and its interval excludes 1/3.

Both conditions are estimable now. The error rate comes from the same judges on the same
difficulty and arrangement set at 150 items; the share comes from their `--obvious 0`
behaviour, which is the closest thing to a prior this data offers and is an assumption
stated here rather than buried.

This exists because the lesson was already written down and not applied. J1 was registered
without asking whether its halves could clear the same floor, and the pre-registration says
so; J2' was then proposed at the same difficulty without the check being run either.

  python scripts/power_j2prime.py
"""
import glob
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

NULL = 1 / 3
FLOOR = 40
NEEDED = 4
N_FULL, N_PILOT = 1763, 150
DRAWS = 40000
RNG = np.random.default_rng(0)


def counts(phase, obvious):
    """Per judge, (errors that could name A, of them naming A) at one difficulty."""
    d = defaultdict(lambda: [0, 0])
    for path in sorted(glob.glob(f"results/exp01/{phase}_*_o{obvious}_*.jsonl")):
        with open(path) as f:
            meta = json.loads(f.readline())
            if meta["chosen_at_slot"] == "A":
                continue
            for line in f:
                r = json.loads(line)
                L = r["parsed_letter"]
                if L in "ABCD" and L != meta["chosen_at_slot"]:
                    d[meta["model"]][0] += 1
                    d[meta["model"]][1] += L == "A"
    return d


def readable(lam, s):
    """P(clears the floor and the interval excludes 1/3), by simulation."""
    n = RNG.poisson(lam, DRAWS)
    ok = n >= FLOOR
    if not ok.any():
        return 0.0
    k = RNG.binomial(np.maximum(n, 1), s)
    p = k / np.maximum(n, 1)
    se = np.sqrt(np.maximum(p * (1 - p), 1e-9) / np.maximum(n, 1))
    excl = np.abs(p - NULL) > 1.96 * se
    return float((ok & excl).mean())


def at_least(ps, need):
    """P(at least `need` of the independent events fire)."""
    dist = np.zeros(len(ps) + 1)
    dist[0] = 1.0
    for p in ps:
        dist[1:] = dist[1:] * (1 - p) + dist[:-1] * p
        dist[0] *= 1 - p
    return float(dist[need:].sum())


def main():
    print((__doc__ or "").split("  python")[0].strip())
    pilot = counts("P1c", 3)
    hard = counts("P2b", 0)
    models = sorted(set(pilot) | set(hard))

    print("\n" + "=" * 96)
    print("Errors available at --obvious 3 on the slot-balanced set, scaled to 1,763 items")
    print("=" * 96)
    print(f"  {'judge':30s} {'n_err* at 150':>13s} {'expected at 1763':>17s} "
          f"{'P(clears 40)':>13s} {'share at --obvious 0':>21s}")
    lam, share = {}, {}
    for m in models:
        n150 = pilot.get(m, [0, 0])[0]
        lam[m] = n150 * N_FULL / N_PILOT
        h = hard.get(m, [0, 0])
        share[m] = h[1] / h[0] if h[0] else float("nan")
        p_floor = float((RNG.poisson(lam[m], DRAWS) >= FLOOR).mean())
        print(f"  {m.split('/')[-1]:30s} {n150:13d} {lam[m]:17.0f} {p_floor:13.3f} "
              f"{share[m]:21.4f}")

    print("\n" + "=" * 96)
    print("P(a readable sign), and P(at least 4 of 5), at three assumptions about the share")
    print("=" * 96)
    print("  'as at --obvious 0' uses each judge's own value there. The other two columns")
    print("  hold every judge at one distance from the null, as a floor and a ceiling on")
    print("  what the assumption can be worth.\n")
    print(f"  {'judge':30s} {'as at --obvious 0':>18s} {'all at 0.45':>12s} "
          f"{'all at 0.60':>12s}")
    cols = {"own": [], "0.45": [], "0.60": []}
    for m in models:
        a = readable(lam[m], share[m]) if share[m] == share[m] else 0.0
        b = readable(lam[m], 0.45)
        c = readable(lam[m], 0.60)
        cols["own"].append(a)
        cols["0.45"].append(b)
        cols["0.60"].append(c)
        print(f"  {m.split('/')[-1]:30s} {a:18.3f} {b:12.3f} {c:12.3f}")
    print(f"\n  {'P(at least 4 of 5 readable)':30s} "
          f"{at_least(cols['own'], NEEDED):18.4f} {at_least(cols['0.45'], NEEDED):12.4f} "
          f"{at_least(cols['0.60'], NEEDED):12.4f}")
    print(f"  {'P(at least 3 of 5 readable)':30s} "
          f"{at_least(cols['own'], 3):18.4f} {at_least(cols['0.45'], 3):12.4f} "
          f"{at_least(cols['0.60'], 3):12.4f}")

    print("\n" + "=" * 96)
    print("What this says about buying the pass")
    print("=" * 96)
    print("""
  A readable sign needs two things and the first one is the binding one: two judges expect
  fewer errors than the floor, so no assumption about the share rescues them. The threshold
  of 4 asks for more readable judges than the difficulty can supply, and the probability of
  meeting it is the number printed above rather than an argument.

  This is J1's defect in a second design. The floor was registered in exp01b because H3
  could not fire for want of errors; J1 halved the same sample at the same difficulty; J2'
  proposes the same difficulty again. The item count is not the lever -- 1,763 is already
  the whole benchmark -- so the lever is the difficulty, and at --obvious 0 the same judges
  have thousands of errors each.""")


if __name__ == "__main__":
    main()
