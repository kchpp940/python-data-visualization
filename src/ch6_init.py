"""Chapter 6 notebook initialization — Altair backend, Excel reader, export helpers.

Only ``ch6-exercise-*.ipynb`` should import from this module. Other chapters
continue to use the slim ``data_paths`` module for path constants only.

This module is side-effect free: importing it does **not** modify Altair's
global state. Call ``init_chapter6()`` explicitly from the notebook setup cell
to apply the recommended config (vegafusion backend, lifted row cap).

Usage (first cell of any ch6 notebook)::

    import sys; sys.path.insert(0, '..')
    from src.ch6_init import (
        RAW_DATA_DIR, IMAGES_DIR,
        pd, np, alt,
        read_excel_safe, save_altair_chart,
        init_chapter6,
    )
    init_chapter6()
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Union

import numpy as np
import pandas as pd

from data_paths import RAW_DATA_DIR, IMAGES_DIR, REPO_ROOT  # noqa: E402
from src.output_manager import (  # noqa: E402
    OutputManager,
    OverwritePolicy,
    WriteRecord,
    get_output_manager,
)

import altair as alt  # noqa: E402

DEFAULT_LARGE_DATA_THRESHOLD: int = 200_000


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
) -> dict:
    """One-shot initialiser for Chapter 6 notebooks.

    Applies the recommended config: prefer ``vegafusion`` and lift Altair's
    5000-row cap entirely.  If vegafusion is not available a warning is emitted
    and the notebook falls back to the ``default`` backend.

    Returns
    -------
    dict
        Status dict from :func:`configure_altair`.  Capture and display this
        in the notebook setup cell to confirm configuration succeeded::

            status = init_chapter6()
            status

    This is the **only** place where Altair's global state is mutated during
    normal use.  ``excel_reader`` and ``altair_export`` scripts import this
    module without triggering any Altair configuration.
    """
    return configure_altair(backend=backend, disable_max_rows=True)


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
# Chart export (delegates to src.output_manager.OutputManager)
# ---------------------------------------------------------------------------
class _NullContext:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def save_altair_chart(
    chart,
    output_dir: Optional[Union[str, Path]] = None,
    stem: Optional[str] = None,
    *,
    formats=("png", "svg", "html"),
    scale_factor: float = 2.0,
    chapter: Optional[Union[int, str]] = None,
    overwrite: Union[str, OverwritePolicy] = OverwritePolicy.WARN,
) -> dict:
    """Save an Altair chart to PNG / SVG / HTML.

    HTML uses the default renderer.  PNG/SVG temporarily switch to ``vl-convert``
    so vegafusion-backed charts can still produce static assets.

    When *output_dir* is ``None`` the chart is routed through the module-level
    :class:`~src.output_manager.OutputManager` (see :func:`get_output_manager`),
    which writes to the unified ``<repo>/output/altair/`` directory and honours
    the configured overwrite policy.  Passing an explicit *output_dir* restores
    the pre-existing "write to an arbitrary folder" behaviour — this is kept for
    backwards compatibility with older notebooks.

    When *stem* is ``None`` and the chart carries a ``title``, the title is used
    to derive a safe stem; otherwise we fall back to ``"untitled"``.
    """
    manager: Optional[OutputManager] = None
    if output_dir is None:
        manager = get_output_manager()
        if overwrite != manager.overwrite:
            manager = OutputManager(
                root=manager.root,
                overwrite=overwrite,
                category_dirs=manager._category_dirs,
                dry_run=manager.dry_run,
            )
    else:
        output_dir = Path(output_dir)

    if stem is None:
        try:
            title = getattr(chart, "title", None) or ""
            if isinstance(title, dict):
                title = title.get("text", "") or ""
            stem = str(title)
        except Exception:  # pragma: no cover - defensive
            stem = ""
        stem = stem or "untitled"

    if manager is not None:
        records = manager.save_altair(
            chart,
            stem,
            chapter=chapter,
            formats=formats,
            scale_factor=scale_factor,
        )
        return {fmt: str(rec.path) for fmt, rec in records.items()}

    # Legacy path: write directly to the caller-provided folder.
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved: dict = {}

    for fmt in formats:
        target = output_dir / f"{stem}.{fmt}"
        if target.exists() and overwrite == OverwritePolicy.ERROR:
            raise FileExistsError(
                f"Refusing to overwrite {target} (overwrite='error')."
            )
        if target.exists() and overwrite == OverwritePolicy.SKIP:
            saved[fmt] = str(target)
            continue
        if target.exists() and overwrite == OverwritePolicy.WARN:
            warnings.warn(f"Overwriting existing output file: {target}", stacklevel=2)
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


def export_ch6_demo(
    chart,
    stem: str,
    *,
    chapter: int = 6,
    formats=("png", "svg", "html"),
    scale_factor: float = 2.0,
    overwrite: Union[str, OverwritePolicy] = OverwritePolicy.WARN,
) -> dict:
    """Export a Chapter 6 demo chart through the unified output layer.

    This is a thin convenience wrapper around
    :meth:`src.output_manager.OutputManager.save_altair` that pre-fills
    ``chapter=6`` so notebooks can export demo figures with a single call::

        export_ch6_demo(chart, stem="fuel_cost_scatter")

    The chart is written to ``<repo>/output/altair/ch06_<stem>.<ext>`` and
    the overwrite policy defaults to ``WARN`` — pass ``overwrite=OverwritePolicy.ERROR``
    to turn accidental overwrites into hard errors.
    """
    manager = get_output_manager()
    if overwrite != manager.overwrite:
        manager = OutputManager(
            root=manager.root,
            overwrite=overwrite,
            category_dirs=manager._category_dirs,
            dry_run=manager.dry_run,
        )
    records = manager.save_altair(
        chart,
        stem,
        chapter=chapter,
        formats=formats,
        scale_factor=scale_factor,
    )
    return {fmt: str(rec.path) for fmt, rec in records.items()}


class ChartExportManager:
    """High-level chart export helper backed by :class:`OutputManager`.

    This is the class used in ``ch6-exercise-3`` for the
    ``exporter.export()`` / ``exporter.export_batch()`` workflow.  It
    delegates all path resolution and overwrite handling to
    :class:`~src.output_manager.OutputManager` so the exported files end
    up in the unified output layer (``<repo>/output/altair/``).

    Typical usage in a notebook::

        from src.ch6_init import ChartExportManager, get_output_manager
        exporter = ChartExportManager(
            output_manager=get_output_manager(),
            chapter=6,
        )
        result = exporter.export(chart, "my_chart", formats=("html", "png"))
    """

    def __init__(
        self,
        *,
        output_manager: Optional[OutputManager] = None,
        chapter: Optional[Union[int, str]] = None,
        default_formats: Sequence[str] = ("html", "png", "svg"),
        scale_factor: float = 2.0,
    ) -> None:
        self._manager: OutputManager = output_manager or get_output_manager()
        self._chapter = chapter
        self._default_formats = tuple(default_formats)
        self._scale_factor = scale_factor
        self._records: list[WriteRecord] = []

    def export(
        self,
        chart: Any,
        stem: str,
        *,
        formats: Optional[Iterable[str]] = None,
        display: bool = False,
    ) -> dict:
        """Export a single chart.

        Parameters
        ----------
        chart:
            An Altair chart object.
        stem:
            Filename stem (extension-less).
        formats:
            Formats to export.  Defaults to ``self.default_formats``.
        display:
            If ``True``, print a summary line per format.

        Returns
        -------
        dict
            ``{"success": bool, "paths": {...}, "errors": {...}}``.
        """
        fmts = tuple(formats) if formats else self._default_formats
        records = self._manager.save_altair(
            chart,
            stem,
            chapter=self._chapter,
            formats=fmts,
            scale_factor=self._scale_factor,
        )
        self._records.extend(records.values())
        paths: dict[str, str] = {}
        errors: dict[str, str] = {}
        for fmt, rec in records.items():
            if rec.status == "failed":
                errors[fmt] = rec.error or "unknown error"
            else:
                paths[fmt] = str(rec.path)
            if display:
                status = rec.status.upper()
                suffix = f" — {rec.error}" if rec.error else ""
                print(f"  [{status}] {rec.path}{suffix}")
        return {
            "success": len(errors) == 0,
            "paths": paths,
            "errors": errors,
        }

    def export_batch(
        self,
        chart_map: Mapping[str, Any],
        *,
        formats: Optional[Iterable[str]] = None,
    ) -> list[dict]:
        """Export multiple charts.

        Parameters
        ----------
        chart_map:
            Mapping of ``stem`` -> chart object.
        formats:
            Formats for every chart.  Defaults to ``self.default_formats``.

        Returns
        -------
        list[dict]
            One result dict per chart, each with the same structure as
            :meth:`export`.
        """
        results: list[dict] = []
        for stem, chart in chart_map.items():
            result = self.export(chart, stem, formats=formats)
            result["chart_id"] = stem
            results.append(result)
        return results

    def display_status(self) -> None:
        """Print a summary of all exports performed so far."""
        print(self._manager.report())
        failures = self._manager.failures()
        if failures:
            print(f"\n{len(failures)} failure(s):")
            for rec in failures:
                print(f"  - {rec.path}: {rec.error}")

    def list_exports(self) -> list[Path]:
        """Return paths of all successfully written files."""
        return [
            rec.path
            for rec in self._records
            if rec.status in ("written", "overwritten")
        ]


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
    "read_excel_safe",
    "save_altair_chart",
    "export_ch6_demo",
    "ChartExportManager",
    "OutputManager",
    "OverwritePolicy",
    "get_output_manager",
]
