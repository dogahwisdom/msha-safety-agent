"""Tests for MSHA data ingestion (Step 1)."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from src.data.clean import clean_accidents, clean_mines, join_accidents_mines
from src.data.config import (
    ACCIDENTS_TXT,
    CLASSIFIER_FEATURE_COLUMNS,
    CLASSIFIER_TARGET_COLUMN,
    MINES_TXT,
    SUMMARY_JSON,
    TEST_CSV,
    TRAIN_CSV,
)
from src.data.load import load_accidents, load_mines
from src.data.split import stratified_train_test_split


@pytest.fixture(scope="module")
def raw_accidents() -> pd.DataFrame:
    assert ACCIDENTS_TXT.exists(), f"Missing raw file: {ACCIDENTS_TXT}"
    return load_accidents(ACCIDENTS_TXT)


@pytest.fixture(scope="module")
def raw_mines() -> pd.DataFrame:
    assert MINES_TXT.exists(), f"Missing raw file: {MINES_TXT}"
    return load_mines(MINES_TXT)


def test_raw_accidents_has_expected_columns(raw_accidents: pd.DataFrame) -> None:
    required = {"DOCUMENT_NO", "MINE_ID", "DEGREE_INJURY_CD", "NARRATIVE", "CAL_YR"}
    assert required.issubset(raw_accidents.columns)
    assert len(raw_accidents) > 200_000


def test_cleaning_reduces_rows_and_removes_invalid_degree(raw_accidents: pd.DataFrame) -> None:
    cleaned, log = clean_accidents(raw_accidents)
    assert len(cleaned) < len(raw_accidents)
    assert cleaned[CLASSIFIER_TARGET_COLUMN].eq("?").sum() == 0
    assert cleaned["NARRATIVE"].isna().sum() == 0
    assert (cleaned["NARRATIVE"].str.strip() == "").sum() == 0
    assert any(entry["step"] == "drop_invalid_degree_injury_cd" for entry in log)


def test_classifier_features_present_after_cleaning(raw_accidents: pd.DataFrame) -> None:
    cleaned, _ = clean_accidents(raw_accidents)
    for column in CLASSIFIER_FEATURE_COLUMNS:
        assert column in cleaned.columns
        invalid = cleaned[column].fillna("").str.strip().isin(["", "?"]).sum()
        assert invalid == 0, f"{column} still has invalid values after cleaning"


def test_mine_join_and_split(raw_accidents: pd.DataFrame, raw_mines: pd.DataFrame) -> None:
    accidents_clean, _ = clean_accidents(raw_accidents)
    mines_clean = clean_mines(raw_mines)
    merged, join_info = join_accidents_mines(accidents_clean, mines_clean)
    assert join_info["total_rows"] == len(merged)
    assert join_info["matched_mine_rows"] > 0

    train, test, split_info = stratified_train_test_split(merged)
    assert split_info["train_rows"] + split_info["test_rows"] == len(merged)
    assert split_info["test_rows"] / len(merged) == pytest.approx(0.2, rel=0.01)

    # No document overlap between splits
    assert set(train["DOCUMENT_NO"]).isdisjoint(set(test["DOCUMENT_NO"]))


def test_cleaning_synthetic_hand_computed_counts() -> None:
    """Hard-coded tiny input with expected row counts after each filter stage."""
    frame = pd.DataFrame(
        [
            {
                "DOCUMENT_NO": "1",
                "MINE_ID": "0100001",
                "DEGREE_INJURY_CD": "03",
                "CAL_YR": "2010",
                "SUBUNIT_CD": "01",
                "CLASSIFICATION_CD": "01",
                "OCCUPATION_CD": "100",
                "ACTIVITY_CD": "001",
                "INJURY_SOURCE_CD": "001",
                "NATURE_INJURY_CD": "001",
                "INJ_BODY_PART_CD": "001",
                "MINING_EQUIP_CD": "01",
                "COAL_METAL_IND": "C",
                "ACCIDENT_TYPE_CD": "01",
                "NARRATIVE": "Valid record kept.",
                "ACCIDENT_DT": "01/01/2010",
                "DEGREE_INJURY": "DAYS AWAY FROM WORK ONLY",
            },
            {
                "DOCUMENT_NO": "2",
                "MINE_ID": "0100002",
                "DEGREE_INJURY_CD": "?",
                "CAL_YR": "2010",
                "SUBUNIT_CD": "01",
                "CLASSIFICATION_CD": "01",
                "OCCUPATION_CD": "100",
                "ACTIVITY_CD": "001",
                "INJURY_SOURCE_CD": "001",
                "NATURE_INJURY_CD": "001",
                "INJ_BODY_PART_CD": "001",
                "MINING_EQUIP_CD": "01",
                "COAL_METAL_IND": "C",
                "ACCIDENT_TYPE_CD": "01",
                "NARRATIVE": "Invalid degree removed.",
                "ACCIDENT_DT": "01/01/2010",
                "DEGREE_INJURY": "NO VALUE FOUND",
            },
            {
                "DOCUMENT_NO": "3",
                "MINE_ID": "0100003",
                "DEGREE_INJURY_CD": "00",
                "CAL_YR": "2025",
                "SUBUNIT_CD": "01",
                "CLASSIFICATION_CD": "01",
                "OCCUPATION_CD": "100",
                "ACTIVITY_CD": "001",
                "INJURY_SOURCE_CD": "001",
                "NATURE_INJURY_CD": "001",
                "INJ_BODY_PART_CD": "001",
                "MINING_EQUIP_CD": "?",
                "COAL_METAL_IND": "C",
                "ACCIDENT_TYPE_CD": "01",
                "NARRATIVE": "Excluded degree code 00.",
                "ACCIDENT_DT": "01/01/2025",
                "DEGREE_INJURY": "ACCIDENT ONLY",
            },
            {
                "DOCUMENT_NO": "4",
                "MINE_ID": "0100004",
                "DEGREE_INJURY_CD": "06",
                "CAL_YR": "2015",
                "SUBUNIT_CD": "01",
                "CLASSIFICATION_CD": "01",
                "OCCUPATION_CD": "100",
                "ACTIVITY_CD": "001",
                "INJURY_SOURCE_CD": "001",
                "NATURE_INJURY_CD": "001",
                "INJ_BODY_PART_CD": "001",
                "MINING_EQUIP_CD": "?",
                "COAL_METAL_IND": "C",
                "ACCIDENT_TYPE_CD": "01",
                "NARRATIVE": "Missing equip imputed to UNK.",
                "ACCIDENT_DT": "01/01/2015",
                "DEGREE_INJURY": "NO DYS AWY FRM WRK,NO RSTR ACT",
            },
        ]
    )
    cleaned, log = clean_accidents(frame)
    assert len(cleaned) == 2
    assert set(cleaned["DOCUMENT_NO"]) == {"1", "4"}
    assert cleaned.loc[cleaned["DOCUMENT_NO"] == "4", "MINING_EQUIP_CD"].iloc[0] == "UNK"
    removed_degree = next(e for e in log if e["step"] == "drop_invalid_degree_injury_cd")
    assert removed_degree["rows_removed"] == 1
    removed_excluded = next(e for e in log if e["step"] == "drop_excluded_degree_injury_cd_for_classifier")
    assert removed_excluded["rows_removed"] == 1


def test_cleaned_data_has_no_degree_zero(raw_accidents: pd.DataFrame) -> None:
    cleaned, _ = clean_accidents(raw_accidents)
    assert "00" not in set(cleaned["DEGREE_INJURY_CD"].astype(str).str.zfill(2))


def test_test_split_contains_all_ten_target_classes() -> None:
    if not TEST_CSV.exists():
        pytest.skip("Run python -m src.data.ingest first")
    test = pd.read_csv(TEST_CSV, usecols=["DEGREE_INJURY_CD"], low_memory=False)
    codes = set(test["DEGREE_INJURY_CD"].astype(str).str.zfill(2))
    expected = {f"{i:02d}" for i in range(1, 11)}
    assert codes == expected, f"Missing from test split: {expected - codes}"
    # Sanity: rare classes still have workable test counts
    counts = test["DEGREE_INJURY_CD"].astype(str).str.zfill(2).value_counts()
    assert counts["01"] >= 100
    assert counts["09"] >= 50


def test_select_classifier_features_excludes_leakage_columns(raw_accidents: pd.DataFrame) -> None:
    from src.data.features import select_classifier_features

    cleaned, _ = clean_accidents(raw_accidents)
    features = select_classifier_features(cleaned.head(100))
    assert "DAYS_LOST" not in features.columns
    assert "DAYS_RESTRICT" not in features.columns
    assert "DEGREE_INJURY_CD" not in features.columns
    assert "NARRATIVE" not in features.columns


def test_ingestion_pipeline_outputs_exist_after_run() -> None:
    """Verify processed artifacts if the full ingest script has been run."""
    if not TRAIN_CSV.exists():
        pytest.skip("Run python -m src.data.ingest first")
    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    train = pd.read_csv(TRAIN_CSV, low_memory=False)
    test = pd.read_csv(TEST_CSV, low_memory=False)
    assert summary["cleaned_rows"] == len(train) + len(test)
    assert summary["split"]["train_rows"] == len(train)
    assert summary["split"]["test_rows"] == len(test)
