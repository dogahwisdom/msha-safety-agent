"""CLI entry point for training and evaluating the injury risk classifier."""

from __future__ import annotations

import argparse

from src.tools.classifier import print_evaluation_report, train_and_evaluate


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and evaluate the MSHA injury risk classifier.")
    parser.add_argument(
        "--include-mine-context",
        action="store_true",
        help="Add mine context columns from the Mines join to classifier inputs.",
    )
    args = parser.parse_args()
    report = train_and_evaluate(include_mine_context=args.include_mine_context)
    print_evaluation_report(report)


if __name__ == "__main__":
    main()
