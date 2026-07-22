# Progress log

## Methodology fix and Groq primary benchmark — COMPLETE (2026-07-22)

### Summary

- **Baselines corrected:** classifier and RAG attempt all 60 questions (no category blocking).
- **Primary result:** Groq llama-3.3-70b live agent — **38.3%** overall vs **30.0%** classifier vs **28.3%** RAG.
- **Offline ablation:** deterministic router **93.3%** (not the primary claim).
- **Leakage verified:** `DAYS_LOST` / `DAYS_RESTRICT` not in `CLASSIFIER_FEATURE_COLUMNS`.
- **Checkpointing:** `BENCHMARK_CHECKPOINT` + `scripts/run_groq_benchmark.sh` for resumable Groq runs.

### Primary benchmark (Groq, corrected baselines)

| System | Classification | Trend | Case | Overall | Tool selection |
|--------|----------------|-------|------|---------|----------------|
| Agent (Groq) | 85.0% | 5.0% | 25.0% | 38.3% | 60.0% |
| Classifier baseline | 90.0% | 0.0% | 0.0% | 30.0% | 100% |
| RAG baseline | 0.0% | 0.0% | 85.0% | 28.3% | 98.3% |

Artifacts: `eval/results/benchmark_runs_groq_fixed.json`, `eval/results/scores_groq_fixed.json` (local, gitignored).

### Step 10 (human evaluation)

Ready to proceed after author review of Section 6.2 in `docs/paper_draft.md`.
