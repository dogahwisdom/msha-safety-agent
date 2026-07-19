"""Tests for narrative retrieval (Step 4)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pytest

from src.tools.retrieval import (
    CHROMA_DIR,
    EMBEDDING_MODEL_NAME,
    RETRIEVAL_META_JSON,
    NarrativeRetriever,
)


@pytest.fixture
def tiny_retriever(tmp_path) -> NarrativeRetriever:
    persist = tmp_path / "chroma"
    retriever = NarrativeRetriever(persist_dir=persist)
    frame = pd.DataFrame(
        [
            {
                "DOCUMENT_NO": "doc1",
                "NARRATIVE": "Miner struck by falling rock in underground coal mine roof fall.",
                "MINE_ID": "0100001",
                "CAL_YR": "2018",
                "OCCUPATION": "Roof bolter",
                "NATURE_INJURY": "FRACTURE",
                "CLASSIFICATION": "FALL OF ROOF",
                "DEGREE_INJURY": "DAYS AWAY FROM WORK ONLY",
                "STATE": "WV",
            },
            {
                "DOCUMENT_NO": "doc2",
                "NARRATIVE": "Electrician received electrical shock from damaged cable on continuous miner.",
                "MINE_ID": "0100002",
                "CAL_YR": "2019",
                "OCCUPATION": "Electrician",
                "NATURE_INJURY": "ELECTRIC SHOCK",
                "CLASSIFICATION": "POWERED HAULAGE",
                "DEGREE_INJURY": "NO DYS AWY FRM WRK,NO RSTR ACT",
                "STATE": "KY",
            },
            {
                "DOCUMENT_NO": "doc3",
                "NARRATIVE": "Haul truck operator caught between equipment and rib while backing up.",
                "MINE_ID": "0100003",
                "CAL_YR": "2020",
                "OCCUPATION": "Haul truck operator",
                "NATURE_INJURY": "CRUSHING",
                "CLASSIFICATION": "POWERED HAULAGE",
                "DEGREE_INJURY": "FATALITY",
                "STATE": "NV",
            },
        ]
    )
    retriever.build_index(frame)
    return retriever


def test_build_and_search_tiny_index(tiny_retriever: NarrativeRetriever) -> None:
    results = tiny_retriever.search("falling rock roof underground", top_k=2)
    assert len(results) >= 1
    assert results[0].document_no == "doc1"
    assert "rock" in results[0].narrative.lower()


def test_embedding_model_documented() -> None:
    assert EMBEDDING_MODEL_NAME == "sentence-transformers/all-MiniLM-L6-v2"


@pytest.mark.slow
def test_full_index_search_hand_checked_queries() -> None:
    if not RETRIEVAL_META_JSON.exists():
        pytest.skip("Run python -m src.tools.run_retrieval_index first")
    retriever = NarrativeRetriever()
    queries = [
        ("roof fall underground coal miner", ["roof", "fall"]),
        ("electrical shock cable miner", ["shock", "electric"]),
        ("haul truck backed into rib", ["truck", "haul"]),
        ("explosion methane ignition", ["explosion", "methane", "ignition"]),
        ("ladder fall from height surface mine", ["ladder", "fall"]),
    ]
    judgments = []
    for query, keywords in queries:
        hits = retriever.search(query, top_k=3)
        assert len(hits) == 3
        top = hits[0].narrative.lower()
        relevant = any(word in top for word in keywords)
        judgments.append({"query": query, "relevant": relevant, "top_narrative": hits[0].narrative[:120]})
    # At least 4 of 5 top results should contain a query-related keyword (hand-checked threshold).
    relevant_count = sum(1 for j in judgments if j["relevant"])
    assert relevant_count >= 4, judgments
