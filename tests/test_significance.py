"""Tests for McNemar significance comparisons."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval.significance_test import _mcnemar, run_significance_tests


def test_mcnemar_perfect_agreement_has_p_one() -> None:
    answers = {f"Q{i:02d}": True for i in range(60)}
    result = _mcnemar(answers, answers)
    assert result["a_wrong_b_right"] == 0
    assert result["a_right_b_wrong"] == 0
    assert result["p_value"] == 1.0
    assert result["significant_at_0_05"] is False


def test_mcnemar_detects_discordant_pairs() -> None:
    agent = {f"Q{i:02d}": i < 23 for i in range(60)}
    baseline = {f"Q{i:02d}": i < 18 for i in range(60)}
    result = _mcnemar(agent, baseline)
    assert result["system_a_correct"] == 23
    assert result["system_b_correct"] == 18
    assert result["a_right_b_wrong"] == 5
    assert result["a_wrong_b_right"] == 0


def test_run_significance_tests_on_groq_benchmark() -> None:
    benchmark = Path("eval/results/benchmark_runs_groq_fixed.json")
    if not benchmark.exists():
        pytest.skip("Groq benchmark results not present locally")
    results = run_significance_tests(benchmark)
    cls = results["comparisons"]["agent_vs_classifier_baseline"]
    rag = results["comparisons"]["agent_vs_rag_baseline"]
    assert cls["system_a_accuracy"] == 0.3833
    assert cls["system_b_accuracy"] == 0.3
    assert rag["system_a_accuracy"] == 0.3833
    assert rag["system_b_accuracy"] == 0.2833
    assert cls["significant_at_0_05"] is False
    assert rag["significant_at_0_05"] is False
