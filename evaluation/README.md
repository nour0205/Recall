# Retrieval evaluation

Milestone 1 evaluates retrieval, not generated answers. Start with the
[milestone report](MILESTONE_1_RETRIEVAL_EVALUATION.md) for conclusions and the
[benchmark annotation rules](benchmarks/README.md) for label semantics.

## Navigation

| File | Purpose |
|---|---|
| [benchmarks/retrieval_v1.json](benchmarks/retrieval_v1.json) | 19 cases with legacy canonical UUID labels |
| [benchmarks/retrieval_v2.json](benchmarks/retrieval_v2.json) | Same cases with acceptable evidence groups; 16 answerable, 3 unanswerable |
| [benchmark.py](benchmark.py) | Versioned schemas and supplied-inventory validation |
| [retrieval.py](retrieval.py) | Evaluation-only vector, BM25, hybrid, and heuristic modes |
| [metrics.py](metrics.py) / [evidence_metrics.py](evidence_metrics.py) | Pure canonical / evidence-group metrics |
| [run_retrieval_benchmark.py](run_retrieval_benchmark.py) | Four-mode canonical benchmark runner |
| [run_reranker_ablation.py](run_reranker_ablation.py) | Shared-pool heuristic ablation |
| [semantic_reranker.py](semantic_reranker.py) / [run_semantic_ablation.py](run_semantic_ablation.py) | Optional MiniLM scorer / three-way shared-pool experiment |
| [rescore_evidence.py](rescore_evidence.py) | Evidence rescoring of saved MiniLM experiment outputs |
| [validate_benchmark.py](validate_benchmark.py) | Schema validation, optionally persisted Chroma reference checks |
| [verify_saved_results.py](verify_saved_results.py) | Offline reproduction of historical per-query and aggregate evidence scores |

## No-key verification

Install the root core requirements and activate your environment first. All
commands below run from the repository root, require no model download or API
key, and do not generate answers:

```sh
python -m unittest discover -s tests
python -m evaluation.validate_benchmark
python -m evaluation.verify_saved_results
```

The validation command checks both schemas; it does not establish corpus
existence without `--corpus`. Saved-result verification checks the source and
v2 benchmark hashes and reproduces every query's scores and the aggregates.
It does not assert that today's corpus equals the historical corpus.

## Live corpus validation and retrieval runs

The following require the original persisted `.chroma` collection (`api-demo`)
and, for retrieval experiments, `data/whoosh_index/`. These local databases are
deliberately not versioned. Run from the repository root because index paths
are relative to the working directory.

```sh
python -m evaluation.validate_benchmark --corpus
```

This command checks Chroma chunk existence and document ownership without
retrieval or OpenAI calls. Historical corpus: 27 Chroma chunks across 12 documents;
Whoosh has 28 including one extra `ml` chunk. The mismatch is preserved and
reported, not silently repaired. The catalog is not a corpus inventory.

With those databases and a valid local `.env` for OpenAI embeddings:

```sh
python -m evaluation.run_retrieval_benchmark
python -m evaluation.run_reranker_ablation
```

These write new timestamped JSON results under `evaluation/results/`. The
four-mode runner uses canonical v1 labels. Ablations share the full RRF pool:
top 10 per backend, potentially up to 20 distinct chunks, then final top 5.
Live retrieval uses embedding API calls and can incur cost. Re-ingestion creates
new UUIDs, so newly ingested documents cannot reproduce the historical gold
labels without an explicit corpus/label migration. A fresh clone can inspect
and reproduce saved scores, but cannot rerun identical historical retrieval
without the matching databases. No corpus restore tool is supplied.

## Optional semantic reranking

Core requirements do not include PyTorch or Sentence Transformers. Only when
running MiniLM, install the separate pinned CPU dependencies into your activated
environment (or a separate environment with the core requirements):

```sh
python -m pip install -r evaluation/requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
python -m evaluation.run_semantic_ablation
```

The runtime pins Sentence Transformers 5.1.2, Transformers 4.57.1, and
PyTorch 2.9.0+cpu. The model is `cross-encoder/ms-marco-MiniLM-L6-v2`, revision
`233902d25c440f23af6f7d6e94d2946bac0bee0a`; CPU FP32, batch size 16, pair limit 512.
No score blending, thresholds, or production import path uses this scorer.

The first run downloads model weights. You may set `HF_HOME` to
`.eval-model-cache` to keep downloads in the ignored local cache. Loading and
warmup are separate from recorded query inference latency. Semantic unit tests
inject fake scorers and do not load/download the model.

## Evidence rescoring

```sh
python -m evaluation.rescore_evidence
```

This existing runner validates gold references against persisted Chroma and
writes a new timestamped JSON/Markdown report using saved rankings, without
retrieval or reranking. For a fresh clone without Chroma, use
`python -m evaluation.verify_saved_results` instead: it reproduces the saved
numbers without writing another historical artifact.

## Results index

Dates and filenames identify experiments, not interchangeable benchmark snapshots.

| Stage | Artifacts |
|---|---|
| Five-case pilot, before Whoosh fix | [JSON](results/retrieval_v1_20261003T191144327644Z.json) |
| Five-case pilot, after fix | [JSON](results/retrieval_v1_20261003T202351628580Z.json) |
| Final 19-case canonical run | [JSON](results/retrieval_v1_20261003T204707249551Z.json), [Markdown](results/retrieval_v1_20261003T204707249551Z.md) |
| Detailed ranking analysis | [JSON](results/retrieval_v1_20261003T204707249551Z_failure_analysis.json), [Markdown](results/retrieval_v1_20261003T204707249551Z_failure_analysis.md) |
| Heuristic shared-pool ablation | [JSON](results/reranker_ablation_20261003T210540073940Z.json), [Markdown](results/reranker_ablation_20261003T210540073940Z.md) |
| MiniLM shared-pool experiment | [JSON](results/semantic_ablation_20261004T092737920669Z.json), [Markdown](results/semantic_ablation_20261004T092737920669Z.md) |
| Final evidence-group rescoring | [JSON](results/evidence_rescore_20261004T100113793072Z.json), [Markdown](results/evidence_rescore_20261004T100113793072Z.md) |

Pilots used earlier labels; do not compare their recall directly to final v1.
Evidence rescoring uses v2 and saved final top-five outputs; alternatives are
accepted by explicit UUID membership, not semantic similarity. Quality summaries
exclude unanswerable cases; those outputs remain inspectable. No generation
evaluation has run. Root `eval_cases.json` and `run_eval.py` are legacy smoke
artifacts, not these benchmarks; the script targets removed `/ask_routed` and
should not be used as current reproduction guidance.
