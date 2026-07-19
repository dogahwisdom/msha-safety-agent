"""Paths and constants for MSHA data ingestion."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = Path(os.environ.get("MSHA_RAW_DIR", PROJECT_ROOT / "data" / "raw"))
PROCESSED_DIR = Path(os.environ.get("MSHA_PROCESSED_DIR", PROJECT_ROOT / "data" / "processed"))

ACCIDENTS_URL = "https://arlweb.msha.gov/OpenGovernmentData/DataSets/Accidents.zip"
MINES_URL = "https://arlweb.msha.gov/OpenGovernmentData/DataSets/Mines.zip"

ACCIDENTS_ZIP = RAW_DIR / "Accidents.zip"
MINES_ZIP = RAW_DIR / "Mines.zip"
ACCIDENTS_TXT = RAW_DIR / "Accidents.txt"
MINES_TXT = RAW_DIR / "Mines.txt"

ACCIDENTS_CLEAN_CSV = PROCESSED_DIR / "accidents_clean.csv"
MINES_CLEAN_CSV = PROCESSED_DIR / "mines_clean.csv"
TRAIN_CSV = PROCESSED_DIR / "accidents_train.csv"
TEST_CSV = PROCESSED_DIR / "accidents_test.csv"
SUMMARY_JSON = PROCESSED_DIR / "ingestion_summary.json"

# MSHA pipe-delimited files use latin-1 and may contain non-UTF-8 characters.
MSHA_ENCODING = "latin-1"
PIPE_DELIMITER = "|"

# Calendar year lower bound from dataset scope (MSHA Part 50 since 2000).
MIN_CALENDAR_YEAR = 2000

# Structured fields used by the classifier tool (see docs/paper_draft.md Section 4).
CLASSIFIER_FEATURE_COLUMNS = [
    "SUBUNIT_CD",
    "CLASSIFICATION_CD",
    "OCCUPATION_CD",
    "ACTIVITY_CD",
    "INJURY_SOURCE_CD",
    "NATURE_INJURY_CD",
    "INJ_BODY_PART_CD",
    "MINING_EQUIP_CD",
    "COAL_METAL_IND",
    "ACCIDENT_TYPE_CD",
]

CLASSIFIER_TARGET_COLUMN = "DEGREE_INJURY_CD"

# Injury degree codes excluded from classifier training and evaluation (unlearnable or out of scope).
# Code 00 (accident only) had n=1 after cleaning; cannot be learned or evaluated as a class.
CLASSIFIER_EXCLUDED_TARGET_CODES = ["00"]

# Structured fields that must NOT be used as classifier inputs (leakage or post-outcome data).
# See PROGRESS.md Step 2 handoff for rationale against MSHA Part 50 field definitions.
CLASSIFIER_LEAKAGE_COLUMNS = [
    "DEGREE_INJURY_CD",
    "DEGREE_INJURY",
    "DAYS_LOST",
    "DAYS_RESTRICT",
    "SCHEDULE_CHARGE",
    "RETURN_TO_WORK_DT",
    "TRANS_TERM",
    "NO_INJURIES",
    "IMMED_NOTIFY_CD",
    "IMMED_NOTIFY",
    "NARRATIVE",
    "DOCUMENT_NO",
    "CLOSED_DOC_NO",
]

# Out-of-time evaluation split for Step 2 robustness check (train through 2020, test 2021 onward).
OUT_OF_TIME_TRAIN_MAX_YEAR = 2020
OUT_OF_TIME_TEST_MIN_YEAR = 2021

# Mine context columns joined from the Mines dataset.
MINE_CONTEXT_COLUMNS = [
    "CURRENT_MINE_TYPE",
    "CURRENT_MINE_STATUS",
    "PRIMARY_CANVASS",
    "NO_EMPLOYEES",
    "STATE",
]

TEST_FRACTION = 0.2
RANDOM_SEED = 42
