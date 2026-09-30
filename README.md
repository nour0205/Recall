<div align="center">

# 🧠 Recall

### A grounded AI study assistant built on Retrieval-Augmented Generation

Recall helps students understand, revise, and retrieve knowledge from their own learning materials.

By combining **hybrid retrieval**, **LLM reasoning**, and **source attribution**, Recall generates answers that remain connected to the original documents.

<br/>

**Architecture** · **Features** · **Evaluation** · **Quick Start**

</div>

---

## 📚 Why Recall?

Students rarely struggle because information is unavailable.

They struggle because knowledge is scattered across:

- lecture notes
- course documents
- revision material
- personal summaries

General-purpose chatbots can generate fluent answers, but they cannot guarantee that answers come from the student's own learning material.

Recall follows a **retrieval-first approach**:

1. Retrieve relevant knowledge from user documents
2. Generate answers grounded in retrieved evidence
3. Expose the sources supporting each response

> Make AI-assisted learning more reliable, transparent, and verifiable.

---

## ✨ Core Capabilities

| Capability | Description |
|---|---|
| 🎯 Intent-aware responses | Adapts answers based on learning objectives such as explanation, source retrieval, and revision planning |
| 🔎 Hybrid retrieval | Combines semantic vector retrieval with BM25 keyword search |
| 🔗 Source attribution | Links generated answers back to supporting documents |
| 🧠 Grounded generation | Uses retrieved evidence to reduce unsupported responses |
| 📚 Knowledge ingestion | Processes and indexes learning materials |
| 📊 Retrieval debugging | Provides visibility into retrieval decisions |

---

## 🏗 Architecture

<p align="center">
<img src="diagram.png" width="700" alt="Recall architecture">
</p>

Recall follows a retrieval-first RAG pipeline:

```
User Question
      |
      v
Intent Routing
      |
      v
+----------------------+
|   Hybrid Retrieval   |
|                      |
| Vector Search        |
| BM25 Keyword Search  |
+----------------------+
      |
      v
Reciprocal Rank Fusion
      |
      v
Reranking
      |
      v
Grounded LLM Generation
      |
      v
Answer + Source Attribution
```

The architecture separates retrieval from generation to improve transparency and reliability.

---

## 🔍 Retrieval Pipeline

### 1. Intent Routing

Recall identifies the user's objective:

- concept explanation
- source retrieval
- exam preparation

### 2. Hybrid Retrieval

Recall combines two complementary retrieval strategies:

- **Semantic retrieval** using embeddings
- **Keyword retrieval** using BM25

This improves robustness across conceptual questions and terminology-heavy queries.

### 3. Ranking

Retrieved candidates are merged using Reciprocal Rank Fusion and refined before generation.

### 4. Grounded Generation

The LLM generates responses from retrieved evidence while preserving source references.

---

## 💡 Design Decisions

### Why hybrid retrieval?

Semantic search captures meaning, while keyword retrieval preserves exact technical terms. Combining both provides a stronger retrieval foundation.

### Why source attribution?

Generated answers need verification. Recall exposes the evidence behind responses instead of producing unsupported outputs.

### Why intent-aware responses?

Different learning tasks require different response strategies:

| Intent | Response |
|---|---|
| Concept explanation | Educational explanation |
| Source retrieval | Locate relevant passages |
| Exam preparation | Structured revision guidance |

---

## 📈 Evaluation

Recall includes an evaluation workflow covering:

| Component | Status |
|---|---|
| Intent routing | Implemented |
| Source attribution | Implemented |
| Retrieval inspection | Implemented |
| API evaluation workflow | Implemented |

Future benchmarking will compare retrieval strategies using metrics such as Recall@k, MRR, source relevance, and answer faithfulness.

---

## 🧩 Repository Structure

```
Recall/
├── app/
│   ├── api/
│   ├── ingestion/
│   ├── orchestration/
│   ├── rag/
│   ├── schemas/
│   └── vectordb/
├── recall-frontend/
├── data/
└── run_eval.py
```

---

## 🛠 Technology Stack

**AI / Retrieval**

- LLM API
- Embeddings
- ChromaDB
- Whoosh BM25
- Reciprocal Rank Fusion

**Backend**

- Python
- FastAPI
- Pydantic

**Frontend**

- React
- TypeScript
- Vite
- Tailwind CSS

---

## 🚀 Quick Start

```bash
git clone https://github.com/nour0205/Recall.git
cd Recall
python -m venv .venv
pip install -r requirements.txt
```

Configure environment variables and start the backend:

```bash
python -m uvicorn app.api.main:app --reload
```

Run the frontend:

```bash
cd recall-frontend
npm install
npm run dev
```

---

## 🚧 Limitations & Roadmap

### Current limitations

- Single-user local deployment
- Text-based ingestion
- Limited evaluation corpus

### Roadmap

**Retrieval quality**

- [ ] Retrieval benchmark
- [ ] Improved reranking
- [ ] Automated evaluation pipeline

**User experience**

- [ ] PDF/DOCX ingestion
- [ ] Streaming responses

**Engineering**

- [ ] Docker deployment
- [ ] CI/CD pipeline

---

## 🌱 Motivation

Recall started from a simple observation:

> The problem was not forgetting concepts. It was forgetting where you learned them.

The project explores how retrieval-based AI systems can make generated answers more useful, transparent, and trustworthy.
