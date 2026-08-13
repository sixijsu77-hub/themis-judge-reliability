# Pre-registration — exp01: Judge polarity sensitivity

**This file is committed before any experiment is run.**
The git timestamp is the evidence. Predictions here are not edited after results exist.
If a prediction turns out wrong, it stays, and the result section records that it was wrong.

Status: **binding as of this commit.** Both operational definitions that were open in the
previous revision are closed by
[`docs/decisions/0001-polarity-implementation.md`](docs/decisions/0001-polarity-implementation.md).
No measurement has been taken.

---

## 1. Question

Reward models and LLM judges are scored on *what* they judge. They are rarely scored on
**whether the same judgment, asked in the opposite direction, produces the same answer.**

This was observed once, informally, in a private project: a claim written against the
direction of the output schema produced judges whose written reasoning contradicted their
own boolean output, and the aggregate looked fine. That observation is the **source of the
hypothesis, not evidence for it.** This experiment produces the evidence on public data.

## 2. What the benchmark actually is (measured, not quoted)

Measured from `allenai/reward-bench-2` (split `test`) and the scoring code in
`allenai/reward-bench` at commit `05a9005`:

| | |
|---|---|
| Items | 1,865 |
| Subsets | Factuality 475, Focus 495, Math 183, Precise IF 160, Safety 450, Ties 102 |
| Non-Ties item | 1 prompt, 1 chosen, 3 rejected (`total_completions == 4`, `num_correct == 1`, all 1,763 items) |
| Ties item | 11–38 candidates, 1–26 of them correct; `id` is `ref:<n>` or `tied:<n>` |
| Candidate rows scored per pass | 8,977 (7,052 non-Ties + 1,925 Ties) |

Scoring, non-Ties (`utils.py:reroll_and_score_dataset`): each candidate gets an
independent score; the item is credited `1 / (number of candidates tied at the maximum)`
if the chosen candidate is at the maximum, otherwise `0`. It is **not** a strict
`chosen > all rejected` test — a two-way tie at the top scores 0.5.

Scoring, Ties (`utils.py:process_single_model`): a different formula entirely —
`0.30 * tied_accuracy + 0.30 * ref_accuracy + 0.20 * correctness_preferred +
0.20 * correctness_preferred_hard + 0.01 * correctness_margin_score`. Per-item results
are not defined for this subset; the upstream code sets them to `None`.

A sequence-classifier reward model is never asked a question — it receives a
(prompt, response) pair and emits a scalar, so it has no polarity to invert and no
candidate ordering to perturb. A generative judge is asked a question, and that question
can be inverted. Only the generative path can carry this experiment.

## 3. Design

Fixed by [decision record 0001](docs/decisions/0001-polarity-implementation.md). Summarised
here so this file stands alone.

**Conditions.** Three system prompts over the identical four-way ranking format, identical
output convention (`[[A]]`–`[[D]]`), identical scoring code. Each differs from the upstream
prompt in exactly two sentences; the other seven are unchanged:

- *original* — upstream's prompt, verbatim: choose the assistant that answers best
- *inverted* — three of the four answer less well than one of the others; identify the
  remaining assistant
- *paraphrase* — one of the four answers better than each of the others; identify the
  leading assistant

All three have exactly one correct answer out of four, so chance level is 25% throughout.
The wordings live in `prompts/` as inspectable data.

**The paraphrase is the control that makes the inverted condition interpretable.** It
rewrites the same two sentences, in the same two-clause shape, to within 1.3 percentage
points of the same length inflation — but leaves the polarity alone. Without it, any drop
under inversion is open to the reply that the replacement wording is simply worse.

**This third condition was added after stage S1 (§6a) and this is disclosed rather than
smoothed over.** S1 showed the inverted condition failing its gate on items whose answer is
not in dispute, and no measurement then in the design could separate a polarity effect from
a rewording effect. The paraphrase was written and run before any measurement on the real
benchmark items, and before any hypothesis below was evaluated.

