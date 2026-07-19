# Project Progress Tracker

This file tracks the ten-step implementation loop from `docs/paper_draft.md`. Read this file first when resuming work across sessions.

Last updated: 2026-07-19 (Steps 1–10 code complete; notebooks added)

---

## Step 1. Data acquisition and cleaning

**Status:** done

**Note:** Verified by running `python -m src.data.ingest` and `pytest tests/test_data_ingest.py`. External review follow-up items below are addressed.

**Sources downloaded (cached in `data/raw/`):**
- Accident Injuries: https://arlweb.msha.gov/OpenGovernmentData/DataSets/Accidents.zip
- Mine Identification: https://arlweb.msha.gov/OpenGovernmentData/DataSets/Mines.zip

**Filtering decisions (in order):**
1. Drop duplicate `DOCUMENT_NO` (0 found in current extract).
2. Drop rows with missing `DOCUMENT_NO` or `MINE_ID` (0 removed).
3. Drop rows with invalid `DEGREE_INJURY_CD` (blank or `?`): 910 removed.
4. Drop rows with `CAL_YR` before 2000: 0 removed.
5. Drop rows with invalid core classifier codes (`SUBUNIT_CD`, `CLASSIFICATION_CD`, `OCCUPATION_CD`, `ACTIVITY_CD`, `INJURY_SOURCE_CD`, `NATURE_INJURY_CD`, `INJ_BODY_PART_CD`, `COAL_METAL_IND`, `ACCIDENT_TYPE_CD`): 32,063 removed total across these steps. Occupation missingness is the largest single loss (30,554).
6. Impute missing or invalid `MINING_EQUIP_CD` as `UNK` rather than drop rows: 127,532 imputed (53.0% of kept rows). Over half of kept records lack equipment codes; dropping them would cut far below prior study sizes.
7. Drop rows with missing `NARRATIVE`: 10 removed (needed for retrieval index).
8. Drop rows with `DEGREE_INJURY_CD` `00` (accident only): 1 removed. Singleton class cannot be learned or evaluated.

**Split:** 80/20 stratified on `DEGREE_INJURY_CD` plus calendar year buckets (mostly five-year spans; final bucket 2020 to 2026). Strata with fewer than two records are collapsed for split assignment only (original labels unchanged).

**Test split class coverage (verified 2026-07-19):** All ten target classes (01 to 10) appear in the held-out test set. Counts: 01=240, 02=491, 03=17,514, 04=4,102, 05=8,620, 06=14,223, 07=2,108, 08=307, 09=114, 10=409.

**Note on degree-00 reporting:** An earlier PROGRESS draft listed code 00 with count 1 from a run before step 8 (degree exclusion) was added. Current code and `ingestion_summary.json` agree: code 00 is absent; cleaned count is 240,640.

**Summary statistics (verified from `data/processed/ingestion_summary.json` after review follow-up re-ingest):**
| Stage | Rows |
|-------|------|
| Raw accidents | 273,614 |
| Raw mines | 91,905 |
| After cleaning | 240,640 |
| Train | 192,512 |
| Test | 48,128 |
| Mine join matched | 240,640 (100%) |
| Year range | 2000 to 2026 |

**Class distribution (cleaned, 10 classes after excluding code 00):**
| Code | Label | Count |
|------|-------|-------|
| 01 | Fatality | 1,204 |
| 02 | Permanent total/partial disability | 2,453 |
| 03 | Days away from work only | 87,573 |
| 04 | Days away and restricted | 20,508 |
| 05 | Days restricted only | 43,099 |
| 06 | No days away, no restriction | 71,110 |
| 07 | Occupational illness | 10,542 |
| 08 | Natural causes | 1,534 |
| 09 | Non-employees | 571 |
| 10 | All other (incl. first aid) | 2,046 |

**Output files:**
- `data/processed/accidents_clean.csv`
- `data/processed/mines_clean.csv`
- `data/processed/accidents_train.csv`
- `data/processed/accidents_test.csv`
- `data/processed/ingestion_summary.json`

**Comparison to prior MSHA studies:** The paper cites roughly 228,000 records in one prior study. Our cleaned set has 240,640 records with complete core structured fields and narrative. The difference is expected: we impute equipment codes instead of dropping those rows, and we require narrative text.

### External review follow-up (2026-07-19)

**1. UNK equipment rate by year:** UNK is stable at roughly 48 to 60% across all calendar years (not concentrated in early years only). Example: 2000 at 49.9%, 2015 at 58.2%, 2024 at 55.1%. The classifier may still learn year-correlated patterns through other fields, but UNK itself does not show a strong early-year-only bias. Step 2 will report whether adding `CAL_YR` as a feature changes results.

