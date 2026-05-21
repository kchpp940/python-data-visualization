"""Chapter 6 notebook initialization — backward-compatible entry point.

DEPRECATED: For new code, prefer importing directly from ``src.ch6`` package::

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

This module re-exports everything from the new modular package to maintain
backward compatibility with existing Chapter 6 notebooks.
"""

from __future__ import annotations

from src.ch6 import (
    REPO_ROOT,
    RAW_DATA_DIR,
    IMAGES_DIR,
    DEFAULT_LARGE_DATA_THRESHOLD,
    alt,
    np,
    pd,
    configure_altair,
    init_chapter6,
    display_init_status,
    read_excel_safe,
    save_altair_chart,
    ChartExportManager,
)

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
