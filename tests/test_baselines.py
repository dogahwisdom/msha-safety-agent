"""Tests for baseline systems (Step 6)."""

from __future__ import annotations

from src.baselines.classifier_baseline import ClassifierBaseline


def test_classifier_baseline_parses_structured_question() -> None:
    question = (
        "Predict injury degree for: subunit_cd=03, classification_cd=05, "
        "occupation_cd=452010, activity_cd=05, injury_source_cd=2080, "
        "nature_injury_cd=010, inj_body_part_cd=410, mining_equip_cd=UNK, "
        "coal_metal_ind=C, accident_type_cd=01."
    )
    baseline = ClassifierBaseline()
    result = baseline.answer(question)
    assert result["tools_used"] == ["classify_injury_risk"]
    assert "Predicted injury degree code:" in result["answer"]


def test_classifier_baseline_rejects_open_ended_question() -> None:
    baseline = ClassifierBaseline()
    result = baseline.answer("How many fatalities occurred in 2015?")
    assert result["tools_used"] == []
    assert "only handles classification" in result["answer"]
