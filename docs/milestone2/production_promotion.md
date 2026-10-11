# Milestone 2.5 — Production promotion

Plain Vector + BM25 + RRF is the production hybrid path. Strict v2 is the
preferred practical generation trade-off on the controlled 19-case benchmark;
neither decision implies universal superiority. Evaluation artifacts remain
unchanged. No evaluation rerun, new prompt variant, judge, or RAGAS was introduced.

## Inspection before integration

The committed `/ask` endpoint called `plan_question`, then `hybrid_retrieve`
with five candidates per backend, and supplied the first three fused chunks to
`build_answer_prompt`. Request `document_id` and `owner` scoped retrieval, but
planner `targets` and request `document_ids` were ignored. The local API edit
instead deduplicated the five chunks by document. Both behaviors could omit
complementary evidence.

Main retrieval already used dense embeddings, Whoosh BM25, and RRF (`k=60`).
Main generation used route-specific study-brief formatting, citations, and
context-only/refusal instructions, but also required supporting sections and
review tips. The local prompt edit strengthened citations while retaining those
expansion requirements. Neither prompt enforced the validated strict behavior.

A refusal, empty answer, or generation exception triggered the generic fallback.
That path retrieved candidates, applied the lexical heuristic reranker, and
used a separate `[1]` citation prompt. The document retrieval helper also
reranked. MiniLM had no production entry point.

## Production path after integration

```text
/ask → intent planner → request/planner document scope
     → dense candidates (10) + BM25 candidates (10) → RRF → top 5 chunks
     → production Strict v2 prompt with ordered [S#] sources → GPT-4o-mini
     → answer, route, sources, study_hint
```

Explicit `document_id` takes precedence over `document_ids`, which take precedence
over validated planner registry targets. Owner scope combines with the document
filter using Chroma-compatible AND/IN clauses; BM25 uses the same predicates.
The existing BM25 post-search filtering architecture is retained. New ingestion
now writes owner/source metadata to both indexes; historical indexes are not
rebuilt or backfilled.

The top five RRF chunks are retained in order, including multiple chunks from
one document. Blank chunks are excluded before both prompt and source assembly.
The `hybrid_retrieve` function retains its existing default candidate behavior
for legacy callers; `/ask` and generic RAG helpers explicitly select ten
candidates per backend. Heuristic code is retained for experiments but removed
from default generation and document-helper paths. MiniLM stays evaluation-only.

`app/orchestration/prompts.py` owns the copied Strict v2 system text and user
template. Runtime does not import or read evaluation artifacts. All routes share
these grounding rules rather than forcing extra study-brief sections. Planner
classification, validation, and route values remain intact; wiring previously
ignored document targets fixes the concrete scoping bug.

Model settings remain GPT-4o-mini, temperature 0, max_tokens 800. No supported
answer is rewritten. Empty context returns exactly `I don't know.` without a
generation call. An explicit leading refusal is normalized to that sentence and
any trailing content is removed. Refusals return no sources or study hint and
never trigger fallback. Generation exceptions retain the existing generic RAG
fallback, now with plain hybrid/RRF retrieval and the same strict prompt.

The response schema remains `answer`, `route`, `sources`, `study_hint`; source
items retain their existing fields. Source order matches prompt labels. This
promotion does not add a semantic citation verifier or automatic quality judge.

## Tests and remaining differences

Offline production tests exercise the actual FastAPI endpoint with stubbed
planner, model, and index infrastructure; they also test real fusion and scope
predicates. They check top-five chunk order, shared-document evidence, source
labels/schema, exact refusal termination, every route, supported multi-part
response preservation, fallback, planner scope, and ingestion metadata.
Prompt tests check critical rules without brittle whole-prompt equality.

These tests validate orchestration contracts, not a model's factual decisions.
The promoted prompt still has the measured Strict v2 failures: incomplete
answers on 008/010/012 and unsupported elaboration on 013. Its recorded
groundedness was 18/19, mean completeness 14.5/16, citation correctness 15/16,
and expected refusals 3/3; these are isolated evaluation results, not measured
production scores.

Production retains a live planner, live retrieval, optional document/owner scope,
SDK defaults/retries, exception fallback, and a separate deterministic study-hint
field. The benchmark bypassed those layers and froze context. Planner registry
and historical owner metadata may limit scoped recall; BM25 filters after its
candidate limit. Study hints are unchanged and were not included in generation
quality scoring. Source citations are prompt-enforced, not semantically verified.
Temperature zero/model aliases do not guarantee identical future responses.

No live smoke call or full benchmark rerun was needed. Regression tests consume
no model tokens and do not touch corpus databases. Milestone 2.5 completes
integration; production end-to-end re-evaluation remains future work.
