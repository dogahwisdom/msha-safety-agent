"""Single-shot RAG baseline: retrieval + one LLM call, no tool orchestration (Step 6)."""

from __future__ import annotations

from typing import Any

from src.agent.logging_utils import RunLogger
from src.agent.llm_client import get_llm_client, get_llm_model
from src.tools.retrieval import NarrativeRetriever

RAG_SYSTEM_PROMPT = """You answer mine safety questions using only the retrieved MSHA incident narratives provided.
If the narratives are insufficient, say so. Cite narrative document numbers you rely on.
"""


class RAGBaseline:
    def __init__(
        self,
        retriever: NarrativeRetriever | None = None,
        model: str | None = None,
        top_k: int = 5,
    ) -> None:
        self.retriever = retriever or NarrativeRetriever()
        self.model = model or get_llm_model()
        self.top_k = top_k
        self.client = get_llm_client()

    def answer(self, question: str, logger: RunLogger | None = None) -> dict[str, Any]:
        logger = logger or RunLogger("rag_baseline")
        logger.log_question(question)
        hits = self.retriever.search_as_dicts(question, top_k=self.top_k)
        logger.log_tool_call("search_narratives", {"query": question, "top_k": self.top_k}, hits)
        context = "\n\n".join(
            f"Document {h['document_no']} (score={h['score']}): {h['narrative']}" for h in hits
        )
        response = self.client.chat.completions.create(
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
        logger.log_final_answer(answer, usage_dict)
        return {
            "answer": answer,
            "tools_used": ["search_narratives"],
            "usage": usage_dict,
            "log_path": str(logger.log_path),
        }
