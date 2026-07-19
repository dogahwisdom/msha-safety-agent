"""Plain classifier baseline: structured classification only, no open-ended NL (Step 6)."""

from __future__ import annotations

import re
from typing import Any

from src.agent.logging_utils import RunLogger
from src.tools.classifier import InjuryRiskClassifier


CODE_PATTERN = re.compile(r"\b(0[1-9]|10)\b")


class ClassifierBaseline:
    """Answers only by extracting structured fields from the question and classifying."""

    def __init__(self, classifier: InjuryRiskClassifier | None = None) -> None:
        self._classifier = classifier

    @property
    def classifier(self) -> InjuryRiskClassifier:
        if self._classifier is None:
            self._classifier = InjuryRiskClassifier.load()
        return self._classifier

    def answer(self, question: str, logger: RunLogger | None = None) -> dict[str, Any]:
        logger = logger or RunLogger("classifier_baseline")
        logger.log_question(question)
        fields = _extract_fields_from_question(question)
        if not fields:
            answer = (
                "This baseline only handles classification-style questions with explicit "
                "structured MSHA field codes in the question text."
            )
            logger.log_final_answer(answer, {})
            return {"answer": answer, "tools_used": [], "usage": {}, "log_path": str(logger.log_path)}

        import pandas as pd

        frame = pd.DataFrame([fields])
        prediction = self.classifier.predict(frame)[0]
        answer = f"Predicted injury degree code: {prediction}"
        logger.log_tool_call("classify_injury_risk", fields, {"prediction": str(prediction)})
        logger.log_final_answer(answer, {})
        return {
            "answer": answer,
            "tools_used": ["classify_injury_risk"],
            "usage": {},
            "log_path": str(logger.log_path),
        }


def _extract_fields_from_question(question: str) -> dict[str, str] | None:
    """Parse field codes if present in patterns like subunit_cd=01."""
    keys = [
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
    ]
    found: dict[str, str] = {}
    lower = question.lower()
    for key in keys:
        match = re.search(rf"{key}\s*[=:]\s*(\w+)", lower)
        if match:
            found[key.upper()] = match.group(1).upper()
    if len(found) < 8:
        return None
    found.setdefault("MINING_EQUIP_CD", "UNK")
    return found