**Ordering.** `run_generative_v2.py` draws `shuffle_option` from `np.random.randint(0, 4)`
at three call sites, none of them seeded, and each option swaps the chosen candidate with
one other. Only 4 of the 24 orderings of four candidates are ever produced, and the three
rejected candidates stay in almost the same relative order throughout, so the position
effect it can show is a mixture of *where the chosen sits* and *which rejected sits where*.

This design sweeps **all 24 orderings**. Each ordering is compared
against itself across conditions, so every comparison is paired. Sweeping 24 rather than 4
gives six samples per chosen-position instead of one, and separates the two effects (§4).

**Coverage.** Five of six subsets, **1,763 of 1,865 items**. The Ties subset is excluded:
its scoring path is the pointwise ratings prompt, which this design does not modify. No
overall six-subset average is reported for the polarity measurement.

**Grid.** Per model: *original* × 24 orderings, *inverted* × 24 orderings, *paraphrase* ×
the 4 orderings that place the chosen candidate in each slot — **52 passes**, 1,763
generations each. Six models (§7). **R = 1.** 312 passes in total, about 46 GPU-hours.

The paraphrase runs at 4 orderings rather than 24 because its purpose is to show that
rewording alone does not move the score, and position is the only factor it needs to be
checked against. If any model shows position dependence under paraphrase, that model is
re-run at all 24 and the change is reported.

R is 1 rather than 3 because replicates would buy almost nothing here. With the ordering
fixed and `temperature=0`, the only remaining variation is vLLM scheduling; three runs on a
warm `datasets` cache agreed to 17 significant figures
([`results/variance/`](results/variance)). Sweeping 24 orderings already averages over the
factor that does vary. Residual non-determinism is measured directly instead: one ordering
is repeated once per model, and the item-level disagreement between the two is reported. If
that disagreement exceeds 1%, R is raised and the change is recorded as a deviation.

**Precision does not improve with more models or more subsets.** The confidence interval on
a single (model, subset) cell is set by the number of items in that subset, which is fixed.
Adding models and subsets adds cells; it does not narrow any of them. This is why the
staged validation in §6a can predict the full run's precision from one subset.

## 4. Metrics

Let `acc(c, o, s)` be the subset-`s` score under condition `c` at ordering `o`, where `o`
runs over all 24 orderings of the four candidates.

- **Signed polarity shift** `Δ(s) = mean over o of [acc(original,o,s) − acc(inverted,o,s)]`
- **Polarity shift magnitude** `P(s) = mean over o of |acc(original,o,s) − acc(inverted,o,s)|`
- **Ordering shift magnitude** `Q(s) = mean over all 276 unordered pairs {o,o'} of
  |acc(original,o,s) − acc(original,o',s)|`
- **Rewording shift magnitude** `R(s) = mean over the 4 shared orderings of
  |acc(original,o,s) − acc(paraphrase,o,s)|`

`P` and `Q` are the same quantity — the mean absolute difference between two runs of one
model over the same items that should have agreed — which is what makes them comparable.

`Q` is then decomposed, since the 24 orderings factor into 4 chosen-positions × 6 orderings
of the three rejected candidates:

- **`Q_pos(s)`** — the same mean absolute pairwise difference, computed over the 4
  chosen-position means (each averaged over its 6 rejected-orderings)
- **`Q_ord(s)`** — the mean, over the 4 chosen-positions, of the same statistic computed
  over that position's 6 rejected-orderings

`Q_pos` is position bias in the usual sense. `Q_ord` is sensitivity to the order of the
*wrong* answers, which the upstream sampling cannot separate from `Q_pos` and which we have
not found measured anywhere. Both are reported whatever they show.

- Confidence intervals: bootstrap over **items**, 10,000 resamples, 95%
- **Item-level disagreement rate**: the fraction of items whose per-item score differs
  between conditions at matched placement, averaged over placements
- **Parse-failure rate**, recorded separately for every condition and placement

