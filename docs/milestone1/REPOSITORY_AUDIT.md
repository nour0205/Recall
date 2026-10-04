# Public-repository preparation audit

Audit date: 2026-10-04. No retrieval or generation experiments were rerun.

| Classification | Finding and handling |
|---|---|
| Keep | Application/frontend source, frontend lockfile, unit tests, v1/v2 benchmarks, evaluation code, milestone report |
| Generated but retain | Small timestamped result JSON/Markdown and failure analyses; index them by stage instead of deleting pilot history |
| Ignore locally | `.env`, virtual environments, Python/tool caches, frontend dependencies/build output, Chroma/Whoosh stores, model downloads |
| Historical, potentially confusing | `diagram.png` and `Pipeline2.png` show older architectures; retained but not used as current diagrams |
| Historical smoke checks | `eval_cases.json` and `run_eval.py` remain; the script targets removed `/ask_routed` and is not a working current benchmark command |
| Tracked generated build | `recall-frontend/dist/` was already tracked. Ignore rules now cover future output, but do not untrack it. Retained to avoid staging unrelated removals; use source and `npm run dev` |
| Existing user changes | Backend/frontend/catalog modifications, untracked milestone code/tests, and a pre-existing deletion of `recall-frontend/src.zip`; not reverted, staged, or committed |
| Stale catalog | `data/document_catalog.json` is not the experimental corpus inventory; retained without repairs |
| Dependencies | Root requirements previously listed only Whoosh; now list direct core/legacy-script dependencies at inspected installed versions. ML evaluation dependencies remain separate |
| Documentation | Removed unsupported grounding guarantees, mandatory-reranking claims, obsolete future-roadmap claims, and the unsubstantiated MIT statement (no license file exists) |
| Machine references | No absolute local filesystem paths were found in retained evaluation artifacts. A local-environment repair note in the milestone report was replaced with portable test instructions. New documentation uses repository-relative paths |
| Secrets | No credential patterns detected in inspected tracked/current project text or reachable Git blob history (261 object/path entries inspected). Local `.env` is untracked and ignored; its values are not reported. This is a pattern audit, not a security certification |

## Reproducibility and publication status

Benchmark definitions and historical result files were not edited. Core pins
cover direct dependencies; transitive packages are not fully locked. Offline
verification checks their provenance hashes and reproduces final evidence
scores. Live historical retrieval needs matching local databases, which are
not committed; re-ingestion changes UUIDs. The 27-Chroma/28-Whoosh mismatch
remains explicit. No algorithms, production routes, or generation logic changed.

The README now identifies experimental MiniLM separately from production's
existing heuristic fallback. The preferred baseline is a milestone decision,
not a completed production rollout. Generation quality remains unmeasured.

Commit and push the reviewed code, benchmarks, tests, documentation, and saved
results before sharing links: the audit found the milestone directories were
still untracked. No commit/push was performed by this preparation task. Review
the existing user changes separately rather than blindly committing everything.
Licensing remains an owner decision; no license was invented or added.

## Verification

- Full suite: 63 tests passed, including offline historical-score reproduction
  and rejection of a tampered provenance hash.
- Both benchmark schemas and all current Chroma gold references validated.
- All 14 benchmark/result artifact SHA256 hashes remain unchanged.
- Public metrics and rounding checked against their saved JSON sources.
- Repository-facing Markdown links/fences and new-document privacy checks passed.
- Mermaid structural syntax checked; no rendering engine was installed or run.
- No API calls, model downloads, retrieval reruns, or generation evaluations.
