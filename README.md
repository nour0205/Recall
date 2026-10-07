# Recall

Recall is an AI study assistant grounded in personal course material. It ingests study notes, retrieves relevant evidence using hybrid search, routes questions by learning intent, and generates grounded answers with source references.

**FastAPI ? React / TypeScript / Vite ? OpenAI ? ChromaDB ? Whoosh BM25 ? RRF**

## What Recall does

- **Build a study library:** ingest pasted course notes, split them into overlapping chunks, and index them with document IDs, chunk IDs, and course metadata.
- **Search meaning and terminology:** combine Chroma vector retrieval with Whoosh BM25 using Reciprocal Rank Fusion (RRF).
- **Adapt to learning intent:** a planner selects concept explanation, source recall, exam preparation, or a general answer route.
- **Generate source-backed study answers:** route-specific prompts request explanations, revision priorities, and citations; responses include source passages and study hints.
- **Provide a React interface:** add notes, ask questions, inspect source references, and browse/search document previews.
- **Measure retrieval quality:** versioned benchmarks, deterministic metrics, shared-pool reranker ablations, and saved experiment reports.

Prompts request grounded answers and “I don't know.” when evidence is insufficient. Milestone 2 evaluates generation and refusal quality in a controlled benchmark; prompt variants remain evaluation-only.

## Architecture

```mermaid
flowchart TD
    Material["Course material: pasted text"] --> Chunks["Chunking + metadata"]
    Chunks --> Dense["Chroma vector index"]
    Chunks --> Sparse["Whoosh BM25 index"]
    Question["User question"] --> Planner["Intent planner"]
    Planner --> Vector["Vector retrieval: OpenAI embeddings"]
    Planner --> BM25["BM25 retrieval"]
    Dense --> Vector
    Sparse --> BM25
    Vector --> RRF["Reciprocal Rank Fusion"]
    BM25 --> RRF
    RRF --> Context["Grounded context"]
    Context --> Prompt["Route-specific prompt"]
    Planner --> Prompt
    Prompt --> LLM["GPT-4o-mini"]
    LLM --> Answer["Answer + sources + study guidance"]
```

Routes select prompt style, not different retrievers. Routed `/ask` uses the first three hybrid retrieval results; fallback generation retains the lexical heuristic reranker. MiniLM remains evaluation-only.

## Why Recall is more than a basic RAG chatbot

Dense + sparse retrieval finds evidence; intent-aware orchestration adapts answer structure to the study task. Grounded generation connects answers to passages, and empirical evaluation tests whether retrieval complexity helps.

## Retrieval Evaluation ? Milestone 1

**19 manually curated questions: 16 answerable, 3 unanswerable.** Experiments compare vector, BM25, hybrid/RRF, heuristic, and MiniLM CrossEncoder reranking. Evidence groups accept equivalent chunks; complete coverage requires all answer components.

Evidence scores compare orderings of the **same hybrid pool**, averaged over 16 answerable cases:

| Ordering | Evidence MRR | Complete coverage@3 |
|---|---:|---:|
| Hybrid / RRF | **0.96875** | 0.93750 |
| MiniLM CrossEncoder | 0.95833 | **1.00000** |
| Heuristic reranker | 0.93750 | 0.93750 |

Among the evaluated hybrid orderings, plain Vector + BM25 + RRF remains the preferred evaluation baseline because it offers the best current quality / simplicity / latency trade-off on this benchmark. The earlier canonical four-mode benchmark favored vector-only, so no universal superiority claim is made.

## Key engineering findings

- **Evaluation exposed a BM25 natural-language parsing bug:** free-text questions were interpreted as query syntax. The fix analyzes input and searches literal terms.
- **Heuristic reranking degraded ranking quality:** canonical-rank ablation found 0 improved, 10 unchanged, and 6 worsened answerable cases.
- **MiniLM performed better than the heuristic**, but did not clearly outperform plain RRF and added about **0.65 s CPU reranking latency** per query in the experiment. It remains evaluation-only.
- **Evidence groups corrected exact-UUID scoring artifacts:** overlapping chunks can contain equivalent evidence, so requiring one arbitrary UUID can misrepresent retrieval quality.

## Milestone 2 — Generation Quality & Groundedness

**19 frozen questions: 16 answerable and 3 deliberate refusal cases.** Four prompt variants used the same retrieved contexts, source mappings, GPT-4o-mini, temperature 0, and generation settings. Human reviewers used a fixed rubric for correctness, groundedness, completeness, refusal correctness, and citation correctness. No LLM judge or RAGAS was used for the final labels.

### Prompt comparison

| Prompt | Groundedness | Mean completeness | Citation correctness | Unsupported elaboration |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 5/19 · 26.32% | 16/16 · 100% | 3/17 · 17.65% | 14/19 |
| Strict v1 | 19/19 · 100% | 13.5/16 · 84.375% | 15/15 · 100% | 0/19 |
| Balanced v2 | 15/19 · 78.95% | 15.5/16 · 96.875% | 12/16 · 75% | 4/19 |
| Strict v2 | 18/19 · 94.74% | 14.5/16 · 90.625% | 15/16 · 93.75% | 1/19 |

