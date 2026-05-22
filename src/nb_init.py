"""Shared notebook initialization layer.

Every chapter notebook under ``code/`` performs the same four startup steps:

1. Bootstrap the repo root onto ``sys.path`` so that ``src.*`` is importable
   regardless of where Jupyter was launched from (``code/``, repo root, or
   any parent directory).  This happens in an inline preamble at the top of
   the first cell *before* the first ``from src.…`` import (see below).
2. Re-export the path constants from :mod:`data_paths`.
3. Re-export the common libraries (``pandas``, ``numpy``) so every notebook
   has a consistent import surface.
4. Expose a small :class:`DatasetRegistry` that centralises the file names and
   one-line descriptions of the bundled datasets, replacing the repeated
   ``src_file = RAW_DATA_DIR / 'EPA_fuel_economy.csv'`` lines.

Usage (first cell of any notebook)::

    # --- bootstrap: locate repo root, inject into sys.path, then import ---
    from pathlib import Path
    import os, sys

    _ROOT = os.environ.get("PY_DATA_VIS_ROOT")
    if _ROOT:
        _ROOT = Path(_ROOT).expanduser().resolve()
    else:
        _ROOT = Path.cwd()
        while _ROOT != _ROOT.parent and not (_ROOT / "data_paths.py").exists():
            _ROOT = _ROOT.parent

    if not (_ROOT / "data_paths.py").exists():
        raise RuntimeError(
            "Cannot locate python-data-visualization repo root. "
            "Set PY_DATA_VIS_ROOT to the repo directory, or launch "
            "Jupyter from inside the repo."
        )

    sys.path.insert(0, str(_ROOT))
    sys.path.insert(0, str(_ROOT / "src"))

    from src.ch3_init import RAW_DATA_DIR, IMAGES_DIR, datasets, pd, np, plt, ticker
    datasets.describe('epa')

The bootstrap is intentionally written inline in the notebook (not imported)
because it must run *before* the first ``from src.…`` import.  Once it has
run, this module and the chapter wrappers take over and handle paths,
datasets, and plotting backends.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import numpy as np  # noqa: F401  (re-exported for notebooks)
import pandas as pd  # noqa: F401


# ---------------------------------------------------------------------------
# Path constants (delegated to data_paths).
#
# The repo-root / sys.path injection used to live here.  It has been moved
# into an inline bootstrap at the top of every notebook's first cell, because
# it must complete *before* the `from src.nb_init` import itself can succeed.
# See the module docstring for the canonical bootstrap snippet.
# ---------------------------------------------------------------------------
from data_paths import REPO_ROOT, CODE_DIR, DATA_DIR, RAW_DATA_DIR, IMAGES_DIR  # noqa: E402


# ---------------------------------------------------------------------------
# Dataset registry
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class _DatasetInfo:
    key: str
    filename: str
    description: str
    loader: str = "csv"


class DatasetRegistry:
    """Centralised catalogue of the datasets bundled with the project.

    Attributes
    ----------
    epa:
        :class:`_DatasetInfo` for ``EPA_fuel_economy.csv`` (raw, per-row
        records).
    epa_summary:
        :class:`_DatasetInfo` for ``EPA_fuel_economy_summary.csv``
        (pre-aggregated).
    amazon_books:
        :class:`_DatasetInfo` for ``AmazonBooks.xlsx``.
    """

    def __init__(self) -> None:
        self.epa = _DatasetInfo(
            key="epa",
            filename="EPA_fuel_economy.csv",
            description=(
                "Raw EPA fuel economy dataset — one row per vehicle model/year. "
                "Columns include make/model/year, cylinders, transmission, "
                "displacement, vehicle class, CO2 emissions, barrels per year, "
                "and fuel cost."
            ),
        )
        self.epa_summary = _DatasetInfo(
            key="epa_summary",
            filename="EPA_fuel_economy_summary.csv",
            description=(
                "Pre-aggregated EPA fuel economy dataset — one row per make. "
                "Derived from the raw EPA file."
            ),
        )
        self.amazon_books = _DatasetInfo(
            key="amazon_books",
            filename="AmazonBooks.xlsx",
            description=(
                "Amazon Books dataset — rating / review / price / category info "
                "for a cross-section of book listings."
            ),
            loader="excel",
        )
        self._by_key = {
            info.key: info
            for info in (self.epa, self.epa_summary, self.amazon_books)
        }
        self._by_filename = {info.filename: info for info in self._by_key.values()}

    # -- lookup -------------------------------------------------------------
    def get(self, key: str) -> _DatasetInfo:
        """Return the :class:`_DatasetInfo` for ``key``.

        ``key`` may be the short name (``"epa"``) or the full filename
        (``"EPA_fuel_economy.csv"``). Raises :class:`KeyError` on unknown keys.
        """
        if key in self._by_key:
            return self._by_key[key]
        if key in self._by_filename:
            return self._by_filename[key]
        raise KeyError(
            f"Unknown dataset key {key!r}; known keys: "
            f"{sorted(self._by_key)}"
        )

    def path(self, key: str) -> Path:
        """Return the absolute :class:`~pathlib.Path` for dataset ``key``."""
        return RAW_DATA_DIR / self.get(key).filename

    def describe(self, key: str) -> str:
        """Return the human-readable description for dataset ``key``."""
        return self.get(key).description

    # -- loading ------------------------------------------------------------
    def load(self, key: str, **kwargs) -> pd.DataFrame:
        """Load dataset ``key`` into a :class:`pandas.DataFrame`.

        CSV files are loaded with :func:`pandas.read_csv`; Excel files use
        :func:`pandas.read_excel` (engine chosen by file extension). Extra
        ``kwargs`` are forwarded to the underlying reader.
        """
        info = self.get(key)
        p = self.path(key)
        if info.loader == "excel":
            suffix = p.suffix.lower()
            engine = kwargs.pop(
                "engine",
                "openpyxl" if suffix in (".xlsx", ".xlsm") else None,
            )
            return pd.read_excel(p, engine=engine, **kwargs)
        return pd.read_csv(p, **kwargs)

    # -- iteration ----------------------------------------------------------
    def keys(self):
        return self._by_key.keys()

    def __iter__(self):
        return iter(self._by_key.values())

    def __contains__(self, key: str) -> bool:
        return key in self._by_key or key in self._by_filename


datasets = DatasetRegistry()


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------
def load_epa(**kwargs) -> pd.DataFrame:
    """Load the raw EPA fuel economy CSV."""
    return datasets.load("epa", **kwargs)


def load_epa_summary(**kwargs) -> pd.DataFrame:
    """Load the aggregated EPA fuel economy CSV."""
    return datasets.load("epa_summary", **kwargs)


def load_amazon_books(**kwargs) -> pd.DataFrame:
    """Load the Amazon Books Excel workbook."""
    return datasets.load("amazon_books", **kwargs)


__all__ = [
    "REPO_ROOT",
    "CODE_DIR",
    "DATA_DIR",
    "RAW_DATA_DIR",
    "IMAGES_DIR",
    "np",
    "pd",
    "datasets",
    "DatasetRegistry",
    "load_epa",
    "load_epa_summary",
    "load_amazon_books",
]
