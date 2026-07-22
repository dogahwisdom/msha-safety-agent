"""Run agent and baselines on the benchmark (Step 8)."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.agent.llm_client import llm_provider
from src.agent.logging_utils import RunLogger
from src.agent.orchestrator import MSHASafetyAgent
from src.baselines.classifier_baseline import ClassifierBaseline
from src.baselines.offline_tool_agent import OfflineToolAgent
from src.baselines.rag_baseline import RAGBaseline

BENCHMARK_DIR = _ROOT / "benchmark"
RESULTS_DIR = Path(__file__).resolve().parent / "results"


def _load_questions() -> list[dict[str, Any]]:
    payload = json.loads((BENCHMARK_DIR / "questions.json").read_text(encoding="utf-8"))
    return payload["questions"]


def _checkpoint_path() -> Path | None:
    raw = os.environ.get("BENCHMARK_CHECKPOINT", "").strip()
    return Path(raw) if raw else None


def _load_checkpoint() -> set[tuple[str, str]]:
    path = _checkpoint_path()
    if path is None or not path.exists():
        return set()
    done: set[tuple[str, str]] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        done.add((row["system"], row["question_id"]))
    return done


def _append_checkpoint(row: dict[str, Any]) -> None:
    path = _checkpoint_path()
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()


def _run_system(
    name: str,
    answer_fn: Callable[..., dict[str, Any]],
    questions: list[dict],
    *,
    pass_category: bool = False,
) -> list[dict]:
    done = _load_checkpoint()
    rows = []
    for item in questions:
        if (name, item["id"]) in done:
            continue
        logger = RunLogger(name, log_dir=RESULTS_DIR / "logs")
        start = time.time()
        try:
            if pass_category:
                result = answer_fn(item["question"], logger, category=item["category"])
            else:
                result = answer_fn(item["question"], logger)
            error = None
        except Exception as exc:  # noqa: BLE001 - benchmark runner must capture failures
            result = {"answer": "", "tools_used": [], "usage": {}, "log_path": str(logger.log_path)}
            error = str(exc)
        latency_s = round(time.time() - start, 3)
        row = {
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
        rows.append(row)
        _append_checkpoint(row)
    return rows


def _systems() -> dict[str, tuple[Callable[..., dict[str, Any]], bool]]:
    provider = llm_provider()
    if provider:
        agent = MSHASafetyAgent()
        classifier = ClassifierBaseline()
        rag = RAGBaseline()
        systems = {
            "agent": (lambda q, lg, category="": agent.answer(q, logger=lg), False),
            "classifier_baseline": (lambda q, lg, category="": classifier.answer(q, logger=lg), False),
            "rag_baseline": (lambda q, lg, category="": rag.answer(q, logger=lg), False),
        }
    else:
        offline = OfflineToolAgent()
        classifier = ClassifierBaseline()
        rag = RAGBaseline()
        systems = {
            "agent": (lambda q, lg, category="": offline.answer(q, logger=lg, category=category), True),
            "classifier_baseline": (lambda q, lg, category="": classifier.answer(q, logger=lg), False),
            "rag_baseline": (lambda q, lg, category="": rag.answer(q, logger=lg), False),
        }

    only = os.environ.get("BENCHMARK_SYSTEMS", "").strip()
    if only:
        names = {part.strip() for part in only.split(",") if part.strip()}
        unknown = names - set(systems)
        if unknown:
            raise ValueError(f"Unknown BENCHMARK_SYSTEMS entries: {sorted(unknown)}")
        systems = {name: systems[name] for name in systems if name in names}
    return systems


def run_all() -> dict[str, Any]:
    questions = _load_questions()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    mode = llm_provider() or "offline_tools"
    all_rows: list[dict] = []
    for name, (fn, pass_category) in _systems().items():
        all_rows.extend(_run_system(name, fn, questions, pass_category=pass_category))
    out_name = os.environ.get("BENCHMARK_OUTPUT", "benchmark_runs.json")
    out_path = RESULTS_DIR / out_name
    payload = {
        "questions": len(questions),
        "mode": mode,
        "results": all_rows,
    }
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    return {"output": str(out_path), "mode": mode, "result_count": len(all_rows)}


if __name__ == "__main__":
    summary = run_all()
    print(json.dumps(summary, indent=2))
