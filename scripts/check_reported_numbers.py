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
pins and round counts are not measurements and are exempt by pattern. COPIED_OK, which
exempts a figure from the second check, is keyed on the value *and the file*: a reason is
about a place, and keyed on the value alone an exemption granted to one script cleared the
same digits in every other one.

What it does not catch, and the widest one is not about numbers at all. Everything listed
below concerns a figure that is wrong, missing or untraceable. **A claim carrying no figure is
invisible to all of it**, and so is every other check here — the digests, the convention tags,
the exemption scoping, the fixtures.

Not only the figureless claim, and the line is further out than that. The claims side of this
check is the tracked markdown; results/*.txt is the corpus those claims are checked against, so
a sentence an artefact writes about itself is never read as a claim at all, whatever it
carries. The printed face sees floats of three or more decimals, so an integer in a generator's
narrative escapes that too. The paragraph behind this entry carried three figures -- 2, 150 and
1,763 -- all of them correct; replacing them with wrong ones produces the same zero hits.
**What nothing here sees is any claim an artefact makes about itself.**

The occasion for all of this: an artefact can report a result in its table and, in the same
file on the same run, say the question is still open. That happened on 2026-08-16 to
results/validation/exchangeable_full_ladder.txt, which printed a level as differing above a
paragraph saying that level stayed undetermined and would need the rebuild the run had just
performed. Nothing numeric was wrong, so nothing fired. No check here will ever see that
class; the one time a mechanical stand-in was built for a neighbouring semantic question, it
certified the accident it was written for. What sees it is a reader holding the table and the
paragraph in view at once, and this entry exists so the next reader knows that is their job.

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
import ast
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
    # Cost-plan products in the pre-registration tables: arithmetic on counts that are
    # themselves checked, and no run produces them. Each was recomputed before being listed.
    "35260", "35,260",      # 5 judges x 1,763 items x 4 orderings
    "211560", "211,560",    # 5 x 1,763 x 24
    "23400", "23,400",      # Safety 450 x 24 x 2 conditions + 450 x 4 paraphrase
    "507744", "507,744",    # 1,763 x 24 x 4 x 3
    # This one does not reconcile with its own row, which reads "S3 repeated on two more
    # models" and would be 46,800. It is 2 x 450 x 24 x 2 -- S3 without its paraphrase arm.
    # Listed with what it is rather than with a reason that would be false; the scenario was
    # never run and the pre-registration is not edited to match a later recomputation.
    "43200", "43,200",
    "46800", "46,800",      # 2 x 23,400, the figure that row's own description implies
}
# A line ending in this marker holds a one-off environment measurement — a wall clock, a
# throughput — that no committed script reproduces. The count is printed on every run so
# the exemption cannot grow quietly.
ONE_OFF = "<!-- measured once -->"
NUM = re.compile(r"(?<![\w.])(\d+(?:,\d{3})*(?:\.\d+)?)(?![\w])")
# Table rows are NOT skipped. They were until 2026-08-16, on the first alternative of this
# pattern, and that exempted every markdown table in the repository -- which is where most of
# its numbers live. Turning it on newly checked 361 tokens and found six untraceable
# measurements, one of them load-bearing for a registered choice.
SKIP_LINE = re.compile(r"^\s*(```|<!--|\[.*\]:|#{1,6}\s)")
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
#
# Keyed on (value, file), because a reason is about a place. Keyed on the value alone, an
# exemption granted for one script cleared the same digits in every other one -- so a figure
# excused here as a search bound would have excused a copied measurement somewhere else, which
# is the whole failure --copied exists to catch. An exemption wider than the reason that
# granted it is this repository's most repeated shape.
COPIED_OK = {
    ("0.0005", "scripts/constant_preference.py"):
        "grid endpoint, a chosen search bound",
    ("0.0001", "scripts/constant_preference.py"):
        "optimiser floor, written 1e-4 and reported by repr(), a chosen bound",
    ("0.565", "scripts/check_reported_numbers.py"):
        "the worked example in this file's own docstring, of a value that escapes",
}


SELF = "scripts/check_reported_numbers.py"
# The tables above declare which values are special. Their keys have to be written literally,
# and once COPIED_OK is keyed on (value, file) those keys are string literals in this file
# that no entry covers -- so the list would flag itself and then need an entry per entry.
TABLES = {"ALLOWED", "COPIED_OK", "CONVENTION_BOUND"}


def _table_lines(tree):
    """Lines of this file's own exemption tables. A declaration is not a measurement."""
    lines = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id in TABLES for t in node.targets):
            lines.update(range(node.lineno, (node.end_lineno or node.lineno) + 1))
    return lines


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


# Figures whose value depends on a scoring convention. Explicit, and therefore incomplete:
# these are the ones that have already caused a disagreement, not every one that could. A
# new convention-dependent figure has to be added by hand and nothing notices that it was not.
CONVENTION_BOUND = {"0.6205", "0.0686"}
CONVENTION_TAG = re.compile(r"<!--\s*unparseable=(0(?:\.25)?)\s*-->")


def _paragraphs(lines):
    """(first line number, text) for each blank-line-delimited block."""
    out, start = [], None
    for i, line in enumerate(lines):
        if line.strip():
            start = i if start is None else start
        elif start is not None:
            out.append((start + 1, "\n".join(lines[start:i])))
            start = None
    if start is not None:
        out.append((start + 1, "\n".join(lines[start:])))
    return out


def convention_bearing():
    """Convention-bound figures quoted without declaring the convention, or declaring two.

    Two numbers can both be right and still disagree, and "which one is wrong" is then the
    wrong first question. It has happened three times in this project. Once it was these
    figures: a reviewer recomputed the spread and got a different third decimal, and the
    whole of it was whether an unparseable verdict scores 0 or upstream's quarter credit.
    docs/errata.md carries that account.

    docs/findings/0003 claims those figures are "stated wherever they appear". This checks
    that claim rather than trusting it, and the claim was false -- README's summary carried
    both figures and named the convention only for upstream's contrasting value.

    **The first version of this check passed that README.** It looked for the word
    "unparseable" within four lines, and the misleading passage contained it, referring to
    upstream's value. A proximity test cannot tell "the convention is stated for this figure"
    from "the word appears nearby", and it certified the exact accident it was written for.

    So the declaration is a tag rather than prose: `<!-- unparseable=0 -->` in the paragraph.
    That is mechanical, and it buys the property proximity could not -- **two paragraphs
    quoting one figure under different declared conventions is a contradiction this can
    see.** What it cannot see is whether the prose beside the tag agrees with it; the tag
    obliges an author to decide, and a reader still has to be told in words.

    The two figures have to be written literally here, because a check that polices a figure
    has to name it. They were first exempted in COPIED_OK, and that exemption matched on the
    value alone -- so digits excused for being *policed* here were excused for being *copied*
    anywhere. COPIED_OK is keyed on (value, file) now and this table is skipped structurally,
    which made both entries dead; removing them changed nothing, so they are gone.
    """
    missing, conflict = convention_findings(
        [(p, open(p, errors="ignore").read()) for p in tracked(r"\.md$")])

    n = len(missing) + len(conflict)
    print(f"\n[convention] convention-bound figures quoted without a declared convention: {n}")
    for path, lineno, what in missing:
        print(f"  {path}:{lineno}  {what}")
    for fig, seen in conflict:
        print(f"  {fig} is quoted under more than one convention:")
        for tag, path, lineno in seen:
            print(f"      {path}:{lineno}  unparseable={tag}")
    if n:
        print("  Put <!-- unparseable=0 --> in the paragraph, and say it in words too. A")
        print("  reader who recomputes under the other convention gets a different number")
        print("  and nothing tells them both are right.")
    return n


def convention_findings(docs):
    """(missing, conflict) for [(path, text)]. Pure, so scripts/check_the_checks.py can
    feed it the accident rather than trusting that it would have caught it."""
    missing, declared = [], {}
    for path, text in docs:
        for lineno, para in _paragraphs(text.splitlines()):
            here = {f for f in CONVENTION_BOUND if f in para}
            if not here:
                continue
            tags = set(CONVENTION_TAG.findall(para))
            if not tags:
                missing.extend((path, lineno, f) for f in sorted(here))
            elif len(tags) > 1:
                missing.append((path, lineno, f"two conventions declared: {sorted(tags)}"))
            else:
                tag = next(iter(tags))
                for f in sorted(here):
                    declared.setdefault(f, []).append((tag, path, lineno))

    conflict = [(fig, seen) for fig, seen in sorted(declared.items())
                if len({t for t, _, _ in seen}) > 1]
    return missing, conflict


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
        tables = _table_lines(tree) if path == SELF else set()
        for node in ast.walk(tree):
            if getattr(node, "lineno", None) in tables:
                continue
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                for m in re.findall(r"(?<![\w.])\d+\.\d{3,}", node.value):
                    if m not in ALLOWED and (m, path) not in COPIED_OK:
                        hits.append((path, node.lineno, m, "printed"))
            elif (isinstance(node, ast.Constant) and isinstance(node.value, float)
                  and _decimals(node.value) >= 4):
                m = repr(node.value)
                if m not in ALLOWED and (m, path) not in COPIED_OK:
                    hits.append((path, node.lineno, m, "consumed"))
    print(f"\n[copied] numbers in scripts that look measured, not chosen: {len(hits)}")
    for path, line, m, kind in hits:
        print(f"  {path}:{line}  {m}  ({kind})")
    if hits:
        print("  Read them from a result file. A measurement in code is a measurement")
        print("  nobody re-derives when the run behind it changes.")
    return len(hits)


def prose_findings(docs, haystack):
    """(unaccounted, one_off) for [(path, text)] against a set of tokens seen in outputs.

    Pure, so scripts/check_the_checks.py can hand it a line and see what the gate makes of it.
    Its predecessor was a loop inside main() reading files off disk, and the fixture written
    against it took a bare string and never applied SKIP_LINE -- so it could not have detected
    that SKIP_LINE was skipping every markdown table, which it did for the whole life of that
    pattern. A check whose fixture bypasses the part that decides is not a fixture.
    """
    unaccounted, one_off = [], []
    for doc, text in docs:
        for lineno, line in enumerate(text.splitlines(), 1):
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
    return unaccounted, one_off


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

    n_laundered = copied_measurements() + truncated_outputs() + convention_bearing()
    print(f"\nprose files : {len(docs)}")
    print(f"output files: {len(outputs)}  ({', '.join(outputs[:4])}{' ...' if len(outputs) > 4 else ''})")
    print()

    unaccounted, one_off = prose_findings(
        [(d, open(d, errors="ignore").read()) for d in docs], haystack)

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
