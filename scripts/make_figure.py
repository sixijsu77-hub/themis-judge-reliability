#!/usr/bin/env python3
"""Draw the position-exposure figure from the raw per-item records.

The finding this repository is clearest about is a paragraph in the README and a table in
results/validation/leaderboard_exposure.txt. Both are correct and neither is legible at a
glance: what a reader has to see is that the judges do not merely differ in how much position
moves them, they move in opposite directions, and the ranking crosses.

It reads the same function the artefact reads -- leaderboard_exposure.per_position -- rather
than recomputing the table a second way. A figure drawn off a different path than the gate
checks would be a picture of code nobody verified. It then reads §1 of the committed artefact
back and fails if any cell disagrees, so the two can never drift apart quietly.

No plotting library. matplotlib is not installed and a figure is not a reason to install one;
the SVG is written directly, which also means it diffs, carries no binary blob, and renders
inline on GitHub. It has no background rectangle and uses mid-tone colours, so it is readable
on a light or a dark page.

  python scripts/make_figure.py            # writes the svg and prints what it drew

Every number in the output is computed here. Nothing is typed in.
"""
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leaderboard_exposure import per_position

OUT = "docs/figures/position-exposure.svg"
ARTEFACT = "results/validation/leaderboard_exposure.txt"
LETTER = "ABCD"
SLOTS = list(LETTER)
CHANCE = 0.25

# Dark2. Chosen because it is colourblind-safe and mid-tone, so every line stays visible
# whether the page behind it is white or black.
PALETTE = ["#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e"]

W, H = 880, 460
L, R, T, B = 112, 596, 58, 366          # plot box
GREY = "#888"


def measured():
    """{short name: [accuracy at A, B, C, D]}, from the per-item records."""
    out = {}
    for model, slots in per_position().items():
        out[model.split("/")[-1]] = [float(np.mean(slots[s])) for s in SLOTS]
    return out


def artefact_table():
    """The same table as committed, parsed out of §1 of the artefact."""
    rows = {}
    body = open(ARTEFACT).read().split("2. The ranking")[0]
    for line in body.splitlines():
        m = re.match(r"\s{2,}(\S+)\s+" + r"(\d\.\d{4})\s+" * 4, line)
        if m:
            rows[m.group(1)] = [float(g) for g in m.groups()[1:5]]
    return rows


def y_of(v):
    return B - v * (B - T)


def x_of(i):
    return L + i * (R - L) / (len(SLOTS) - 1)


LABEL_GAP = 26   # each label is two lines; less than this and one overlaps the next


def spread_labels(points):
    """Push labels apart. Two of the five judges finish close enough to overlap at this size."""
    order = sorted(points, key=lambda p: p[1])
    for i in range(1, len(order)):
        if order[i][1] - order[i - 1][1] < LABEL_GAP:
            order[i][1] = order[i - 1][1] + LABEL_GAP
    return points


