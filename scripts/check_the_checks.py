#!/usr/bin/env python3
"""Feed each accident this repository has had to the check that is supposed to catch it.

A check is a claim: "this class of mistake cannot get past me." The claim is testable and
was not tested, three times in one day, and each time the check passed while the mistake it
was named for walked through. The pattern was always the same — a mark saying "looked here"
over a place nobody had looked.

So every check gets a fixture: the accident, reproduced small enough to run, and the
assertion that the check flags it. When a new check is added, its accident is added here in
the same commit. If the accident is not caught, the check is filtering on the wrong thing
and the fixture says so before anyone trusts it.

  python scripts/check_the_checks.py

Exit code 0 when every accident is caught, 1 otherwise.
"""
import ast
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_reported_numbers import (ALLOWED, COPIED_OK, NUM, _decimals,
                                    convention_findings, prose_findings)
from make_figure import artefact_table, verdict
from summarize_graded import CONCLUSION, contra_cell

# The sentence a judge writes under each inverted wording. The corrected prompt drops
# "remaining", which the detector for the old one is keyed on.
INV_OLD = "Assistant C is the remaining assistant, since the other three answer less well."
INV_NEW = "Assistant C is the one assistant that is not among those three."

# A stand-in for §1 of leaderboard_exposure.txt. Deliberately not the real judges or the real
# numbers: what is under test is the comparison, and a fixture carrying live figures would
# start looking like data and go stale beside it.
FIG_TABLE = """
    judge                               at A      at B      at C      at D      mean    spread
    Judge-One                         0.5000    0.4000    0.3000    0.2000    0.3500    0.3000
    Judge-Two                         0.6000    0.6000    0.6000    0.6000    0.6000    0.0000

2. The ranking those scores induce, by arrangement
"""
FIG_ACC = {"Judge-One": [0.5, 0.4, 0.3, 0.2], "Judge-Two": [0.6, 0.6, 0.6, 0.6]}

# README's summary, as it stood on 2026-08-16. It quotes two convention-bound figures and
# names a convention -- upstream's contrasting one. The first version of the convention check
# looked for the word within four lines and passed this paragraph.
README_AS_IT_WAS = """**And it reaches the score.** On identical items with only the correct answer's position
changed, a judge's accuracy moves by up to 0.6205 and by as little as 0.0686, and the
ranking those scores induce inverts. Upstream credits an unparseable verdict 0.25; first
place changes on that convention alone.
"""
TAGGED = README_AS_IT_WAS + "<!-- unparseable=0 -->\n"
TAGGED_OTHER = README_AS_IT_WAS + "<!-- unparseable=0.25 -->\n"

# Each entry: what happened, the source it happened in, the file it is attributed to, and
# which face should flag it -- None where the check is expected to stay quiet.
ACCIDENTS = [
    ("a measured accuracy typed into a dict the script consumes",
     'OBS = {"judge-a": ([0.9917, 0.8117, 0.6633, 0.5133], 0.2697, 0.2503)}',
     "scripts/anywhere.py", "consumed"),
    ("a figure typed into a print statement, laundered into results/",
     'def main():\n    print("""\\n  the ceiling is +0.2818 on the balanced set\\n""")',
     "scripts/anywhere.py", "printed"),
    ("the pilot accuracies copied out of a run into module scope",
     'PILOT_ACC = {3: [.9933, .9933, .9933, .9867], 0: [.8533, .5333, .3933, .3000]}',
     "scripts/anywhere.py", "consumed"),
    # An exemption is granted for a reason, and a reason is about a place. Keyed on the value
    # alone, one granted to a search bound cleared the same digits in every other script.
    ("a figure exempted elsewhere, hardcoded where no exemption covers it",
     'SPREAD = 0.0005', "scripts/anywhere.py", "consumed"),
    ("the same figure in the file its exemption names",
     'grid = [0.0005, 0.005]', "scripts/constant_preference.py", None),
]


def flags(src, path):
    """Which faces of the copied-measurement check fire on this source, read as `path`."""
    out = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            for m in re.findall(r"(?<![\w.])\d+\.\d{3,}", node.value):
                if m not in ALLOWED and (m, path) not in COPIED_OK:
                    out.add("printed")
        elif (isinstance(node, ast.Constant) and isinstance(node.value, float)
              and _decimals(node.value) >= 4):
            m = repr(node.value)
            if m not in ALLOWED and (m, path) not in COPIED_OK:
                out.add("consumed")
    return out


def prose_gate_catches(line, outputs):
    """Would the prose gate flag a number on this line, given these output files?

    Routed through the gate's own prose_findings, so the line meets SKIP_LINE, SKIP_TOKEN and
    ALLOWED exactly as a tracked file's line does. The version this replaces ran NUM.findall on
    a bare string and never applied SKIP_LINE, which is why no fixture could see that every
    markdown table row was being skipped.
    """
    have = set()
    for text in outputs:
        have.update(NUM.findall(text))
        have.update(t.replace(",", "") for t in NUM.findall(text))
    unaccounted, _ = prose_findings([("fixture.md", line)], have)
    return bool(unaccounted)


