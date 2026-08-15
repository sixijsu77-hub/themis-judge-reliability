#!/usr/bin/env python3
"""Check that numbers written in prose can be traced to a committed output.

Three published claims in this repository were wrong, and a fourth was ambiguous. Every one
was a sentence written by hand next to a table that a script had generated correctly. The
rule "generate tables from raw data" was being followed; it just did not reach the prose.

So this does not ask anyone to be careful. It extracts every number from the tracked
Markdown and requires each one to appear literally in a tracked output file — the artefacts
under results/.

**Those artefacts are only as trustworthy as the scripts that write them, and "written by a
script" is not the same as "computed by a script".** A figure typed into a print statement is
laundered: the script emits it into results/, the gate finds it there, and prose quoting it
passes. That is worse than a number the gate cannot see, because the gate certifies it. It
happened here — one script carried twenty-five such figures, several of them stale after the
computation behind them changed. So a second check runs: any numeral with three or more
decimal places inside a string literal in scripts/*.py is a finding, whether or not it is
currently correct.

  python scripts/check_reported_numbers.py --copied      # that check alone

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

The two faces have different thresholds and a measurement can sit between them. Text is
checked from three decimals, float literals from four, so **a measured value written as a
float literal with exactly three decimals is caught by neither** — `0.565` as a number
escapes while the same digits inside a string do not. The asymmetry is deliberate: at three
decimals the float side floods with legitimately chosen values, grid points and simulation
parameters, and an exemption list long enough to absorb them would be worth less than the
check. Two-decimal measurements escape on both sides for the same reason.

Constants a script *consumes* are still invisible. scripts/constant_preference.py held twenty
accuracies as input literals, four of which matched no run at all and the rest of which came
from a different phase than the quantity they were used to predict; the section's conclusion
was wrong and this gate reported clean throughout. The --laundered check catches numbers on
the way out, not on the way in. Anything a script consumes should be read from a result file,
and where it cannot be, nothing here will notice. A figure computed and reported in
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


# A measurement copied into code, exempted with its reason. The discipline is ALLOWED's:
# every entry needs a reason and a longer list is a weaker check.
COPIED_OK = {
    "0.0005": "grid endpoint in constant_preference.py, a chosen search bound",
    "0.0001": "optimiser floor in constant_preference.py, a chosen search bound",
    "0.565": "the worked example in this file's own docstring, of a value that escapes",
}


def truncated_outputs():
    """Tracked results files that are empty or end mid-run.

    A results file is evidence, and an empty one is silent: nothing in this gate mentions a
    file that no prose happens to cite, so a run killed by a timeout can be committed as a
    zero-byte artefact and every check still passes. That happened on 2026-08-15, to the
    output of the script this gate had just been extended to police.
    """
    bad = []
    for path in tracked(r"^results/.*\.txt$"):
        try:
            data = open(path, errors="replace").read()
        except OSError:
            bad.append((path, "unreadable"))
            continue
        if not data.strip():
            bad.append((path, "empty"))
        elif len(data.splitlines()) < 3:
            bad.append((path, f"only {len(data.splitlines())} lines"))
    print(f"\n[outputs] tracked results/*.txt that are empty or nearly so: {len(bad)}")
    for path, why in bad:
        print(f"  {path}  ({why})")
    if bad:
        print("  Re-run the script that writes it. An artefact with nothing in it is not")
        print("  evidence, and nothing else here would notice.")
    return len(bad)


def _decimals(v):
    s = repr(float(v))
    return len(s.split(".")[1].rstrip("0")) if "." in s else 0


def copied_measurements():
    """Numbers in scripts that look measured rather than chosen.

    The axis is not "does it get printed". It is **chosen or measured**. A number someone
    picked -- a threshold, a grid point, a seed, a simulation parameter -- belongs in code
    and is round. A number that came out of a run does not belong in code at all, and it
    arrives written to four decimal places because that is how it was printed.

    Both faces are checked because they are complementary and the repository has produced
    each of them:

      consumed   a float literal with four or more decimals. This is the shape that flipped
                 a conclusion: twenty accuracies typed into a dict, several from the wrong
                 phase and four matching no run at all
      printed    a numeral inside a string literal, which a print statement launders into
                 results/ where the prose gate then accepts it as evidence

    Neither catches the other. Tested against both forms of the accident.
    """
    import ast
    import glob
    # The fixture file holds the accidents on purpose -- flagging it would mean deleting the
    # evidence that the checks work. It is the one file exempted by path rather than value.
    skip = {"scripts/check_the_checks.py"}
    hits = []
    for path in sorted(glob.glob("scripts/*.py")):
        if path in skip:
            continue
        try:
            tree = ast.parse(open(path).read())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                for m in re.findall(r"(?<![\w.])\d+\.\d{3,}", node.value):
                    if m not in ALLOWED and m not in COPIED_OK:
                        hits.append((path, node.lineno, m, "printed"))
            elif (isinstance(node, ast.Constant) and isinstance(node.value, float)
                  and _decimals(node.value) >= 4):
                m = repr(node.value)
                if m not in ALLOWED and m not in COPIED_OK:
                    hits.append((path, node.lineno, m, "consumed"))
    print(f"\n[copied] numbers in scripts that look measured, not chosen: {len(hits)}")
    for path, line, m, kind in hits:
        print(f"  {path}:{line}  {m}  ({kind})")
    if hits:
        print("  Read them from a result file. A measurement in code is a measurement")
        print("  nobody re-derives when the run behind it changes.")
    return len(hits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--copied", action="store_true",
                    help="only the check for measurements living in code")
    ap.add_argument("--also", nargs="*", default=[],
                    help="extra files to check, for drafts that are not tracked yet")
    args = ap.parse_args()
    if args.copied:
        return 1 if (copied_measurements() + truncated_outputs()) and args.strict else 0

    outputs = tracked(r"^results/.*\.(txt|jsonl)$")
    # Match whole numeric tokens, not substrings: "1777" must not be satisfied by the
    # "1777" inside "0.17777". Small integers would otherwise always be found somewhere.
    haystack = set()
    for f in outputs:
        text = open(f, errors="ignore").read()
        haystack.update(NUM.findall(text))
        haystack.update(t.replace(",", "") for t in NUM.findall(text))
    docs = tracked(r"\.md$") + list(args.also)

    n_laundered = copied_measurements() + truncated_outputs()
    print(f"\nprose files : {len(docs)}")
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

    if not unaccounted and n_laundered:
        print("\nprose is clean but the checks above are not; see them")
        return 1 if args.strict else 0
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
