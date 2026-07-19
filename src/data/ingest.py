"""Main entry point for MSHA data ingestion."""

from __future__ import annotations

import argparse

from src.data.clean import clean_accidents, clean_mines, join_accidents_mines
from src.data.config import (
    ACCIDENTS_CLEAN_CSV,
    MINES_CLEAN_CSV,
    SUMMARY_JSON,
    TEST_CSV,
    TRAIN_CSV,
)
from src.data.download import ensure_raw_data
from src.data.load import load_accidents, load_mines
from src.data.split import stratified_train_test_split
from src.data.summary import build_summary, print_summary, save_summary


def run(force_download: bool = False) -> dict:
    """Download, clean, join, split, and summarize MSHA data."""
    paths = ensure_raw_data(force=force_download)

    accidents_raw = load_accidents(paths["accidents"])
    mines_raw = load_mines(paths["mines"])

    accidents_clean, cleaning_log = clean_accidents(accidents_raw)
    mines_clean = clean_mines(mines_raw)
    merged, join_info = join_accidents_mines(accidents_clean, mines_clean)

    train, test, split_info = stratified_train_test_split(merged)

    summary = build_summary(
        raw_accident_rows=len(accidents_raw),
        raw_mine_rows=len(mines_raw),
        cleaning_log=cleaning_log,
        join_info=join_info,
        split_info=split_info,
        train=train,
        test=test,
        cleaned=merged,
    )

    TRAIN_CSV.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(ACCIDENTS_CLEAN_CSV, index=False)
    mines_clean.to_csv(MINES_CLEAN_CSV, index=False)
    train.to_csv(TRAIN_CSV, index=False)
    test.to_csv(TEST_CSV, index=False)
    save_summary(summary, SUMMARY_JSON)

    print_summary(summary)
    print(f"\nWrote processed files under {TRAIN_CSV.parent}")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest and clean MSHA accident data.")
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Re-download raw zip files even if local copies exist.",
    )
    args = parser.parse_args()
    run(force_download=args.force_download)


if __name__ == "__main__":
    main()
