"""Shared path constants for python-data-visualization notebooks.

Only exposes directory paths — no plotting, Excel, or export logic lives here.

Usage (first cell of any notebook under ``code/``)::

    import sys; sys.path.insert(0, '..')
    from data_paths import RAW_DATA_DIR, IMAGES_DIR

Notes
-----
Only the legacy ``RAW_DATA_DIR`` and ``IMAGES_DIR`` are materialised on import,
because older notebooks write directly to those paths.  The unified output
layer (``OUTPUT_DIR`` and its sub-directories) is **not** created here — it is
materialised lazily by :class:`src.output_manager.OutputManager` the first time
an artefact is actually written.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parent
CODE_DIR: Path = REPO_ROOT / "code"
DATA_DIR: Path = REPO_ROOT / "code" / "data"
RAW_DATA_DIR: Path = DATA_DIR / "raw"
IMAGES_DIR: Path = REPO_ROOT / "code" / "images"

OUTPUT_DIR: Path = REPO_ROOT / "output"
OUTPUT_ALTAIR_DIR: Path = OUTPUT_DIR / "altair"
OUTPUT_PLOTLY_DIR: Path = OUTPUT_DIR / "plotly"
OUTPUT_NOTEBOOK_DIR: Path = OUTPUT_DIR / "notebook"
OUTPUT_README_DIR: Path = OUTPUT_DIR / "readme"

# Legacy paths — create eagerly so older notebooks keep working.
for _p in (RAW_DATA_DIR, IMAGES_DIR):
    _p.mkdir(parents=True, exist_ok=True)

__all__ = [
    "REPO_ROOT",
    "CODE_DIR",
    "DATA_DIR",
    "RAW_DATA_DIR",
    "IMAGES_DIR",
    "OUTPUT_DIR",
    "OUTPUT_ALTAIR_DIR",
    "OUTPUT_PLOTLY_DIR",
    "OUTPUT_NOTEBOOK_DIR",
    "OUTPUT_README_DIR",
]
