"""Tool wrappers and OpenAI function schemas for the agent."""

from __future__ import annotations

import json
from typing import Any

from src.tools.classifier import InjuryRiskClassifier
from src.tools.retrieval import NarrativeRetriever
from src.tools.trends import TrendAnalyzer

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "classify_injury_risk",
            "description": "Predict MSHA injury degree class from structured fields.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subunit_cd": {"type": "string"},
                    "classification_cd": {"type": "string"},
                    "occupation_cd": {"type": "string"},
                    "activity_cd": {"type": "string"},
                    "injury_source_cd": {"type": "string"},
                    "nature_injury_cd": {"type": "string"},
                    "inj_body_part_cd": {"type": "string"},
                    "mining_equip_cd": {"type": "string"},
                    "coal_metal_ind": {"type": "string"},
                    "accident_type_cd": {"type": "string"},
                },
                "required": [
                    "subunit_cd",
                    "classification_cd",
                    "occupation_cd",
                    "activity_cd",
                    "injury_source_cd",
                    "nature_injury_cd",
                    "inj_body_part_cd",
                    "mining_equip_cd",
                    "coal_metal_ind",
                    "accident_type_cd",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_trends",
            "description": "Run a trend query over MSHA records.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "enum": ["count_by_year", "year_over_year_change", "count_by_group", "compare_periods"],
                    },
                    "filters": {"type": "object"},
                    "group_column": {"type": "string"},
                    "top_n": {"type": "integer"},
                    "period_a_start": {"type": "integer"},
                    "period_a_end": {"type": "integer"},
                    "period_b_start": {"type": "integer"},
                    "period_b_end": {"type": "integer"},
                },
                "required": ["query_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_narratives",
            "description": "Semantic search over historical injury narratives.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
]


class AgentToolExecutor:
    """Execute agent tools against trained classifier, trend analyzer, and retriever."""

    def __init__(
        self,
        classifier: InjuryRiskClassifier | None = None,
        trends: TrendAnalyzer | None = None,
        retriever: NarrativeRetriever | None = None,
    ) -> None:
        self.classifier = classifier or InjuryRiskClassifier.load()
        self.trends = trends or TrendAnalyzer()
        self.retriever = retriever or NarrativeRetriever()

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        if tool_name == "classify_injury_risk":
            row = {k.upper(): v for k, v in arguments.items()}
            frame = _single_row_frame(row)
            prediction = self.classifier.predict(frame)[0]
            return {"predicted_degree_code": str(prediction)}

        if tool_name == "analyze_trends":
            query_type = arguments["query_type"]
            filters = arguments.get("filters") or {}
            if query_type == "count_by_year":
                result = self.trends.count_by_year(filters)
            elif query_type == "year_over_year_change":
                result = self.trends.year_over_year_change(filters)
            elif query_type == "count_by_group":
                result = self.trends.count_by_group(
                    arguments.get("group_column", "STATE"),
                    filters,
                    top_n=arguments.get("top_n"),
                )
            elif query_type == "compare_periods":
                result = self.trends.compare_periods(
                    (arguments["period_a_start"], arguments["period_a_end"]),
                    (arguments["period_b_start"], arguments["period_b_end"]),
                    filters,
                )
            else:
                raise ValueError(f"Unknown query_type: {query_type}")
            return result.to_dict()

        if tool_name == "search_narratives":
            return self.retriever.search_as_dicts(
                arguments["query"],
                top_k=int(arguments.get("top_k", 5)),
            )

        raise ValueError(f"Unknown tool: {tool_name}")


def _single_row_frame(row: dict[str, str]) -> Any:
    import pandas as pd

    mapping = {
        "SUBUNIT_CD": row.get("SUBUNIT_CD", ""),
        "CLASSIFICATION_CD": row.get("CLASSIFICATION_CD", ""),
        "OCCUPATION_CD": row.get("OCCUPATION_CD", ""),
        "ACTIVITY_CD": row.get("ACTIVITY_CD", ""),
        "INJURY_SOURCE_CD": row.get("INJURY_SOURCE_CD", ""),
        "NATURE_INJURY_CD": row.get("NATURE_INJURY_CD", ""),
        "INJ_BODY_PART_CD": row.get("INJ_BODY_PART_CD", ""),
        "MINING_EQUIP_CD": row.get("MINING_EQUIP_CD", "UNK"),
        "COAL_METAL_IND": row.get("COAL_METAL_IND", ""),
        "ACCIDENT_TYPE_CD": row.get("ACCIDENT_TYPE_CD", ""),
        "DEGREE_INJURY_CD": "06",
    }
    return pd.DataFrame([mapping])
