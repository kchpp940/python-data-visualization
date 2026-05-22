"""Chapter 3/4 notebook initialization — Matplotlib backend on top of shared init.

Both Chapter 3 and 4 use Matplotlib (plus ``pandas``/``numpy``). This module
re-exports everything from :mod:`src.nb_init` and additionally imports
``matplotlib.pyplot`` and ``matplotlib.ticker`` so the first cell of a
notebook can be a single, stable import block.

Usage (first cell of a ch3 / ch4 notebook)::

    from src.ch3_init import (
        RAW_DATA_DIR, IMAGES_DIR,
        pd, np, plt, ticker,
        datasets,
    )
    df = datasets.load("epa")
    datasets.describe("epa")

Chapter 4 notebooks can import from :mod:`src.ch4_init` (which is an alias
of this module) for semantic clarity.
"""

from __future__ import annotations

from matplotlib import pyplot as plt  # noqa: F401
from matplotlib import ticker  # noqa: F401

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
    "ticker",
    "datasets",
    "DatasetRegistry",
    "load_epa",
    "load_epa_summary",
    "load_amazon_books",
]