**2. Occupation missingness by year:** Drop rate is 7.5 to 20.3% per year, with a spike in 2003 to 2004 (20.3% and 15.2%) but otherwise mostly 8 to 15%. Not contractor-concentrated: only 1.7% of occupation-missing dropped rows have a contractor ID. Stated limitation: early 2000s reporting may under-represent incidents with missing occupation codes.

**3. Classifier feature list and leakage check (Step 2 handoff):**

Planned inputs (from `src/data/config.py`):
- Accident-side codes: `SUBUNIT_CD`, `CLASSIFICATION_CD`, `OCCUPATION_CD`, `ACTIVITY_CD`, `INJURY_SOURCE_CD`, `NATURE_INJURY_CD`, `INJ_BODY_PART_CD`, `MINING_EQUIP_CD`, `COAL_METAL_IND`, `ACCIDENT_TYPE_CD`
- Mine context (optional ablation): `CURRENT_MINE_TYPE`, `CURRENT_MINE_STATUS`, `PRIMARY_CANVASS`, `NO_EMPLOYEES`, `STATE`

Explicitly excluded from inputs (`CLASSIFIER_LEAKAGE_COLUMNS`):
- `DEGREE_INJURY_CD`, `DEGREE_INJURY` (target and label text)
- `DAYS_LOST`, `DAYS_RESTRICT`, `SCHEDULE_CHARGE`, `RETURN_TO_WORK_DT` (post-outcome or severity proxies)
- `TRANS_TERM`, `NO_INJURIES`, `IMMED_NOTIFY_CD`, `IMMED_NOTIFY` (outcome-adjacent)
- `NARRATIVE`, `DOCUMENT_NO`, `CLOSED_DOC_NO` (retrieval or identifiers, not classifier inputs)

Target: `DEGREE_INJURY_CD` (codes 01 to 10).

Step 2 must select inputs via `src/data/features.py` (`select_classifier_features`). Do not use `frame.drop(columns=[target])` on the full cleaned dataframe.

**4. Temporal split:** Primary evaluation keeps the current 80/20 random stratified split for comparability with prior MSHA studies. Step 2 will add an out-of-time robustness check: train on 2000 to 2020, test on 2021 onward (`OUT_OF_TIME_TRAIN_MAX_YEAR` / `OUT_OF_TIME_TEST_MIN_YEAR` in config).

**5. Class imbalance:** Step 2 will report macro F1 and per-class recall, with fatality (01) and permanent disability (02) broken out explicitly. Accuracy alone is not sufficient.

**6. Degree-00 singleton:** Excluded in cleaning step 8 (1 row removed). Documented in `CLASSIFIER_EXCLUDED_TARGET_CODES`.

**7. Mine join spot check:** Ten randomly sampled rows verified manually: `MINE_ID` matched raw Mines file and joined `STATE`, `PRIMARY_CANVASS`, `CURRENT_MINE_TYPE` values matched exactly. Zero duplicate `MINE_ID` in cleaned mines table. 100% match rate is plausible because every accident record carries a valid `MINE_ID` and the mines table is comprehensive. Note: `NO_EMPLOYEES` is empty for 7,680 rows (3.2%); not a join failure.

**8. Partial year 2026:** Dataset includes 2,374 cleaned rows for 2026 vs 5,159 for 2025 and 5,471 for 2024. Step 3 trend tool must not treat 2026 as a full year in year-over-year comparisons.

**9. Synthetic unit test:** Added `test_cleaning_synthetic_hand_computed_counts` with hard-coded expected row counts after filtering (2 kept of 4 input rows).

**Ready for Step 2.**

---

## Step 2. Classifier tool

**Status:** done

**Note:** Verified by `python -m src.tools.run_classifier` and `pytest tests/test_classifier.py` (5 passed).

**Module:** `src/tools/classifier.py` (`InjuryRiskClassifier`), CLI: `python -m src.tools.run_classifier`

**Model:** `RandomForestClassifier` (100 trees, `class_weight=balanced`). Inputs via `select_classifier_features()` (10 accident-side code fields). Target: `DEGREE_INJURY_CD` (10 classes, codes 01 to 10). Mine context features off by default (`--include-mine-context` optional).

**Primary evaluation (stratified holdout, n_test=48,128):**
| Metric | Value |
|--------|-------|
| Accuracy | 0.574 |
| Macro F1 | 0.562 |
| Weighted F1 | 0.565 |

**Per-class recall (stratified holdout):**
| Code | Recall | Support |
|------|--------|---------|
| 01 Fatality | 0.538 | 240 |
| 02 Permanent disability | 0.809 | 491 |
| 03 Days away only | 0.647 | 17,514 |
| 04 Days away + restricted | 0.097 | 4,102 |
| 05 Restricted only | 0.398 | 8,620 |
| 06 No days away/restriction | 0.663 | 14,223 |
| 07 Occupational illness | 0.999 | 2,108 |
| 08 Natural causes | 0.951 | 307 |
| 09 Non-employees | 0.298 | 114 |
| 10 All other | 0.134 | 409 |

