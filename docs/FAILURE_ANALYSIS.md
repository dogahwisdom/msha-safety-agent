# Benchmark failure analysis (Step 9 supplement)

Generated from `eval/results/failure_cases.json` after offline tool-routing evaluation (mode: `offline_tools`, agent overall accuracy **93.3%**).

## Summary

| System | Failures | Primary cause |
|--------|----------|---------------|
| Agent (offline) | 4 / 60 | Classifier errors (2), retrieval rank (2) |
| Classifier baseline | 42 / 60 | Cannot answer trend or case questions by design |
| RAG baseline (retrieval-only) | 42 / 60 | Cannot answer classification or trend questions by design |

Baselines scoring 30% overall is **expected**: each baseline only covers one of three question categories (20/60).

## Agent failures (4)

### Classification (2): CLS-03, CLS-14

- **Reason:** Classifier predicted degree code `03` (days away from work); reference answer was a different severity code.
- **Category:** Model limitation, not routing failure. Random forest macro F1 is 0.562 with weak recall on several classes (04, 09, 10).
- **Paper framing:** Tool was selected correctly; wrong answer reflects classifier accuracy (~90% on benchmark classification subset), not orchestration failure.

### Case-grounded (2): CASE-14, CASE-15

- **Reason:** Semantic retrieval returned plausible narratives but did not rank the reference document in the top-5 results.
- **Category:** Embedding retrieval limitation — similar wording retrieved different incidents.
- **Paper framing:** Honest RAG failure mode; full agent still achieved 90% on case questions.

## Baseline failures (by design)

- **Classifier baseline:** Rejects or fails all 40 trend + case questions (`"only handles classification-style questions"`).
- **Retrieval-only baseline:** Succeeds on case questions where document overlap scoring passes; fails all classification and trend questions.

## Trend category (agent)

After fixing filter parsing (`fatalities`, `degree-code-XX` hyphen forms), the offline agent achieved **100% (20/20)** on trend questions.

## Recommendations for live LLM evaluation

When a free LLM (Groq or Ollama) is available:

1. Compare tool-selection rate — offline agent is 100% because category is passed in; live LLM must infer from natural language alone.
2. Expect additional failures from misread tool JSON or hallucinated counts.
3. Groq `llama-3.3-70b-versatile` is recommended over local 7B models for function calling.

See [FREE_LLM_OPTIONS.md](FREE_LLM_OPTIONS.md).
