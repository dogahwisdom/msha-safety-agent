# Project Progress Tracker

This file tracks the ten-step implementation loop from `docs/paper_draft.md`. Read this file first when resuming work across sessions.

Last updated: 2026-07-19 (Step 1 done, awaiting user review)

---

## Step 1. Data acquisition and cleaning

**Status:** done

**Note:** Verified by running `python -m src.data.ingest` and `pytest tests/test_data_ingest.py` (5 passed).

**Sources downloaded (cached in `data/raw/`):**
- Accident Injuries: https://arlweb.msha.gov/OpenGovernmentData/DataSets/Accidents.zip
- Mine Identification: https://arlweb.msha.gov/OpenGovernmentData/DataSets/Mines.zip

**Filtering decisions (in order):**
1. Drop duplicate `DOCUMENT_NO` (0 found in current extract).
2. Drop rows with missing `DOCUMENT_NO` or `MINE_ID` (0 removed).
3. Drop rows with invalid `DEGREE_INJURY_CD` (blank or `?`): 910 removed.
4. Drop rows with `CAL_YR` before 2000: 0 removed.
5. Drop rows with invalid core classifier codes (`SUBUNIT_CD`, `CLASSIFICATION_CD`, `OCCUPATION_CD`, `ACTIVITY_CD`, `INJURY_SOURCE_CD`, `NATURE_INJURY_CD`, `INJ_BODY_PART_CD`, `COAL_METAL_IND`, `ACCIDENT_TYPE_CD`): 32,063 removed total across these steps. Occupation missingness is the largest single loss (30,554).
6. Impute missing or invalid `MINING_EQUIP_CD` as `UNK` rather than drop rows: 127,537 imputed. Over half of kept records lack equipment codes; dropping them would cut far below prior study sizes.
7. Drop rows with missing `NARRATIVE`: 10 removed (needed for retrieval index).

**Split:** 80/20 stratified on `DEGREE_INJURY_CD` plus five-year calendar buckets. Strata with fewer than two records are collapsed for split assignment only (original labels unchanged). One singleton degree-00 record landed in train only.

**Summary statistics (verified from `data/processed/ingestion_summary.json`):**
| Stage | Rows |
|-------|------|
| Raw accidents | 273,614 |
| Raw mines | 91,905 |
| After cleaning | 240,641 |
| Train | 192,512 |
| Test | 48,129 |
| Mine join matched | 240,641 (100%) |
| Year range | 2000 to 2026 |

**Class distribution (cleaned):**
| Code | Label | Count |
|------|-------|-------|
| 00 | Accident only | 1 |
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

**Comparison to prior MSHA studies:** The paper cites roughly 228,000 records in one prior study. Our cleaned set has 240,641 records with complete core structured fields and narrative. The difference is expected: we impute equipment codes instead of dropping those rows, and we require narrative text.

**Awaiting user confirmation before Step 2.**

---

## Step 2. Classifier tool

**Status:** not started

**Note:** Waiting on user confirmation of Step 1 summary statistics.

---

## Step 3. Trend analysis tool

**Status:** not started

**Note:** Not started.

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