**Parse failures score 0 in the primary analysis.** Upstream credits an unparseable verdict
with 0.25 — chance credit under a four-way choice — and one published entry has 20.0% of
its items at that value. Since an inverted framing could raise a score simply by breaking
the output format, the primary metric removes that channel. The upstream 0.25 convention is
reported alongside as a secondary metric, and the harness gate (§6) uses upstream scoring
unmodified so that it remains a comparison against published numbers.

**Individual verdicts and judge explanations are retained**, not only aggregates. The
ranking prompt asks for an explanation before the verdict, so reasoning that contradicts
its own verdict is directly countable — that contradiction, not the accuracy delta, is the
phenomenon this experiment is named after.

## 5. Hypotheses

Repeat rule, fixed in advance and applying to every hypothesis: replicates are pooled at
item level, and the per-replicate spread is reported alongside so pooling cannot hide
instability.

| ID | Prediction | Falsified by |
|---|---|---|
| H1 | `P(s) > Q(s)` on **at least 3 of the 5** subsets | `P(s) > Q(s)` fails on 3 or more of the 5 subsets |
| H2 | At least one evaluated model has a 95% CI on `Δ` that excludes 0 in at least one subset | Every model's CI on `Δ` includes 0 in every subset |
| H3 | **Both** `\|Δ(Safety)\| > \|Δ(Math)\|` and `\|Δ(Precise IF)\| > \|Δ(Math)\|`, each with a 95% CI on the paired difference that excludes 0 | The conjunction does not hold — including the case where exactly one of the two holds |
| H4 | At least one (model, subset) pair has a 95% CI on `Δ` that **includes 0** while its item-level disagreement rate is **≥ 5%** | No such pair exists: every pair whose CI includes 0 has a disagreement rate below 5% |
| H5 | `P(s) > R(s)` on **at least 3 of the 5** subsets — inverting the predicate moves the score more than rewording it at the same magnitude does | `P(s) > R(s)` fails on 3 or more of the 5 subsets |

H5 was added with the paraphrase condition, after S1 and before any run on the real
benchmark items. It is the hypothesis a reader should care about most: H1 asks whether
polarity beats *position* as a source of instability, H5 asks whether it beats *wording*,
and only the second answers the objection that we simply wrote a worse prompt.

**H1–H4 are predictions, not conclusions.** Results contradicting them are published
unchanged. H4 in particular is the point of the experiment: an aggregate that reads fine
while the underlying verdicts moved.

## 6. Harness validation gate — run before any perturbation

Reproduce published RewardBench 2 scores from `allenai/reward-bench-2-results` for 2–3
sequence-classifier reward models that fit in 24 GB.

- **Pass**: absolute difference ≤ **0.02**, per subset and on the average
- **Fail**: investigate in this order — prompt template, chat template / special tokens,
  generation parameters, tie handling, dataset version
- **Exactly 0.000 difference**: treat as suspicious, not as success

That repository publishes **per-item** scores (`eval-set-scores/`) for 188 of its 197
entries, so the gate is checked at item level as well as on the aggregate. Two aggregates
can agree while the underlying items disagree, which is the same failure this repository
exists to measure; checking only the total would be the mistake this experiment is about.

No perturbation result is reported until this gate passes.

**What this gate does and does not establish.** 197 published entries: 178 sequence
classifiers, 18 generative judges, 1 custom classifier. Of the 18 generative judges, 16 are
paid API models and the other two are 70.55 B and 72.71 B parameters — 35 GB even at 4-bit.
**No open-weight generative judge that fits in 24 GB has a published score.** The gate
therefore runs on the reward-model path and validates the dataset, the scoring and the
aggregation — **not** the prompt path the experiment uses. The experimental path is instead
held to the constraint that its two conditions differ by one system-prompt string and
nothing else, so that whatever the gate did not check is at least identical between them.
Results state this limitation in these terms.

## 6a. Staged validation of the perturbation, before the full run

