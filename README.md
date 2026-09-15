<div align="center">

# Recall

### A retrieval-first study assistant grounded in your own course materials

Recall turns lecture notes into a searchable knowledge base and generates concise, source-backed explanations, revision guidance, and source recall answers.

[Architecture](#architecture) · [Features](#core-capabilities) · [Quick start](#quick-start) · [API](#api)

</div>

## Why Recall?

General-purpose chatbots can produce fluent answers without showing whether the information came from a student's actual course material. Recall takes a retrieval-first approach: it searches the uploaded knowledge base before generation and instructs the language model to answer only from the retrieved context.

The result is a study workflow designed to help students:

- understand concepts using their own notes;
- locate where a topic was taught;
- prepare for exams with intent-specific responses;
- inspect the passages supporting an answer.

## Core capabilities

| Capability | Implementation |
|---|---|
| Intent-aware responses | An LLM planner classifies questions as concept explanation, source recall, exam preparation, or fallback |
| Hybrid retrieval | OpenAI embeddings with ChromaDB vector search plus Whoosh BM25 keyword search |
| Rank fusion | Reciprocal Rank Fusion merges and deduplicates vector and keyword results |
| Reranking | A transparent lexical-overlap heuristic reorders fused candidates |
| Grounded generation | Route-specific prompts restrict answers to retrieved course material |
| Source attribution | Responses expose document IDs, passages, retrieval method, and ranking scores |
| Knowledge ingestion | Text is normalized, chunked with overlap, deduplicated, embedded, and indexed |
| Study interface | React and TypeScript UI for ingestion, questions, knowledge browsing, and study insights |

## Architecture

<p align="center">
  <img src="diagram.png" alt="Recall retrieval and answer pipeline" width="560">
</p>

A question passes through intent classification, vector and keyword retrieval, Reciprocal Rank Fusion, heuristic reranking, and grounded answer generation. The API returns the answer together with its supporting passages and a route-aware study hint.

> The current reranker is intentionally lightweight and interpretable. A learned cross-encoder and comparative retrieval benchmarks are planned improvements.

## Repository structure

```text
Recall/
├── app/
│   ├── api/             # FastAPI routes and request flow
│   ├── catalog/         # Document metadata catalog
│   ├── embeddings/      # OpenAI embedding client
│   ├── ingestion/       # Text chunking and overlap
│   ├── llm/             # Language-model client
│   ├── orchestration/   # Intent planner, prompts, and study hints
│   ├── rag/             # Retrieval, rank fusion, reranking, generation
│   ├── schemas/         # Pydantic API and retrieval models
│   └── vectordb/        # ChromaDB and Whoosh adapters
├── recall-frontend/     # React + TypeScript + Vite interface
├── data/                # Local document catalog
├── eval_cases.json      # Evaluation cases
└── run_eval.py          # API evaluation harness
```

## Technology

**Backend:** Python · FastAPI · Pydantic · OpenAI API  
**Retrieval:** ChromaDB · Whoosh BM25 · Reciprocal Rank Fusion  
**Frontend:** React · TypeScript · Vite · Tailwind CSS · Recharts  
**Local persistence:** ChromaDB collection · Whoosh index · JSON catalog

## Quick start

### Prerequisites

- Python 3.10+
- Node.js 18+
- An OpenAI API key

### 1. Clone and configure the backend

```bash
git clone https://github.com/nour0205/Recall.git
cd Recall

python -m venv .venv
```

Activate the environment:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install the dependencies and create your local environment file:

```bash
pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell, use `Copy-Item .env.example .env`. Then replace the placeholder in `.env` with your OpenAI API key.

### 2. Start the API

```bash
python -m uvicorn app.api.main:app --reload
```

- API: http://127.0.0.1:8000
- Interactive documentation: http://127.0.0.1:8000/docs

### 3. Start the frontend

In a second terminal:

```bash
cd recall-frontend
npm install
npm run dev
```

The interface runs at http://localhost:5173.

## API

### Ingest study material

```http
POST /ingest
Content-Type: application/json
```

```json
{
  "document_id": "machine-learning-week-3",
  "text": "Your lecture content...",
  "document_type": "lecture_note",
  "course": "Machine Learning",
  "topic_tags": ["overfitting", "regularization"]
}
```

### Ask a grounded question

```http
POST /ask
Content-Type: application/json
```

```json
{
  "question": "What is overfitting?",
  "document_id": "machine-learning-week-3"
}
```

The response contains:

```json
{
  "answer": "...",
  "route": "concept_explanation",
  "sources": [
    {
      "document_id": "machine-learning-week-3",
      "chunk_index": 0,
      "text": "...",
      "retrieval_type": "hybrid",
      "hybrid_score": 0.0325,
      "rerank_score": 3.0
    }
  ],
  "study_hint": "..."
}
```

Additional endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/documents` | List indexed documents |
| `POST` | `/debug/retrieve` | Inspect retrieved and ranked candidates |
| `POST` | `/debug/plan` | Inspect the planner output |

## Evaluation status

The repository includes an initial API evaluation harness and a small set of routing and source-attribution cases. This is an early baseline rather than a published benchmark.

The next evaluation milestone is a versioned dataset comparing vector-only, keyword-only, hybrid, and hybrid-plus-reranking configurations using retrieval metrics such as Recall@k and MRR. Results will be published only after they are reproducible.

## Current limitations

- Single-user local deployment
- Text input rather than native PDF/document parsing
- LLM-based intent classification adds latency and cost
- Heuristic rather than learned reranking
- No document update or deletion workflow
- Evaluation corpus is currently limited

## Roadmap

- [ ] Add automated unit and integration tests
- [ ] Add GitHub Actions CI
- [ ] Build a reproducible retrieval benchmark
- [ ] Add cross-encoder reranking
- [ ] Support PDF and DOCX ingestion
- [ ] Add document lifecycle operations
- [ ] Add streaming responses and multi-user isolation
- [ ] Package the stack with Docker Compose

## License

Released under the [MIT License](LICENSE).
