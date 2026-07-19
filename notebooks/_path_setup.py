"""Shared path setup for Jupyter notebooks. Import at the top of each notebook."""

from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    """Return repository root (parent of notebooks/)."""
    here = Path.cwd().resolve()
    if (here / "src" / "data").exists():
        return here
    if (here.parent / "src" / "data").exists():
        return here.parent
    raise RuntimeError(
        "Could not locate project root. Start Jupyter from the repo root or notebooks/ directory."
    )


def setup_imports() -> Path:
    """Add src to sys.path and return project root."""
    root = project_root()
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root
