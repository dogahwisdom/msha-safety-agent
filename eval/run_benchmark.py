"""Run agent and baselines on the benchmark (Step 8)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable

from src.agent.logging_utils import RunLogger
from src.agent.orchestrator import MSHASafetyAgent
from src.baselines.classifier_baseline import ClassifierBaseline
from src.baselines.rag_baseline import RAGBaseline

BENCHMARK_DIR = Path(__file__).resolve().parents[1] / "benchmark"
RESULTS_DIR = Path(__file__).resolve().parent / "results"


def _load_questions() -> list[dict[str, Any]]:
    payload = json.loads((BENCHMARK_DIR / "questions.json").read_text(encoding="utf-8"))
    return payload["questions"]


def _run_system(name: str, answer_fn: Callable[[str, RunLogger], dict[str, Any]], questions: list[dict]) -> list[dict]:
    rows = []
    for item in questions:
        logger = RunLogger(name, log_dir=RESULTS_DIR / "logs")
        start = time.time()
        try:
            result = answer_fn(item["question"], logger)
            error = None
        except Exception as exc:  # noqa: BLE001 - benchmark runner must capture failures
            result = {"answer": "", "tools_used": [], "usage": {}, "log_path": str(logger.log_path)}
            error = str(exc)
        latency_s = round(time.time() - start, 3)
        rows.append(
            {
                "question_id": item["id"],
                "category": item["category"],
                "question": item["question"],
                "system": name,
                "answer": result.get("answer", ""),
                "tools_used": result.get("tools_used", []),
                "usage": result.get("usage", {}),
                "latency_s": latency_s,
                "log_path": result.get("log_path"),
                "error": error,
            }
        )
    return rows


def run_all() -> dict[str, Any]:
    questions = _load_questions()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    systems = {
        "agent": lambda q, lg: MSHASafetyAgent().answer(q, logger=lg),
        "classifier_baseline": lambda q, lg: ClassifierBaseline().answer(q, logger=lg),
        "rag_baseline": lambda q, lg: RAGBaseline().answer(q, logger=lg),
    }
    all_rows: list[dict] = []
    for name, fn in systems.items():
        all_rows.extend(_run_system(name, fn, questions))
    out_path = RESULTS_DIR / "benchmark_runs.json"
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump({"questions": len(questions), "results": all_rows}, handle, indent=2, ensure_ascii=False)
    return {"output": str(out_path), "result_count": len(all_rows)}


if __name__ == "__main__":
    summary = run_all()
    print(json.dumps(summary, indent=2))
