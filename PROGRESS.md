# Progress log

## Pre-submission checklist (2026-07-22)

Three items must be complete before human data collection or paper submission. Human sessions remain **blocked** until Item 1 is confirmed by UMaT, not assumed.

---

### Item 1. Ethics and consent process - DONE (code/docs only; UMaT confirmation still blocking)

**What changed:**
- Added blocking TODO at top of `eval/human_eval/materials.md`.
- Created `eval/human_eval/consent_form.md` with draft plain-language consent (pseudonymous IDs, 36 blocks, about 45 to 60 min, voluntary participation).
- Updated `eval/human_eval/facilitator_guide.md` to reference ethics blocking.
- Updated `docs/paper_draft.md` §6.5 and `docs/REPRODUCTION.md` to state collection has not started.

**Verified:** Draft files exist; no ethics requirement was invented. Researcher must confirm with UMaT supervisor before any session.

**Still blocking:** Real answer from UMaT on informed consent vs formal ethics clearance.

---

### Item 2. Statistical caution (McNemar exact test) - DONE

**What changed:**
- `eval/significance_test.py` uses McNemar's exact test (`scipy.stats.binomtest`) on `eval/results/scores_groq_fixed.json`.
- Added `tests/test_significance.py` (3 passed).
- Added `make significance-test` target and Path B step 10 in `docs/REPRODUCTION.md`.
- Updated `docs/paper_draft.md` Abstract, Section 6.2, and Section 7 Limitations with exact test language and real p-values.

**Results (n=60 paired questions, McNemar exact test on Groq scores):**
| Comparison | Discordant pairs | Agent-favor / Baseline-favor | Exact p-value | Significant at alpha=0.05? |
|------------|------------------|------------------------------|---------------|----------------------------|
| Agent vs classifier | 7 | 6 / 1 | 0.125 | No |
| Agent vs RAG | 30 | 18 / 12 | 0.362 | No |

Overall differences (38.3% vs 30.0% vs 28.3%) are directional, not statistically confirmed at n = 60.

---

### Item 3. Single-run disclosure and category-level framing - DONE

**What changed in `docs/paper_draft.md`:**
- **Abstract:** McNemar non-significance, category underperformance (CLS 85% vs 90%, CASE 25% vs 85%), breadth-not-dominance framing, ethics blocking note.
- **§6.2:** Category context under results table; McNemar paragraph (same numbers as Item 2).
- **§7:** Updated contributions paragraph with significance and category framing; new limitation on single Groq run and non-determinism; expanded live LLM weakness bullet.

---

## Step 10. Human evaluation materials - COMPLETE (materials only)

- `make human-eval-stimuli` generates blinded packets from Groq primary benchmark.
- 20 participant packets (`P001`–`P020`), ESS scale, `score_responses.py` for post-collection aggregation.
- **No participant data collected.** Blocked on Item 1 (UMaT ethics).

---

## Groq primary benchmark - COMPLETE (2026-07-22)

| System | Classification | Trend | Case | Overall | Tool selection |
|--------|----------------|-------|------|---------|----------------|
| Agent (Groq) | 85.0% | 5.0% | 25.0% | 38.3% | 60.0% |
| Classifier baseline | 90.0% | 0.0% | 0.0% | 30.0% | 100% |
| RAG baseline | 0.0% | 0.0% | 85.0% | 28.3% | 98.3% |

Artifacts: `eval/results/benchmark_runs_groq_fixed.json`, `eval/results/scores_groq_fixed.json` (local, gitignored).
