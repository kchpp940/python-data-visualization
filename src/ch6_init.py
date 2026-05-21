"""Chapter 6 notebook initialization — Altair backend, Excel reader, export workflow.

Only ``ch6-exercise-*.ipynb`` should import from this module. Other chapters
continue to use the slim ``data_paths`` module for path constants only.

This module is side-effect free: importing it does **not** modify Altair's
global state. Call ``init_chapter6()`` explicitly from the notebook setup cell
to apply the recommended config (vegafusion backend, lifted row cap) and
create a :class:`ChartExportManager` for unified chart exporting.

**Recommended import for all Chapter 6 notebooks**::

    import sys; sys.path.insert(0, '..')
    from src.ch6_init import (
        RAW_DATA_DIR, IMAGES_DIR,
        pd, np, alt,
        read_excel_safe,
        init_chapter6, display_init_status,
        ChartExportManager,
    )
    status = init_chapter6(notebook_name="ch6-exercise-1")
    display_init_status(status)
    exporter = status["export_manager"]

**Export charts with the unified workflow**::

    exporter.export(my_chart, "scatter_plot", display=True)
    exporter.display_status()

    # Or batch export
    exporter.export_batch({
        "chart1": chart1,
        "chart2": chart2,
    })

.. note::
    :func:`save_altair_chart` is kept for backward compatibility only.
    New notebooks should use :class:`ChartExportManager` via
    ``init_chapter6(notebook_name=...)``.
"""

from __future__ import annotations

import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from data_paths import RAW_DATA_DIR, IMAGES_DIR, REPO_ROOT  # noqa: E402

import altair as alt  # noqa: E402

DEFAULT_LARGE_DATA_THRESHOLD: int = 200_000
DEFAULT_EXPORT_FORMATS: Tuple[str, ...] = ("html", "png", "svg")
DEFAULT_SCALE_FACTOR: float = 2.0


def configure_altair(
    *,
    backend: str = "vegafusion",
    max_rows: Optional[int] = None,
    disable_max_rows: bool = False,
    renderer: Optional[str] = None,
    embed_options: Optional[dict] = None,
) -> dict:
    """Configure Altair for the current notebook session.

    Parameters
    ----------
    backend:
        Data transformer backend. ``"vegafusion"`` (default) avoids the 5000-row
        inline-data limit. ``"default"`` keeps Altair's built-in JSON transformer.
        If the requested backend is not available, falls back to ``"default"`` and
        emits a warning so the caller is aware of the downgrade.
    max_rows:
        Set ``alt.data_transformers.max_rows`` to this value.  ``None`` leaves
        the current value untouched.  Mutually exclusive with
        ``disable_max_rows``.
    disable_max_rows:
        If ``True``, call ``alt.data_transformers.disable_max_rows()`` to lift
        Altair's built-in row cap entirely.  Mutually exclusive with
        ``max_rows``.
    renderer:
        Mime renderer (e.g. ``"vl-convert"``, ``"png"``, ``"svg"``).
    embed_options:
        Additional vega-embed options forwarded to the renderer.

    Returns
    -------
    dict
        A status dict with keys:

        - ``backend`` (str): the active transformer name after configuration
        - ``requested_backend`` (str): the backend originally requested
        - ``fell_back`` (bool): ``True`` if the requested backend was unavailable
          and a fallback to ``"default"`` occurred
        - ``max_rows_disabled`` (bool): ``True`` if the row cap was lifted
        - ``max_rows`` (int or None): current ``max_rows`` value, or ``None`` if
          the cap is disabled

    Raises
    ------
    ValueError
        If both ``max_rows`` and ``disable_max_rows`` are set.
    """

    if max_rows is not None and disable_max_rows:
        raise ValueError(
            "max_rows and disable_max_rows are mutually exclusive — "
            "set one or the other, not both."
        )

    requested_backend = backend
    fell_back = False

    available = set(alt.data_transformers.names())
    if backend not in available:
        warnings.warn(
            f"Altair backend '{backend}' is not installed (available: "
            f"{sorted(available)}). Falling back to 'default'. "
            f"Install the missing backend (e.g. `pip install vegafusion`) "
            f"to enable large-dataset rendering.",
            stacklevel=2,
        )
        backend = "default"
        fell_back = True

    alt.data_transformers.enable(backend)

    if max_rows is not None:
        try:
            alt.data_transformers.max_rows = max_rows
        except AttributeError:  # pragma: no cover - older Altair
            pass
    elif disable_max_rows:
        alt.data_transformers.disable_max_rows()

    if renderer is not None:
        try:
            alt.renderers.enable(renderer, embed=embed_options or {})
        except Exception:  # pragma: no cover - renderer may be missing
            pass

    # Read back the current state
    active_backend = alt.data_transformers.active
    try:
        current_max_rows = alt.data_transformers.max_rows
        max_rows_disabled = False
    except Exception:
        current_max_rows = None
        max_rows_disabled = True

    return {
        "backend": active_backend,
        "requested_backend": requested_backend,
        "fell_back": fell_back,
        "max_rows_disabled": max_rows_disabled,
        "max_rows": current_max_rows,
    }


