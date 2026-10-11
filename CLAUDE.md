# Recall: context for Claude

Recall is a study assistant: students ingest their own lecture notes and ask questions; answers come only from those notes, with `[S#]` citations, or exactly `I don't know.`. The owner (Nour) is preparing it as a portfolio project for AI / RAG / agentic-AI internships in France, so changes should be explainable in an interview and backed by measurement where possible.

## Commands (run from the repository root)

```sh
python -m unittest discover -s tests          # offline, no API key needed
python -m evaluation.validate_benchmark        # benchmark schema checks
python -m evaluation.verify_saved_results      # recompute saved Milestone 1 scores
uvicorn app.api.main:app --reload              # backend on :8000 (needs OPENAI_API_KEY in .env)
cd recall-frontend && npm ci && npm run dev    # frontend on :5173
docker compose up --build                      # both, with persistent volumes
```

CI (`.github/workflows/ci.yml`) runs the three Python checks, the frontend `tsc` and build, and both Docker image builds on every PR.

## Architecture

- `app/api/main.py`: FastAPI. `POST /ingest`, `POST /ask`, `GET /documents`, `/debug/*`.
- Ingest: SHA-256 dedupe → `ingestion/chunker.py` (sentence-packed chunks ≤500 chars, each prefixed with the whole previous chunk) → `embeddings/embedder.py` (OpenAI `text-embedding-3-small`) → the same chunk UUID is written to Chroma (`.chroma`, collection `api-demo`), Whoosh BM25 (`data/whoosh_index`) and `data/document_catalog.json`.
- Ask:
  1. `orchestration/planner.py`: gpt-4o-mini classifies the intent (`concept_explanation | source_recall | exam_preparation | unknown`) and may pick document targets from `orchestration/registry.py`. An explicit `document_id`/`document_ids` in the request wins.
  2. `rag/hybrid_retriever.py`: 10 dense + 10 BM25 candidates, Reciprocal Rank Fusion (k=60), top 5 in order.
  3. `orchestration/prompts.py`: Strict v2 grounded prompt, the same for every route. Sources are rendered as `[S1] DOCUMENT: … CONTENT: …`.
  4. gpt-4o-mini, temperature 0, max_tokens 800 (`llm/client.py`, `config.py`).
  5. `normalize_answer()` turns a leading refusal into exactly `I don't know.`. Refusals return no sources and never trigger the fallback; only a generation error falls back to `rag/pipeline.py`.
  6. `orchestration/utils.py` adds a rule-based study hint.
- `recall-frontend/`: React + Vite + Tailwind; pages Landing, Ingest, Knowledge, Ask; backend URL `http://127.0.0.1:8000`.
- MiniLM cross-encoder and the lexical heuristic reranker exist for experiments only; neither is on the production path.

## Evaluation (in `evaluation/`; see the milestone reports there)

- Benchmark: 19 hand-written questions over 12 short ML, OS and database notes (16 answerable, 3 out of scope). v1 has canonical gold chunks; v2 adds evidence groups (OR within a group, AND across groups), because chunk overlap duplicates evidence.
- Milestone 1 (retrieval): Hit@K, Recall@K, MRR and evidence coverage. Vector MRR 0.854, BM25 0.815, hybrid 0.802, hybrid + heuristic reranker 0.693 on canonical labels. Evidence rescoring covered only hybrid and the rerankers (hybrid 0.969). Decision: plain hybrid/RRF; the heuristic reranker is rejected; MiniLM is not worth its latency yet.
- Milestone 2 (generation): retrieval frozen, 4 prompts, manual labels for correctness, groundedness, completeness, refusal, citations and prompt compliance. Baseline grounded 5/19; Strict v1 19/19 but under-answers; Strict v2 grounded 18/19 with completeness 14.5/16. Strict v2 is now in production (`docs/milestone2/production_promotion.md`).

## Rules for changes

- Never edit files under `evaluation/benchmarks/`, `evaluation/results/` or `evaluation/prompts/`. Their bytes are pinned by SHA-256 hashes, and `.gitattributes` marks them `-text` (`grounded_strict_v2.json` is intentionally CRLF). New experiments write new files.
- `app/config.py` raises without `OPENAI_API_KEY`. Tests that import app modules must stub the embedder or set a placeholder key; tests never call OpenAI.
- `recall-frontend/dist/` is tracked historical build output; don't commit rebuilt `dist` files with unrelated changes.
- The local `.chroma` and Whoosh stores aren't versioned. Re-ingesting creates new UUIDs, which no longer match the gold labels.
- Report results honestly: small benchmark, no significance claims, and say when a comparison wasn't run.

## Known weaknesses (priorities for improvement)

1. Full-chunk overlap makes top-5 contexts contain near-duplicate text. Consider sentence-level overlap and near-duplicate removal before the prompt, and measure it against the benchmark.
2. The planner adds an LLM call but barely changes behaviour: all routes share one prompt, the hints are hard-coded for two topics, and the registry lists Postgres/SQL Server/MongoDB docs that aren't in the corpus. Make it matter or remove it.
3. Strict v2 answers are very short (~22 words), which clashes with a study-assistant product. Idea: a cited strict answer first, plus a grounded "explain more".
4. Chroma and Whoosh are written separately with no rollback, and have already drifted (27 vs 28 chunks).
5. Not yet evaluated: chunking, planner intent accuracy, the full `/ask` path end to end. Hybrid vs vector-only was never compared on the evidence-group labels.
6. Ingestion is paste-text only (no PDF); no auth or deployment; OpenAI-only.

## Roadmap (agreed order)

1. Done: CI, Docker, portable tests, Strict v2 in production.
2. Frontend redesign: one main Ask screen with clickable `[S#]` citations and a source panel that highlights the chunk; a document library with upload; remove the fake landing-page charts (`lib/constants.ts`); shadcn/ui on the existing React/Vite/Tailwind stack.
3. README rewritten as a case study: pitch + GIF, problem, architecture diagram, key results, what was learned, quickstart, limitations.
4. End-to-end evaluation of `/ask` with an LLM judge calibrated against the existing human labels (report agreement per dimension); a larger benchmark.
5. PDF ingestion with page-level citations, structure-aware chunking, French-language support.
6. A tool-using agent (search notes, read document, quiz/flashcards, multi-part question decomposition), evaluated against plain RAG; optionally an MCP server.
7. Production signals: tracing (e.g. Langfuse), an OpenAI/Mistral provider switch, a live demo.
