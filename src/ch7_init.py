"""Chapter 7 notebook initialization — Plotly backend and unified output layer.

Only ``ch7-exercise-*.ipynb`` should import from this module. Other chapters
continue to use the slim ``data_paths`` module for path constants only.

This module is side-effect free: importing it does **not** create any directory.
Directories are materialised lazily by :class:`src.output_manager.OutputManager` the
first time an artefact is written.

Usage (first cell of any ch7 notebook)::

    import sys; sys.path.insert(0, '..')
    from src.ch7_init import (
        RAW_DATA_DIR, IMAGES_DIR,
        pd, np, px, go,
        save_plotly_chart,
        OutputManager, OverwritePolicy, get_output_manager,
    )
"""

from __future__ import annotations

from typing import Optional, Sequence, Union

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from data_paths import RAW_DATA_DIR, IMAGES_DIR, REPO_ROOT  # noqa: E402
from src.output_manager import (  # noqa: E402
    OutputManager,
    OverwritePolicy,
    WriteRecord,
    get_output_manager,
)


def save_plotly_chart(
    fig,
    stem: str,
    *,
    chapter: Optional[Union[int, str]] = 7,
    formats: Sequence[str] = ("png", "html"),
    width: Optional[int] = None,
    height: Optional[int] = None,
    scale: float = 2.0,
    overwrite: Union[str, OverwritePolicy] = OverwritePolicy.WARN,
) -> dict:
    """Save a Plotly figure through the unified output layer.

    HTML always uses ``fig.write_html`` (with ``include_plotlyjs="cdn"``); static
    formats (png / svg / pdf / jpeg) use ``fig.write_image`` via kaleido.

    Parameters
    ----------
    fig:
        A plotly ``Figure`` (``go.Figure`` or ``px.*`` return value).
    stem:
        Filename stem (extension-less).
    chapter:
        Chapter prefix — defaults to 7 so ch7 notebooks produce ``ch07_<stem>``.
        Pass ``None`` to disable the prefix.
    formats:
        Formats to export.
    width, height, scale:
        Forwarded to ``fig.write_image`` for static formats.
    overwrite:
        Overwrite policy (default ``WARN``).

    Returns
    -------
    dict
        ``{fmt: path_str}`` mapping for every format successfully written.
    """
    manager = get_output_manager()
    if overwrite != manager.overwrite:
        manager = OutputManager(
            root=manager.root,
            overwrite=overwrite,
            category_dirs=manager._category_dirs,
            dry_run=manager.dry_run,
        )
    records = manager.save_plotly(
        fig,
        stem,
        chapter=chapter,
        formats=formats,
        width=width,
        height=height,
        scale=scale,
    )
    return {fmt: str(rec.path) for fmt, rec in records.items()}


def export_ch7_demo(
    fig,
    stem: str,
    *,
    formats: Sequence[str] = ("png", "html"),
    width: Optional[int] = None,
    height: Optional[int] = None,
    scale: float = 2.0,
    overwrite: Union[str, OverwritePolicy] = OverwritePolicy.WARN,
) -> dict:
    """Thin wrapper around :func:`save_plotly_chart` with ``chapter=7`` fixed."""
    return save_plotly_chart(
        fig,
        stem,
        chapter=7,
        formats=formats,
        width=width,
        height=height,
        scale=scale,
        overwrite=overwrite,
    )


__all__ = [
    "REPO_ROOT",
    "RAW_DATA_DIR",
    "IMAGES_DIR",
    "np",
    "pd",
    "px",
    "go",
    "save_plotly_chart",
    "export_ch7_demo",
    "OutputManager",
    "OverwritePolicy",
    "WriteRecord",
    "get_output_manager",
]