def main():
    bad = 0
    print("copied-measurement check, against the accidents it was built from\n")
    for what, src, path, face in ACCIDENTS:
        got = flags(src, path)
        ok = (face in got) if face else not got
        bad += not ok
        print(f"  {'PASS' if ok else 'FAIL'}  {what}")
        print(f"        expected {face or 'nothing'}, fired: {sorted(got) or 'nothing'}")

    print("\nprose gate, against a number no script produced")
    caught = prose_gate_catches("the ceiling is 0.2818 on the balanced set",
                                ["a table with 0.3875 and 0.3167 in it"])
    bad += not caught
    print(f"  {'PASS' if caught else 'FAIL'}  a stale figure quoted in prose")

    print("\nprose gate, against markdown tables, where most of this repository's numbers are")
    for what, line, want in [
        ("an untraceable figure on a table row", "| Qwen2.5-7B | 0.98765 |", True),
        ("the same row, indented", "  | Qwen2.5-7B | 0.98765 |", True),
        ("a traceable figure on a table row", "| Qwen2.5-7B | 0.3875 |", False),
    ]:
        got = prose_gate_catches(line, ["a table with 0.3875 and 0.3167 in it"])
        ok = got == want
        bad += not ok
        print(f"  {'PASS' if ok else 'FAIL'}  {what}")
        print(f"        expected {'flagged' if want else 'quiet'}, "
              f"{'flagged' if got else 'quiet'}")

    print("\nprose gate, against a number that IS in an output")
    quiet = not prose_gate_catches("the ceiling is 0.3875 on the balanced set",
                                   ["a table with 0.3875 and 0.3167 in it"])
    bad += not quiet
    print(f"  {'PASS' if quiet else 'FAIL'}  a traceable figure is not flagged")

    print("\nconvention check, against the paragraph its first version passed")
    for what, docs, want in [
        ("the figures quoted with only upstream's convention named",
         [("README.md", README_AS_IT_WAS)], True),
        ("the same paragraph, convention declared", [("README.md", TAGGED)], False),
        ("two files declaring different conventions for one figure",
         [("README.md", TAGGED), ("docs/f.md", TAGGED_OTHER)], True),
    ]:
        missing, conflict = convention_findings(docs)
        fired = bool(missing or conflict)
        ok = fired == want
        bad += not ok
        print(f"  {'PASS' if ok else 'FAIL'}  {what}")
        print(f"        expected {'flagged' if want else 'quiet'}, "
              f"{'flagged' if fired else 'quiet'}")

    print("\nfigure's cross-check, which refuses to draw off a table it disagrees with")
    for what, table, want in [
        ("the artefact agrees cell for cell", FIG_TABLE, "matches"),
        ("one cell moved in the third decimal", FIG_TABLE.replace("0.3000", "0.3070", 1),
         "differs"),
        ("a judge the artefact does not carry",
         FIG_TABLE.replace("Judge-Two", "Judge-Three"), "differs"),
        ("§1 no longer parses at all", "the artefact was reformatted", "unread"),
    ]:
        got = verdict(FIG_ACC, artefact_table(table))
        ok = got == want
        bad += not ok
        print(f"  {'PASS' if ok else 'FAIL'}  {what}")
        print(f"        expected {want}, got {got}")

    print("\ncontradiction detector, against the prompt it would have been blind to")
    for what, pattern, text, want in [
        ("the old detector on the old wording", "inverted", INV_OLD, True),
        ("the old detector on the corrected wording", "inverted", INV_NEW, False),
        ("the new detector on the corrected wording", "inverted_fixed", INV_NEW, True),
        ("the new detector on the old wording", "inverted_fixed", INV_OLD, False),
    ]:
        got = bool(CONCLUSION[pattern].search(text))
        ok = got == want
        bad += not ok
        print(f"  {'PASS' if ok else 'FAIL'}  {what}")
        print(f"        expected {'match' if want else 'no match'}, "
              f"{'match' if got else 'no match'}")

    print("\nnothing detected is not nothing found")
    for what, args, want in [("a condition that was never run", (0, 0), "not evaluated"),
                             ("a condition with no contradictions in it", (0, 500), "0.0%")]:
        cell = contra_cell(*args)
        ok = want in cell
        bad += not ok
        print(f"  {'PASS' if ok else 'FAIL'}  {what}")
        print(f"        expected {want!r}, got {cell.strip()!r}")

    print("\nempty-output check, against a truncated artefact")
    caught = not "".strip()
    bad += not caught
    print(f"  {'PASS' if caught else 'FAIL'}  a zero-byte results file")

    print("\nwhat these fixtures do not establish")
    print("  Each is the accident as it happened, not the class it belongs to. A check that")
    print("  passes here has been shown to catch one instance; the shapes named in")
    print("  check_reported_numbers.py under 'What it does not catch' are still uncaught,")
    print("  and this file does not test for them because they are known to fail.")
    print(f"\n{'all accidents caught' if not bad else f'{bad} not caught'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
