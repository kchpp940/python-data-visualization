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
from typing import Optional, Union

import numpy as np
import pandas as pd

from data_paths import RAW_DATA_DIR, IMAGES_DIR, REPO_ROOT  # noqa: E402

from src.dataset_metadata import (  # noqa: E402
    DATASETS,
    DatasetStatic,
    DatasetProfile,
    DatasetInfo,
    README_START_MARKER,
    README_END_MARKER,
    list_datasets,
    get_dataset_metadata,
    get_dataset_profile,
    get_dataset_info,
    print_dataset_summary,
    get_chapter_datasets,
    generate_readme_section,
    update_readme,
    invalidate_cache,
    notebook_init,
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
    "alt",
    "np",
    "pd",
    "configure_altair",
    "init_chapter6",
    "read_excel_safe",
    "save_altair_chart",
    "DATASETS",
    "DatasetStatic",
    "DatasetProfile",
    "DatasetInfo",
    "README_START_MARKER",
    "README_END_MARKER",
    "list_datasets",
    "get_dataset_metadata",
    "get_dataset_profile",
    "get_dataset_info",
    "print_dataset_summary",
    "get_chapter_datasets",
    "generate_readme_section",
    "update_readme",
    "invalidate_cache",
    "notebook_init",
]
