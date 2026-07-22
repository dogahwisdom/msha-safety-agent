"""Single-shot RAG baseline: retrieval + one LLM call, no tool orchestration (Step 6)."""

from __future__ import annotations

from typing import Any

from src.agent.logging_utils import RunLogger
from src.agent.llm_client import chat_completion_with_retry, get_llm_client, get_llm_model, llm_provider
from src.tools.retrieval import NarrativeRetriever

RAG_SYSTEM_PROMPT = """You answer mine safety questions using only the retrieved MSHA incident narratives provided.
If the narratives are insufficient, say so. Cite narrative document numbers you rely on.
For count or trend questions, state clearly that you only have narrative excerpts, not aggregate statistics.
"""


def _retrieval_query(question: str) -> str:
    lower = question.lower()
    for marker in ("similar to:", "similar to", "narrative snippet:"):
        if marker in lower:
            return question[lower.index(marker) + len(marker) :].strip()
    return question.strip()


class RAGBaseline:
    def __init__(
        self,
        retriever: NarrativeRetriever | None = None,
        model: str | None = None,
        top_k: int = 5,
    ) -> None:
        self.retriever = retriever or NarrativeRetriever()
        self._model = model
        self.top_k = top_k
        self._client = None

    @property
    def model(self) -> str:
        if self._model is None:
            self._model = get_llm_model()
        return self._model

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = get_llm_client()
        return self._client

    def answer(self, question: str, logger: RunLogger | None = None) -> dict[str, Any]:
        logger = logger or RunLogger("rag_baseline")
        logger.log_question(question)
        query = _retrieval_query(question)
        hits = self.retriever.search_as_dicts(query, top_k=self.top_k)
        logger.log_tool_call("search_narratives", {"query": query, "top_k": self.top_k}, hits)
        context = "\n\n".join(
            f"Document {h['document_no']} (score={h['score']}): {h['narrative']}" for h in hits
        )
        if llm_provider():
            response = chat_completion_with_retry(
                self.client,
                model=self.model,
                messages=[
                    {"role": "system", "content": RAG_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Question: {question}\n\nRetrieved narratives:\n{context}",
                    },
                ],
            )
            answer = response.choices[0].message.content or ""
            usage = response.usage
            usage_dict = {
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
            }
        else:
            if not hits:
                answer = "No similar narratives were retrieved."
            else:
                parts = [
                    f"Based on retrieved incidents, document {h['document_no']} (score={h['score']}): "
                    f"{h['narrative'][:250]}"
                    for h in hits[:3]
                ]
                answer = " ".join(parts)
            usage_dict = {}
        logger.log_final_answer(answer, usage_dict)
        return {
            "answer": answer,
            "tools_used": ["search_narratives"],
            "usage": usage_dict,
            "log_path": str(logger.log_path),
        }
