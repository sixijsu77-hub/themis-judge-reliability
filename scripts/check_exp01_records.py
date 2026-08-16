#!/usr/bin/env python3
"""Check every field of every record an exp01 run wrote, before those files are committed.

Rule of this repository: read a file end to end before putting it under version control.
That is a judgement a person makes once and then stops making, and a run produces a hundred
files. This makes it a check instead: the schema below names every key that may appear, and
anything else fails. A field that arrives because an upstream version started emitting it,
or because a prompt leaked into a column that was not meant to carry one, has nowhere to
hide.

  python scripts/check_exp01_records.py            # exit 1 if anything is off
  python scripts/check_exp01_records.py --quiet    # only the verdict
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orderings import ALL, FIXED_DISTRACTORS, SLOT_BALANCED, SLOT_OF

# `condition` names which polarity prompt a pass used. Every phase before exp01f ran the
# original alone and recorded the prompt path; the key is required from exp01f on, and older
# records predate it.
META_KEYS = {"_record", "phase", "model", "ordering", "chosen_at_slot", "permutation",
             "obvious", "dataset", "prompt", "evaluator", "max_model_len", "n_items",
             "seconds", "note"}
CONDITION_FROM = ("F1", "G1")
ROW_KEYS = {"id", "subset", "results", "parsed_letter", "judgement_text"}
SUBSETS = {"Factuality", "Focus", "Math", "Precise IF", "Safety", "UltraFeedback"}
PHASES = {"P1a", "P1b", "P1c", "P2a", "P2b", "J3", "F1", "G1"}


def check(path):
    problems = []
    with open(path) as f:
        try:
            meta = json.loads(f.readline())
        except json.JSONDecodeError as e:
            return [f"first line is not JSON: {e}"]
        if meta.get("_record") != "metadata":
            return ["first line is not a metadata record"]
        expected = META_KEYS | ({"condition"} if meta.get("phase") in CONDITION_FROM else set())
        extra = set(meta) - expected
        missing = expected - set(meta)
        if extra:
            problems.append(f"metadata has unexpected keys: {sorted(extra)}")
        if missing:
            problems.append(f"metadata is missing keys: {sorted(missing)}")
        if meta.get("phase") not in PHASES:
            problems.append(f"phase {meta.get('phase')!r} is not one of {sorted(PHASES)}")
        o = meta.get("ordering")
        allowed = (SLOT_BALANCED if meta.get("phase") in ("P1c", "P2b", "J3", "F1", "G1")
                   else FIXED_DISTRACTORS)
        if o not in allowed:
            problems.append(f"ordering {o} is not in the set {meta.get('phase')} uses, "
                            f"{allowed}")
        elif meta.get("permutation") != list(ALL[o]) or meta.get("chosen_at_slot") != SLOT_OF[o]:
            problems.append(f"ordering {o} recorded as {meta.get('permutation')} / "
                            f"{meta.get('chosen_at_slot')}, should be {list(ALL[o])} / "
                            f"{SLOT_OF[o]}")
        if meta.get("obvious") not in (0, 1, 2, 3):
            problems.append(f"obvious {meta.get('obvious')!r} is not a difficulty level")

        n = 0
        disagree = 0
        letters, subsets = set(), set()
        for i, line in enumerate(f, start=2):
            try:
                r = json.loads(line)
            except json.JSONDecodeError as e:
                problems.append(f"line {i} is not JSON: {e}")
                continue
            n += 1
            if set(r) != ROW_KEYS:
                problems.append(f"line {i} has keys {sorted(r)}, expected {sorted(ROW_KEYS)}")
                continue
            if not isinstance(r["id"], str) or not r["id"]:
                problems.append(f"line {i}: id is not a non-empty string")
            if r["subset"] not in SUBSETS:
                problems.append(f"line {i}: subset {r['subset']!r} unexpected")
            if not isinstance(r["results"], (int, float)) or not 0 <= r["results"] <= 1:
                problems.append(f"line {i}: results {r['results']!r} outside [0, 1]")
            if not isinstance(r["judgement_text"], str):
                problems.append(f"line {i}: judgement_text is not a string")
            letters.add(r["parsed_letter"])
            subsets.add(r["subset"])
            # The patch records where the chosen candidate was placed; the metadata records
            # what the ordering index implies. If those ever disagree, every accuracy in
            # every table is wrong, and nothing else here would notice.
            if r["parsed_letter"] in "ABCD":
                if abs((1.0 if r["parsed_letter"] == meta["chosen_at_slot"] else 0.0)
                       - r["results"]) > 1e-9:
                    disagree += 1
        if disagree:
            problems.append(f"{disagree} verdicts where 'parsed_letter == chosen_at_slot' "
                            f"disagrees with the score the evaluator assigned")
        if n != meta.get("n_items"):
            problems.append(f"metadata says n_items={meta.get('n_items')} but the file has {n}")
        stray = letters - set("ABCD") - {"error", None}
        if stray:
            problems.append(f"parsed_letter values outside A-D and error: {sorted(map(str, stray))}")
    return problems


# What keying by `id` alone costs, per dataset. This is a property of the source, not of the
# row count: RewardBench 2 duplicates forty ids among its 1,763 non-Ties items, UltraFeedback
# duplicates none. Asserting it by size read "1,763 rows" as "RewardBench 2" and failed the
# first dataset that was neither.
#
# The four RewardBench 2 sets share the number because they share the draw, not because they
# share a size: build_control_set.py takes the same seed and the same non-Ties pool at every
# --obvious level, so all four hold the same 1,763 items and therefore the same forty
# duplicated ids. Checked, rather than assumed from the count matching.
ID_COLLISIONS = {"p1b_o3": 40, "p2_o0": 40,
                 "control_o1_full": 40, "control_o2_full": 40}


def item_keys():
    """Check that (subset, id) identifies an item and that `id` alone does not.

    The schema check passed 220 of 220 while forty items were silently merging in every
    analysis that keyed on id. Its stated scope was schema and placement, so this is an
    extension -- but a check whose silence gets read as coverage is the shape that has cost
    this repository most, and the fix is to make the check say the thing out loud.
    """
    problems = []
    for path in sorted(glob.glob("data/*/test.jsonl")):
        rows = [json.loads(l) for l in open(path)]
        pairs = {(r["subset"], r["id"]) for r in rows}
        ids = {r["id"] for r in rows}
        lost = len(rows) - len(ids)
        if len(pairs) != len(rows):
            problems.append(f"{path}: (subset, id) is not unique -- "
                            f"{len(rows) - len(pairs)} rows collide")
        name = path.split("/")[1]
        want = ID_COLLISIONS.get(name, 0)
        if lost != want:
            problems.append(f"{path}: keying by id alone loses {lost}, expected {want}; "
                            f"the source's id duplication changed")
        print(f"  {path:34s} rows={len(rows):5d}  by (subset,id)={len(pairs):5d}  "
              f"by id={len(ids):5d}  lost={lost}")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    print("item keys in the control sets")
    key_problems = item_keys()
    for p in key_problems:
        print(f"  FAIL {p}")
    files = sorted(glob.glob("results/exp01/*.jsonl"))
    bad = len(key_problems)
    for path in files:
        problems = check(path)
        if problems:
            bad += 1
            print(f"FAIL {path}")
            for p in problems:
                print(f"       {p}")
        elif not args.quiet:
            print(f"ok   {path}")
    print(f"\n{len(files) - bad} of {len(files)} exp01 result files match the schema, and")
    print("their recorded placement agrees with the score the evaluator assigned")
    if bad:
        print("=== FAIL ===")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
