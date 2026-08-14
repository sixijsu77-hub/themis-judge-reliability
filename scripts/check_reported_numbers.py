#!/usr/bin/env python3
"""Check that numbers written in prose can be traced to a committed output.

Three published claims in this repository were wrong, and a fourth was ambiguous. Every one
was a sentence written by hand next to a table that a script had generated correctly. The
rule "generate tables from raw data" was being followed; it just did not reach the prose.

So this does not ask anyone to be careful. It extracts every number from the tracked
Markdown and requires each one to appear literally in a tracked output file — the artefacts
under results/, which are written by scripts and never by hand. A number a script never
produced has nowhere to hide.

  python scripts/check_reported_numbers.py           # report
  python scripts/check_reported_numbers.py --strict  # exit 1 if anything is unaccounted for

Exemptions live in ALLOWED below and each needs a reason. Dates, section numbers, version
pins and round counts are not measurements and are exempt by pattern.

What it does not catch. Matching is on whole numeric tokens, so a small integer written in
prose will usually be satisfied by some unrelated id or count in the outputs: writing "42"
passes whether or not 42 is the right answer. The check bites on distinctive figures —
decimals, large counts — and is close to useless below about three digits. It also cannot
tell a number that is present but describes the wrong thing. It narrows the failure mode
that has actually occurred here four times; it does not close it.

It sees only numbers written in tracked prose. A figure computed and reported in
conversation, or in a commit message, or in a comment on an issue, is invisible to it — and a
prediction that exists nowhere in the repository cannot later be said to have been made. That
happened: the probability that H3 would be falsified by sample size was computed and stated
before P1b ran, and was not committed until afterwards. The gate cannot close that; only the
habit of writing a prediction into a file before the run can, and
scripts/project_sample_size.py is where that one now lives.

Code spans were skipped whole until 2026-08-14, which exempted every figure written inside
backticks -- four confidence-interval bounds in a comparison between judges were escaping
the check on that route. Only spans that name something, by containing a letter or a slash,
are skipped now. A span of digits and punctuation is a measurement and is checked.
"""
import argparse
import re
import subprocess
import sys

# Numbers that are not measurements. Kept deliberately short: the wider this gets, the less
# the check is worth.
ALLOWED = {
    # thresholds and design constants fixed in advance, not measured
    "0.02", "0.25", "0.05", "0.10", "10", "25", "75", "50", "3", "4", "5", "6", "2", "1", "0",
    "10000", "10,000",   # bootstrap resamples, chosen not measured
    "14104", "14,104",   # 1763 x 8, arithmetic on numbers that are themselves checked
    "5400", "5,400",     # 150 x 3 x 4 x 3, likewise
    # dataset shape, checked by scripts/audit_published_results.py
    "1865", "1,865", "1763", "1,763", "8977", "8,977", "188", "197", "179", "178", "18", "14",
    # hardware and environment
    "24", "4090", "3.10.12", "2.13.0", "2.9.0", "0.13.0", "4.57.6", "8", "7", "12", "13",
    # figures quoted in docs/errata.md as the values that were wrong
    "0.00625",
}
# A line ending in this marker holds a one-off environment measurement — a wall clock, a
# throughput — that no committed script reproduces. The count is printed on every run so
# the exemption cannot grow quietly.
ONE_OFF = "<!-- measured once -->"
NUM = re.compile(r"(?<![\w.])(\d+(?:,\d{3})*(?:\.\d+)?)(?![\w])")
SKIP_LINE = re.compile(r"^\s*(\||```|<!--|\[.*\]:|#{1,6}\s)")
# Version pins, dates, urls, code spans and section refs are not measurements.
SKIP_TOKEN = re.compile(
    r"\[[^\]]*\]\([^)]*\)"          # markdown links, target and label both
    r"|`[^`]*[A-Za-z/][^`]*`"       # code spans naming something: a model, a flag, a path
    r"|\S*/\S*"                     # anything path-shaped
    r"|\d{4}-\d{2}-\d{2}"           # dates
    r"|@[0-9a-f]{7,}"               # commit refs
    r"|https?://\S*"
    r"|\bv?\d+\.\d+\.\d+\b"         # version pins
    r"|§\d+|#\d+"                   # section and issue refs
)


def tracked(pattern):
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.split()
    return [f for f in out if re.search(pattern, f)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--also", nargs="*", default=[],
                    help="extra files to check, for drafts that are not tracked yet")
    args = ap.parse_args()

    outputs = tracked(r"^results/.*\.(txt|jsonl)$")
    # Match whole numeric tokens, not substrings: "1777" must not be satisfied by the
    # "1777" inside "0.17777". Small integers would otherwise always be found somewhere.
    haystack = set()
    for f in outputs:
        text = open(f, errors="ignore").read()
        haystack.update(NUM.findall(text))
        haystack.update(t.replace(",", "") for t in NUM.findall(text))
    docs = tracked(r"\.md$") + list(args.also)

    print(f"prose files : {len(docs)}")
    print(f"output files: {len(outputs)}  ({', '.join(outputs[:4])}{' ...' if len(outputs) > 4 else ''})")
    print()

    unaccounted, one_off = [], []
    for doc in docs:
        for lineno, line in enumerate(open(doc, errors="ignore"), 1):
            if SKIP_LINE.match(line):
                continue
            if ONE_OFF in line:
                one_off.append((doc, lineno, line.strip()[:88]))
                continue
            clean = SKIP_TOKEN.sub(" ", line)
            for tok in NUM.findall(clean):
                if tok in ALLOWED or tok.replace(",", "") in ALLOWED:
                    continue
                bare = tok.replace(",", "")
                if bare in haystack or tok in haystack:
                    continue
                # A rounded quotation of a longer figure counts as accounted for:
                # "70.55" in prose against "70.5478..." in the output.
                if any(h.startswith(bare) for h in haystack if "." in bare):
                    continue
                unaccounted.append((doc, lineno, tok, line.strip()[:88]))

    print(f"one-off measurements, exempt by marker: {len(one_off)}")
    for doc, lineno, ctx in one_off:
        print(f"  {doc}:{lineno}  {ctx}")
    print()

    if not unaccounted:
        print("every other number in prose appears in a committed output file")
        return 0

    print(f"{len(unaccounted)} number(s) with no matching committed output:\n")
    for doc, lineno, tok, ctx in unaccounted:
        print(f"  {doc}:{lineno}  [{tok}]")
        print(f"      {ctx}")
    print("\nEither the number came from somewhere a script does not write, or it is wrong.")
    print("Add it to a generated output, or add it to ALLOWED with a reason.")
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
