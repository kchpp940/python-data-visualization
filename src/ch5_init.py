"""Chapter 5 notebook initialization — Seaborn backend on top of shared init.

Chapter 5 notebooks use Seaborn (on top of Matplotlib) plus ``pandas``/``numpy``.
This module re-exports everything from :mod:`src.nb_init` and additionally
imports :mod:`seaborn` (and the usual Matplotlib symbols) so the first cell
of a notebook can be a single, stable import block.

Usage (first cell of a ch5 notebook)::

    from src.ch5_init import (
        RAW_DATA_DIR, IMAGES_DIR,
        pd, np, sns,
        datasets,
    )
    df = datasets.load("epa_summary")
    datasets.describe("epa_summary")
"""

from __future__ import annotations

import seaborn as sns  # noqa: F401
from matplotlib import pyplot as plt  # noqa: F401

from src.nb_init import (  # noqa: F401,E402
    REPO_ROOT,
    CODE_DIR,
    DATA_DIR,
    RAW_DATA_DIR,
    IMAGES_DIR,
    np,
    pd,
    datasets,
    DatasetRegistry,
    load_epa,
    load_epa_summary,
    load_amazon_books,
)

__all__ = [
    "REPO_ROOT",
    "CODE_DIR",
    "DATA_DIR",
    "RAW_DATA_DIR",
    "IMAGES_DIR",
    "np",
    "pd",
    "plt",
    "sns",
    "datasets",
    "DatasetRegistry",
    "load_epa",
    "load_epa_summary",
    "load_amazon_books",
]
