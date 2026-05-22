"""Chapter 7 notebook initialization — Plotly backend on top of shared init.

Chapter 7 notebooks use Plotly Express/Graph-Objects plus ``pandas``/``numpy``.
This module re-exports everything from :mod:`src.nb_init` and additionally
imports :mod:`plotly.express` and :mod:`plotly.graph_objects` so the first
cell of a notebook can be a single, stable import block.

Usage (first cell of a ch7 notebook)::

    from src.ch7_init import (
        RAW_DATA_DIR, IMAGES_DIR,
        pd, np, px, go,
        datasets,
    )
    df = datasets.load("epa_summary")
    datasets.describe("epa_summary")
"""

from __future__ import annotations

import plotly.express as px  # noqa: F401
import plotly.graph_objects as go  # noqa: F401

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
    "px",
    "go",
    "datasets",
    "DatasetRegistry",
    "load_epa",
    "load_epa_summary",
    "load_amazon_books",
]
