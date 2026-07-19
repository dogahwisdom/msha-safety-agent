"""Structured logging for agent and baseline runs."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

DEFAULT_LOG_DIR = Path(__file__).resolve().parents[2] / "eval" / "logs"


class RunLogger:
    """Append-only JSONL logger for tool calls, reasoning steps, and final answers."""

    def __init__(self, system_name: str, log_dir: Path | None = None) -> None:
        self.system_name = system_name
        self.log_dir = log_dir or DEFAULT_LOG_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.run_id = f"{system_name}_{uuid.uuid4().hex[:12]}"
        self.log_path = self.log_dir / f"{self.run_id}.jsonl"
        self.started_at = time.time()

    def log(self, event_type: str, payload: dict[str, Any]) -> None:
        record = {
            "run_id": self.run_id,
            "system": self.system_name,
            "event_type": event_type,
            "timestamp": time.time(),
            "elapsed_s": round(time.time() - self.started_at, 3),
            **payload,
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def log_question(self, question: str) -> None:
        self.log("question", {"question": question})

    def log_tool_call(self, tool_name: str, arguments: dict[str, Any], result: Any) -> None:
        self.log(
            "tool_call",
            {"tool_name": tool_name, "arguments": arguments, "result": result},
        )

    def log_reasoning(self, content: str) -> None:
        self.log("reasoning", {"content": content})

    def log_final_answer(self, answer: str, usage: dict[str, Any] | None = None) -> None:
        self.log("final_answer", {"answer": answer, "usage": usage or {}})