def init_chapter6(
    *,
    backend: str = "vegafusion",
    notebook_name: Optional[str] = None,
    export_base_dir: Optional[Union[str, Path]] = None,
    export_formats: Tuple[str, ...] = DEFAULT_EXPORT_FORMATS,
    export_scale_factor: float = DEFAULT_SCALE_FACTOR,
) -> Dict[str, Any]:
    """One-shot initialiser for Chapter 6 notebooks.

    Applies the recommended config: prefer ``vegafusion`` and lift Altair's
    5000-row cap entirely.  If vegafusion is not available a warning is emitted
    and the notebook falls back to the ``default`` backend.

    Optionally creates a :class:`ChartExportManager` for unified chart
    exporting, avoiding repetitive save code in each notebook cell.

    Parameters
    ----------
    backend:
        Altair data transformer backend. Defaults to ``"vegafusion"``.
    notebook_name:
        If provided, creates a :class:`ChartExportManager` with this name.
        Export files will be prefixed with this name and placed in a
        subdirectory of the same name.
    export_base_dir:
        Base directory for exports. Defaults to ``IMAGES_DIR`` if not provided.
    export_formats:
        Default export formats for the manager.
    export_scale_factor:
        Default scale factor for PNG/SVG exports.

    Returns
    -------
    dict
        Status dict with keys:

        - ``altair``: status dict from :func:`configure_altair`
        - ``export_manager``: :class:`ChartExportManager` instance if
          ``notebook_name`` was provided, else ``None``
        - ``notebook_name``: the notebook name if provided
        - ``initialized_at``: datetime of initialization

        Capture and display this in the notebook setup cell to confirm
        configuration succeeded::

            status = init_chapter6(notebook_name="ch6-exercise-1")
            display_init_status(status)

    This is the **only** place where Altair's global state is mutated during
    normal use.  ``excel_reader`` and ``altair_export`` scripts import this
    module without triggering any Altair configuration.
    """
    altair_status = configure_altair(backend=backend, disable_max_rows=True)

    export_manager = None
    if notebook_name:
        base_dir = Path(export_base_dir) if export_base_dir else IMAGES_DIR
        export_manager = ChartExportManager(
            base_dir=base_dir,
            notebook_name=notebook_name,
            formats=export_formats,
            scale_factor=export_scale_factor,
        )

    return {
        "altair": altair_status,
        "export_manager": export_manager,
        "notebook_name": notebook_name,
        "initialized_at": datetime.now(),
    }


