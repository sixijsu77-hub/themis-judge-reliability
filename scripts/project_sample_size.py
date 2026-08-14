#!/usr/bin/env python3
"""Project how many usable errors P1b will have, from what P1a already measured.

H3 reads the share of errors landing at the first slot among the arrangements where an error
can land there. At `--obvious 3` a judge is right on nearly everything, so the count that
statistic divides by is small and can fall below the 40 the rule needs to fire. Whether it
does is knowable in advance from P1a's 150 items, and the point of writing it down before
P1b runs is that a prediction nobody recorded is not a prediction.

That is not hypothetical here. This projection was computed and reported in conversation
before P1b finished, and never committed, which is exactly the failure the repository's
prose-number gate exists to catch and cannot: the gate reads tracked files.

  python scripts/project_sample_size.py

Once P1b exists the observed counts are printed beside the projection, so the record checks
itself rather than inviting anyone to remember what was predicted.
"""
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

N_FULL = 1763           # items in P1b
N_PILOT = 150           # items in P1a
MIN_N_ERR = 40          # the floor below which H3 cannot fire, from section 3
NEEDED = 4              # judges whose interval must contain the null for H3 to hold
DRAWS = 20000
RNG = np.random.default_rng(0)


def usable(phase):
    """{model: (usable errors, verdicts where an error could name A)} at --obvious 3."""
    out = {}
    for path in sorted(glob.glob(f"results/exp01/{phase}_*_o3_*.jsonl")):
        with open(path) as f:
            meta = json.loads(f.readline())
            if meta["chosen_at_slot"] == "A":
                continue          # an error here cannot name A; excluded by construction
            n = err = 0
            for line in f:
                r = json.loads(line)
                if r["parsed_letter"] not in "ABCD":
                    continue
                n += 1
                err += r["parsed_letter"] != meta["chosen_at_slot"]
            a, b = out.get(meta["model"], (0, 0))
            out[meta["model"]] = (a + err, b + n)
    return out


def main():
    print(__doc__.split("  python")[0].strip() if __doc__ else "")
    pilot, actual = usable("P1a"), usable("P1b")
    if not pilot:
        sys.exit("no P1a --obvious 3 runs found")

    print("\n" + "=" * 100)
    print(f"projection from {N_PILOT} items to {N_FULL}, and the probability H3 cannot fire")
    print("=" * 100)
    print(f"  {'judge':32s} {'n_obs':>6s} {'errors':>7s} {'rate':>7s} {'projected':>10s} "
          f"{'95% interval':>15s} {'P(<40)':>7s} {'observed':>9s}")
    p_below = []
    for m in sorted(pilot):
        err, n = pilot[m]
        n_full = int(round(N_FULL / N_PILOT * n))
        # Beta-binomial: uncertainty in the rate, then in the count at that rate.
        draws = RNG.binomial(n_full, RNG.beta(err + 0.5, n - err + 0.5, DRAWS))
        p = float((draws < MIN_N_ERR).mean())
        p_below.append(p)
        obs = actual.get(m, (None, None))[0]
        print(f"  {m.split('/')[-1]:32s} {n:6d} {err:7d} {err/n:7.4f} "
              f"{n_full*err/n:10.0f} [{np.percentile(draws,2.5):4.0f},"
              f"{np.percentile(draws,97.5):5.0f}] {p:7.3f} "
              + (f"{obs:9d}" if obs is not None else f"{'—':>9s}"))
    k = np.array(p_below)
    n_j = len(k)
    # How many judges fall below, as a Poisson-binomial over independent judges.
    counts = np.zeros(n_j + 1)
    counts[0] = 1.0
    for p in k:
        counts[1:] = counts[1:] * (1 - p) + counts[:-1] * p
        counts[0] *= 1 - p
    cannot = float(counts[n_j - NEEDED + 1:].sum())
    print(f"\n  P(no judge below the floor)                      = {counts[0]:.4f}")
    print(f"  P(at least {n_j - NEEDED + 1} below, so H3 cannot reach {NEEDED}) = {cannot:.4f}")
    print("\n  That last number is the chance H3 is falsified by sample size rather than by")
    print("  anything about the judges, and it is written here before P1b decides.")
    if actual:
        short = [m for m in actual if actual[m][0] < MIN_N_ERR]
        print(f"\n  Observed: {len(short)} of {len(actual)} judges below the floor"
              + (f" ({', '.join(m.split('/')[-1] for m in sorted(short))})" if short else ""))


if __name__ == "__main__":
    main()
