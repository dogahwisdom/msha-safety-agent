"""Clean and join MSHA accident and mine identification records."""

from __future__ import annotations

import pandas as pd

from src.data.config import (
    CLASSIFIER_FEATURE_COLUMNS,
    CLASSIFIER_TARGET_COLUMN,
    MINE_CONTEXT_COLUMNS,
    MIN_CALENDAR_YEAR,
)


def _is_invalid_code(series: pd.Series) -> pd.Series:
    """True where a MSHA code field is missing, blank, or marked invalid with '?'."""
    normalized = series.fillna("").astype(str).str.strip()
    return normalized.eq("") | normalized.eq("?")


def clean_accidents(accidents: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """
    Clean accident records for downstream tools.

    Filtering decisions (each applied in order):
    1. Drop duplicate DOCUMENT_NO (MSHA unique key). None expected in current extract.
    2. Drop rows with missing DOCUMENT_NO or MINE_ID.
    3. Drop rows with invalid DEGREE_INJURY_CD (blank or '?'). This is the classifier target.
    4. Drop rows with CAL_YR before 2000. Dataset scope starts in 2000; a handful of bad rows may exist.
    5. Drop rows missing any core structured classifier code except MINING_EQUIP_CD.
       Prior MSHA studies require complete structured fields; occupation is the largest loss here.
    6. Impute missing or invalid MINING_EQUIP_CD as 'UNK' rather than dropping rows.
       Over half of raw records lack equipment codes; dropping them would exceed prior study filters.
    7. Drop rows with blank NARRATIVE. Retrieval and RAG require text; empty narratives add no value.
    """
    log: list[dict] = []
    frame = accidents.copy()
    frame["_keep"] = True

    log.append({"step": "raw_loaded", "rows_before": 0, "rows_after": len(frame), "rows_removed": 0})

    dup_count = int(frame["DOCUMENT_NO"].duplicated().sum())
    if dup_count:
        dup_docs = frame.loc[frame["DOCUMENT_NO"].duplicated(keep="first"), "DOCUMENT_NO"]
        frame.loc[frame["DOCUMENT_NO"].isin(dup_docs), "_keep"] = False
        log.append(
            {
                "step": "drop_duplicate_document_no",
                "rows_before": len(frame),
                "rows_after": int(frame["_keep"].sum()),
                "rows_removed": dup_count,
            }
        )

    for column in ["DOCUMENT_NO", "MINE_ID"]:
        invalid = _is_invalid_code(frame[column])
        before_keep = int(frame["_keep"].sum())
        frame.loc[invalid & frame["_keep"], "_keep"] = False
        log.append(
            {
                "step": f"drop_missing_{column.lower()}",
                "rows_before": before_keep,
                "rows_after": int(frame["_keep"].sum()),
                "rows_removed": before_keep - int(frame["_keep"].sum()),
            }
        )

    invalid_degree = _is_invalid_code(frame[CLASSIFIER_TARGET_COLUMN])
    before_keep = int(frame["_keep"].sum())
    frame.loc[invalid_degree & frame["_keep"], "_keep"] = False
    log.append(
        {
            "step": "drop_invalid_degree_injury_cd",
            "rows_before": before_keep,
            "rows_after": int(frame["_keep"].sum()),
            "rows_removed": before_keep - int(frame["_keep"].sum()),
        }
    )

    frame["CAL_YR"] = pd.to_numeric(frame["CAL_YR"], errors="coerce")
    old_year = frame["CAL_YR"].lt(MIN_CALENDAR_YEAR) | frame["CAL_YR"].isna()
    before_keep = int(frame["_keep"].sum())
    frame.loc[old_year & frame["_keep"], "_keep"] = False
    log.append(
        {
            "step": f"drop_calendar_year_before_{MIN_CALENDAR_YEAR}",
            "rows_before": before_keep,
            "rows_after": int(frame["_keep"].sum()),
            "rows_removed": before_keep - int(frame["_keep"].sum()),
        }
    )

    core_columns = [c for c in CLASSIFIER_FEATURE_COLUMNS if c != "MINING_EQUIP_CD"]
    for column in core_columns:
        invalid = _is_invalid_code(frame[column])
        before_keep = int(frame["_keep"].sum())
        frame.loc[invalid & frame["_keep"], "_keep"] = False
        log.append(
            {
                "step": f"drop_invalid_{column.lower()}",
                "rows_before": before_keep,
                "rows_after": int(frame["_keep"].sum()),
                "rows_removed": before_keep - int(frame["_keep"].sum()),
            }
        )

    equip_invalid = _is_invalid_code(frame["MINING_EQUIP_CD"])
    frame.loc[frame["_keep"], "MINING_EQUIP_CD"] = frame.loc[frame["_keep"], "MINING_EQUIP_CD"].where(
        ~equip_invalid, "UNK"
    )
    log.append(
        {
            "step": "impute_missing_mining_equip_cd_as_UNK",
            "rows_before": int(frame["_keep"].sum()),
            "rows_after": int(frame["_keep"].sum()),
            "rows_imputed": int(equip_invalid[frame["_keep"]].sum()),
        }
    )

    invalid_narrative = _is_invalid_code(frame["NARRATIVE"])
    before_keep = int(frame["_keep"].sum())
    frame.loc[invalid_narrative & frame["_keep"], "_keep"] = False
    log.append(
        {
            "step": "drop_missing_narrative",
            "rows_before": before_keep,
            "rows_after": int(frame["_keep"].sum()),
            "rows_removed": before_keep - int(frame["_keep"].sum()),
        }
    )

    cleaned = frame.loc[frame["_keep"]].drop(columns=["_keep"]).copy()
    cleaned["ACCIDENT_DT"] = pd.to_datetime(cleaned["ACCIDENT_DT"], errors="coerce", format="mixed")
    cleaned["CAL_YR"] = cleaned["CAL_YR"].astype(int)
    cleaned["DAYS_LOST"] = pd.to_numeric(cleaned["DAYS_LOST"], errors="coerce")
    cleaned["DAYS_RESTRICT"] = pd.to_numeric(cleaned["DAYS_RESTRICT"], errors="coerce")

    return cleaned, log


def clean_mines(mines: pd.DataFrame) -> pd.DataFrame:
    """Keep one row per MINE_ID with mine context columns used downstream."""
    frame = mines.copy()
    frame = frame.drop_duplicates(subset=["MINE_ID"], keep="first")
    keep_cols = ["MINE_ID"] + [c for c in MINE_CONTEXT_COLUMNS if c in frame.columns]
    return frame[keep_cols].copy()


def join_accidents_mines(accidents: pd.DataFrame, mines: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Left join accidents to mines on MINE_ID.

    Records without a mine match are kept but flagged. They still have accident-side COAL_METAL_IND.
    """
    merged = accidents.merge(mines, on="MINE_ID", how="left", indicator=True)
    unmatched = int((merged["_merge"] == "left_only").sum())
    merged["MINE_MATCH"] = merged["_merge"].eq("both")
    merged = merged.drop(columns=["_merge"])
    join_info = {
        "total_rows": len(merged),
        "matched_mine_rows": int(merged["MINE_MATCH"].sum()),
        "unmatched_mine_rows": unmatched,
    }
    return merged, join_info