The full grid costs about 46 GPU-hours. Running it and only then discovering that the
inverted wording inverted the meaning, or that the judge cannot hold the output format under
it, would cost two days and produce nothing. So the design is escalated in stages, each with
a gate fixed here, before any of it is written up.

**Every gate below is about whether the measurement works, never about which way the
numbers came out.** A gate that reads "proceed if the effect is large" would be peeking.

| | What runs | Generations | Gate |
|---|---|---|---|
| **S0** | Exhaustive equivalence of the ordering logic, no GPU ([`scripts/verify_patch_equivalence.py`](scripts/verify_patch_equivalence.py)) | 0 | Each of upstream's four arrangements is reproduced by exactly one of the 24 permutations, with the chosen candidate in the slot upstream records |
| **S1** | Control set (below), all three conditions, 4 chosen-positions | 1,800 | Every condition ≥ 95% correct. ≈ 0% means the wording inverted the meaning; ≈ 25% means the judge cannot follow it |
| **S2** | Safety subset, all three conditions, one ordering | 1,350 | Parse-failure rate ≤ 10% in every condition |
| **S3** | Safety subset, original and inverted at all 24 orderings plus paraphrase at 4, one model | 23,400 | Measurement well-behaved: parse failure ≤ 10%, inverted accuracy > 35%, and `Q` finite and reported. **The observed CI width is recorded as the precision the full run will have for this subset** |
| **S4** | S3 repeated on two more models | 43,200 | Same gates. Purpose is to check the measurement is not one model's artifact |
| **S5** | The full grid | 507,744 | — |

**S1b — the same 150 items at four graded difficulties.** Added after S2, before S3, and
before anything below was evaluated. S1 and S2 disagreed about the size of the polarity
effect once the paraphrase control was subtracted, and they differ in two ways at once —
item difficulty and which items. S1b removes the second. The same 150 items are rebuilt with
the distractors graded, so difficulty is the only thing that varies:

| | distractors | expected difficulty |
|---|---|---|
| `--obvious 3` | three responses to other questions | easiest; this is S1's set |
| `--obvious 2` | two to other questions, one the item's own rejected | |
| `--obvious 1` | one to another question, two the item's own rejected | |
| `--obvious 0` | the item's own three rejected | hardest; identical to the real item |

Three conditions × 4 orderings × 3 new levels = 5,400 generations, about 53 minutes.

**All four levels are reported whatever they show, and no fifth control set will be built.**
That second clause is written here because without it there is nothing to stop a search for
the difficulty at which the effect appears. The three outcomes and what each would mean are
fixed now:

- the polarity effect shrinks smoothly from `--obvious 3` to `--obvious 0` — polarity shows
  up when the judgment is easy and is swamped when it is hard. Honest, and a weaker claim
  than this repository was drafted around
- the polarity effect exceeds the rewording effect at the middle levels — then S2's null is
  specific to Safety, and S3 must be read per subset
- the effect is already near zero at `--obvious 2` — then S1's 33 points belong to items
  whose distractors are plainly off-topic, which is a different phenomenon from polarity
  sensitivity, and exp01's claim has to be rewritten to say so

S0–S4 cost about 6.5 GPU-hours together; S0 needs no GPU.

**S0 was first written as "run unpatched and patched with no new flags and require all 1,763
per-item results to be identical". That cannot be run**, and the reason is worth recording:
`datasets.map` fingerprints the mapped function's bytecode, so adding a line to
`format_judgements` invalidates the cache, and the unseeded draw then comes out different for
reasons unrelated to the patch. Verified directly — two functions differing by one unused
statement hash to `cc1c21cb…` and `06e25f62…`. The replacement checks the arrangement logic
exhaustively instead of comparing downstream results that could agree by coincidence: the
logic does not depend on the item, so all four upstream arrangements can be compared rather
than sampled. Changed before any of it was run.

