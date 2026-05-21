"""Chapter 6 notebook initialization — Altair backend, Excel reader, export workflow.

Only ``ch6-exercise-*.ipynb`` should import from this module. Other chapters
continue to use the slim ``data_paths`` module for path constants only.

This module is side-effect free: importing it does **not** modify Altair's
global state. Call ``init_chapter6()`` explicitly from the notebook setup cell
to apply the recommended config (vegafusion backend, lifted row cap) **and**
to obtain a reusable :class:`AltairExportWorkflow` (accessible on the
returned status dict as ``.export``) that lets the notebook export every
chart in a uniform way (HTML/PNG/SVG) without per-chart save code.

Usage (first cell of any ch6 notebook)::

    import sys; sys.path.insert(0, '..')
    from src.ch6_init import (
        RAW_DATA_DIR, IMAGES_DIR,
        pd, np, alt,
        read_excel_safe, save_altair_chart,
        init_chapter6, AltairExportWorkflow,
    )
    status = init_chapter6()
    status         # inspect backend / row cap state
    status.export  # inspect output dir, naming scheme, available backends
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional, Union

import numpy as np
import pandas as pd

from data_paths import RAW_DATA_DIR, IMAGES_DIR, REPO_ROOT  # noqa: E402

import altair as alt  # noqa: E402

DEFAULT_LARGE_DATA_THRESHOLD: int = 200_000
DEFAULT_EXPORT_FORMATS: tuple[str, ...] = ("png", "svg", "html")
DEFAULT_EXPORT_SCALE: float = 2.0


class ExportStatus(dict):
    """A dict that also exposes an ``.export`` attribute for the workflow.

    Returned by :func:`init_chapter6` so callers can inspect both the backend
    configuration status *and* the export workflow in a single object.
    """

    export: Optional["AltairExportWorkflow"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.export = None

    def _repr_html_(self) -> str:
        rows = "".join(
            f"<tr><th>{k}</th><td><code>{v}</code></td></tr>"
            for k, v in self.items()
        )
        return (
            f"<table><thead><tr><th colspan='2'>Chapter 6 — init status</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
        )


def configure_altair(
    *,
    backend: str = "vegafusion",
    max_rows: Optional[int] = None,
    disable_max_rows: bool = False,
    renderer: Optional[str] = None,
    embed_options: Optional[dict] = None,
) -> ExportStatus:
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
    ExportStatus
        A dict subclass with keys:

        - ``backend`` (str): the active transformer name after configuration
        - ``requested_backend`` (str): the backend originally requested
        - ``fell_back`` (bool): ``True`` if the requested backend was unavailable
          and a fallback to ``"default"`` occurred
        - ``max_rows_disabled`` (bool): ``True`` if the row cap was lifted
        - ``max_rows`` (int or None): current ``max_rows`` value, or ``None`` if
          the cap is disabled

        The object also exposes an ``.export`` attribute that will be set to
        the active :class:`AltairExportWorkflow` after :func:`init_chapter6`
        runs.

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

    return ExportStatus(
        {
            "backend": active_backend,
            "requested_backend": requested_backend,
            "fell_back": fell_back,
            "max_rows_disabled": max_rows_disabled,
            "max_rows": current_max_rows,
        }
    )


def init_chapter6(
    *,
    backend: str = "vegafusion",
    output_dir: Union[str, Path] = IMAGES_DIR,
    stem_prefix: str = "ch6",
    formats: Iterable[str] = DEFAULT_EXPORT_FORMATS,
    scale_factor: float = DEFAULT_EXPORT_SCALE,
) -> ExportStatus:
    """One-shot initialiser for Chapter 6 notebooks.

    Applies the recommended config: prefer ``vegafusion`` and lift Altair's
    5000-row cap entirely.  If vegafusion is not available a warning is emitted
    and the notebook falls back to the ``default`` backend.

    Also creates a reusable :class:`AltairExportWorkflow` and attaches it to
    the returned status dict as ``status.export`` so every chart in the
    notebook can be saved with a single call (no per-chart path, naming, or
    format boilerplate).

    Parameters
    ----------
    backend:
        Data transformer backend forwarded to :func:`configure_altair`.
    output_dir:
        Directory where exported chart files will be written (created if it
        does not exist).  Defaults to ``IMAGES_DIR`` from
        :mod:`data_paths`.
    stem_prefix:
        Prepended to every exported file's stem (e.g. ``"ch6"`` yields
        ``ch6-scatter.png``).  Helps group exported assets by chapter.
    formats:
        File formats to produce for every :meth:`AltairExportWorkflow.save`
        call.  Defaults to ``("png", "svg", "html")``.
    scale_factor:
        Scale factor for raster (PNG) output.  Defaults to ``2.0`` (retina).

    Returns
    -------
    ExportStatus
        Status dict from :func:`configure_altair`.  Capture and display this
        in the notebook setup cell to confirm configuration succeeded::

            status = init_chapter6()
            status
            status.export  # <- reusable exporter

    This is the **only** place where Altair's global state is mutated during
    normal use.  ``excel_reader`` and ``altair_export`` scripts import this
    module without triggering any Altair configuration.
    """
    status = configure_altair(backend=backend, disable_max_rows=True)
    workflow = AltairExportWorkflow(
        output_dir=output_dir,
        stem_prefix=stem_prefix,
        formats=formats,
        scale_factor=scale_factor,
    )
    status.export = workflow
    status["export_dir"] = str(workflow.output_dir)
    status["export_formats"] = list(workflow.formats)
    status["export_stem_prefix"] = workflow.stem_prefix
    status["export_scale_factor"] = workflow.scale_factor
    status["export_has_vl_convert"] = workflow.has_vl_convert
    status["export_has_vegafusion"] = workflow.has_vegafusion
    return status


# ---------------------------------------------------------------------------
# Chart export workflow
# ---------------------------------------------------------------------------
@dataclass
class AltairExportWorkflow:
    """Reusable chart export workflow for Chapter 6 notebooks.

    Encapsulates the output directory, file naming convention, target formats,
    and raster scale factor so notebook cells don't have to repeat them for
    every chart.  Backend availability (``vl-convert``, ``vegafusion``) is
    probed once at construction time and exposed as attributes for easy
    inspection in the notebook.

    Typical usage (after ``init_chapter6()``)::

        chart = alt.Chart(df).mark_circle().encode(...)
        status.export.save(chart, "fuel-cost-scatter")
        # -> writes IMAGES_DIR/ch6-fuel-cost-scatter.{png,svg,html}

    The :meth:`save` call returns a dict of format -> saved path for
    reference or display in the notebook.
    """

    output_dir: Path
    stem_prefix: str = "ch6"
    formats: tuple[str, ...] = DEFAULT_EXPORT_FORMATS
    scale_factor: float = DEFAULT_EXPORT_SCALE
    has_vl_convert: bool = field(init=False)
    has_vegafusion: bool = field(init=False)
    _registry: dict[str, dict[str, str]] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self) -> None:
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.formats = tuple(self.formats)
        self.has_vl_convert = "vl-convert" in alt.renderers.names()
        self.has_vegafusion = "vegafusion" in alt.data_transformers.names()

    def _stem(self, name: str) -> str:
        cleaned = name.strip().replace(" ", "_")
        if self.stem_prefix:
            return f"{self.stem_prefix}-{cleaned}"
        return cleaned

    def save(
        self,
        chart,
        name: str,
        *,
        formats: Optional[Iterable[str]] = None,
        scale_factor: Optional[float] = None,
    ) -> dict[str, str]:
        """Save *chart* using the configured defaults.

        Parameters
        ----------
        chart:
            An Altair chart (``alt.Chart``, ``alt.LayerChart``, etc.).
        name:
            Descriptive fragment used in the output filename, e.g.
            ``"fuel-cost-scatter"``.  Spaces are replaced with underscores
            and the configured ``stem_prefix`` is prepended.
        formats:
            Override the formats for this single call only.
        scale_factor:
            Override the PNG scale factor for this single call only.

        Returns
        -------
        dict[str, str]
            Mapping of format -> absolute output path.
        """
        stem = self._stem(name)
        active_formats = tuple(formats) if formats is not None else self.formats
        active_scale = scale_factor if scale_factor is not None else self.scale_factor

        saved = save_altair_chart(
            chart,
            output_dir=self.output_dir,
            stem=stem,
            formats=active_formats,
            scale_factor=active_scale,
        )
        self._registry[name] = saved
        return saved

    def path_for(self, name: str, fmt: str) -> Optional[str]:
        """Return the saved path for a chart *name* and *fmt*, if previously saved."""
        return self._registry.get(name, {}).get(fmt)

    @property
    def saved(self) -> dict[str, dict[str, str]]:
        """All charts saved via this workflow so far (name -> {format -> path})."""
        return dict(self._registry)

    def _repr_html_(self) -> str:
        fmt = ", ".join(f"<code>{f}</code>" for f in self.formats)
        rows = "".join(
            f"<tr><td><code>{name}</code></td>"
            + "".join(
                f"<td><code>{Path(path).name}</code></td>"
                for path in entry.values()
            )
            + "</tr>"
            for name, entry in self._registry.items()
        ) or (
            "<tr><td colspan='100%' style='color:#999'>"
            "No charts saved yet — call <code>.save(chart, 'name')</code>."
            "</td></tr>"
        )
        return (
            f"<table>"
            f"<thead><tr><th colspan='100%'>AltairExportWorkflow</th></tr></thead>"
            f"<tbody>"
            f"<tr><th>output_dir</th><td><code>{self.output_dir}</code></td></tr>"
            f"<tr><th>stem_prefix</th><td><code>{self.stem_prefix}</code></td></tr>"
            f"<tr><th>formats</th><td>{fmt}</td></tr>"
            f"<tr><th>scale_factor</th><td><code>{self.scale_factor}</code></td></tr>"
            f"<tr><th>has_vl_convert</th><td><code>{self.has_vl_convert}</code></td></tr>"
            f"<tr><th>has_vegafusion</th><td><code>{self.has_vegafusion}</code></td></tr>"
            f"<tr><th colspan='100%'>&nbsp;</th></tr>"
            f"<tr><th colspan='100%'>Saved charts</th></tr>"
            f"{rows}"
            f"</tbody></table>"
        )


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

    HTML uses the default renderer.  PNG/SVG temporarily switch to ``vl-convert``
    so vegafusion-backed charts can still produce static assets.

    .. note::
        Prefer :meth:`AltairExportWorkflow.save` in notebooks — it encapsulates
        ``output_dir``, ``stem`` prefixing, and default formats so you don't
        repeat them for every chart.  This function is the low-level primitive
        used by the workflow.
    """
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


__all__ = [
    "REPO_ROOT",
    "RAW_DATA_DIR",
    "IMAGES_DIR",
    "DEFAULT_LARGE_DATA_THRESHOLD",
    "DEFAULT_EXPORT_FORMATS",
    "DEFAULT_EXPORT_SCALE",
    "alt",
    "np",
    "pd",
    "configure_altair",
    "init_chapter6",
    "read_excel_safe",
    "save_altair_chart",
    "AltairExportWorkflow",
    "ExportStatus",
]