**Out-of-time robustness (train 2000 to 2020, test 2021+, n_test=29,183):**
| Metric | Value |
|--------|-------|
| Accuracy | 0.553 |
| Macro F1 | 0.559 |

Fatality recall drops to 0.456 out-of-time. Classes 04, 09, and 10 remain weak on both splits.

**Comparison to prior MSHA studies (honest):** The paper draft cites prior work using logistic regression, deep neural networks, decision trees, and random forests on similar MSHA record counts (~228k), but does not report their published multiclass accuracy figures in the draft, and those studies often used different targets (days away from work, binary outcome, or aggregated injury classes) rather than 10-way `DEGREE_INJURY_CD` from structured codes alone. Direct numeric comparison is therefore not available without reading each primary source. On this task, accuracy (0.574) exceeds the majority-class baseline (predicting class 03 always: 0.364 on the test split) but macro F1 (0.562) reflects poor recall on several severity codes, especially 04, 09, and 10. This is comparable in spirit to prior supervised severity modeling (structured fields, similar data scale, random forest family) but not demonstrably better or worse than published benchmarks we have not yet extracted. Fatality recall (0.538) is the metric most relevant to safety officers and is moderate, not strong.

**Output files:**
- `data/processed/classifier_evaluation.json`
- `data/processed/injury_risk_classifier.joblib`

---

## Step 3. Trend analysis tool

**Status:** done

**Note:** Verified by `pytest tests/test_trends.py` (6 passed). Notebook: `notebooks/03_trend_analysis.ipynb`.

**Module:** `src/tools/trends.py` (`TrendAnalyzer`)

**Features:** `count_by_year`, `year_over_year_change`, `count_by_group`, `compare_periods`. Filter aliases (e.g. `degree_code`, `coal_metal`, `occupation` substring). **2026 excluded** from YoY and default year counts (partial reporting year).

---

## Step 4. Narrative retrieval tool

**Status:** done

**Note:** Verified by `pytest tests/test_retrieval.py` (tiny index + slow full-index hand-check passed 2026-07-19). Full index: **240,640 narratives** indexed in ~28 min on CPU. Notebook: `notebooks/04_narrative_retrieval.ipynb`.

**Module:** `src/tools/retrieval.py` (`NarrativeRetriever`)

**Embedding:** `sentence-transformers/all-MiniLM-L6-v2` (requires PyTorch). Vector store: ChromaDB at `data/processed/chroma_narratives/`.

**Outputs:** `data/processed/retrieval_index_meta.json`

---

## Step 5. Orchestrator

**Status:** done

**Note:** OpenAI function calling. Requires `OPENAI_API_KEY` in `.env`. Notebook: `notebooks/05_agent_and_baselines.ipynb`.

**Module:** `src/agent/orchestrator.py` (`MSHASafetyAgent`), CLI: `python -m src.agent.run_agent`

**Logging:** Structured JSONL in `eval/logs/`

---

## Step 6. Baselines

**Status:** done

**Note:** Verified by `pytest tests/test_baselines.py`. Notebook: `notebooks/05_agent_and_baselines.ipynb`.

**Modules:** `src/baselines/classifier_baseline.py`, `src/baselines/rag_baseline.py`

---

## Step 7. Benchmark construction

**Status:** done

**Note:** `python benchmark/build_benchmark.py` writes 60 questions (20 classification, 20 trend, 20 case-grounded) and reference answers. **Review `benchmark/questions.json` before Step 8.**

---

## Step 8. Run all three systems

**Status:** done (offline tool mode, 2026-07-19)

**Note:** Ran `python eval/run_benchmark.py` without `OPENAI_API_KEY` using offline tool routing (`OfflineToolAgent`, `RetrievalOnlyBaseline`). Results: `eval/results/benchmark_runs.json` (mode=`offline_tools`, 180 rows). Re-run with API key set for live LLM agent and RAG baseline.

**Offline overall accuracy (Step 9):** agent 88.3%, classifier_baseline 30.0%, rag_baseline 30.0%. Agent tool-selection rate: 100%.

---

## Step 9. Scoring

**Status:** done

**Note:** `python eval/score.py` after Step 8. Writes `eval/results/scores.json` and `eval/results/failure_cases.json`. Offline run scored 91 failure cases (mostly classifier/RAG on out-of-domain question types, as expected).

---

## Step 10. Human evaluation materials

**Status:** done

**Note:** `eval/human_eval/materials.md` (Hoffman et al. 2023 ESS, 9 items). Stimulus builder: `eval/human_eval/build_stimuli.py`. **No simulated human data.**
