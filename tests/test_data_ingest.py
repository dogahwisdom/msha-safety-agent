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
