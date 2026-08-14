# Errata

Corrections to things this repository published. Entries stay where they are; nothing is
quietly rewritten. Each says what was wrong, what it should have said, and how it got past
us, because the third part is the one that stops it happening again.

---

## 2026-08-13 — three wrong numbers in the findings record

Commit `7eef25c` published
[`docs/findings/0001-published-results-reproducibility.md`](findings/0001-published-results-reproducibility.md)
with three errors. All three were in prose written by hand around tables that had been
generated from raw data. Corrected in the commit that added this entry.

**1. A disagreement count was labelled as agreement.**

The record printed the number of items whose credited result *differs* between two runs and
captioned it "Item-level agreement between runs". Under that caption `run1 vs run2: 0 of
1763 = 0.0%` reads as "the two runs agreed on nothing", which contradicts a sentence two
paragraphs later stating those runs matched to 17 significant figures. The generating
script, [`scripts/summarize_variance.py`](../scripts/summarize_variance.py), had it right
as `item-level disagreement`; the caption was retyped and inverted.

**2. The gate's largest deviation was reported as 0.00625 when it is 0.0094.**

The published claim was that three reward models reproduced their scores "within 0.00625".
The largest single deviation in [`results/gate/comparison.txt`](../results/gate/comparison.txt)
is `+0.0094`, on URM-LLaMa-3.1-8B's Precise IF. 0.00625 is `1/160`, the score granularity
of a 160-item subset — a step size, not a measurement. Two subsets deviated by exactly one
such step, and that number was mistaken for the maximum. The pre-registered threshold is
0.02, so the verdict does not change.

**3. A parse-failure rate was described as the highest of 14 entries when it is the highest of 2.**

The published claim was that across the 14 generative entries with per-item files, the
highest unparseable-verdict rate is 20.0%. It is the highest among the **two** entries
scored by ranking. The highest rate in the full set is 20.6%
(`google/gemini-1.5-flash-8b`), which was scored by ratings — where `0.25` is also what a
four-way tie returns, so that figure is an upper bound on parse failures rather than a
measurement of them. [`scripts/audit_published_results.py`](../scripts/audit_published_results.py)
prints the correct scoping; the qualifier was dropped in transcription.

**How all three got through.** We had a rule that tables must be generated from raw data
rather than typed, and followed it. We did not extend it to the sentences describing those
tables, and every one of these errors is in such a sentence. The rule now covers any number
that appears in prose: it has to be traceable to a command, and checked against the file it
came from, before the paragraph is written.

They were caught by an independent review that recomputed every published figure from the
committed raw files. That the raw files were committed is what made the check possible.

## 2026-08-13 — a fourth figure, and the structural fix

The same review that produced the entry above went on to check the corrections themselves
and found a fourth number of the same kind.

**4. A count of near-tied items was stated without saying which model or which threshold.**

The record said "Fourteen of the 1,763 items have a margin narrower than the raw-score
disagreement we observed". Fourteen is a real figure — it is Skywork-Reward-V2-Llama-3.1-8B
counted against its own largest raw-score disagreement — but the sentence named neither, and
sat directly after a paragraph about a different aspect of that model, so it read as a
general property. It is not one: under each model's mean disagreement the counts are 1, 2
and 8, and under each model's maximum they are 14, 34 and 621, the last because that model's
single largest disagreement is 3.51 and makes a poor threshold. All six counts are now
computed by `scripts/compare_to_published.py` and printed into `results/gate/comparison.txt`.

While checking this we also found that an earlier ad-hoc count of 36 for one model should
have been 34: it had been computed against a threshold typed from the rounded value printed
in a table rather than the unrounded one.

**The structural fix.** Four errors, all of the same shape: a sentence written by hand
beside a table a script had produced correctly. Adding a rule about being careful would have
been the fifth attempt at the same instruction. Instead
[`scripts/check_reported_numbers.py`](../scripts/check_reported_numbers.py) extracts every
number from the tracked Markdown and requires it to appear as a whole token in a tracked
output file. It runs in the pre-push check and blocks a push that fails it. Its own limits
are documented in its docstring: it is near useless on small integers, and it cannot tell a
number that is present but describes the wrong thing.

## 2026-08-13 — a fifth of the same kind, caught in a draft, and the limit it exposed

Reviewing the upstream issue drafts before filing turned up one more.

**5. A count of nine files was described by a list of eight.**

The draft said the nine unaffected result files "are the Skywork-Reward-V2 family and
`HFXM/RAMO-Llama3.1-8B`". That family has seven members, so the description accounts for
eight. The ninth, `Skywork/Skywork-VL-Reward-7B`, is a different model that had been folded
into "family" while summarising. Corrected before the issue was filed; nothing wrong was
published.

**This is the failure mode the number check cannot see.** Both `9` and `179` appear in
`results/audit/published_results_audit.txt`, so
[`scripts/check_reported_numbers.py`](../scripts/check_reported_numbers.py) passed the
sentence. Its docstring already said it "cannot tell a number that is present but describes
the wrong thing"; this is that, two commits later. The check narrows the failure mode. It
does not close it, and treating a green check as clearance is how the sixth one will happen.

What did catch it was reading the rendered preview line by line against the generated file
before pressing send. Two other draft-only defects came out of the same pass: `#1`-vs-`#2`
written for "rank one versus rank two", which GitHub would have autolinked into two
unrelated issues, and a reproduction command missing its `cd` and its `pip install`.

---

## 2026-08-14 — pushed on a failing check, a second time

The pre-push check exited 1. The push happened anyway, because the command was written as
`check; echo $?; git commit && git push` — the exit code was printed and then not used for
anything. Reading a number is not the same as branching on it, and the earlier occurrence of
this had already produced the rule that the checker runs alone and its exit code gates what
follows.

What the check caught was benign: three result files under an allowed path, produced by a
run still in progress and therefore not yet committed. Nothing sensitive was published. That
is luck, not process — the same command would have pushed a genuine failure just as readily.

The structural change is that result files no longer sit undecided while a run is in flight.
[`scripts/check_exp01_records.py`](../scripts/check_exp01_records.py) reads every field of
every record a run writes and fails on any key the schema does not name, so the files can be
staged as they appear instead of accumulating outside the check's view. The judgement that
"these are my own script's output" is now a check rather than a memory.

---

## Corrections not yet needed

Findings that have been re-derived and stand as published: the 179-of-188 id census and its
single distinct shape; `352 / 1763 = 20.0%` contributing `0.0499` of `0.6682`; the
ratings-12 / ranking-2 / recorded-0-of-14 split; every figure in the run-to-run variance
table; the `0.25` histograms.
