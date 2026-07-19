"""Tests for trend analysis tool (Step 3)."""

from __future__ import annotations

import pandas as pd
import pytest

from src.data.config import ACCIDENTS_CLEAN_CSV
from src.tools.trends import (
    PARTIAL_CALENDAR_YEAR,
    TrendAnalyzer,
    apply_filters,
    count_by_year,
)


def _manual_count_by_year(frame: pd.DataFrame, year: int, **filters: str) -> int:
    subset = apply_filters(frame, filters)
    subset = subset[subset["CAL_YR"] != PARTIAL_CALENDAR_YEAR]
    return int((subset["CAL_YR"] == year).sum())


@pytest.fixture(scope="module")
def accidents() -> pd.DataFrame:
    if not ACCIDENTS_CLEAN_CSV.exists():
        pytest.skip("Run python -m src.data.ingest first")
    return TrendAnalyzer().frame


# Five hand-checked example queries verified against manual row counts from raw cleaned data.


def test_example_1_roof_bolter_counts_2018_2020(accidents: pd.DataFrame) -> None:
    """Injury counts by year for roof bolter occupation group."""
    filters = {"occupation": "Roof bolter"}
    result = count_by_year(accidents, filters)
    for year in [2018, 2019, 2020]:
        tool_val = int(result.data.loc[result.data["CAL_YR"] == year, "injury_count"].iloc[0])
        manual_val = _manual_count_by_year(accidents, year, **filters)
        assert tool_val == manual_val


def test_example_2_fatality_counts_by_year(accidents: pd.DataFrame) -> None:
    """Annual fatality counts (degree code 01)."""
    filters = {"degree_code": "01"}
    result = count_by_year(accidents, filters)
    row_2015 = int(result.data.loc[result.data["CAL_YR"] == 2015, "injury_count"].iloc[0])
    assert row_2015 == _manual_count_by_year(accidents, 2015, **filters)
    filtered = apply_filters(accidents, filters)
    filtered = filtered[filtered["CAL_YR"] != PARTIAL_CALENDAR_YEAR]
    assert int(result.data["injury_count"].sum()) == len(filtered)


def test_example_3_coal_mine_texas_2022(accidents: pd.DataFrame) -> None:
    filters = {"coal_metal": "C", "state": "TX"}
    manual = _manual_count_by_year(accidents, 2022, **filters)
    tool = int(
        count_by_year(accidents, filters).data.loc[
            lambda d: d["CAL_YR"] == 2022, "injury_count"
        ].iloc[0]
    )
    assert tool == manual


def test_example_4_handling_materials_yoy(accidents: pd.DataFrame) -> None:
    filters = {"classification": "HANDLING OF MATERIALS"}
    result = TrendAnalyzer(accidents).year_over_year_change(filters)
    row_2019 = result.data.loc[result.data["CAL_YR"] == 2019].iloc[0]
    counts = count_by_year(accidents, filters).data
    c2018 = int(counts.loc[counts["CAL_YR"] == 2018, "injury_count"].iloc[0])
    c2019 = int(counts.loc[counts["CAL_YR"] == 2019, "injury_count"].iloc[0])
    assert int(row_2019["absolute_change"]) == c2019 - c2018


def test_example_5_compare_periods_underground_coal(accidents: pd.DataFrame) -> None:
    filters = {"coal_metal": "C"}
    subset = apply_filters(accidents, filters)
    subset = subset[subset["CAL_YR"] != PARTIAL_CALENDAR_YEAR]
    manual_a = int(subset[(subset["CAL_YR"] >= 2010) & (subset["CAL_YR"] <= 2014)].shape[0])
    manual_b = int(subset[(subset["CAL_YR"] >= 2015) & (subset["CAL_YR"] <= 2019)].shape[0])
    result = TrendAnalyzer(accidents).compare_periods((2010, 2014), (2015, 2019), filters)
    assert int(result.data.iloc[0]["injury_count"]) == manual_a
    assert int(result.data.iloc[1]["injury_count"]) == manual_b


def test_partial_year_excluded_from_count_by_year(accidents: pd.DataFrame) -> None:
    result = count_by_year(accidents, {})
    assert PARTIAL_CALENDAR_YEAR not in set(result.data["CAL_YR"])
    assert any(str(PARTIAL_CALENDAR_YEAR) in note for note in result.notes)
