"""Notebook initialization entry point.

Convenience wrapper that applies recommended Chapter 6 configuration:
- Prefer ``vegafusion`` backend for large dataset support
- Lift Altair's 5000-row cap entirely
- Return a status dict with ``export_manager`` key

This is the **only** place where Altair's global state is mutated during
normal use.  Other modules import config components without triggering
any Altair configuration.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from data_paths import IMAGES_DIR

from .altair_config import configure_altair
from .chart_exporter import ChartExportManager


def display_init_status(status: Dict[str, Any]) -> None:
    """Display initialization status in a notebook-friendly format.

    Parameters
    ----------
    status:
        Status dict returned by :func:`init_chapter6`.

    Example
    -------
    >>> status = init_chapter6(notebook_name="my-notebook")
    >>> display_init_status(status)
    """
    try:
        from IPython.display import HTML, display

        backend = status.get("backend", "unknown")
        requested = status.get("requested_backend", backend)
        fell_back = status.get("fell_back", False)
        max_rows_disabled = status.get("max_rows_disabled", False)
        max_rows = status.get("max_rows")
        notebook_name = status.get("notebook_name", "unnamed")

        status_lines = [
            f"<strong>Chapter 6 Initialized:</strong> {notebook_name}",
            f"<ul>",
            f"  <li><strong>Backend:</strong> {backend}",
        ]

        if fell_back:
            status_lines.append(
                f"    <em>(fell back from '{requested}' — install vegafusion for large datasets)</em>"
            )
        status_lines.append(f"</li>")

        if max_rows_disabled:
            status_lines.append(
                f"  <li><strong>Row limit:</strong> disabled (unlimited)</li>"
            )
        else:
            status_lines.append(
                f"  <li><strong>Row limit:</strong> {max_rows or 'default'}</li>"
            )

        export_mgr = status.get("export_manager")
        if export_mgr:
            status_lines.append(
                f"  <li><strong>Export manager:</strong> ready "
                f"(output_dir: {export_mgr.output_dir})</li>"
            )

        status_lines.append("</ul>")
        display(HTML("\n".join(status_lines)))
    except Exception:
        print("Chapter 6 initialization status:")
        print(f"  backend: {status.get('backend', 'unknown')}")
        print(f"  export_manager: {'ready' if status.get('export_manager') else 'none'}")


def init_chapter6(
    *,
    backend: str = "vegafusion",
    notebook_name: Optional[str] = None,
    export_dir: Optional[str] = None,
    default_formats: Tuple[str, ...] = ("png", "svg", "html"),
    default_scale_factor: float = 2.0,
) -> Dict[str, Any]:
    """One-shot initialiser for Chapter 6 notebooks.

    Applies the recommended config: prefer ``vegafusion`` and lift Altair's
    5000-row cap entirely.  If vegafusion is not available a warning is emitted
    and the notebook falls back to the ``default`` backend.

    Parameters
    ----------
    backend:
        Data transformer backend (default ``"vegafusion"``).
    notebook_name:
        Optional name of the notebook for status display.
    export_dir:
        Directory for chart exports. Defaults to ``IMAGES_DIR`` from
        ``data_paths``.
    default_formats:
        Default formats for the export manager.
    default_scale_factor:
        Default scale factor for the export manager.

    Returns
    -------
    dict
        Status dict with keys:

        - ``backend``: active transformer name
        - ``requested_backend``: originally requested backend
        - ``fell_back``: True if fallback occurred
        - ``max_rows_disabled``: True if row cap was lifted
        - ``max_rows``: current max_rows value (or None if disabled)
        - ``export_manager``: a :class:`~src.ch6.chart_exporter.ChartExportManager` instance
        - ``notebook_name``: the notebook name if provided

    Example
    -------
    First cell of any Chapter 6 notebook::

        import sys; sys.path.insert(0, '..')
        from src.ch6 import (
            RAW_DATA_DIR, IMAGES_DIR,
            pd, np, alt,
            read_excel_safe, save_altair_chart,
            init_chapter6, display_init_status,
            ChartExportManager,
        )
        status = init_chapter6(notebook_name="ch6-exercise-3")
        display_init_status(status)
        exporter = status["export_manager"]

        # Later, use the manager:
        # exporter.export(chart, "my_chart")
    """
    config_status = configure_altair(backend=backend, disable_max_rows=True)
    out_dir = export_dir if export_dir is not None else IMAGES_DIR
    manager = ChartExportManager(
        output_dir=out_dir,
        default_formats=default_formats,
        default_scale_factor=default_scale_factor,
    )

    status = dict(config_status)
    status["export_manager"] = manager
    if notebook_name:
        status["notebook_name"] = notebook_name
    return status
