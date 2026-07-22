# Progress log

## Step 10. Human evaluation materials — COMPLETE (2026-07-22)

### Verified

- `make human-eval-stimuli` generated blinded packets from Groq primary benchmark (`benchmark_runs_groq_fixed.json`).
- 12 stratified questions (4 CLS, 4 TRD, 4 CASE) × 3 systems = **36 stimuli** per participant packet.
- **10 participant packets** (`P001`–`P010`) with distinct question order under `eval/human_eval/generated/packets/`.
- Empty response templates under `eval/human_eval/generated/response_templates/`.
- Researcher-only unblinding key: `eval/human_eval/generated/randomization_key.csv` (gitignored).
- `pytest tests/test_human_eval.py` — 3 passed.
- Facilitator guide: `eval/human_eval/facilitator_guide.md`.
- Post-collection aggregation: `eval/human_eval/score_responses.py` (requires real participant CSVs).

### Blocked on you (real participants)

Participant ratings are **not** included. Run in-person or survey sessions at UMaT using the generated packets, save completed CSVs to `eval/human_eval/responses/`, then run `score_responses.py` and update Section 6.5 of the paper.

---

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
