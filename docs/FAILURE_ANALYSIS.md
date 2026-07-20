# Benchmark Failure Analysis

Analysis of incorrect answers from the offline tool-routing evaluation (agent overall accuracy: **93.3%**).

## Summary

| System | Failures | Primary cause |
|--------|----------|---------------|
| Agent (offline) | 4 / 60 | Classifier errors (2), retrieval rank (2) |
| Classifier baseline | 42 / 60 | Out-of-domain question types by design |
| Retrieval baseline | 42 / 60 | Out-of-domain question types by design |

Each single-tool baseline covers one of three question categories (20/60), so 30% overall accuracy is expected.

## Agent failures

### Classification (CLS-03, CLS-14)

The classifier predicted degree code `03` where the reference specified a different severity code. Tool routing was correct; the error reflects classifier performance (macro F1: 0.562) rather than orchestration failure.

### Case-grounded (CASE-14, CASE-15)

Semantic retrieval returned plausible narratives but did not rank the reference document in the top five results — a known limitation of embedding-based search over large corpora.

## Trend category

After normalizing filter parsing for fatality counts and hyphenated degree-code forms, the offline agent achieved **100% (20/20)** on trend questions.

## Live LLM comparison

Supplementary Ollama runs (`qwen2.5:7b`) scored 53.3% overall with 0% on trends, indicating that smaller local models are insufficient for reliable function calling on this benchmark. Cloud models with stronger tool-use capability (e.g. Llama 3.3 70B via Groq) are recommended for live evaluation.

See [FREE_LLM_OPTIONS.md](FREE_LLM_OPTIONS.md) for provider configuration.
