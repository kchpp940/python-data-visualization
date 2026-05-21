"""Altair backend configuration.

Handles Altair renderer backend selection, row limit management, and
fallback logic when optional dependencies are missing.

This module is side-effect free: importing it does **not** modify Altair's
global state. Call :func:`configure_altair` explicitly to apply settings.
"""

from __future__ import annotations

import warnings
from typing import Optional

import altair as alt

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