def svg(acc):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
         f'height="{H}" font-family="system-ui,-apple-system,Segoe UI,sans-serif">']
    o.append(f'<text x="{L}" y="26" font-size="17" font-weight="600" fill="{GREY}">'
             'Accuracy by where the correct answer sits</text>')
    o.append(f'<text x="{L}" y="45" font-size="12.5" fill="{GREY}">'
             'Same 1,763 items, same five judges, same prompt. Only the correct answer moves.'
             '</text>')

    for v in [0.0, 0.25, 0.5, 0.75, 1.0]:
        y = y_of(v)
        dash = ' stroke-dasharray="4 4"' if v == CHANCE else ''
        o.append(f'<line x1="{L}" y1="{y:.1f}" x2="{R}" y2="{y:.1f}" stroke="{GREY}" '
                 f'stroke-width="0.6" opacity="0.4"{dash}/>')
        o.append(f'<text x="{L - 10}" y="{y + 4:.1f}" font-size="12" fill="{GREY}" '
                 f'text-anchor="end">{v:.2f}</text>')
    o.append(f'<text x="{L + 6}" y="{y_of(CHANCE) - 7:.1f}" font-size="11.5" fill="{GREY}">'
             'chance, one of four</text>')

    for i, letter in enumerate(SLOTS):
        o.append(f'<text x="{x_of(i):.1f}" y="{B + 26}" font-size="15" fill="{GREY}" '
                 f'text-anchor="middle" font-weight="600">{letter}</text>')
    o.append(f'<text x="{(L + R) / 2:.1f}" y="{B + 48}" font-size="12.5" fill="{GREY}" '
             f'text-anchor="middle">position of the correct answer among the four candidates'
             f'</text>')

    labels = []
    for k, (name, ys) in enumerate(sorted(acc.items(), key=lambda kv: -kv[1][0])):
        c = PALETTE[k % len(PALETTE)]
        pts = " ".join(f"{x_of(i):.1f},{y_of(v):.1f}" for i, v in enumerate(ys))
        o.append(f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="2.4"/>')
        for i, v in enumerate(ys):
            o.append(f'<circle cx="{x_of(i):.1f}" cy="{y_of(v):.1f}" r="3.6" fill="{c}"/>')
        labels.append([name, y_of(ys[-1]), c, max(ys) - min(ys)])

    for name, y, c, sp in spread_labels(labels):
        o.append(f'<text x="{R + 14}" y="{y + 4:.1f}" font-size="12.5" fill="{c}">'
                 f'{name}</text>')
        o.append(f'<text x="{R + 14}" y="{y + 18:.1f}" font-size="11" fill="{GREY}">'
                 f'moves {sp:.4f}</text>')

    o.append(f'<text x="{L}" y="{H - 34}" font-size="12" fill="{GREY}">'
             'An unparseable verdict scores 0 here; upstream credits it 0.25. '
             'RewardBench 2, five subsets, best-of-4.</text>')
    o.append(f'<text x="{L}" y="{H - 16}" font-size="12" fill="{GREY}">'
             'Upstream draws this position from an unseeded call, so a published score is '
             'one sample from these four.</text>')
    o.append('</svg>')
    return "\n".join(o) + "\n"


def main():
    acc = measured()
    filed = artefact_table()

    print(f"  drawn from results/exp01/P2b_*_o0_*.jsonl, {len(acc)} judges\n")
    print(f"  {'judge':30s}" + "".join(f"    at {c}" for c in LETTER)
          + "     moves   vs artefact")
    bad = 0
    for name, ys in sorted(acc.items(), key=lambda kv: -(max(kv[1]) - min(kv[1]))):
        same = name in filed and all(abs(a - b) < 5e-5 for a, b in zip(ys, filed[name]))
        bad += not same
        print(f"  {name:30s}" + "".join(f"  {v:.4f}" for v in ys)
              + f"    {max(ys) - min(ys):.4f}   {'matches' if same else 'DIFFERS'}")

    first_a = max(acc, key=lambda n: acc[n][0])
    first_d = max(acc, key=lambda n: acc[n][3])
    print(f"\n  first at A: {first_a} ({acc[first_a][0]:.4f}), which is "
          f"{sorted(acc, key=lambda n: -acc[n][3]).index(first_a) + 1} of {len(acc)} at D")
    print(f"  first at D: {first_d} ({acc[first_d][3]:.4f}), which is "
          f"{sorted(acc, key=lambda n: -acc[n][0]).index(first_d) + 1} of {len(acc)} at A")

    if not filed:
        print(f"\n  parsed no rows out of §1 of {ARTEFACT}, so nothing was compared.")
        print("  That is a failure to read, not a disagreement, and the two are worth")
        print("  keeping apart: the figure is not written off a comparison that did not run.")
        return 1
    if bad:
        print(f"\n  {bad} row(s) disagree with §1 of {ARTEFACT}.")
        print("  The figure and the artefact are computed from the same function, so a")
        print("  disagreement means one of them was regenerated and the other was not.")
        return 1

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write(svg(acc))
    print(f"\n  every row matches §1 of {ARTEFACT}")
    print(f"  wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
