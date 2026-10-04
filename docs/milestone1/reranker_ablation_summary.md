# Heuristic Reranker Ablation

16 answerable benchmark queries, using the same shared hybrid/RRF candidate pool before and after reranking.

| Rank outcome | Queries |
| --- | ---: |
| Improved | 0 |
| Unchanged | 10 |
| Worsened | 6 |

| Ordering | MRR |
| --- | ---: |
| Hybrid / RRF | 0.802 |
| Hybrid + heuristic reranker | 0.693 |

The lexical heuristic reranker improved none of the 16 answerable queries and worsened six, so it was not selected as the preferred retrieval configuration.

[Raw source artifact](../../evaluation/results/reranker_ablation_20261003T210540073940Z.json)
