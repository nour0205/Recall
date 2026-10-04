# Hero

Recall
RAG Retrieval Evaluation

19 benchmark questions
16 answerable · 3 unanswerable

Evidence MRR
Hybrid / RRF: 0.969
MiniLM: 0.958
Heuristic: 0.938

Preferred evaluation baseline: Vector + BM25 + RRF
Footer: Current-corpus pilot · 16 answerable cases scored

# Ablation

Heuristic reranker ablation
0 improved · 10 unchanged · 6 worsened
Canonical MRR: 0.802 → 0.693
Footer: Earliest canonical rank · same full hybrid pool · 16 cases

# Architecture

Question → Vector (OpenAI + Chroma) and BM25 (Whoosh) → RRF → Context → GPT-4o-mini
Dashed side branches: heuristic and MiniLM, evaluated experiments
Footer: Evaluation decision · application paths unchanged

Source numbers and caveats: [results_summary.md](results_summary.md).
