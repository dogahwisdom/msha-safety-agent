"""CLI to run a single agent question with full logging."""

from __future__ import annotations

import argparse
import json

from src.agent.orchestrator import MSHASafetyAgent


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the MSHA safety agent on one question.")
    parser.add_argument("question", type=str, help="Natural language question")
    args = parser.parse_args()
    agent = MSHASafetyAgent()
    result = agent.answer(args.question)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
