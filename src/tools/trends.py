"""Trend and aggregation queries over cleaned MSHA accident records (Step 3)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from src.data.config import ACCIDENTS_CLEAN_CSV

# 2026 is a partial reporting year in the current extract; exclude from YoY rate comparisons.
PARTIAL_CALENDAR_YEAR = 2026

FILTER_COLUMN_ALIASES: dict[str, str] = {
    "occupation": "OCCUPATION",
    "occupation_code": "OCCUPATION_CD",
    "injury_type": "NATURE_INJURY",
    "injury_type_code": "NATURE_INJURY_CD",
    "classification": "CLASSIFICATION",
    "classification_code": "CLASSIFICATION_CD",
    "equipment": "MINING_EQUIP",
    "equipment_code": "MINING_EQUIP_CD",
    "mine_id": "MINE_ID",
    "state": "STATE",
    "commodity": "PRIMARY_CANVASS",
    "coal_metal": "COAL_METAL_IND",
    "degree": "DEGREE_INJURY",
    "degree_code": "DEGREE_INJURY_CD",
    "accident_type": "ACCIDENT_TYPE",
    "body_part": "INJ_BODY_PART",
}


@dataclass
class TrendQueryResult:
    """Structured result from a trend query."""

    query_type: str
    filters: dict[str, Any]
    data: pd.DataFrame
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_type": self.query_type,
            "filters": self.filters,
            "notes": self.notes,
            "rows": self.data.to_dict(orient="records"),
        }


def load_accidents_frame(path: str | None = None) -> pd.DataFrame:
    csv_path = path or str(ACCIDENTS_CLEAN_CSV)
    frame = pd.read_csv(csv_path, low_memory=False)
    frame["CAL_YR"] = pd.to_numeric(frame["CAL_YR"], errors="coerce").astype("Int64")
    return frame


def _resolve_filter_column(key: str) -> str:
    normalized = key.strip().lower()
    if normalized in FILTER_COLUMN_ALIASES:
        return FILTER_COLUMN_ALIASES[normalized]
    upper = key.upper()
    return upper


def apply_filters(frame: pd.DataFrame, filters: dict[str, Any] | None) -> pd.DataFrame:
    """Filter accidents by field values. Keys accept aliases from FILTER_COLUMN_ALIASES."""
    if not filters:
        return frame.copy()
    subset = frame.copy()
    for key, value in filters.items():
        column = _resolve_filter_column(key)
        if column not in subset.columns:
            raise ValueError(f"Unknown filter column: {key} -> {column}")
        if column == "DEGREE_INJURY_CD":
            normalized = subset[column].astype(str).str.strip().str.zfill(2)
            if isinstance(value, list):
                allowed = {str(v).strip().zfill(2) for v in value}
                subset = subset[normalized.isin(allowed)]
            else:
                subset = subset[normalized == str(value).strip().zfill(2)]
            continue
        if isinstance(value, list):
            subset = subset[subset[column].isin(value)]
        elif column == "OCCUPATION" and isinstance(value, str):
            # Occupation labels are long compound strings; allow case-insensitive substring match.
            subset = subset[
                subset[column].astype(str).str.upper().str.contains(value.upper(), na=False)
            ]
        else:
            subset = subset[subset[column].astype(str).str.upper() == str(value).upper()]
    return subset


def count_by_year(
    frame: pd.DataFrame,
    filters: dict[str, Any] | None = None,
    exclude_partial_years: bool = True,
) -> TrendQueryResult:
    """Count injury records grouped by calendar year."""
    subset = apply_filters(frame, filters)
    notes: list[str] = []
    if exclude_partial_years:
        partial_mask = subset["CAL_YR"] == PARTIAL_CALENDAR_YEAR
        if partial_mask.any():
            notes.append(
                f"Excluded {int(partial_mask.sum())} records from CAL_YR={PARTIAL_CALENDAR_YEAR} "
                "(partial year in current extract)."
            )
            subset = subset[subset["CAL_YR"] != PARTIAL_CALENDAR_YEAR]
    counts = (
        subset.groupby("CAL_YR", as_index=False)
        .size()
        .rename(columns={"size": "injury_count"})
        .sort_values("CAL_YR")
    )
    return TrendQueryResult(
        query_type="count_by_year",
        filters=filters or {},
        data=counts,
        notes=notes,
    )


def year_over_year_change(
    frame: pd.DataFrame,
    filters: dict[str, Any] | None = None,
    exclude_partial_years: bool = True,
) -> TrendQueryResult:
    """Compute year-over-year absolute and percent change in injury counts."""
    counts = count_by_year(frame, filters, exclude_partial_years=exclude_partial_years)
    data = counts.data.copy()
    data["prev_count"] = data["injury_count"].shift(1)
    data["absolute_change"] = data["injury_count"] - data["prev_count"]
    data["percent_change"] = (
        (data["absolute_change"] / data["prev_count"] * 100).round(2)
    )
    data = data.dropna(subset=["prev_count"])
    return TrendQueryResult(
        query_type="year_over_year_change",
        filters=filters or {},
        data=data,
        notes=counts.notes,
    )


def count_by_group(
    frame: pd.DataFrame,
    group_column: str,
    filters: dict[str, Any] | None = None,
    top_n: int | None = None,
) -> TrendQueryResult:
    """Count records grouped by a categorical column (e.g. occupation, state)."""
    column = _resolve_filter_column(group_column)
    subset = apply_filters(frame, filters)
    if column not in subset.columns:
        raise ValueError(f"Unknown group column: {group_column}")
    counts = (
        subset.groupby(column, as_index=False)
        .size()
        .rename(columns={"size": "injury_count"})
        .sort_values("injury_count", ascending=False)
    )
    if top_n is not None:
        counts = counts.head(top_n)
    return TrendQueryResult(
        query_type="count_by_group",
        filters={**(filters or {}), "group_column": column, "top_n": top_n},
        data=counts,
        notes=[],
    )


def compare_periods(
    frame: pd.DataFrame,
    period_a: tuple[int, int],
    period_b: tuple[int, int],
    filters: dict[str, Any] | None = None,
) -> TrendQueryResult:
    """Compare injury counts between two inclusive calendar-year ranges."""
    subset = apply_filters(frame, filters)
    start_a, end_a = period_a
    start_b, end_b = period_b
    count_a = int(subset[(subset["CAL_YR"] >= start_a) & (subset["CAL_YR"] <= end_a)].shape[0])
    count_b = int(subset[(subset["CAL_YR"] >= start_b) & (subset["CAL_YR"] <= end_b)].shape[0])
    data = pd.DataFrame(
        [
            {"period": f"{start_a}-{end_a}", "injury_count": count_a},
            {"period": f"{start_b}-{end_b}", "injury_count": count_b},
        ]
    )
    notes = []
    if end_a >= PARTIAL_CALENDAR_YEAR or end_b >= PARTIAL_CALENDAR_YEAR:
        notes.append(f"Ranges including {PARTIAL_CALENDAR_YEAR} may reflect partial-year reporting.")
    return TrendQueryResult(
        query_type="compare_periods",
        filters={**(filters or {}), "period_a": period_a, "period_b": period_b},
        data=data,
        notes=notes,
    )


class TrendAnalyzer:
    """Facade for trend queries used by the agent and tests."""

    def __init__(self, frame: pd.DataFrame | None = None) -> None:
        self.frame = frame if frame is not None else load_accidents_frame()

    def count_by_year(self, filters: dict[str, Any] | None = None) -> TrendQueryResult:
        return count_by_year(self.frame, filters)

    def year_over_year_change(self, filters: dict[str, Any] | None = None) -> TrendQueryResult:
        return year_over_year_change(self.frame, filters)

    def count_by_group(
        self,
        group_column: str,
        filters: dict[str, Any] | None = None,
        top_n: int | None = None,
    ) -> TrendQueryResult:
        return count_by_group(self.frame, group_column, filters, top_n)

    def compare_periods(
        self,
        period_a: tuple[int, int],
        period_b: tuple[int, int],
        filters: dict[str, Any] | None = None,
    ) -> TrendQueryResult:
        return compare_periods(self.frame, period_a, period_b, filters)
