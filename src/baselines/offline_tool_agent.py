"""Tool-routing agent without LLM calls (for offline benchmark runs)."""

from __future__ import annotations

import json
import re
from typing import Any

from src.agent.logging_utils import RunLogger
from src.agent.tools import AgentToolExecutor
from src.baselines.classifier_baseline import ClassifierBaseline, _extract_fields_from_question


class OfflineToolAgent:
    """Route benchmark questions to tools by category; format tool JSON as the answer."""

    def __init__(
        self,
        executor: AgentToolExecutor | None = None,
        classifier: ClassifierBaseline | None = None,
    ) -> None:
        self.executor = executor or AgentToolExecutor()
        self.classifier = classifier or ClassifierBaseline()

    def answer(
        self,
        question: str,
        logger: RunLogger | None = None,
        *,
        category: str = "",
    ) -> dict[str, Any]:
        logger = logger or RunLogger("agent")
        logger.log_question(question)

        if category == "classification" or "subunit_cd=" in question.lower():
            return self.classifier.answer(question, logger)

        if category == "case_grounded" or "similar to" in question.lower():
            query = _extract_retrieval_query(question)
            args = {"query": query, "top_k": 5}
            hits = self.executor.execute("search_narratives", args)
            logger.log_tool_call("search_narratives", args, hits)
            lines = [
                f"Document {h['document_no']} (score={h['score']}): {h['narrative'][:200]}"
                for h in hits
            ]
            answer = "Retrieved similar incidents:\n" + "\n".join(lines)
            logger.log_final_answer(answer, {})
            return {
                "answer": answer,
                "tools_used": ["search_narratives"],
                "usage": {},
                "log_path": str(logger.log_path),
            }

        if category == "trend" or question.lower().startswith("how many") or question.lower().startswith("compare"):
            tool_name, args, payload = self._trend_tool_call(question)
            logger.log_tool_call(tool_name, args, payload)
            answer = _format_trend_answer(question, payload)
            logger.log_final_answer(answer, {})
            return {
                "answer": answer,
                "tools_used": ["analyze_trends"],
                "usage": {},
                "log_path": str(logger.log_path),
            }

        answer = "Offline agent could not route this question to a tool."
        logger.log_final_answer(answer, {})
        return {"answer": answer, "tools_used": [], "usage": {}, "log_path": str(logger.log_path)}

    def _trend_tool_call(self, question: str) -> tuple[str, dict[str, Any], Any]:
        lower = question.lower()
        filters: dict[str, Any] = {}

        degree_hyphen = re.search(r"degree[- ]code[- ](\d{2})", lower)
        if degree_hyphen:
            filters["degree_code"] = degree_hyphen.group(1)
        elif "fatalit" in lower:
            filters["degree_code"] = "01"
        elif "degree code 02" in lower or "permanent disability" in lower:
            filters["degree_code"] = "02"

        if "coal mine" in lower:
            filters["coal_metal"] = "C"
        if "metal/non-metal" in lower:
            filters["coal_metal"] = "M"
        if " in texas" in lower:
            filters["state"] = "TX"
        if " in nevada" in lower:
            filters["state"] = "NV"
        if "handling-of-materials" in lower or "handling of materials" in lower:
            filters["classification"] = "HANDLING OF MATERIALS"
        if "powered haulage" in lower:
            filters["classification"] = "POWERED HAULAGE"
        if "fall of roof" in lower:
            filters["classification"] = "FALL OF ROOF OR BACK"
        if "roof bolter" in lower:
            filters["occupation"] = "Roof bolter"

        period_match = re.search(
            r"between\s+(\d{4})-(\d{4})\s+and\s+(\d{4})-(\d{4})",
            question,
            flags=re.IGNORECASE,
        )
        if period_match:
            a0, a1, b0, b1 = map(int, period_match.groups())
            args = {
                "query_type": "compare_periods",
                "filters": filters,
                "period_a_start": a0,
                "period_a_end": a1,
                "period_b_start": b0,
                "period_b_end": b1,
            }
            payload = self.executor.execute("analyze_trends", args)
            return "analyze_trends", args, payload

        year_match = re.search(r"\bin\s+(\d{4})\b", question)
        year = int(year_match.group(1)) if year_match else None
        args = {"query_type": "count_by_year", "filters": filters}
        payload = self.executor.execute("analyze_trends", args)
        return "analyze_trends", args, {"payload": payload, "target_year": year}


def _extract_retrieval_query(question: str) -> str:
    for prefix in ("similar to:", "similar to", "narrative snippet:"):
        idx = question.lower().find(prefix)
        if idx >= 0:
            return question[idx + len(prefix) :].strip()
    return question.strip()


def _format_trend_answer(question: str, payload: Any) -> str:
    if isinstance(payload, dict) and "target_year" in payload:
        rows = payload["payload"]["rows"]
        year = payload["target_year"]
        for row in rows:
            if int(row["CAL_YR"]) == year:
                return f"There were {row['injury_count']} matching MSHA injuries in {year}."
        return f"No count found for year {year}. Tool rows: {json.dumps(rows[-5:], ensure_ascii=False)}"

    rows = payload.get("rows", payload) if isinstance(payload, dict) else payload
    if isinstance(payload, dict) and payload.get("query_type") == "compare_periods":
        lines = []
        for row in payload["rows"]:
            lines.append(f"Period {row['period']}: {row['injury_count']} injuries")
        return "\n".join(lines)

    return json.dumps(payload, ensure_ascii=False)