Mean completeness averages required-point coverage over the 16 answerable cases. Citation correctness excludes each prompt's human-labeled N/A cases; full denominators and failures are in the report.

The baseline covered every required point but frequently continued beyond the supplied evidence. Strict v1 eliminated unsupported elaboration and raised groundedness from 26.3% to 100%, while reducing completeness. Later controlled ablations exposed a measurable grounding–completeness trade-off: Strict v2 fixed the false refusal and improved completeness, but retained one unsupported-elaboration case and three incomplete answers. These findings apply to this 19-case evaluation set; no statistical significance or universally best prompt is claimed.

### Before / after: grounded generation

**Question:** What happens if the learning rate is too large during gradient descent?

**Baseline excerpt:**
> A **learning rate** that is too large results in overshooting the optimal parameter values, leading to instability in the training process [S1].

**Strict v1 answer:**
> A learning rate that is too large may cause divergence [S1].

**Why the baseline failed:** The supplied notes support possible divergence, but not the added overshooting, erratic-update, or tuning claims. A citation alone does not establish source support.

### Evaluation methodology

```text
Frozen question → Frozen top-5 retrieved chunks → Prompt variant
              → GPT-4o-mini → Human review against fixed rubric
```

**Only the prompt changed between ablations.** Hybrid Vector + BM25 + RRF contexts were frozen from the baseline; retrieval was not rerun. References and required-point metadata never entered the generation prompt. Production prompts remain unchanged.

[Milestone 2 report](evaluation/MILESTONE_2_GENERATION_EVALUATION.md) · [Final four-way comparison](evaluation/results/generation_prompt_ablation_comparison_final.md) · [Frozen benchmark and references](evaluation/benchmarks/generation_reference_v1.json) · [Human-review artifacts](evaluation/MILESTONE_2_GENERATION_EVALUATION.md#finalized-human-reviews)

## Screenshots / demo

*Product screenshots and a short demo will be added here.* The current interface includes note ingestion, question answering with source inspection, and a searchable library.

## Tech stack

| Area | Technologies |
|---|---|
| Backend | Python, FastAPI, Pydantic |
| Retrieval / AI | OpenAI `text-embedding-3-small`, ChromaDB, Whoosh BM25, RRF, GPT-4o-mini |
| Frontend | React, TypeScript, Vite, Tailwind CSS, Framer Motion |
| Evaluation | Standard-library unittest, JSON benchmarks, deterministic metrics; optional sentence-transformers / Transformers / PyTorch |

## Run locally

Python 3.12 / Node.js 22. Run backend commands from the repository root. Ingestion and questions require an OpenAI API key and incur usage costs.

```sh
python -m venv .venv
```

Activate with `.venv\Scripts\Activate.ps1` on PowerShell, or `source .venv/bin/activate` on macOS/Linux. Then:

```sh
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and replace the placeholder locally. Start the API:

```sh
python -m uvicorn app.api.main:app --reload
```

API: `http://127.0.0.1:8000` ? interactive docs: `http://127.0.0.1:8000/docs`

In a second terminal:

```sh
cd recall-frontend
npm ci
npm run dev
```

Open Vite's URL (normally `http://localhost:5173`). Ingest **text**, not PDFs. Endpoints: `POST /ask`, `POST /ingest`, `GET /documents`. This is a local development project without authentication or deployment configuration.

## Evaluation / reproducibility

Tests and saved-result verification require no API calls or model downloads:

```sh
python -m unittest discover -s tests
python -m evaluation.validate_benchmark
python -m evaluation.verify_saved_results
```

- [Milestone 1 methodology and results](evaluation/MILESTONE_1_RETRIEVAL_EVALUATION.md)
- [Evaluation commands, setup, and saved artifacts](evaluation/README.md)

Semantic reranking dependencies are optional and separate from core requirements; see [optional semantic setup](evaluation/README.md#optional-semantic-reranking).

Saved scores reproduce offline; identical live reruns require historical local indexes, which are not versioned. Re-ingestion changes UUIDs. Scope: 27 Chroma chunks / 12 documents; Whoosh has one extra chunk and the catalog is stale. Latency is experimental, not a production benchmark.

## Repository structure

| Path | Purpose |
|---|---|
| `app/` | Ingestion, retrieval, intent planning, generation, and API |
| `recall-frontend/` | React application and frontend lockfile |
| `evaluation/` | Benchmarks v1/v2, metrics, experiments, and saved results |
| `tests/` | Unit tests; semantic scorers are mocked |
| `docs/milestone1/` | Traceable public results and presentation sources |

## Roadmap

- **Milestone 1 ? Retrieval evaluation:** complete.
- **Milestone 2 — Generation quality & groundedness evaluation:** complete; four controlled prompt experiments with finalized human review. Production prompt adoption remains separate.
