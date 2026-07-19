"""Summary statistics for ingestion output."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.data.config import CLASSIFIER_TARGET_COLUMN


def degree_distribution(frame: pd.DataFrame) -> dict[str, int]:
    """Count records per DEGREE_INJURY_CD with human-readable labels when available."""
    counts = frame[CLASSIFIER_TARGET_COLUMN].value_counts().sort_index()
    labels = frame.groupby(CLASSIFIER_TARGET_COLUMN)["DEGREE_INJURY"].first()
    return {
        str(code): {
            "count": int(counts[code]),
            "label": str(labels.get(code, "")),
        }
        for code in counts.index
    }


def year_distribution(frame: pd.DataFrame) -> dict[str, int]:
    """Count records per calendar year."""
    return {str(k): int(v) for k, v in frame["CAL_YR"].value_counts().sort_index().items()}


def build_summary(
    raw_accident_rows: int,
    raw_mine_rows: int,
    cleaning_log: list[dict],
    join_info: dict,
    split_info: dict,
    train: pd.DataFrame,
    test: pd.DataFrame,
    cleaned: pd.DataFrame,
) -> dict:
    """Assemble a JSON-serializable summary of the ingestion pipeline."""
    return {
        "raw": {
            "accident_rows": raw_accident_rows,
            "mine_rows": raw_mine_rows,
        },
        "cleaning_log": cleaning_log,
        "cleaned_rows": len(cleaned),
        "join": join_info,
        "split": split_info,
        "class_distribution": {
            "cleaned": degree_distribution(cleaned),
            "train": degree_distribution(train),
            "test": degree_distribution(test),
        },
        "year_range": {
            "min": int(cleaned["CAL_YR"].min()),
            "max": int(cleaned["CAL_YR"].max()),
        },
        "year_distribution_cleaned": year_distribution(cleaned),
    }


def print_summary(summary: dict) -> None:
    """Print human-readable summary statistics to stdout."""
    print("\n=== MSHA Data Ingestion Summary ===\n")
    print(f"Raw accident rows:     {summary['raw']['accident_rows']:,}")
    print(f"Raw mine rows:         {summary['raw']['mine_rows']:,}")
    print(f"Cleaned rows:          {summary['cleaned_rows']:,}")
    print(f"Train rows:            {summary['split']['train_rows']:,}")
    print(f"Test rows:             {summary['split']['test_rows']:,}")
    print(f"Year range (cleaned):  {summary['year_range']['min']} to {summary['year_range']['max']}")
    print(f"Mine join matched:     {summary['join']['matched_mine_rows']:,}")
    print(f"Mine join unmatched:   {summary['join']['unmatched_mine_rows']:,}")

    print("\n--- Cleaning steps ---")
    for step in summary["cleaning_log"]:
        if "rows_removed" in step:
            print(
                f"  {step['step']}: {step['rows_after']:,} rows remain "
                f"({step['rows_removed']:,} removed)"
            )
        elif "rows_imputed" in step:
            print(f"  {step['step']}: {step['rows_imputed']:,} values imputed")

    print("\n--- Class distribution (cleaned) ---")
    for code, info in sorted(summary["class_distribution"]["cleaned"].items()):
        label = info["label"]
        print(f"  {code} ({label}): {info['count']:,}")

    print("\n--- Class distribution (train / test) ---")
    train_dist = summary["class_distribution"]["train"]
    test_dist = summary["class_distribution"]["test"]
    for code in sorted(summary["class_distribution"]["cleaned"].keys()):
        train_n = train_dist.get(code, {}).get("count", 0)
        test_n = test_dist.get(code, {}).get("count", 0)
        label = summary["class_distribution"]["cleaned"][code]["label"]
        print(f"  {code} ({label}): train={train_n:,}, test={test_n:,}")


def save_summary(summary: dict, path: Path) -> None:
    """Write summary JSON to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