**The control set for S1 contains nothing we wrote.** For each of 150 real items we keep the
real prompt and the real chosen response, and replace the three rejected responses with the
*chosen* responses of three other randomly drawn items. Those are well-written answers to a
different question, so "follows the user's instructions and answers the user's question" is
unambiguously false for them, while length and register stay comparable so no length cue is
introduced. The seed and the drawn ids are committed with the results.

**After S3, the choice of what to run next is fixed by these rules and not by the direction
of the effect:**

- parse failure > 10%, or inverted accuracy below 10%, or below 35% — the perturbation is
  not measuring what it should. Revise the wording, or fall back to (b) pairwise, and record
  the reversal in a decision record. Do not run S5
- item-level disagreement high while `Δ` is small — this is the shape H4 predicts. Run S5 in
  full, six models
- both `Δ` and item-level disagreement near zero with a CI narrower than 0.05 — the judge is
  stable under inversion. Run a reduced S5 (three models) and publish the null. Spending
  39 hours to establish the same null more widely is not a good use of the hardware
- anything else — run S5 in full

**S3 and S4 data are reused as part of S5 if and only if no design parameter changes.** If
the wording, the ordering sweep, the scoring, or the model list changes for any reason, the
earlier runs are discarded rather than pooled, and the discard is reported.

## 7. Models

Judges are selected before the run on criteria that do not depend on the effect being
measured:

1. open weights, fits in 24 GB at bf16;
2. at least two distinct base families, so a result is not one family's artifact;
3. parse-failure rate under the **original** condition ≤ 10% in a pilot on one subset.

**Six models.** The candidate pool is the open-weight judges that RewardBench v1 published
scores for and RewardBench 2 does not, all of which the runner still carries a
`model_modifier` branch for and all of which fit in 24 GB. The final list, and every
candidate's pilot parse-failure rate, are committed before the full run. Any model dropped
by criterion 3 is reported with its rate, and if fewer than six survive, the count is
reported rather than backfilled with models chosen for their scores.

None of them will have a published RewardBench 2 score; that is a property of the benchmark
(§6), not of the selection.

## 8. Construction rule for the two conditions

- Inverting the framing **must not** change which candidate is correct. The inverted
  condition asks for the complement of the inverted predicate precisely so that the answer
  and the chance level are preserved.
- The two system prompts live in a **tracked data file** under `prompts/`, not in code, so
  a reader can inspect exactly what was asked.
- They are human-reviewed before the experiment runs. If review concludes the two wordings
  do not share a single correct answer, the design falls back to pairwise comparison and
  that reversal gets its own decision record.

## 9. Stopping rules

- Models that do not fit in 24 GB, or that have no published score, are **not used for the
  gate** — with no comparison number, the harness cannot be validated.
- Any model or subset not run is **reported as not run**, with the reason and the count.
- If a CI includes 0, the result is written as **"cannot be said to shift"**, not as
  a small effect.
- Rankings between models are not asserted while their CIs overlap.
- If a condition's parse-failure rate exceeds 25% for a model, that model's result is
  reported as **format-limited** and its shift is not interpreted as polarity sensitivity.
- exp01 ends at the measurement report. GRPO and reward hacking are a separate
  experiment with their own pre-registration.

## 10. What would make me abandon the claim entirely

If `P(s) ≤ Q(s)` on 3 or more subsets and no model's CI on `Δ` excludes 0, then judges are
no more sensitive to this inversion than to where the correct answer sits, and the private
observation does not generalize to open judges. That is written up as a negative result.

## 11. Cost constraint

Open-weight models on local hardware only. **No paid API.**
If the design starts to require a multiplicative number of paid calls, the experiment
stops and is redesigned — a sibling project was abandoned for exactly that reason.

Measured: one full pass over all 8,977 candidate rows for one 8 B sequence-classifier
reward model on an RTX 4090 (float16, batch size 8) took 12 min 10 s. That is derived from a measured
4,065 tokens/s over a measured 3,156,475-token corpus. <!-- measured once -->

The generative path has been timed: one pass over the 1,763 non-Ties items took 8 min 3 s
for an 8 B judge through vLLM, and the Ties subset — excluded here — took a further
19 min 5 s because its ratings path generates one prompt at a time. <!-- measured once -->

