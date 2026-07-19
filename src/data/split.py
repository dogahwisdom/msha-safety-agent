"""Stratified train and test split for cleaned accident records."""

from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split

from src.data.config import CLASSIFIER_TARGET_COLUMN, RANDOM_SEED, TEST_FRACTION


def _year_bucket(year: int) -> str:
    """Group calendar years into five-year buckets for stratification."""
    if year < 2005:
        return "2000-2004"
    if year < 2010:
        return "2005-2009"
    if year < 2015:
        return "2010-2014"
    if year < 2020:
        return "2015-2019"
    return "2020-2026"


def make_stratify_label(frame: pd.DataFrame) -> pd.Series:
    """
    Build a combined stratification label from injury degree and calendar year bucket.

    Injury degree captures class balance. Year bucket preserves temporal coverage in both splits.
    """
    buckets = frame["CAL_YR"].map(_year_bucket)
    return frame[CLASSIFIER_TARGET_COLUMN].astype(str) + "_" + buckets.astype(str)


def _ensure_sufficient_strata(labels: pd.Series, min_count: int = 2) -> tuple[pd.Series, int]:
    """
    Collapse labels until every stratum has at least min_count members.

    Used only for split assignment; original DEGREE_INJURY_CD values are unchanged in the data.
    """
    merged_count = 0
    current = labels.copy()

    for _ in range(10):
        counts = current.value_counts()
        if counts.min() >= min_count:
            break
        rare = counts[counts < min_count].index
        merged_count += len(rare)

        if any("_" in str(label) for label in rare):
            current = current.where(
                ~current.isin(rare),
                other=current.str.split("_").str[0] + "_OTHER",
            )
            continue

        mask = current.isin(rare)
        current = current.where(~mask, other="RARE")

    counts = current.value_counts()
    if counts.min() < min_count:
        merged_count += int((counts < min_count).sum())
        modal = counts.idxmax()
        rare_labels = counts[counts < min_count].index
        current = current.where(~current.isin(rare_labels), other=modal)

    return current, merged_count


def stratified_train_test_split(
    frame: pd.DataFrame,
    test_size: float = TEST_FRACTION,
    random_state: int = RANDOM_SEED,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Split cleaned records into train and test sets with stratification.

    Stratification uses injury degree plus five-year calendar buckets. Strata with
    fewer than two records are collapsed into broader buckets (degree_OTHER, then RARE)
    for split assignment only. Original labels in the saved data are not modified.
    """
    labels, merged = _ensure_sufficient_strata(make_stratify_label(frame))

    train, test = train_test_split(
        frame,
        test_size=test_size,
        random_state=random_state,
        stratify=labels,
    )

    info = {
        "train_rows": len(train),
        "test_rows": len(test),
        "test_fraction": test_size,
        "random_seed": random_state,
        "strata_count": int(labels.nunique()),
        "rare_strata_merged": merged,
    }
    return train.reset_index(drop=True), test.reset_index(drop=True), info
