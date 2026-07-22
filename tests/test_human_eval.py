"""Tests for human evaluation stimulus generation."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from eval.human_eval.build_stimuli import (
    build_stimulus_rows,
    build_stimuli,
    select_question_ids,
)


def _tiny_benchmark(path: Path) -> None:
    rows = []
    for category in ("CLS", "TRD", "CASE"):
        for idx in range(1, 5):
            qid = f"{category}-{idx:02d}"
            for system in ("agent", "classifier_baseline", "rag_baseline"):
                rows.append(
                    {
                        "question_id": qid,
                        "category": category,
                        "question": f"Question for {qid}",
                        "system": system,
                        "answer": f"Answer from {system} on {qid}",
                    }
                )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"results": rows}), encoding="utf-8")


def test_select_question_ids_stratified(tmp_path: Path) -> None:
    benchmark = tmp_path / "benchmark.json"
    _tiny_benchmark(benchmark)
    payload = json.loads(benchmark.read_text(encoding="utf-8"))
    selected = select_question_ids(payload["results"], questions_per_category=2, seed=7)
    assert len(selected) == 6
    assert len([q for q in selected if q.startswith("CLS-")]) == 2
    assert len([q for q in selected if q.startswith("TRD-")]) == 2
    assert len([q for q in selected if q.startswith("CASE-")]) == 2


def test_build_stimulus_rows_blinds_all_three_systems() -> None:
    rows = [
        {
            "question_id": "CLS-01",
            "category": "classification",
            "question": "Q1",
            "system": "agent",
            "answer": "A1",
        },
        {
            "question_id": "CLS-01",
            "category": "classification",
            "question": "Q1",
            "system": "classifier_baseline",
            "answer": "A2",
        },
        {
            "question_id": "CLS-01",
            "category": "classification",
            "question": "Q1",
            "system": "rag_baseline",
            "answer": "A3",
        },
    ]
    stimuli, mapping = build_stimulus_rows(rows, ["CLS-01"], seed=1)
    assert len(stimuli) == 3
    labels = {row["system_blinded_label"] for row in stimuli}
    assert labels == {"A", "B", "C"}
    assert "system_actual" not in stimuli[0]
    assert {row["system_actual"] for row in mapping} == {
        "agent",
        "classifier_baseline",
        "rag_baseline",
    }


def test_build_stimuli_writes_packets(tmp_path: Path) -> None:
    benchmark = tmp_path / "benchmark.json"
    out_dir = tmp_path / "generated"
    _tiny_benchmark(benchmark)
    path = build_stimuli(
        results_path=benchmark,
        out_dir=out_dir,
        seed=99,
        questions_per_category=2,
        participant_count=2,
    )
    assert path.exists()
    packets = list((out_dir / "packets").glob("P*_packet.md"))
    templates = list((out_dir / "response_templates").glob("P*_responses.csv"))
    assert len(packets) == 2
    assert len(templates) == 2
    with (out_dir / "randomization_key.csv").open(encoding="utf-8", newline="") as handle:
        key_rows = list(csv.DictReader(handle))
    assert len(key_rows) == 18
