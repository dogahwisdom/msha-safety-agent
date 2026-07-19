"""RAG baseline without LLM: retrieval plus formatted narrative excerpts."""

from __future__ import annotations

import re
from typing import Any

from src.agent.logging_utils import RunLogger
from src.tools.retrieval import NarrativeRetriever


class RetrievalOnlyBaseline:
    """Returns top retrieved narratives without an LLM synthesis step."""

    def __init__(self, retriever: NarrativeRetriever | None = None, top_k: int = 5) -> None:
        self.retriever = retriever or NarrativeRetriever()
        self.top_k = top_k

    def answer(self, question: str, logger: RunLogger | None = None) -> dict[str, Any]:
        logger = logger or RunLogger("rag_baseline")
        logger.log_question(question)
        query = _extract_query(question)
        hits = self.retriever.search_as_dicts(query, top_k=self.top_k)
        logger.log_tool_call("search_narratives", {"query": query, "top_k": self.top_k}, hits)
        if not hits:
            answer = "No similar narratives were retrieved."
        else:
            parts = [
                f"Based on retrieved incidents, document {h['document_no']} (score={h['score']}): "
                f"{h['narrative'][:250]}"
                for h in hits[:3]
            ]
            answer = " ".join(parts)
        logger.log_final_answer(answer, {})
        return {
            "answer": answer,
            "tools_used": ["search_narratives"],
            "usage": {},
            "log_path": str(logger.log_path),
        }


def _extract_query(question: str) -> str:
    lower = question.lower()
    for marker in ("similar to:", "similar to", "narrative snippet:"):
        if marker in lower:
            return question[lower.index(marker) + len(marker) :].strip()
    return question.strip()