def display_init_status(status: Dict[str, Any]) -> None:
    """Display a formatted init status report in the notebook.

    Shows Altair backend configuration and export manager status (if present)
    in a unified, easy-to-read format.

    Parameters
    ----------
    status:
        Status dict returned by :func:`init_chapter6`.
    """
    try:
        from IPython.display import HTML, display

        altair_status = status.get("altair", {})
        export_manager = status.get("export_manager")
        notebook_name = status.get("notebook_name", "N/A")
        initialized_at = status.get("initialized_at")

        backend = altair_status.get("backend", "unknown")
        requested_backend = altair_status.get("requested_backend", "unknown")
        fell_back = altair_status.get("fell_back", False)
        max_rows_disabled = altair_status.get("max_rows_disabled", False)
        max_rows = altair_status.get("max_rows")

        backend_status_color = "#ef4444" if fell_back else "#22c55e"
        backend_status_text = "⚠️ FALLBACK" if fell_back else "✅ ACTIVE"

        rows_status_color = "#22c55e" if max_rows_disabled else "#f59e0b"
        rows_status_text = "Unlimited" if max_rows_disabled else f"{max_rows:,} rows"

        export_html = ""
        if export_manager is not None:
            export_html = f"""
            <div style="margin-top: 16px; padding-top: 16px;
                 border-top: 1px solid #e5e7eb;">
                <div style="display: flex; align-items: center; gap: 8px;
                     margin-bottom: 12px;">
                    <span style="font-size: 1.1em;">📤</span>
                    <strong style="font-size: 1em; color: #1f2937;">
                        Chart Export Manager
                    </strong>
                </div>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                     gap: 10px;">
                    <div style="padding: 10px; background: #eff6ff; border-radius: 6px;">
                        <div style="color: #1e40af; font-size: 0.85em;
                             font-weight: 500;">📁 Export Directory</div>
                        <div style="font-family: monospace; font-size: 0.85em;
                             color: #374151; word-break: break-all;">
                            {export_manager.export_dir}
                        </div>
                    </div>

                    <div style="padding: 10px; background: #fef3c7; border-radius: 6px;">
                        <div style="color: #92400e; font-size: 0.85em;
                             font-weight: 500;">📄 Default Formats</div>
                        <div style="font-family: monospace; font-size: 0.9em;
                             color: #374151;">
                            {", ".join(export_manager._formats)}
                        </div>
                    </div>

                    <div style="padding: 10px; background: #dcfce7; border-radius: 6px;">
                        <div style="color: #166534; font-size: 0.85em;
                             font-weight: 500;">🔍 Scale Factor</div>
                        <div style="font-size: 1.1em; font-weight: 600; color: #166534;">
                            {export_manager._scale_factor}x
                        </div>
                    </div>

                    <div style="padding: 10px; background: #f3e8ff; border-radius: 6px;">
                        <div style="color: #6b21a8; font-size: 0.85em;
                             font-weight: 500;">📓 Notebook</div>
                        <div style="font-family: monospace; font-size: 0.9em;
                             color: #374151;">
                            {export_manager.notebook_name}
                        </div>
                    </div>
                </div>

                <div style="margin-top: 12px; padding: 10px; background: #f0fdf4;
                     border-left: 4px solid #22c55e; border-radius: 4px;">
                    <div style="color: #166534; font-size: 0.9em;">
                        <strong>Usage:</strong>
                        <code style="background: #dcfce7; padding: 2px 6px;
                             border-radius: 4px;">
                            exporter.export(chart, "chart_name", display=True)
                        </code>
                    </div>
                </div>
            </div>
            """

        time_str = initialized_at.strftime("%Y-%m-%d %H:%M:%S") if initialized_at else "N/A"

        html = f"""
        <div style="padding: 16px; border: 1px solid #e5e7eb;
             border-radius: 8px; background: linear-gradient(to bottom, #f0f9ff, #ffffff);">
            <div style="display: flex; align-items: center; gap: 8px;
                 margin-bottom: 16px;">
                <span style="font-size: 1.4em;">🚀</span>
                <strong style="font-size: 1.2em; color: #1e3a8a;">
                    Chapter 6 Initialization Complete
                </strong>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                 gap: 12px;">
                <div style="padding: 12px; background: #ffffff; border: 1px solid #e5e7eb;
                     border-radius: 6px;">
                    <div style="color: #6b7280; font-size: 0.85em;
                         font-weight: 500; margin-bottom: 4px;">Altair Backend</div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="display: inline-block; width: 10px; height: 10px;
                              border-radius: 50%; background: {backend_status_color};"></span>
                        <span style="font-family: monospace; font-weight: 600; color: #1f2937;">
                            {backend}
                        </span>
                        <span style="font-size: 0.75em; padding: 2px 6px;
                              border-radius: 4px; background: #f3f4f6; color: #6b7280;">
                            requested: {requested_backend}
                        </span>
                    </div>
                    <div style="margin-top: 4px; font-size: 0.8em; color: {backend_status_color};
                         font-weight: 500;">
                        {backend_status_text}
                    </div>
                </div>

                <div style="padding: 12px; background: #ffffff; border: 1px solid #e5e7eb;
                     border-radius: 6px;">
                    <div style="color: #6b7280; font-size: 0.85em;
                         font-weight: 500; margin-bottom: 4px;">Row Limit</div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="display: inline-block; width: 10px; height: 10px;
                              border-radius: 50%; background: {rows_status_color};"></span>
                        <span style="font-weight: 600; color: #1f2937;">
                            {rows_status_text}
                        </span>
                    </div>
                    <div style="margin-top: 4px; font-size: 0.8em; color: {rows_status_color};
                         font-weight: 500;">
                        {'Default 5000-row limit removed' if max_rows_disabled
                         else 'Default row limit active'}
                    </div>
                </div>

                <div style="padding: 12px; background: #ffffff; border: 1px solid #e5e7eb;
                     border-radius: 6px;">
                    <div style="color: #6b7280; font-size: 0.85em;
                         font-weight: 500; margin-bottom: 4px;">Notebook</div>
                    <div style="font-family: monospace; font-weight: 600; color: #1f2937;">
                        {notebook_name}
                    </div>
                    <div style="margin-top: 4px; font-size: 0.8em; color: #6b7280;">
                        {time_str}
                    </div>
                </div>
            </div>

            {export_html}
        </div>
        """
        display(HTML(html))
    except Exception as e:
        print(f"Chapter 6 Init Status:")
        print(f"  Altair backend: {status.get('altair', {}).get('backend', 'unknown')}")
        print(f"  Notebook: {status.get('notebook_name', 'N/A')}")
        if status.get('export_manager'):
            print(f"  Export manager: {status['export_manager']}")


