"""Score benchmark runs against reference answers (Step 9)."""

from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

RESULTS_PATH = Path(__file__).resolve().parent / "results" / os.environ.get("BENCHMARK_OUTPUT", "benchmark_runs.json")
REFERENCES_PATH = Path(__file__).resolve().parents[1] / "benchmark" / "reference_answers.json"
_scores_name = os.environ.get("SCORES_OUTPUT")
if not _scores_name:
    _bench = os.environ.get("BENCHMARK_OUTPUT", "benchmark_runs.json")
    _scores_name = "scores.json" if _bench == "benchmark_runs.json" else _bench.replace("benchmark_runs", "scores").replace(".json", ".json")
SCORES_PATH = Path(__file__).resolve().parent / "results" / _scores_name
FAILURES_PATH = Path(__file__).resolve().parent / "results" / _scores_name.replace("scores", "failure_cases")


def _extract_number(text: str) -> int | None:
    matches = re.findall(r"\b(\d{1,6})\b", text.replace(",", ""))
    return int(matches[0]) if matches else None


def _score_row(row: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    answer = row.get("answer", "")
    ref_type = reference.get("type")
    correct = False
    reason = ""

    if ref_type == "degree_code":
        expected = reference["value"]
        found = re.findall(r"\b(0[1-9]|10)\b", answer)
        correct = expected in found
        reason = "missing expected degree code" if not correct else "degree code matched"

    elif ref_type == "count":
        expected = int(reference["value"])
        predicted = _extract_number(answer)
        correct = predicted == expected
        reason = f"expected {expected}, got {predicted}"

    elif ref_type == "period_compare":
        # Accept if both period totals appear in answer within +/- 5%
        counts = [int(r["injury_count"]) for r in reference["counts"]]
        nums = [int(x) for x in re.findall(r"\b(\d{1,6})\b", answer.replace(",", ""))]
        correct = all(any(abs(n - c) <= max(1, int(0.05 * c)) for n in nums) for c in counts)
        reason = "period totals not found within tolerance" if not correct else "period totals matched"

    elif ref_type == "document_set":
        docs = reference.get("document_numbers", [])
        must = reference.get("must_include")
        if must:
            correct = must in answer
            reason = f"must include document {must}"
        else:
            correct = any(doc in answer for doc in docs[:3])
            reason = "top retrieved document not cited" if not correct else "document cited"

    else:
        reason = "unknown reference type"

    tool_expected = set()
    tools_used = set(row.get("tools_used") or [])
    tool_correct = True  # filled by caller with expected tools list

    return {
        "correct": correct,
        "reason": reason,
        "tools_used": list(tools_used),
        "tool_correct": tool_correct,
    }


def score_results() -> dict[str, Any]:
    runs = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))["results"]
    references = json.loads(REFERENCES_PATH.read_text(encoding="utf-8"))
    questions_path = Path(__file__).resolve().parents[1] / "benchmark" / "questions.json"
    questions = {q["id"]: q for q in json.loads(questions_path.read_text(encoding="utf-8"))["questions"]}

    scored = []
    failures = []
    for row in runs:
        ref = references[row["question_id"]]
        qmeta = questions[row["question_id"]]
        expected_tools = set(qmeta.get("expected_tools", []))
        score = _score_row(row, ref)
        if row["system"] == "agent":
            score["tool_correct"] = bool(expected_tools.intersection(score["tools_used"]))
        elif row["system"] == "classifier_baseline":
            score["tool_correct"] = "classify_injury_risk" in score["tools_used"]
        elif row["system"] == "rag_baseline":
            score["tool_correct"] = "search_narratives" in score["tools_used"]
        else:
            score["tool_correct"] = set(score["tools_used"]) == expected_tools
        record = {**row, **score, "reference": ref, "expected_tools": list(expected_tools)}
        scored.append(record)
        if not score["correct"] or row.get("error"):
            failures.append(
                {
                    "question_id": row["question_id"],
                    "system": row["system"],
                    "category": row["category"],
                    "reason": score["reason"],
                    "error": row.get("error"),
                    "answer_excerpt": row.get("answer", "")[:300],
                }
            )

    by_system_category: dict[str, dict[str, list[bool]]] = defaultdict(lambda: defaultdict(list))
    tool_correct_counts: dict[str, list[bool]] = defaultdict(list)
    latency_by_system: dict[str, list[float]] = defaultdict(list)
    tokens_by_system: dict[str, list[int]] = defaultdict(list)

    for row in scored:
        by_system_category[row["system"]][row["category"]].append(row["correct"])
        tool_correct_counts[row["system"]].append(row["tool_correct"])
        latency_by_system[row["system"]].append(float(row.get("latency_s", 0)))
        usage = row.get("usage") or {}
        tokens_by_system[row["system"]].append(int(usage.get("total_tokens", 0)))

    summary = {"by_system_category": {}, "tool_selection": {}, "latency_cost": {}}
    for system, cats in by_system_category.items():
        summary["by_system_category"][system] = {
            cat: {
                "accuracy": round(sum(vals) / len(vals), 4) if vals else 0.0,
                "n": len(vals),
            }
            for cat, vals in cats.items()
        }
        all_vals = [v for vals in cats.values() for v in vals]
        summary["by_system_category"][system]["overall"] = {
            "accuracy": round(sum(all_vals) / len(all_vals), 4) if all_vals else 0.0,
            "n": len(all_vals),
        }
        summary["tool_selection"][system] = {
            "correct_rate": round(sum(tool_correct_counts[system]) / len(tool_correct_counts[system]), 4),
            "n": len(tool_correct_counts[system]),
        }
        lat = latency_by_system[system]
        tok = tokens_by_system[system]
        summary["latency_cost"][system] = {
            "mean_latency_s": round(sum(lat) / len(lat), 3) if lat else 0,
            "mean_tokens": round(sum(tok) / len(tok), 1) if tok else 0,
            "total_tokens": int(sum(tok)),
        }

    SCORES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SCORES_PATH.open("w", encoding="utf-8") as handle:
        json.dump({"summary": summary, "rows": scored}, handle, indent=2, ensure_ascii=False)
    with FAILURES_PATH.open("w", encoding="utf-8") as handle:
        json.dump(failures, handle, indent=2, ensure_ascii=False)
    return {"summary": summary, "failures": len(failures)}


if __name__ == "__main__":
    print(json.dumps(score_results(), indent=2))
