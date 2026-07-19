"""Framework-free LLM orchestrator with native function calling (Step 5)."""

from __future__ import annotations

import json
from typing import Any

from src.agent.llm_client import get_llm_client, get_llm_model
from src.agent.logging_utils import RunLogger
from src.agent.prompts import SYSTEM_PROMPT
from src.agent.tools import TOOL_SCHEMAS, AgentToolExecutor


class MSHASafetyAgent:
    """Tool-augmented agent loop using OpenAI-compatible function calling."""

    def __init__(
        self,
        model: str | None = None,
        tool_executor: AgentToolExecutor | None = None,
        max_tool_rounds: int = 6,
    ) -> None:
        self.client = get_llm_client()
        self.model = model or get_llm_model()
        self.tool_executor = tool_executor or AgentToolExecutor()
        self.max_tool_rounds = max_tool_rounds

    def answer(self, question: str, logger: RunLogger | None = None) -> dict[str, Any]:
        logger = logger or RunLogger("agent")
        logger.log_question(question)
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]
        total_usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        tools_used: list[str] = []

        for _ in range(self.max_tool_rounds):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
            )
            usage = response.usage
            if usage:
                total_usage["prompt_tokens"] += usage.prompt_tokens or 0
                total_usage["completion_tokens"] += usage.completion_tokens or 0
                total_usage["total_tokens"] += usage.total_tokens or 0

            message = response.choices[0].message
            if message.content:
                logger.log_reasoning(message.content)

            tool_calls = message.tool_calls or []
            if not tool_calls:
                final = message.content or ""
                logger.log_final_answer(final, total_usage)
                return {
                    "answer": final,
                    "tools_used": tools_used,
                    "usage": total_usage,
                    "log_path": str(logger.log_path),
                }

            messages.append(message.model_dump())
            for call in tool_calls:
                tool_name = call.function.name
                arguments = json.loads(call.function.arguments or "{}")
                result = self.tool_executor.execute(tool_name, arguments)
                tools_used.append(tool_name)
                logger.log_tool_call(tool_name, arguments, result)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

        fallback = "Unable to produce a final answer within the tool call limit."
        logger.log_final_answer(fallback, total_usage)
        return {
            "answer": fallback,
            "tools_used": tools_used,
            "usage": total_usage,
            "log_path": str(logger.log_path),
        }
