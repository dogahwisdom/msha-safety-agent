"""Load raw MSHA pipe-delimited files into pandas DataFrames."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.config import MSHA_ENCODING, PIPE_DELIMITER


def _strip_strings(frame: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace and surrounding quotes from string columns."""
    out = frame.copy()
    for column in out.select_dtypes(include="object").columns:
        out[column] = out[column].astype(str).str.strip().str.strip('"')
        out[column] = out[column].replace({"nan": pd.NA, "None": pd.NA})
    return out


def load_accidents(path: Path) -> pd.DataFrame:
    """Load the Accident Injuries dataset."""
    frame = pd.read_csv(
        path,
        sep=PIPE_DELIMITER,
        dtype=str,
        encoding=MSHA_ENCODING,
        low_memory=False,
    )
    return _strip_strings(frame)


def load_mines(path: Path) -> pd.DataFrame:
    """Load the Mines (mine identification) dataset."""
    frame = pd.read_csv(
        path,
        sep=PIPE_DELIMITER,
        dtype=str,
        encoding=MSHA_ENCODING,
        low_memory=False,
    )
    return _strip_strings(frame)