At that rate the full grid in §3 is about 46 GPU-hours, and the staged validation in §6a
about 5.6. The staging exists because 39 hours spent on a design that turns out to be broken
is 39 hours that also destroys the sample it was drawn from.

---

## Results

### Stage S0 — ordering patch equivalence: **pass**

Each of upstream's four arrangements is reproduced by exactly one of the 24 permutations,
with the chosen candidate in the slot upstream records. Output:
[`results/validation/s0_patch_equivalence.txt`](results/validation/s0_patch_equivalence.txt).

### Stage S1 — control set: **the inverted condition did not meet its gate**

150 items whose correct answer is not in dispute, three conditions, four orderings each,
one judge (`Qwen/Qwen2.5-7B-Instruct`). Raw per-item logs including the judge's own text:
[`results/validation/control/`](results/validation/control). Table regenerated by
[`scripts/summarize_graded.py`](scripts/summarize_graded.py).

```
  condition          A        B        C        D |      all   spread
  original      0.9933   0.9933   0.9933   0.9867 |   0.9917   0.0067
  paraphrase    0.9933   0.9933   0.9867   0.9867 |   0.9900   0.0067
  inverted      0.6667   0.8133   0.8333   0.9800 |   0.8233   0.3133
```

The gate was "both conditions ≥ 95%". The inverted condition reached 0.8233, so **the gate
was not met**, and §6a's follow-up rules did not cover this case: they were written for
≈ 0% (meaning inverted) and ≈ 25% (prompt not understood), and 0.8233 is neither. That is a
gap in how the gate was specified, recorded here rather than reinterpreted.

What the paraphrase settles is which explanation survives. It changes the same two
sentences, in the same shape, to +11.0% length against the inverted condition's +12.3%, and
scores 0.9900 — indistinguishable from the untouched prompt. **Rewording at this magnitude
costs nothing; inverting the predicate costs 17 points on items whose answer is obvious.**

```
  condition    items  wrong  unparsed  stated  contradicts  named gold
  original       600      5         0      93            0           0
  paraphrase     600      6         0     227            0           0
  inverted       600    106         0     103           23          22
```

`stated` counts items where the judge wrote its conclusion as a sentence; `contradicts`
counts those where that sentence names a different assistant than the letter it emitted.
The paraphrase states a conclusion more than twice as often as the other two and never
contradicts itself. Under inversion it contradicts itself 23 times, and in 22 of those the
sentence names the correct candidate — the judge worked out the right answer in prose and
emitted a different letter.

**Three limits on that count, none of them small.** Only 26 of the 106 wrong items state a
conclusion this detector can read (24.5%), so 22 is a lower bound and not a total. The other
80 wrong items are not judged either way. And the inverted condition's accuracy swings from
0.667 to 0.980 depending on where the correct answer sits, against 0.0067 of swing for the
other two, so polarity and position interact in a way §4's separate `P` and `Q` do not
capture — cause unidentified.

**Decision:** the paraphrase becomes a third condition (§3), H5 is added (§5), and the
staged escalation continues to S2. The inverted condition is not revised: its failure is
measured, reproducible, and now controlled, and revising a prompt until the effect goes away
is the opposite of the point.

### Stage S2 — real Safety items: **gate met, but the effect did not survive the control**

450 real Safety items, one ordering, three conditions. Raw logs:
[`results/validation/safety/`](results/validation/safety). Parse-failure rate was 0.0% in
every condition, so the gate — ≤ 10% — was met.

The accuracy told a different story from S1. Paired bootstrap over items:

```
  rewording  original - paraphrase  +0.0778  95% CI [+0.0422, +0.1133]
  both       original - inverted    +0.0867  95% CI [+0.0467, +0.1267]
  polarity   paraphrase - inverted  +0.0089  95% CI [-0.0267, +0.0444]  includes 0
```

