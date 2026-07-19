"""Tests for the injury risk classifier (Step 2)."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from src.data.config import TEST_CSV, TRAIN_CSV
from src.tools.classifier import (
    CLASSIFIER_REPORT_JSON,
    InjuryRiskClassifier,
    normalize_target_labels,
    train_and_evaluate,
)


def _synthetic_frame() -> pd.DataFrame:
    """Small separable dataset: subunit code determines injury degree."""
    rows = []
    for idx, (subunit, degree) in enumerate(
        [
            ("01", "01"),
            ("01", "01"),
            ("02", "06"),
            ("02", "06"),
            ("03", "03"),
            ("03", "03"),
        ]
    ):
        rows.append(
            {
                "SUBUNIT_CD": subunit,
                "CLASSIFICATION_CD": "01",
                "OCCUPATION_CD": "100",
                "ACTIVITY_CD": "001",
                "INJURY_SOURCE_CD": "001",
                "NATURE_INJURY_CD": "001",
                "INJ_BODY_PART_CD": "001",
                "MINING_EQUIP_CD": "01",
                "COAL_METAL_IND": "C",
                "ACCIDENT_TYPE_CD": "01",
                "DEGREE_INJURY_CD": degree,
            }
        )
    return pd.DataFrame(rows)


def test_normalize_target_labels_zero_pads() -> None:
    series = pd.Series([1, "3", "09", "10"])
    assert list(normalize_target_labels(series)) == ["01", "03", "09", "10"]


def test_classifier_fit_predict_on_synthetic_data() -> None:
    frame = _synthetic_frame()
    model = InjuryRiskClassifier()
    model.fit(frame)
    predictions = model.predict(frame)
    assert len(predictions) == len(frame)
    assert set(predictions).issubset(set(model.labels_))


def test_classifier_does_not_use_leakage_columns() -> None:
    frame = _synthetic_frame()
    frame["DAYS_LOST"] = 999
    frame["NARRATIVE"] = "should not be used"
    model = InjuryRiskClassifier()
    model.fit(frame)
    # If leakage columns were used, fit would still succeed; verify feature list excludes them.
    assert "DAYS_LOST" not in model.feature_columns_
    assert "NARRATIVE" not in model.feature_columns_


@pytest.mark.slow
def test_train_and_evaluate_on_processed_data(tmp_path) -> None:
    if not TRAIN_CSV.exists() or not TEST_CSV.exists():
        pytest.skip("Run python -m src.data.ingest first")
    report_path = tmp_path / "classifier_evaluation.json"
    report = train_and_evaluate(save_model=False, report_path=report_path)
    assert report_path.exists()
    primary = report["evaluations"][0]
    assert primary["split_name"] == "stratified_holdout"
    assert primary["n_test"] > 40_000
    assert 0.0 < primary["accuracy"] < 1.0
    assert len(primary["confusion_matrix"]) == len(primary["labels"])
    # All ten classes should appear in evaluation labels
    assert len(primary["labels"]) == 10


def test_saved_evaluation_report_exists_after_full_run() -> None:
    if not CLASSIFIER_REPORT_JSON.exists():
        pytest.skip("Run python -m src.tools.run_classifier first")
    report = json.loads(CLASSIFIER_REPORT_JSON.read_text(encoding="utf-8"))
    assert "evaluations" in report
    assert report["evaluations"][0]["macro_f1"] > 0
