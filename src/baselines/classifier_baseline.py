"""Plain classifier baseline: structured classification only, no open-ended NL (Step 6)."""

from __future__ import annotations

import re
from typing import Any

from src.agent.logging_utils import RunLogger
from src.data.config import CLASSIFIER_FEATURE_COLUMNS
from src.tools.classifier import InjuryRiskClassifier


CODE_PATTERN = re.compile(r"\b(0[1-9]|10)\b")

_FIELD_ALIASES = {
    "subunit_cd": "SUBUNIT_CD",
    "classification_cd": "CLASSIFICATION_CD",
    "occupation_cd": "OCCUPATION_CD",
    "activity_cd": "ACTIVITY_CD",
    "injury_source_cd": "INJURY_SOURCE_CD",
    "nature_injury_cd": "NATURE_INJURY_CD",
    "inj_body_part_cd": "INJ_BODY_PART_CD",
    "mining_equip_cd": "MINING_EQUIP_CD",
    "coal_metal_ind": "COAL_METAL_IND",
    "accident_type_cd": "ACCIDENT_TYPE_CD",
}


class ClassifierBaseline:
    """Answers every benchmark question using only the injury-risk classifier."""

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

        import pandas as pd

        fields, source = _fields_for_question(question)
        frame = pd.DataFrame([fields])
        prediction = self.classifier.predict(frame)[0]
        answer = (
            f"Classifier-only baseline ({source}): predicted injury degree code {prediction}. "
            "This baseline has no trend or retrieval tools; count and case-similarity "
            "questions are answered with a single severity prediction only."
        )
        logger.log_tool_call("classify_injury_risk", fields, {"prediction": str(prediction)})
        logger.log_final_answer(answer, {})
        return {
            "answer": answer,
            "tools_used": ["classify_injury_risk"],
            "usage": {},
            "log_path": str(logger.log_path),
        }


def _extract_fields_from_question(question: str) -> dict[str, str]:
    """Parse explicit field codes from patterns like subunit_cd=01."""
    found: dict[str, str] = {}
    lower = question.lower()
    for key in _FIELD_ALIASES:
        match = re.search(rf"{key}\s*[=:]\s*(\w+)", lower)
        if match:
            found[_FIELD_ALIASES[key]] = match.group(1).upper()
    return found


def _infer_defaults_from_text(question: str) -> dict[str, str]:
    """Best-effort structured defaults when the question has no explicit codes."""
    lower = question.lower()
    defaults = {column: "UNK" for column in CLASSIFIER_FEATURE_COLUMNS}
    defaults["MINING_EQUIP_CD"] = "UNK"
    defaults["COAL_METAL_IND"] = "M"
    defaults["ACCIDENT_TYPE_CD"] = "99"

    if "coal mine" in lower or "coal mines" in lower:
        defaults["COAL_METAL_IND"] = "C"
    if "metal/non-metal" in lower or "metal mine" in lower:
        defaults["COAL_METAL_IND"] = "M"

    if "roof bolter" in lower:
        defaults["OCCUPATION_CD"] = "345"
    if "handling-of-materials" in lower or "handling of materials" in lower:
        defaults["CLASSIFICATION_CD"] = "31"

    degree_match = re.search(r"degree[- ]code[- ]?(\d{2})", lower)
    if degree_match:
        defaults["SUBUNIT_CD"] = "03"
    elif "fatalit" in lower:
        defaults["SUBUNIT_CD"] = "03"

    return defaults


def _fields_for_question(question: str) -> tuple[dict[str, str], str]:
    extracted = _extract_fields_from_question(question)
    if len(extracted) >= 8:
        extracted.setdefault("MINING_EQUIP_CD", "UNK")
        return extracted, "structured field codes from question"

    if extracted:
        merged = _infer_defaults_from_text(question)
        merged.update(extracted)
        merged.setdefault("MINING_EQUIP_CD", "UNK")
        return merged, "partial field codes plus inferred defaults"

    defaults = _infer_defaults_from_text(question)
    return defaults, "inferred defaults only"
