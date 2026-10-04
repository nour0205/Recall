<div align="center">

A personal study assistant using **Retrieval-Augmented Generation over course materials**.
Recall indexes pasted course notes, retrieves supporting passages, and generates
study answers with source citations. An intent-routing layer adapts the prompt
for concept explanations, source recall, and exam preparation.

**Backend:** FastAPI · OpenAI `text-embedding-3-small` · ChromaDB · Whoosh BM25 ·
Reciprocal Rank Fusion · GPT-4o-mini

**Frontend:** React · TypeScript · Vite · Tailwind CSS

## Architecture and scope

```text
Course text -> overlapping chunks -> Chroma + Whoosh indexes
Question -> intent routing -> vector + BM25 -> RRF -> context -> GPT-4o-mini
                                                        -> answer, sources, study hint
```

The app supports text ingestion, questions, and document browsing.
Prompts instruct the model to use supplied notes and abstain when
evidence is insufficient; answer quality and refusal reliability have not yet
been evaluated.

Routed `/ask` uses the first three hybrid retrieval results. The fallback generation
path retains the existing **lexical heuristic** reranker. Evaluation decisions
in `evaluation/` have not been applied to those paths; MiniLM is evaluation-only.

## RAG Evaluation — Milestone 1

A manually curated **19-question benchmark** (16 answerable, 3 unanswerable)
compares vector retrieval, BM25, hybrid/RRF, heuristic reranking, and semantic
CrossEncoder reranking. Shared-pool ablations isolate reranking; latency and
quality are reported separately. Evidence groups accept equivalent overlapping
chunks while requiring all answer components for complete coverage.

Final evidence scores below compare the three orderings of the same hybrid pool;
quality averages include the 16 answerable cases only.

| Ordering | Evidence MRR | Complete evidence coverage@3 |
|---|---:|---:|
| Hybrid / RRF | **0.96875** | 0.93750 |
| MiniLM CrossEncoder | 0.95833 | **1.00000** |
| Heuristic reranker | 0.93750 | 0.93750 |

Among the evaluated hybrid orderings, plain Vector + BM25 + RRF is currently
retained as the preferred baseline because it offers the best quality / simplicity /
latency trade-off on this benchmark.

The earlier canonical four-mode benchmark favored vector-only. Evidence-group
rescoring compared the hybrid orderings; neither comparison establishes universal
superiority.

The initial heuristic reranker was rejected as the preferred baseline after
ablation showed degraded ranking quality. MiniLM was evaluated experimentally
and not selected for production: its measured coverage gain did not justify
approximately **0.65 s of CPU reranking latency** per query on this benchmark.
The corpus is small (27 Chroma chunks across 12 documents), and Whoosh contains
one additional chunk.

[Full methodology and results](evaluation/MILESTONE_1_RETRIEVAL_EVALUATION.md) ·
[Evaluation commands and saved artifacts](evaluation/README.md)

## Run locally

Tested with Python 3.12 and Node.js 22. Run backend commands from the repository
root. OpenAI-backed ingestion and questions require your own API key and incur
API usage; tests and saved-result verification do not.

```sh
python -m venv .venv
```

Activate with `.venv\Scripts\Activate.ps1` on PowerShell, or
`source .venv/bin/activate` on macOS/Linux. Then:

```sh
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and replace the placeholder locally. Start the API:

```sh
python -m uvicorn app.api.main:app --reload
```

API: `http://127.0.0.1:8000` · interactive docs: `http://127.0.0.1:8000/docs`

In a second terminal:

```sh
cd recall-frontend
npm ci
npm run dev
```

Open the URL printed by Vite (normally `http://localhost:5173`). Ingest **text**
through the app or `POST /ingest`; PDF parsing is not implemented. Main endpoints
are `POST /ask`, `POST /ingest`, and `GET /documents`.
The app is a local development project,
without authentication or a production deployment configuration.

## Verify without API calls

```sh
python -m unittest discover -s tests
python -m evaluation.validate_benchmark
python -m evaluation.verify_saved_results
```

Semantic model dependencies are **optional** and separate from core requirements.
See [evaluation setup](evaluation/README.md#optional-semantic-reranking) before
running a model experiment.

## Repository guide

| Path | Purpose |
|---|---|
| `app/` | Backend, ingestion, retrieval, routing, and generation |
| `recall-frontend/` | React application source and frontend lockfile |
| `evaluation/benchmarks/` | Versioned manual retrieval labels and annotation rules |
| `evaluation/results/` | Retained experiment outputs and failure analyses |
| `tests/` | Standard-library unit tests; semantic scorers are mocked |
| `docs/milestone1/` | Traceable results and source material for public presentation |

Historical databases and model caches are not versioned. Saved evidence metrics
can be reproduced offline; live retrieval reruns require the matching persisted
corpus and indexes. Re-ingestion changes UUIDs. The document catalog is stale
relative to the experimental corpus; it is not benchmark ground truth.
