# Milestone 2 — Generation Quality & Groundedness

## Final results

Milestone 2 is complete: four controlled prompt experiments, each with 19 saved
generations and finalized manual review. The benchmark has 16 answerable cases
and three deliberate refusals. All answerable cases had sufficient frozen
retrieved evidence. No LLM judge or RAGAS was used; labels are manually adjudicated
and aggregates are deterministic. No weighted overall score is computed.

See the [final four-way comparison](results/generation_prompt_ablation_comparison_final.md)
for every dimension with its eligible denominator, operational measurements,
failure details, and exact per-case transitions. The
[machine-readable comparison](results/generation_prompt_ablation_comparison_final.json)
records exact fractions and provenance hashes.

The baseline covered all required points but produced unsupported elaboration on
14/19 cases. Strict v1 achieved 19/19 groundedness with zero unsupported
elaboration, while full completeness fell to 12/16. Balanced v2 restored full
completeness to 15/16 but reintroduced unsupported content on four cases.
Strict v2 targeted omissions and the false refusal: mean completeness rose from
13.5/16 to 14.5/16, with 18/19 groundedness and one unsupported-elaboration case.
It is not universally best. Its remaining failures are dependency definitions
(008), omitted mechanism (010), omitted performance pattern (012), and an
unsupported generalization explanation (013).

These are results on a controlled 19-case evaluation set. No statistical
significance or generalization beyond this set is claimed. All ablations reuse
the exact baseline contexts and [S#] mappings; only the prompt changed. Production
prompts remain unchanged. Saved responses were not regenerated for this report.

## Finalized human reviews

The Markdown sheets are the original blank inspection aids. Final labels reside
in the companion JSON artifacts; all four pass finalized validation.

| Experiment | Finalized labels | Inspection sheet | Exact prompt |
| --- | --- | --- | --- |
| Baseline | [JSON](results/generation_baseline_v1_human_review.json) | [Markdown](results/generation_baseline_v1_human_review.md) | Saved in [raw baseline](results/generation_baseline_v1.json) |
| Strict v1 | [JSON](results/generation_strict_prompt_v1_human_review.json) | [Markdown](results/generation_strict_prompt_v1_human_review.md) | [Definition](prompts/grounded_strict_v1.json) |
| Balanced v2 | [JSON](results/generation_balanced_prompt_v2_human_review.json) | [Markdown](results/generation_balanced_prompt_v2_human_review.md) | [Definition](prompts/grounded_balanced_v2.json) |
| Strict v2 | [JSON](results/generation_strict_prompt_v2_human_review.json) | [Markdown](results/generation_strict_prompt_v2_human_review.md) | [Definition](prompts/grounded_strict_v2.json) |

Correctness, groundedness, completeness, refusal correctness, citation correctness,
and optional prompt compliance remain separate. N/A labels are excluded per
dimension. Strict v1 refusal correctness includes its false refusal on answerable
case 004 (3/4); the three expected refusal cases pass 3/3 for every prompt.

Offline validation and report tooling:

```sh
python -m unittest discover -s tests
python -m evaluation.generation_human_review validate evaluation/results/generation_strict_prompt_v2_human_review.json --finalized
```

`python -m evaluation.generation_prompt_comparison --final` creates the final
comparison only when both output paths are new; existing reports are protected
against overwrite. No API call, retrieval, or answer judging occurs.

## Baseline methodology

The frozen sidecar [`generation_reference_v1.json`](benchmarks/generation_reference_v1.json)
contains the 19 retrieval-v2 IDs, preserving the gap at 018. Cases 005, 019,
and 020 require refusal. Reference answers are synthesis examples, not exact-match
targets. The sidecar contains the approved manual rubric; no automated answer
quality scoring or LLM judge is implemented.

Correctness, groundedness, point completeness, refusal correctness, and citation
correctness remain separate. Optional prompt compliance is separate from refusal
correctness. All raw-result human evaluation fields start as `null`, meaning
unscored, rather than failed or not applicable.

## Controlled configuration

The runner reuses `evaluation.retrieval.retrieve(mode="hybrid", k=5,
candidate_k=10)`: Vector + BM25 + production RRF (`k=60`), returning the first
five chunks without document deduplication. The per-backend candidate depth
matches the Milestone 1 controlled evaluation. It calls the unchanged production
`build_answer_prompt()` with the fixed `unknown` route, selecting its generic
branch. No planner, API application, fallback, heuristic reranker, or MiniLM
reranker is invoked.

Generation uses the production Chat Completions parameters: `gpt-4o-mini`,
temperature `0`, and `max_tokens=800`. A direct SDK call preserves response model,
finish reason, usage, response ID, and system fingerprint; production `chat()`
discards these fields. Evaluation clients have a 60-second timeout and no
automatic retries. Embedding calls use the production `text-embedding-3-small`
model. These options affect this evaluation process only.

Temperature zero and the model alias do not guarantee identical future answers.
Exact prompt messages, the prompt function hash, request/response model IDs,
source order, runtime versions, and corpus/benchmark hashes are saved for audit.
Reference answers, required-point text, expected behavior, and rubric labels never
enter the generation prompt. Only the question and retrieved notes do.

## Evidence availability before generation

Each required point maps to v2 evidence groups. Availability is OR within a group
and AND across mapped groups, checked using document and chunk identity. This is
a pre-generation context check, not an answer-quality score. Case 003's explicit
IPC point narrows the group's acceptable alternatives to the two chunks that
actually mention IPC. Case 013 keeps rotation and the single-split rationale
separate. Refusal points have no factual evidence requirement and use `null`.

The frozen sidecar pins retrieval-v2 bytes and current Chroma texts. Preflight
validates evidence identities in both existing databases and checks the frozen
Chroma text hash. Corpus hashes before and after the run capture Chroma texts,
metadata, and stored Whoosh records. Existing cross-index inventory differences
are recorded; missing benchmark evidence is fatal. This runner neither creates
an index nor ingests corpus data.

## Tests and one-run execution

From the repository root, with the pinned backend requirements installed:

```powershell
.venv-generation/Scripts/python.exe -m unittest discover -s tests -p "test_generation_baseline.py" -v
.venv-generation/Scripts/python.exe -m evaluation.run_generation_baseline
```

The live run requires the existing `.chroma` collection, `data/whoosh_index`,
and `OPENAI_API_KEY` through the existing configuration. Output defaults to
[`results/generation_baseline_v1.json`](results/generation_baseline_v1.json).
An existing output prevents execution before credentials or network access.
There is no automatic retry or resume. Do not rerun the baseline to replace an
unfavorable answer or an API failure.

Each case is checkpointed before retrieval, before its generation request, and
after success/failure. Before-request checkpoints already contain evidence
availability and exact prompt messages. Failures retain stage, exception type,
HTTP status, and request ID without serializing credentials or request headers.
The summary reports completion counts, generation latency, token usage, and
insufficient-context IDs only. It does not score answer quality.
