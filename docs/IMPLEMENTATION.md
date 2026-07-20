# Implementation Log

Engineering record for the ten-step pipeline in `docs/paper_draft.md`.

Last updated: July 2026

---

## Step 1. Data acquisition and cleaning

**Status:** done

**Validation:** `python -m src.data.ingest`, `pytest tests/test_data_ingest.py`.

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

**Degree-00 exclusion:** Code 00 (accident only) is excluded from training and evaluation (`CLASSIFIER_EXCLUDED_TARGET_CODES`); cleaned count is 240,640.

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

### Data quality and design notes

**1. UNK equipment rate by year:** UNK is stable at roughly 48–60% across calendar years (2000: 49.9%, 2015: 58.2%, 2024: 55.1%). Equipment code imputation does not introduce a strong early-year bias.

**2. Occupation missingness by year:** Drop rate is 7.5 to 20.3% per year, with a spike in 2003 to 2004 (20.3% and 15.2%) but otherwise mostly 8 to 15%. Not contractor-concentrated: only 1.7% of occupation-missing dropped rows have a contractor ID. Stated limitation: early 2000s reporting may under-represent incidents with missing occupation codes.

**3. Classifier feature specification and leakage check:**

Planned inputs (from `src/data/config.py`):
- Accident-side codes: `SUBUNIT_CD`, `CLASSIFICATION_CD`, `OCCUPATION_CD`, `ACTIVITY_CD`, `INJURY_SOURCE_CD`, `NATURE_INJURY_CD`, `INJ_BODY_PART_CD`, `MINING_EQUIP_CD`, `COAL_METAL_IND`, `ACCIDENT_TYPE_CD`
- Mine context (optional ablation): `CURRENT_MINE_TYPE`, `CURRENT_MINE_STATUS`, `PRIMARY_CANVASS`, `NO_EMPLOYEES`, `STATE`

Explicitly excluded from inputs (`CLASSIFIER_LEAKAGE_COLUMNS`):
- `DEGREE_INJURY_CD`, `DEGREE_INJURY` (target and label text)
- `DAYS_LOST`, `DAYS_RESTRICT`, `SCHEDULE_CHARGE`, `RETURN_TO_WORK_DT` (post-outcome or severity proxies)
- `TRANS_TERM`, `NO_INJURIES`, `IMMED_NOTIFY_CD`, `IMMED_NOTIFY` (outcome-adjacent)
- `NARRATIVE`, `DOCUMENT_NO`, `CLOSED_DOC_NO` (retrieval or identifiers, not classifier inputs)

Target: `DEGREE_INJURY_CD` (codes 01 to 10).

Inputs are selected via `src/data/features.py` (`select_classifier_features`).

**4. Temporal split:** Primary evaluation uses an 80/20 random stratified split. Out-of-time robustness: train on 2000–2020, test on 2021+ (`OUT_OF_TIME_TRAIN_MAX_YEAR` / `OUT_OF_TIME_TEST_MIN_YEAR` in config).

**5. Class imbalance:** Macro F1 and per-class recall reported; fatality (01) and permanent disability (02) broken out explicitly.

**6. Degree-00 singleton:** Excluded in cleaning step 8 (1 row removed). Documented in `CLASSIFIER_EXCLUDED_TARGET_CODES`.

**7. Mine join spot check:** Ten randomly sampled rows verified manually: `MINE_ID` matched raw Mines file and joined `STATE`, `PRIMARY_CANVASS`, `CURRENT_MINE_TYPE` values matched exactly. Zero duplicate `MINE_ID` in cleaned mines table. 100% match rate is plausible because every accident record carries a valid `MINE_ID` and the mines table is comprehensive. Note: `NO_EMPLOYEES` is empty for 7,680 rows (3.2%); not a join failure.

**8. Partial year 2026:** 2,374 cleaned rows for 2026 vs 5,159 for 2025. Trend tool excludes 2026 from year-over-year comparisons.

**9. Synthetic unit test:** `test_cleaning_synthetic_hand_computed_counts` validates filtering with hard-coded expected counts.

---

## Step 2. Classifier tool

**Status:** done

**Validation:** `python -m src.tools.run_classifier`, `pytest tests/test_classifier.py`.

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

**Comparison to prior MSHA studies:** Prior work on similar MSHA record counts (~228k) uses logistic regression, neural networks, decision trees, and random forests, often with different targets (days away from work, binary outcome, or aggregated classes) rather than 10-way `DEGREE_INJURY_CD` from structured codes alone. Direct numeric comparison is therefore limited. On this task, accuracy (0.574) exceeds the majority-class baseline (class 03 always: 0.364) but macro F1 (0.562) reflects weak recall on severity codes 04, 09, and 10. Fatality recall (0.538) is the metric most relevant to safety officers.

**Output files:**
- `data/processed/classifier_evaluation.json`
- `data/processed/injury_risk_classifier.joblib`

---

## Step 3. Trend analysis tool

**Status:** done

**Validation:** `pytest tests/test_trends.py`.

**Module:** `src/tools/trends.py` (`TrendAnalyzer`)

**Features:** `count_by_year`, `year_over_year_change`, `count_by_group`, `compare_periods`. Filter aliases (e.g. `degree_code`, `coal_metal`, `occupation` substring). **2026 excluded** from YoY and default year counts (partial reporting year).

---

## Step 4. Narrative retrieval tool

**Status:** done

**Validation:** `pytest tests/test_retrieval.py`. Full index: 240,640 narratives (~28 min on CPU).

**Module:** `src/tools/retrieval.py` (`NarrativeRetriever`)

**Embedding:** `sentence-transformers/all-MiniLM-L6-v2` (requires PyTorch). Vector store: ChromaDB at `data/processed/chroma_narratives/`.

**Outputs:** `data/processed/retrieval_index_meta.json`

---

## Step 5. Orchestrator

**Status:** done

**Module:** `src/agent/orchestrator.py` (`MSHASafetyAgent`). Supports OpenAI-compatible providers (Groq, Ollama, OpenAI) and offline tool routing.

**Logging:** Structured JSONL in `eval/logs/`.

---

## Step 6. Baselines

**Status:** done

**Validation:** `pytest tests/test_baselines.py`.

**Modules:** `src/baselines/classifier_baseline.py`, `src/baselines/rag_baseline.py`

---

## Step 7. Benchmark construction

**Status:** done

**Output:** 60 questions (20 per category) in `benchmark/questions.json` with reference answers derived from cleaned data.

---

## Step 8. Run all three systems

**Status:** done

Offline tool-routing evaluation: agent 93.3% overall, 100% tool selection. Outputs: `eval/results/benchmark_runs.json`. Failure analysis: `docs/FAILURE_ANALYSIS.md`.

Supplementary live LLM run (Ollama qwen2.5:7b): 53.3% overall, 88.3% tool selection. Provider options: `docs/FREE_LLM_OPTIONS.md`.

---

## Step 9. Scoring

**Status:** done

`eval/score.py` produces `eval/results/scores.json` and `eval/results/failure_cases.json`.

---

## Step 10. Human evaluation

**Status:** materials complete; data collection pending

Protocol and stimulus builder: `eval/human_eval/materials.md`, `eval/human_eval/build_stimuli.py`.
