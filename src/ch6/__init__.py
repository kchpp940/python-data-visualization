"""Chapter 6 package — Altair visualization toolkit.

This package provides modular components for Chapter 6 notebooks:
- altair_config:   Altair backend configuration and row limit management
- excel_reader:    Safe Excel file reading with automatic engine selection
- chart_exporter:  Multi-format chart export with history and batch support
- notebook_init:   One-shot notebook initialization (convenience entry point)

Usage (recommended for new code)::

    from src.ch6 import (
        RAW_DATA_DIR, IMAGES_DIR,
        pd, np, alt,
        read_excel_safe, save_altair_chart,
        ChartExportManager,
        init_chapter6, display_init_status,
    )
    status = init_chapter6(notebook_name="my-notebook")
    display_init_status(status)
    exporter = status["export_manager"]

For backward compatibility, the old ``src.ch6_init`` module still works
and re-exports everything from this package.
"""

from __future__ import annotations

from data_paths import RAW_DATA_DIR, IMAGES_DIR, REPO_ROOT

import numpy as np
import pandas as pd
import altair as alt

from .altair_config import configure_altair, DEFAULT_LARGE_DATA_THRESHOLD
from .excel_reader import read_excel_safe
from .chart_exporter import ChartExportManager, save_altair_chart
from .notebook_init import init_chapter6, display_init_status

__all__ = [
    "REPO_ROOT",
    "RAW_DATA_DIR",
    "IMAGES_DIR",
    "DEFAULT_LARGE_DATA_THRESHOLD",
    "alt",
    "np",
    "pd",
    "configure_altair",
    "init_chapter6",
    "display_init_status",
    "read_excel_safe",
    "save_altair_chart",
    "ChartExportManager",
]
