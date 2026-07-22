"""Tests for baseline systems (Step 6)."""

from __future__ import annotations

import pytest

from src.baselines.classifier_baseline import ClassifierBaseline
from src.tools.classifier import CLASSIFIER_MODEL_PATH


@pytest.fixture
def baseline() -> ClassifierBaseline:
    if not CLASSIFIER_MODEL_PATH.exists():
        pytest.skip("Run python -m src.tools.run_classifier first")
    return ClassifierBaseline()


def test_classifier_baseline_parses_structured_question(baseline: ClassifierBaseline) -> None:
    question = (
        "Predict injury degree for: subunit_cd=03, classification_cd=05, "
        "occupation_cd=452010, activity_cd=05, injury_source_cd=2080, "
        "nature_injury_cd=010, inj_body_part_cd=410, mining_equip_cd=UNK, "
        "coal_metal_ind=C, accident_type_cd=01."
    )
    result = baseline.answer(question)
    assert result["tools_used"] == ["classify_injury_risk"]
    assert "predicted injury degree code" in result["answer"].lower()


def test_classifier_baseline_attempts_open_ended_question() -> None:
    baseline = ClassifierBaseline()
    if not CLASSIFIER_MODEL_PATH.exists():
        pytest.skip("Run python -m src.tools.run_classifier first")
    result = baseline.answer("How many fatalities occurred in 2015?")
    assert result["tools_used"] == ["classify_injury_risk"]
    assert "classifier-only baseline" in result["answer"].lower()
