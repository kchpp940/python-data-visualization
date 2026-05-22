"""Shared path constants for python-data-visualization notebooks.

Only exposes directory paths — no plotting, Excel, or export logic lives here.

Usage (first cell of any notebook under ``code/``)::

    import sys; sys.path.insert(0, '..')
    from data_paths import RAW_DATA_DIR, IMAGES_DIR
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parent
CODE_DIR: Path = REPO_ROOT / "code"
DATA_DIR: Path = REPO_ROOT / "code" / "data"
RAW_DATA_DIR: Path = DATA_DIR / "raw"
IMAGES_DIR: Path = REPO_ROOT / "code" / "images"

for _p in (RAW_DATA_DIR, IMAGES_DIR):
    _p.mkdir(parents=True, exist_ok=True)

__all__ = [
    "REPO_ROOT",
    "CODE_DIR",
    "DATA_DIR",
    "RAW_DATA_DIR",
    "IMAGES_DIR",
]