# ---------------------------------------------------------------------------
# Excel reading
# ---------------------------------------------------------------------------
def read_excel_safe(
    path: Union[str, Path],
    sheet_name: Union[int, str] = 0,
    **kwargs,
) -> pd.DataFrame:
    """Read an Excel file with an engine chosen automatically.

    * ``.xlsx`` / ``.xlsm`` -> ``openpyxl``
    * ``.xls``             -> ``xlrd`` (if installed) or ``openpyxl``
    """
    p = Path(path)
    suffix = p.suffix.lower()
    engine = kwargs.pop("engine", None)
    if engine is None:
        if suffix in (".xlsx", ".xlsm"):
            engine = "openpyxl"
        elif suffix == ".xls":
            try:
                import xlrd  # noqa: F401
                engine = "xlrd"
            except ImportError:  # pragma: no cover
                engine = "openpyxl"
    return pd.read_excel(p, sheet_name=sheet_name, engine=engine, **kwargs)


# ---------------------------------------------------------------------------
# Chart export
# ---------------------------------------------------------------------------
class _NullContext:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def save_altair_chart(
    chart,
    output_dir: Union[str, Path],
    stem: str,
    *,
    formats=("png", "svg", "html"),
    scale_factor: float = 2.0,
) -> dict:
    """Save an Altair chart to PNG / SVG / HTML.

    .. deprecated::
        Prefer :class:`ChartExportManager` for unified export workflow with
        consistent naming, automatic directory management, and status tracking.
        This function is kept for backward compatibility.

    HTML uses the default renderer.  PNG/SVG temporarily switch to ``vl-convert``
    so vegafusion-backed charts can still produce static assets.
    """
    warnings.warn(
        "save_altair_chart() is deprecated. Use ChartExportManager instead for "
        "unified export workflow with consistent naming and status tracking. "
        "See init_chapter6(notebook_name=...) for details.",
        DeprecationWarning,
        stacklevel=2,
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved: dict = {}

    for fmt in formats:
        target = output_dir / f"{stem}.{fmt}"
        if fmt == "html":
            chart.save(str(target))
        else:
            try:
                if "vl-convert" in alt.renderers.names():
                    ctx = alt.renderers.enable("vl-convert", ppi=72 * scale_factor)
                else:
                    ctx = _NullContext()
                with ctx:
                    chart.save(str(target))
            except Exception:
                chart.save(str(target))
        saved[fmt] = str(target)
    return saved


# ---------------------------------------------------------------------------
# Chart Export Manager
# ---------------------------------------------------------------------------
class ChartExportManager:
    """Unified chart export workflow for Chapter 6 notebooks.

    Provides consistent file naming, output directory management, export
    history tracking, and status display. Avoids repetitive save code in
    each notebook cell.

    Parameters
    ----------
    base_dir:
        Base directory for exports. A subdirectory named after the notebook
        stem will be created under this path.
    notebook_name:
        Name of the current notebook (e.g. "ch6-exercise-1") used to create
        the export subdirectory and prefix filenames.
    formats:
        Default export formats. Defaults to ``DEFAULT_EXPORT_FORMATS``.
    scale_factor:
        PNG/SVG scale factor (multiplied by 72 PPI). Defaults to
        ``DEFAULT_SCALE_FACTOR``.

    Examples
    --------
    Basic usage in a notebook::

        exporter = ChartExportManager(IMAGES_DIR, "ch6-exercise-1")
        exporter.export(chart, "scatter_plot_fuel_cost")
        exporter.display_status()
    """

    def __init__(
        self,
        base_dir: Union[str, Path],
        notebook_name: str,
        *,
        formats: Tuple[str, ...] = DEFAULT_EXPORT_FORMATS,
        scale_factor: float = DEFAULT_SCALE_FACTOR,
    ) -> None:
        self._base_dir = Path(base_dir)
        self._notebook_name = notebook_name
        self._formats = formats
        self._scale_factor = scale_factor
        self._export_dir = self._base_dir / notebook_name
        self._export_dir.mkdir(parents=True, exist_ok=True)
        self._history: List[Dict[str, Any]] = []
        self._created_at = datetime.now()

    @property
    def export_dir(self) -> Path:
        """The directory where charts are exported."""
        return self._export_dir

    @property
    def notebook_name(self) -> str:
        """Notebook name used for file naming."""
        return self._notebook_name

    @property
    def history(self) -> List[Dict[str, Any]]:
        """Read-only view of export history."""
        return list(self._history)

    @property
    def total_exports(self) -> int:
        """Total number of charts exported."""
        return len(self._history)

    def _build_filename(self, chart_id: str, fmt: str) -> str:
        """Build consistent filename: {notebook}_{chart_id}.{fmt}."""
        return f"{self._notebook_name}_{chart_id}.{fmt}"

    def _build_output_path(self, chart_id: str, fmt: str) -> Path:
        """Build full output path for a chart format."""
        return self._export_dir / self._build_filename(chart_id, fmt)

    def export(
        self,
        chart: Any,
        chart_id: str,
        *,
        formats: Optional[Tuple[str, ...]] = None,
        scale_factor: Optional[float] = None,
        display: bool = False,
    ) -> Dict[str, Any]:
        """Export an Altair chart to multiple formats.

        Parameters
        ----------
        chart:
            The Altair chart object to export.
        chart_id:
            Unique identifier for this chart (used in filename). Should be
            a valid filename component (no spaces or special characters).
        formats:
            Override default export formats for this chart only.
        scale_factor:
            Override default scale factor for this chart only.
        display:
            If True, display the result summary after export.

        Returns
        -------
        dict
            Export result with keys:
            - ``chart_id``: the chart identifier
            - ``timestamp``: when the export occurred
            - ``formats``: which formats were exported
            - ``paths``: dict mapping format to output path as string
            - ``success``: True if all formats exported successfully
            - ``errors``: list of (format, error_message) tuples
        """
        use_formats = formats or self._formats
        use_scale = scale_factor or self._scale_factor
        timestamp = datetime.now()

        result = {
            "chart_id": chart_id,
            "timestamp": timestamp,
            "formats": use_formats,
            "paths": {},
            "success": True,
            "errors": [],
        }

        for fmt in use_formats:
            target = self._build_output_path(chart_id, fmt)
            try:
                if fmt == "html":
                    chart.save(str(target))
                else:
                    try:
                        if "vl-convert" in alt.renderers.names():
                            ctx = alt.renderers.enable(
                                "vl-convert", ppi=72 * use_scale
                            )
                        else:
                            ctx = _NullContext()
                        with ctx:
                            chart.save(str(target))
                    except Exception:
                        chart.save(str(target))
                result["paths"][fmt] = str(target)
            except Exception as e:
                result["success"] = False
                result["errors"].append((fmt, str(e)))

        self._history.append(result)

        if display:
            self._display_result(result)

        return result

    def export_batch(
        self,
        charts: Dict[str, Any],
        *,
        formats: Optional[Tuple[str, ...]] = None,
        scale_factor: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Export multiple charts in batch.

        Parameters
        ----------
        charts:
            Dictionary mapping chart_id to chart object.
        formats:
            Override default export formats.
        scale_factor:
            Override default scale factor.

        Returns
        -------
        list
            List of export result dicts.
        """
        results = []
        for chart_id, chart in charts.items():
            results.append(
                self.export(
                    chart,
                    chart_id,
                    formats=formats,
                    scale_factor=scale_factor,
                    display=False,
                )
            )
        return results

    def _display_result(self, result: Dict[str, Any]) -> None:
        """Display a single export result in notebook-friendly format.

        Failure states are displayed prominently with red borders,
        background highlighting, and explicit error details.
        """
        try:
            from IPython.display import HTML, display

            is_success = result["success"]
            status_color = "#22c55e" if is_success else "#ef4444"
            status_text = "SUCCESS" if is_success else "FAILED"
            border_color = "#22c55e" if is_success else "#ef4444"
            bg_color = "#f0fdf4" if is_success else "#fef2f2"

            paths_html = ""
            if result["paths"]:
                paths_items = "".join(
                    f'<li><code style="color: #3b82f6;">{fmt}</code>: '
                    f'<code style="font-size: 0.85em;">{path}</code></li>'
                    for fmt, path in result["paths"].items()
                )
                paths_html = f"""
                <div style="margin-top: 8px;">
                    <strong>Exported to:</strong>
                    <ul style="margin: 4px 0 0 20px; padding: 0;">{paths_items}</ul>
                </div>
                """

            errors_html = ""
            if result["errors"]:
                errors_items = "".join(
                    f'<div style="padding: 6px 8px; margin: 4px 0; '
                    f'background: #fee2e2; border-left: 3px solid #ef4444; '
                    f'border-radius: 4px;">'
                    f'<code style="color: #991b1b; font-weight: 600;">{fmt}</code>: '
                    f'<span style="color: #991b1b;">{msg}</span>'
                    f'</div>'
                    for fmt, msg in result["errors"]
                )
                errors_html = f"""
                <div style="margin-top: 12px; padding-top: 12px;
                     border-top: 1px dashed #fca5a5;">
                    <strong style="color: #ef4444;">⚠️ Export Errors:</strong>
                    {errors_items}
                </div>
                """

            failed_formats = [fmt for fmt, _ in result["errors"]]
            failed_info = ""
            if failed_formats:
                failed_info = f"""
                <span style="margin-left: 8px; padding: 2px 8px;
                      background: #fecaca; border-radius: 12px;
                      color: #991b1b; font-size: 0.8em; font-weight: 600;">
                    Failed: {", ".join(failed_formats)}
                </span>
                """

            html = f"""
            <div style="padding: 14px; border: 2px solid {border_color};
                 border-radius: 8px; background: {bg_color};">
                <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                    <span style="display: inline-block; width: 14px; height: 14px;
                          border-radius: 50%; background: {status_color};
                          box-shadow: 0 0 0 3px {status_color}33;"></span>
                    <strong style="font-size: 1.05em;">{result["chart_id"]}</strong>
                    <span style="color: {status_color}; font-weight: 700;
                          font-size: 0.9em; padding: 2px 10px;
                          background: {status_color}22; border-radius: 4px;">
                        {status_text}
                    </span>
                    {failed_info}
                </div>
                {paths_html}
                {errors_html}
            </div>
            """
            display(HTML(html))
        except Exception:
            print(f"Exported '{result['chart_id']}': "
                  f"{'OK' if result['success'] else 'FAILED'}")
            for fmt, path in result["paths"].items():
                print(f"  {fmt}: {path}")
            if result.get("errors"):
                print("Errors:")
                for fmt, msg in result["errors"]:
                    print(f"  {fmt}: {msg}")

    def display_status(self) -> None:
        """Display current export manager status in notebook.

        Shows:
        - Export directory
        - Total charts exported
        - Recent export history
        """
        try:
            from IPython.display import HTML, display

            success_count = sum(1 for h in self._history if h["success"])
            fail_count = self.total_exports - success_count

            history_html = ""
            if self._history:
                recent = self._history[-5:][::-1]
                history_items = "".join(
                    f'<tr>'
                    f'<td><code>{h["chart_id"]}</code></td>'
                    f'<td>{h["timestamp"].strftime("%H:%M:%S")}</td>'
                    f'<td>{" ".join(h["formats"])}</td>'
                    f'<td><span style="color: {"#22c55e" if h["success"] else "#ef4444"};'
                    f'">{"✓" if h["success"] else "✗"}</span></td>'
                    f'</tr>'
                    for h in recent
                )
                history_html = f"""
                <div style="margin-top: 16px;">
                    <strong style="color: #374151;">Recent Exports</strong>
                    <table style="width: 100%; margin-top: 8px; border-collapse: collapse;
                           font-size: 0.9em;">
                        <thead>
                            <tr style="background: #f3f4f6;">
                                <th style="text-align: left; padding: 6px 8px;
                                    border: 1px solid #e5e7eb;">Chart ID</th>
                                <th style="text-align: left; padding: 6px 8px;
                                    border: 1px solid #e5e7eb;">Time</th>
                                <th style="text-align: left; padding: 6px 8px;
                                    border: 1px solid #e5e7eb;">Formats</th>
                                <th style="text-align: left; padding: 6px 8px;
                                    border: 1px solid #e5e7eb;">Status</th>
                            </tr>
                        </thead>
                        <tbody>{history_items}</tbody>
                    </table>
                    {f'<p style="color: #6b7280; font-size: 0.85em; margin-top: 4px;">'
                     f'Showing last {len(recent)} of {self.total_exports} total exports'
                     f'</p>' if self.total_exports > 5 else ''}
                </div>
                """

            html = f"""
            <div style="padding: 16px; border: 1px solid #e5e7eb;
                 border-radius: 8px; background: linear-gradient(to bottom, #fafafa, #fff);">
                <div style="display: flex; align-items: center; gap: 8px;
                     margin-bottom: 12px;">
                    <span style="font-size: 1.25em;">📊</span>
                    <strong style="font-size: 1.1em; color: #1f2937;">
                        Chart Export Manager Status
                    </strong>
                </div>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                     gap: 12px;">
                    <div style="padding: 10px; background: #eff6ff; border-radius: 6px;">
                        <div style="color: #1e40af; font-size: 0.85em;
                             font-weight: 500;">📁 Export Directory</div>
                        <div style="font-family: monospace; font-size: 0.9em;
                             color: #374151; word-break: break-all;">
                            {self._export_dir}
                        </div>
                    </div>

                    <div style="padding: 10px; background: #fef3c7; border-radius: 6px;">
                        <div style="color: #92400e; font-size: 0.85em;
                             font-weight: 500;">📓 Notebook</div>
                        <div style="font-family: monospace; font-size: 0.9em;
                             color: #374151;">
                            {self._notebook_name}
                        </div>
                    </div>

                    <div style="padding: 10px; background: #dcfce7; border-radius: 6px;">
                        <div style="color: #166534; font-size: 0.85em;
                             font-weight: 500;">✅ Total Exports</div>
                        <div style="font-size: 1.25em; font-weight: 600; color: #166534;">
                            {success_count}
                            <span style="font-size: 0.75em; color: #6b7280;">
                                ok / {self.total_exports} total
                            </span>
                        </div>
                    </div>

                    <div style="padding: 10px; background: #fee2e2; border-radius: 6px;">
                        <div style="color: #991b1b; font-size: 0.85em;
                             font-weight: 500;">❌ Failed</div>
                        <div style="font-size: 1.25em; font-weight: 600; color: #991b1b;">
                            {fail_count}
                        </div>
                    </div>
                </div>

                <div style="margin-top: 12px; padding-top: 12px;
                     border-top: 1px solid #e5e7eb;">
                    <span style="color: #6b7280; font-size: 0.85em;">
                        Default formats: <code>{", ".join(self._formats)}</code> |
                        Scale factor: <code>{self._scale_factor}x</code> |
                        Manager created: {self._created_at.strftime("%Y-%m-%d %H:%M:%S")}
                    </span>
                </div>

                {history_html}
            </div>
            """
            display(HTML(html))
        except Exception:
            print(f"Export Manager: {self._notebook_name}")
            print(f"  Directory: {self._export_dir}")
            print(f"  Total exports: {self.total_exports}")

    def get_export_path(self, chart_id: str, fmt: str) -> Path:
        """Get the expected path for a chart without exporting it.

        Useful for references or documentation.
        """
        return self._build_output_path(chart_id, fmt)

    def list_exports(self) -> List[Path]:
        """List all files in the export directory."""
        return sorted(self._export_dir.glob("*"))

    def __repr__(self) -> str:
        return (
            f"ChartExportManager(notebook='{self._notebook_name}', "
            f"exports={self.total_exports}, dir='{self._export_dir}')"
        )


__all__ = [
    "REPO_ROOT",
    "RAW_DATA_DIR",
    "IMAGES_DIR",
    "DEFAULT_LARGE_DATA_THRESHOLD",
    "DEFAULT_EXPORT_FORMATS",
    "DEFAULT_SCALE_FACTOR",
    "ChartExportManager",
    "alt",
    "np",
    "pd",
    "configure_altair",
    "init_chapter6",
    "display_init_status",
    "read_excel_safe",
    "save_altair_chart",
]
