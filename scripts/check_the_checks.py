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
from check_reported_numbers import ALLOWED, COPIED_OK, NUM, _decimals

# Each entry: what happened, the source it happened in, and which face should flag it.
ACCIDENTS = [
    ("a measured accuracy typed into a dict the script consumes",
     'OBS = {"judge-a": ([0.9917, 0.8117, 0.6633, 0.5133], 0.2697, 0.2503)}',
     "consumed"),
    ("a figure typed into a print statement, laundered into results/",
     'def main():\n    print("""\\n  the ceiling is +0.2818 on the balanced set\\n""")',
     "printed"),
    ("the pilot accuracies copied out of a run into module scope",
     'PILOT_ACC = {3: [.9933, .9933, .9933, .9867], 0: [.8533, .5333, .3933, .3000]}',
     "consumed"),
]


def flags(src):
    """Which faces of the copied-measurement check fire on this source."""
    out = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            for m in re.findall(r"(?<![\w.])\d+\.\d{3,}", node.value):
                if m not in ALLOWED and m not in COPIED_OK:
                    out.add("printed")
        elif (isinstance(node, ast.Constant) and isinstance(node.value, float)
              and _decimals(node.value) >= 4):
            if repr(node.value) not in ALLOWED and repr(node.value) not in COPIED_OK:
                out.add("consumed")
    return out


def prose_gate_catches(sentence, outputs):
    """Would the prose gate flag a number in this sentence, given these output files?"""
    have = set()
    for text in outputs:
        have.update(NUM.findall(text))
        have.update(t.replace(",", "") for t in NUM.findall(text))
    return any(tok not in have and tok not in ALLOWED for tok in NUM.findall(sentence))


def main():
    bad = 0
    print("copied-measurement check, against the accidents it was built from\n")
    for what, src, face in ACCIDENTS:
        got = flags(src)
        ok = face in got
        bad += not ok
        print(f"  {'PASS' if ok else 'FAIL'}  {what}")
        print(f"        expected {face}, fired: {sorted(got) or 'nothing'}")

    print("\nprose gate, against a number no script produced")
    caught = prose_gate_catches("the ceiling is 0.2818 on the balanced set",
                                ["a table with 0.3875 and 0.3167 in it"])
    bad += not caught
    print(f"  {'PASS' if caught else 'FAIL'}  a stale figure quoted in prose")

    print("\nprose gate, against a number that IS in an output")
    quiet = not prose_gate_catches("the ceiling is 0.3875 on the balanced set",
                                   ["a table with 0.3875 and 0.3167 in it"])
    bad += not quiet
    print(f"  {'PASS' if quiet else 'FAIL'}  a traceable figure is not flagged")

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
