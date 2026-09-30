<div align="center">

🧠 Recall
A grounded AI study assistant built on retrieval-augmented generation
Recall helps students understand, revise, and retrieve knowledge from their own learning materials.
It combines hybrid retrieval, LLM reasoning, and source attribution to generate answers that remain connected to the original documents.

Architecture •
Features •
Evaluation •
Quick Start
</div>

📚 Why Recall?
Students rarely struggle because information is unavailable.
They struggle because information is scattered across:
- lecture notes
- course documents
- revision material
- personal summaries
General-purpose chatbots can generate fluent answers, but they cannot guarantee that answers come from the student's own learning material.
Recall follows a retrieval-first approach:
1. Retrieve relevant knowledge from user documents
2. Generate answers grounded in retrieved evidence
3. Expose the sources supporting each response
The goal: make AI-assisted learning more reliable, transparent, and verifiable.

✨ Core Capabilities
Capability	Description
🎯 Intent-aware responses	Routes questions based on learning objectives such as explanation, source retrieval, and exam preparation
🔎 Hybrid retrieval	Combines semantic vector search with BM25 keyword retrieval
🔗 Source attribution	Shows the passages and documents supporting generated answers
🧠 Grounded generation	Restricts responses to retrieved course material
📚 Knowledge ingestion	Normalizes, chunks, embeds, and indexes learning material
📊 Retrieval debugging	Provides visibility into retrieval and ranking decisions
📝 Study assistance	Generates explanations, revision guidance, and learning hints


🏗 Architecture
<p align="center">
<img src="diagram.png" width="650">
</p>

Recall follows a retrieval-first RAG pipeline:
User Question
      |
      v
Intent Classification
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
The system separates retrieval from generation to improve transparency and reduce unsupported responses.
🔍 Retrieval Pipeline
1. Intent Routing
The system identifies the user's objective:
- concept explanation
- source recall
- exam preparation
2. Hybrid Retrieval
Recall combines:
- semantic retrieval through embeddings
- keyword retrieval through BM25
Combining both improves retrieval robustness across different question types.
3. Ranking
Retrieved candidates are merged using Reciprocal Rank Fusion and refined before generation.
4. Grounded Generation
The LLM generates responses using retrieved evidence and returns source attribution.
💡 Design Decisions
Why hybrid retrieval?
Vector search captures semantic meaning, while keyword retrieval preserves exact terminology from technical documents.
Why source attribution?
Generated answers need verification. Recall exposes the evidence behind responses.
Why intent-aware responses?
Different learning tasks require different answer strategies:
Intent	Response
Concept explanation	Educational explanation
Source recall	Locate relevant passages
Exam preparation	Structured revision guidance


📈 Evaluation
Recall includes an evaluation harness covering:
Component	Status
Intent routing	Implemented
Source attribution	Implemented
Retrieval inspection	Implemented
API evaluation workflow	Implemented


Future benchmarking will compare:
- vector retrieval
- BM25 retrieval
- hybrid retrieval
- improved reranking strategies
🧩 Repository Structure
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
🛠 Technology Stack
AI / Retrieval
- LLM API
- Embeddings
- ChromaDB
- Whoosh BM25
- Reciprocal Rank Fusion
Backend
- Python
- FastAPI
- Pydantic
Frontend
- React
- TypeScript
- Vite
- Tailwind CSS
🚀 Quick Start
git clone https://github.com/nour0205/Recall.git
cd Recall
python -m venv .venv
pip install -r requirements.txt
Configure environment variables and run the backend:
python -m uvicorn app.api.main:app --reload
Run the frontend:
cd recall-frontend
npm install
npm run dev
🚧 Limitations & Roadmap
Current limitations
- Single-user local deployment
- Text-based ingestion
- Limited evaluation corpus
Roadmap
Retrieval quality
- [ ] Retrieval benchmark
- [ ] Improved reranking
- [ ] Automated evaluation pipeline
User experience
- [ ] PDF/DOCX ingestion
- [ ] Streaming responses
Engineering
- [ ] Docker deployment
- [ ] CI/CD pipeline
