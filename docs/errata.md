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

## 2026-08-14 — the control set orders its distractors, and that read as a position effect

[`docs/findings/0002-position-fallback.md`](findings/0002-position-fallback.md) reported that
a judge "acquires" a first-slot preference as items get harder, on the strength of a letter
distribution that goes from uniform to 56.5% `[[A]]` against 8.8% `[[D]]`. The counts are
right. **The reading is not, and two separate things make it wrong.**

The first is arithmetic. `f_A = (1/4) a_A + E_A (1 - a)`, so a judge whose placement of
errors never changes still shows a rising first-slot rate as it becomes less accurate. On the
pilot judge the placement, measured conditionally, is flat — 0.8269, 0.8351, 0.7932 across
the three levels where it can be measured — while `f_A` climbs from 0.2517 to 0.5650. The
gradient was accuracy, not behaviour.

The second is this repository's own control set.
[`scripts/build_control_set.py`](../scripts/build_control_set.py) writes its distractors as
`[foreign] * obvious + [own rejected] * (3 - obvious)`, so the plausible distractors are
always **last in the list**, and the four arrangements hold that list in one relative order.
A judge that simply prefers the hardest distractor therefore produces a letter distribution
that reads as a slot preference — and the apparently preferred slot moves between difficulty
levels because the hard distractor moves. Measured across four judges: at `--obvious 2`,
113, 151 and 162 of the errors go to the third distractor and 0 to 3 go to the first.

What survives is the accuracy, which the finding also reported. Accuracy by the correct
answer's position compares the same four candidates in both arrangements, so a
distractor-quality effect hits both and cancels. So does asking how often *the same
candidate* is named in one slot versus another, which
[`scripts/within_candidate.py`](../scripts/within_candidate.py) now reports: on the
unmodified benchmark item the first rejected response is named 7.90x more often at A than at
B for `Qwen2.5-7B-Instruct` (95% CI 4.67 to 17.40), 5.00x for `Skywork-Critic`, 3.00x for
`Con-J`, and 1.43x with the interval including 1 for `RISE-Judge`.

**The position effect is real and the finding's headline stands; its explanation does not.**
It is not a fallback that appears under load. It is a standing pull toward the first slot,
of a size that differs several-fold between judges, and the earlier reading mistook two
artefacts for a gradient.

---

## 2026-08-14 — a context cap recorded for a run that could not have used it

The judge screen's raw log recorded `max_model_len: 16384` for every candidate, and
`screen_summary.txt` printed "cap used: 16384, which is 2.6x that" by reading the first file
alphabetically. **`NCSOFT/Llama-3-OffsetBias-8B` declares 8192 tokens of context and vLLM
refuses a cap above a model's own declaration**, so that judge cannot have run at 16384. The
number was a constant written into the metadata by the script that assembled the log, not the
value the engine used.

It surfaced because the same constant was passed by the P1a runner, which stopped when it
reached that judge, after 64 of 80 passes, with a validation error from vLLM saying the
user-specified length exceeded the one derived from the model's own configuration.

Three changes. The raw record now says 8192, which is what the engine would have derived,
with the correction noted in the record itself. `summarize_screen.py` prints one cap per
judge rather than quoting a single file's value for all six. `run_p1.py` derives the cap from
each model's config and refuses to run if it falls below the longest request the experiment
can make, which it measures with that judge's own tokenizer rather than reading a constant.

This is the same shape as the five number errors already listed here: a value written by hand
next to data that could have supplied it. The difference is that this one was caught by a
crash rather than by a reader.

---

## 2026-08-15 — a table that proved a convention matters, and did not say which one it used

`leaderboard_exposure.txt` §3 shows that crediting an unparseable verdict 0.25 rather than 0
changes which judge ranks first. §1 of the same file printed per-judge accuracies without
saying which of the two it had used. The choice moves §1's numbers too, not only §2's
ordering: for the two judges with parse failures the spread differs in the third decimal.

It surfaced as a disagreement rather than as a reading. A reviewer recomputed §1
independently, from the runner's own `results` field, and got 0.0689 where the artefact said
0.0686. **Both numbers were right.** One scored unparseable verdicts 0 and the other took
upstream's 0.25 credit, and nothing in §1 distinguished them.
<!-- unparseable=0 -->

The first account of that disagreement — this file's author's — was that a figure had been
copied out of a handoff instead of an artefact. That was wrong, and wrong in a way worth
recording: it named a failure the repository had already had, which made it plausible, and
the plausible explanation stopped the search before the real one. §1 now names its
convention.

Findings that have been re-derived and stand as published: the 179-of-188 id census and its
single distinct shape; `352 / 1763 = 20.0%` contributing `0.0499` of `0.6682`; the
ratings-12 / ranking-2 / recorded-0-of-14 split; every figure in the run-to-run variance
table; the `0.25` histograms.

