"""Download MSHA open data files if they are not already present locally."""

from __future__ import annotations

import zipfile
from pathlib import Path

import requests

from src.data.config import (
    ACCIDENTS_TXT,
    ACCIDENTS_URL,
    ACCIDENTS_ZIP,
    MINES_TXT,
    MINES_URL,
    MINES_ZIP,
    RAW_DIR,
)


def _download_file(url: str, destination: Path) -> None:
    """Stream a remote file to disk."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, stream=True, timeout=300)
    response.raise_for_status()
    with destination.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                handle.write(chunk)


def _extract_zip(zip_path: Path, expected_txt: Path) -> None:
    """Extract a single .txt file from a MSHA zip archive."""
    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(path=zip_path.parent)
    if not expected_txt.exists():
        raise FileNotFoundError(f"Expected extracted file not found: {expected_txt}")


def ensure_raw_data(force: bool = False) -> dict[str, Path]:
    """
    Ensure Accidents.txt and Mines.txt exist under data/raw/.

    Returns paths to the extracted text files.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, Path] = {}

    for name, url, zip_path, txt_path in [
        ("accidents", ACCIDENTS_URL, ACCIDENTS_ZIP, ACCIDENTS_TXT),
        ("mines", MINES_URL, MINES_ZIP, MINES_TXT),
    ]:
        if force or not txt_path.exists():
            if force or not zip_path.exists():
                print(f"Downloading {name} dataset from {url}")
                _download_file(url, zip_path)
            else:
                print(f"Using cached zip for {name}: {zip_path}")
            print(f"Extracting {zip_path.name}")
            _extract_zip(zip_path, txt_path)
        else:
            print(f"Using cached {name} file: {txt_path}")
        results[name] = txt_path

    return results
