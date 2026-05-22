"""Minimal notebook bootstrap — repo-root discovery + sys.path injection.

Every notebook under ``code/`` starts its first code cell with the
canonical inline bootstrap (see below).  This module documents that
pattern and provides :func:`resolve_repo_root` /
:func:`ensure_repo_root_on_path` / :func:`ensure_repo_root_or_raise` so
that non-notebook callers (scripts, tests) can reuse the same logic.

Canonical bootstrap snippet (paste into the first code cell of every
notebook *before* the first ``from src.…`` import)::

    # --- bootstrap: locate repo root, inject into sys.path, then import ---
    from pathlib import Path
    import os, sys

    _ROOT = os.environ.get("PY_DATA_VIS_ROOT")
    if _ROOT:
        _ROOT = Path(_ROOT).expanduser().resolve()
    else:
        _ROOT = Path.cwd()
        while _ROOT != _ROOT.parent and not (_ROOT / "data_paths.py").exists():
            _ROOT = _ROOT.parent

    if not (_ROOT / "data_paths.py").exists():
        raise RuntimeError(
            "Cannot locate python-data-visualization repo root. "
            "Set PY_DATA_VIS_ROOT to the repo directory, or launch "
            "Jupyter from inside the repo."
        )

    sys.path.insert(0, str(_ROOT))
    sys.path.insert(0, str(_ROOT / "src"))

    from src.ch3_init import RAW_DATA_DIR, IMAGES_DIR, datasets, pd, np, plt, ticker
    datasets.describe('epa')

The bootstrap is intentionally written inline in the notebook (not
imported) because it must run *before* the first ``from src.…`` import.
Once it has run, :mod:`src.nb_init` and the chapter wrappers take over
and handle paths, datasets, and plotting backends.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def resolve_repo_root(start: Path | str | None = None) -> Path | None:
    """Locate the repo root.

    Resolution order:
    1. ``PY_DATA_VIS_ROOT`` environment variable (if set and points to a
       directory that contains ``data_paths.py``).
    2. Walk up from ``start`` (default: ``Path.cwd()``) until we find a
       directory that contains ``data_paths.py``.

    Returns the repo root :class:`~pathlib.Path`, or ``None`` if it
    cannot be located.
    """
    env_root = os.environ.get("PY_DATA_VIS_ROOT")
    if env_root:
        p = Path(env_root).expanduser().resolve()
        if (p / "data_paths.py").exists():
            return p

    root = Path(start).resolve() if start else Path.cwd().resolve()
    for candidate in (root, *root.parents):
        if (candidate / "data_paths.py").exists():
            return candidate
    return None


def ensure_repo_root_or_raise(
    start: Path | str | None = None,
) -> Path:
    """Locate the repo root and inject it (and ``src/``) into
    ``sys.path``.  Raises :class:`RuntimeError` with a clear message if
    the repo root cannot be found.
    """
    root = resolve_repo_root(start)
    if root is None:
        env_hint = (
            f" (PY_DATA_VIS_ROOT={os.environ['PY_DATA_VIS_ROOT']!r} was set "
            f"but did not resolve to the repo)"
            if os.environ.get("PY_DATA_VIS_ROOT")
            else ""
        )
        raise RuntimeError(
            "Cannot locate python-data-visualization repo root. "
            "Set PY_DATA_VIS_ROOT to the repo directory, or launch "
            f"the process from inside the repo{env_hint}."
        )
    for p in (str(root), str(root / "src")):
        if p not in sys.path:
            sys.path.insert(0, p)
    return root


def ensure_repo_root_on_path(
    start: Path | str | None = None,
) -> Path | None:
    """Non-raising variant of :func:`ensure_repo_root_or_raise` — returns
    ``None`` instead of raising when the repo cannot be located.
    """
    try:
        return ensure_repo_root_or_raise(start)
    except RuntimeError:
        return None


__all__ = [
    "resolve_repo_root",
    "ensure_repo_root_or_raise",
    "ensure_repo_root_on_path",
]
