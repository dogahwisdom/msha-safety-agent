"""Feature selection for classifier training (leakage-safe columns only)."""

from __future__ import annotations

import pandas as pd

from src.data.config import (
    CLASSIFIER_FEATURE_COLUMNS,
    CLASSIFIER_LEAKAGE_COLUMNS,
    CLASSIFIER_MINE_FEATURE_COLUMNS,
    CLASSIFIER_TARGET_COLUMN,
)


def select_classifier_features(
    frame: pd.DataFrame,
    include_mine_context: bool = False,
) -> pd.DataFrame:
    """
    Return only approved classifier input columns.

    Step 2 must call this (or equivalent explicit column selection). Do not use
    frame.drop(columns=[target]) on the full cleaned dataframe, since leakage
    columns such as DAYS_LOST and DAYS_RESTRICT remain in that frame.
    """
    columns = list(CLASSIFIER_FEATURE_COLUMNS)
    if include_mine_context:
        columns.extend(c for c in CLASSIFIER_MINE_FEATURE_COLUMNS if c in frame.columns)

    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing classifier feature columns: {missing}")

    leaked = [column for column in CLASSIFIER_LEAKAGE_COLUMNS if column in columns]
    if leaked:
        raise ValueError(f"Leakage columns must not be classifier inputs: {leaked}")

    return frame[columns].copy()


def select_classifier_target(frame: pd.DataFrame) -> pd.Series:
    """Return the injury degree target column."""
    if CLASSIFIER_TARGET_COLUMN not in frame.columns:
        raise ValueError(f"Missing target column: {CLASSIFIER_TARGET_COLUMN}")
    return frame[CLASSIFIER_TARGET_COLUMN].copy()