---

## 2026-08-16 — the fix for that said it had been applied everywhere, and it had not

The entry above ends with §1 naming its convention. `docs/findings/0003` then wrote that the
two figures score an unparseable verdict 0 and that this is *"stated wherever they appear"*.

They appear in two tracked files. `README.md` was the other, and it named no convention for
them — the only convention in that paragraph was upstream's contrasting 0.25, three lines
below, attached to a different claim. A reader recomputing the spread from the README would
have reproduced the original disagreement exactly, which is the failure the entry above was
written to close.

The sentence was a claim about a file it did not check. Same shape as the labels already listed
here that stopped describing what they sat next to, and this one asserted the repair.

**The check written for it passed the defect.** Its first version looked for the word
"unparseable" within four lines of the figure; the misleading paragraph contains that word.
A proximity test cannot separate *the convention is stated for this figure* from *the word is
nearby*, so it certified the exact accident it was built from — and it did so at the moment
it was fed that accident, which is the only reason this is an erratum about a check rather
than a check nobody tested. The declaration is now a tag, `<!-- unparseable=0 -->`, which is
mechanical and additionally makes two files declaring different conventions for one figure a
contradiction the gate can see. It still cannot tell whether the prose beside the tag agrees
with it.

Both accidents are fixtures in `scripts/check_the_checks.py`.

---

## 2026-08-16 — an artefact answered its own question and went on asking it

`4ff2aa6` published `results/validation/exchangeable_full_ladder.txt`, which reports every
control level tested for exchangeability at full size. Its table reads `control_o2_full …
differs`. Its closing paragraph, printed by the same script on the same run, read that
`--obvious 2` stays undetermined and that settling it would need that level rebuilt at full
size — which is what the run above it was.

The paragraph was true when it was written into `scripts/check_exchangeable.py`, and stopped
being true the moment the script had the two rebuilt levels to print. The generator carried
prose written before the result existed, so producing the result did not update it.

**How it got past us.** Nothing numeric was wrong. Every check this repository has — the prose
gate, the copied-measurement faces, the convention tags, the truncation check — reads figures,
and this was a claim. The gate reported clean, the pre-push check passed, and the file was
pushed with the contradiction in it.

Correct figures were not what saved it, either. The prose gate reads tracked markdown and
treats `results/*.txt` as the corpus that markdown is checked *against*, so a sentence an
artefact writes about itself is never read as a claim whatever it contains; the paragraph in
question carried three integers, all right, and wrong ones would have fired nothing. **No check
here sees any claim an artefact makes about itself.** Corrected in `e325922`, in both artefacts rather than only
the new one, because fixing the file a reader was pointed at and leaving the older one would
have moved the defect rather than closed it.

The older artefact's figures are cited in `PREREGISTRATION-exp01b.md`, so before it was
regenerated every numeric token in it was compared against the committed version and found
identical; a prose-only edit does not touch the seeded draws, but *should not* is not
*did not*.

The boundary is now written into `scripts/check_reported_numbers.py`, at the head of what it
does not catch, because until then that list read as though every class of drift it misses is
numeric.

---

## 2026-08-16 — the same class again, two rounds later, in the sentence added to close it

`563faa9` published `results/validation/band_strata.txt` with one hand-written line in an
otherwise generated table:

> The gap is taken at B=3; it moves by under a thousandth across the three.

It does not. Recomputed from each band count's own hard estimate, four of the five judges move
by more than a thousandth; `Qwen2.5-7B-Instruct` reads 0.4219, 0.4228 and 0.4154 at the three
band counts, which is several times the width the sentence claimed. **The rows that refute it
were printed in the same artefact, three blocks above it.**

Nothing in the conclusion moved — computed per band count the resolvable set is the same four
judges — but the claim was false, in an artefact, contradicted by that artefact's own table on
the same run. That is the class the entry above this one was written for, and this instance was
committed two rounds after it.

**How it got past us.** The same way: a check reads figures, and results/*.txt is the corpus
figures are checked *against*, so nothing looks at a sentence an artefact writes about itself.
The gate reported clean and the pre-push check passed.

**What is different, and worth more than the correction.** The line was the only hand-written
sentence in a generated table, and it existed to justify not generating one more column. Two
other fixes in the same commit were made by generating a table instead of writing about it; the
same move was available here and was not taken. The fix is to print the gap at each band count
and delete the sentence, which leaves the claim nothing to be wrong about.

The resolvability test was strengthened at the same time and for a separate reason: it compared
the hard stratum's point estimate against the easy half-width, which rests the conclusion on a
number whose own half-width is about the size of the smallest gap. It now asks whether the
easy stratum could resolve the largest disposition the hard interval admits. The answer is the
same four judges, with the margin stated rather than assumed.
