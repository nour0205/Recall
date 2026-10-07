# Controlled grounded-prompt ablation

The evaluation-only prompt is [`grounded_strict_v1`](prompts/grounded_strict_v1.json).
Its JSON contains the exact system text and user-message template. Each raw result
also stores the expanded messages, prompt version, and definition/message hashes.

[`run_strict_prompt_ablation.py`](run_strict_prompt_ablation.py) reads the 19
questions and five source chunks per case directly from the frozen baseline.
Source text, order, metadata, chunk IDs, document IDs, `[S#]` mappings, and existing
evidence-availability labels are copied without changes. The context block is
checked against the original prompt in UTF-8 before generation. No retrieval,
embedding, corpus database, planner, fallback, or reranker is called.

The only experimental change is the prompt. The baseline model alias,
temperature, max_tokens, SDK version, request defaults, timeout, and zero-retry
configuration remain fixed. References, reviewer labels, and previous generated
answers never enter the model prompt. Production Python files, benchmarks,
baseline outputs, and finalized review/report files are hashed before and after
the run. The strict prompt definition is also protected against mid-run changes.

Run offline tests before the single authorized generation run:

```powershell
.venv-generation/Scripts/python.exe -m unittest discover -s tests -p test_strict_prompt_ablation.py -v
.venv-generation/Scripts/python.exe -m evaluation.run_strict_prompt_ablation
```

Output is [`generation_strict_prompt_v1.json`](results/generation_strict_prompt_v1.json).
Existing output prevents execution; the runner never automatically retries,
resumes, overwrites, or scores answers. It checkpoints the exact request before
each call and records responses, latency, usage, model identity, finish reason,
and sanitized failures afterward.

The operational summary compares answer lengths over paired completed cases,
using Unicode characters and whitespace-delimited words including Markdown and
citations. These counts are separate from API tokens and do not measure answer
quality. All new human-evaluation fields remain null for the next review step.
