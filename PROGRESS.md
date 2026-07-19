# Project Progress Tracker

This file tracks the ten-step implementation loop from `docs/paper_draft.md`. Read this file first when resuming work across sessions.

Last updated: 2026-07-19 (Step 1 review follow-up complete)

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

**Split:** 80/20 stratified on `DEGREE_INJURY_CD` plus five-year calendar buckets. Strata with fewer than two records are collapsed for split assignment only (original labels unchanged).

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

**4. Temporal split:** Primary evaluation keeps the current 80/20 random stratified split for comparability with prior MSHA studies. Step 2 will add an out-of-time robustness check: train on 2000 to 2020, test on 2021 onward (`OUT_OF_TIME_TRAIN_MAX_YEAR` / `OUT_OF_TIME_TEST_MIN_YEAR` in config).

**5. Class imbalance:** Step 2 will report macro F1 and per-class recall, with fatality (01) and permanent disability (02) broken out explicitly. Accuracy alone is not sufficient.

**6. Degree-00 singleton:** Excluded in cleaning step 8 (1 row removed). Documented in `CLASSIFIER_EXCLUDED_TARGET_CODES`.

**7. Mine join spot check:** Ten randomly sampled rows verified manually: `MINE_ID` matched raw Mines file and joined `STATE`, `PRIMARY_CANVASS`, `CURRENT_MINE_TYPE` values matched exactly. Zero duplicate `MINE_ID` in cleaned mines table. 100% match rate is plausible because every accident record carries a valid `MINE_ID` and the mines table is comprehensive. Note: `NO_EMPLOYEES` is empty for 7,680 rows (3.2%); not a join failure.

**8. Partial year 2026:** Dataset includes 2,374 cleaned rows for 2026 vs 5,159 for 2025 and 5,471 for 2024. Step 3 trend tool must not treat 2026 as a full year in year-over-year comparisons.

**9. Synthetic unit test:** Added `test_cleaning_synthetic_hand_computed_counts` with hard-coded expected row counts after filtering (2 kept of 4 input rows).

**Ready for Step 2.**

---

## Step 2. Classifier tool

**Status:** not started

**Note:** Pre-Step-2 review items complete. Will use planned feature list above, macro F1 and per-class recall, primary stratified split plus out-of-time robustness check.

---

## Step 3. Trend analysis tool

**Status:** not started

**Note:** Must treat 2026 as partial year in aggregations.

---

## Step 4. Narrative retrieval tool

**Status:** not started

**Note:** Not started.

---

## Step 5. Orchestrator

**Status:** not started

**Note:** Blocked on user choice of LLM provider and API key.

---

## Step 6. Baselines

**Status:** not started

**Note:** Waiting on Steps 2 to 5.

---

## Step 7. Benchmark construction

**Status:** not started

**Note:** Must be written before any system runs on it. Requires user review before Step 8.

---

## Step 8. Run all three systems

**Status:** not started

**Note:** Waiting on user approval of benchmark (Step 7).

---

## Step 9. Scoring

**Status:** not started

**Note:** Not started.

---

## Step 10. Human evaluation materials

**Status:** not started

**Note:** Will end with materials ready for real human collection. No simulated human data.
