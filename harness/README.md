# harness

`run_generative_v2.patch` is the only change this repository makes to the evaluator it runs.
It is kept as a diff rather than a modified copy so that what was changed can be read in a
minute instead of being reconstructed by comparing two 900-line files.

## Applying it

```bash
git clone https://github.com/allenai/reward-bench.git
cd reward-bench && git checkout 05a9005efb607249822c193590c8ecab87c77052
git apply /path/to/harness/run_generative_v2.patch
pip install -e . google-genai together      # the last two are needed to import; see issue #274
```

## What it changes

36 lines, of which 4 modify an existing line and the rest are additions. **No scoring
function is touched** — `process_shuffled`, `process_judgement` and `process_single_model`
are byte-identical to upstream, so an item is credited exactly as upstream credits it.

| Flag | Effect | Default |
|---|---|---|
| `--ordering 0..23` | Fixes the candidate ordering to one of the 24 permutations | unset: upstream's unseeded draw over its 4 arrangements |
| `--system_prompt_file` | Reads the four-way ranking system prompt from a file | unset: upstream's prompt |
| `--skip_ties` | Skips the Ties subset | unset: Ties runs |

It also keeps three columns upstream computes and discards: the judge's response text, the
letter that text was parsed to, and where the chosen candidate sat. Without them the
question this repository exists to ask — does the judge's stated reasoning agree with its own
verdict — cannot be counted at all.

## Why 24 orderings

Upstream draws `shuffle_option` from `np.random.randint(0, 4)` and each value swaps the
chosen candidate with one other, so only 4 of the 24 orderings ever occur and the three
rejected candidates keep almost the same relative order. The position effect that can be
measured from those 4 is a mixture of where the chosen candidate sits and which rejected
candidate sits where. Sweeping all 24 gives six samples per chosen-position and separates
the two.

## Verifying it

[`scripts/verify_patch_equivalence.py`](../scripts/verify_patch_equivalence.py) checks that
each of upstream's four arrangements is reproduced by exactly one of the 24 permutations,
with the chosen candidate in the slot upstream records. It prints the pristine block from
`git show` alongside, so the comparison does not rest on our description of it.

The obvious check — run patched and unpatched and diff the results — cannot be run:
`datasets.map` fingerprints the mapped function's bytecode, so adding a line invalidates the
cache and the unseeded draw comes out different for reasons unrelated to the patch. The
equivalence check above covers all four arrangements rather than sampling, because the
arrangement logic does not depend on the item.

Output: [`results/validation/`](../results/validation).