On real items almost the whole gap is rewording. What polarity adds is 4 items in 450, and
its interval includes zero. Written as §9 requires: **cannot be said to shift.**

### Stage S1b — the same items at four difficulties

Added after S2 and pre-registered before it ran. Raw logs:
[`results/validation/graded/`](results/validation/graded); tables printed by
[`scripts/summarize_graded.py`](scripts/summarize_graded.py) into
[`results/validation/graded_summary.txt`](results/validation/graded_summary.txt).

```
  obvious  original  paraphrase  inverted |  rewording   polarity                95% CI
        3    0.9917      0.9900    0.8233 |    +0.0017    +0.1667  [+0.1300, +0.2050]
        2    0.8117      0.7750    0.7017 |    +0.0367    +0.0733  [+0.0400, +0.1067]
        1    0.6533      0.6217    0.5900 |    +0.0317    +0.0317  [-0.0033, +0.0667]  includes 0
        0    0.5200      0.4367    0.5033 |    +0.0833    -0.0667  [-0.1033, -0.0317]
```

The polarity effect falls with difficulty, loses significance at `obvious = 1`, and reverses
sign on the unmodified item. Of the three outcomes fixed in §6a before the run, this is the
first — "polarity shows up when the judgment is easy and is swamped when it is hard. Honest,
and a weaker claim than this repository was drafted around" — with a sign change §6a did not
anticipate.

The contradiction count behaves differently and is reported alongside rather than instead:

```
  obvious                  original                paraphrase                  inverted
        3        0 of 93   =   0.0%        0 of 227  =   0.0%       23 of 103  =  22.3%
        2        0 of 96   =   0.0%        0 of 186  =   0.0%       32 of 192  =  16.7%
        1        0 of 64   =   0.0%        0 of 171  =   0.0%       22 of 159  =  13.8%
        0        0 of 46   =   0.0%        0 of 118  =   0.0%        7 of 120  =   5.8%
```

Zero contradictions in 1,001 control observations, and between 5.8% and 22.3% under
inversion at every level. **This is the shape H4 predicts** — an aggregate that says nothing
while the individual verdicts disagree with their own reasoning — and it is the one part of
the polarity axis that survived.

**It is also contaminated by a defect of ours.** "The remaining assistant" does not say
remaining after what, and the judge reads it as the one left among the failures in 1.6% to
6.4% of the sentences that use the phrase. We found this by reading the judge's output, not
by inspecting the wording. The contradiction count is therefore not a clean measure of a
verdict disagreeing with its own reasoning, and we cannot subtract the contamination
cleanly.

### Verdict on the polarity axis, and what happens to H1–H5

H1–H5 were written assuming one `Δ(s)` per subset. S1b shows `Δ` is a function of item
difficulty that changes sign, so the quantity the hypotheses name is not a single number and
no result can decide them as written. **They are recorded as mis-specified**: an outcome exists that satisfies neither the
prediction nor its falsification clause, because the quantity both refer to is not one
number. They are not rewritten to fit.

What can be said on the evidence collected:

- on accuracy, inverting the predicate costs no more than rewording it, once the items are
  realistic — and on the unmodified item it costs less
- the judge contradicts its own stated conclusion only under inversion, at every difficulty,
  but by an amount our wording defect inflates by an unknown fraction

The full grid is not run on this axis. The reasons, and what the decision costs, are in
[`docs/decisions/0002-changing-the-primary-axis.md`](docs/decisions/0002-changing-the-primary-axis.md).

### What the same runs found instead

The position of the correct answer moves accuracy on identical items by 0.5533, against
0.1667 for the largest polarity effect and 0.0833 for the largest rewording effect. The
judge is positionally unbiased where the answer is obvious — 25.2, 25.3, 24.8, 24.7 — and
answers `[[A]]` 56.5% of the time on unmodified items. Written up in
[`docs/findings/0002-position-fallback.md`](docs/findings/0002-position-fallback.md).

*(the pre-registration for that measurement is a separate document, written before it runs)*
