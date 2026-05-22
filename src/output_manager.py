"""Unified output layer for chart/figure exports and notebook artifacts.

All generated assets (Altair charts, Plotly static images, README sections,
rendered notebook artefacts) should be written through :class:`OutputManager`
so that file naming, overwrite policy, and failure reporting remain
consistent across chapters.

The module is side-effect free: importing it does **not** create any
directory. Directories are only materialised when ``OutputManager``
methods are invoked (typically from a notebook setup cell).

Typical usage::

    from src.output_manager import (
        OutputManager, get_output_manager, OverwritePolicy,
    )

    manager = get_output_manager()
    manager.save_altair(chart, stem="ch6_exercise_1")
    manager.save_plotly(fig, stem="ch7_exercise_1")
    manager.save_text("# Foo", "ch7", "overview", ext="md", category="readme")
"""

from __future__ import annotations

import re
import shutil
import warnings
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from data_paths import (
    OUTPUT_ALTAIR_DIR,
    OUTPUT_DIR,
    OUTPUT_NOTEBOOK_DIR,
    OUTPUT_PLOTLY_DIR,
    OUTPUT_README_DIR,
)


PathLike = Union[str, Path]


class OverwritePolicy(str, Enum):
    """Policy that decides what happens when a target file already exists.

    ``ERROR``
        Raise :class:`FileExistsError` — safest for CI / reproducible builds.
    ``WARN``
        Emit a :class:`UserWarning` and overwrite.
    ``OVERWRITE``
        Silently overwrite.
    ``SKIP``
        Do nothing; return ``None`` / ``skipped`` status.  The caller can
        inspect the status dict to detect skipped writes.
    """

    ERROR = "error"
    WARN = "warn"
    OVERWRITE = "overwrite"
    SKIP = "skip"


_VALID_STEM_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _is_valid_stem(stem: str) -> bool:
    """Return True if *stem* looks safe to use as a filename stem.

    We deliberately forbid path separators, leading dots and anything that
    would survive the normalisation below.
    """
    if not stem:
        return False
    if "/" in stem or "\\" in stem or "\x00" in stem:
        return False
    return bool(_VALID_STEM_RE.match(stem))


def _normalise_stem(stem: str) -> str:
    """Collapse runs of non-word characters into a single ``_`` and strip."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._-")
    return cleaned or "untitled"


def _normalise_ext(ext: str) -> str:
    """Return *ext* lowercased with a leading ``.`` (e.g. ``"png"`` -> ``".png"``)."""
    ext = (ext or "").strip().lower()
    if not ext:
        raise ValueError("ext must be a non-empty string (e.g. 'png', '.svg').")
    if not ext.startswith("."):
        ext = f".{ext}"
    if not re.fullmatch(r"\.[a-z0-9.]+", ext):
        raise ValueError(f"Invalid ext: {ext!r}")
    return ext


# Category -> default sub-directory (relative to the configured root)
DEFAULT_CATEGORY_DIRS: Mapping[str, Path] = {
    "altair": Path("altair"),
    "plotly": Path("plotly"),
    "notebook": Path("notebook"),
    "readme": Path("readme"),
}


# Extensions we recognise for each category (used for sanity checks only).
_KNOWN_EXTS: Mapping[str, Sequence[str]] = {
    "altair": (".png", ".svg", ".html", ".json"),
    "plotly": (".png", ".svg", ".pdf", ".html", ".json"),
    "notebook": (".ipynb", ".html", ".pdf", ".py"),
    "readme": (".md", ".html", ".txt"),
}


@dataclass(frozen=True)
class WriteRecord:
    """Immutable record of a single write operation."""

    category: str
    stem: str
    ext: str
    path: Path
    status: str              # "written" | "overwritten" | "skipped" | "failed"
    bytes_written: int = 0
    error: Optional[str] = None


class OutputManager:
    """Coordinate output locations for all generated artefacts.

    Parameters
    ----------
    root:
        Top-level output directory.  Defaults to
        :data:`data_paths.OUTPUT_DIR` (``<repo>/output``).
    overwrite:
        One of :class:`OverwritePolicy`.  Defaults to ``WARN`` which
        matches the "loud but forgiving" behaviour notebooks expect.
    category_dirs:
        Optional overrides for the per-category sub-directories.  Keys
        should match the category names used by the ``save_*`` helpers
        (``"altair"``, ``"plotly"``, ``"notebook"``, ``"readme"``).
    dry_run:
        When ``True`` the manager resolves paths and checks overwrite
        policy but never writes to disk.  Useful for smoke-testing
        notebook pipelines in CI.

    Notes
    -----
    A module-level singleton is available via :func:`get_output_manager`.
    Direct construction is also supported for per-chapter isolation.
    """

    def __init__(
        self,
        root: PathLike = OUTPUT_DIR,
        overwrite: Union[str, OverwritePolicy] = OverwritePolicy.WARN,
        category_dirs: Optional[Mapping[str, PathLike]] = None,
        dry_run: bool = False,
    ) -> None:
        self.root: Path = Path(root).expanduser().resolve()
        self.overwrite: OverwritePolicy = OverwritePolicy(overwrite)
        self.dry_run: bool = dry_run

        merged: Dict[str, Path] = {k: Path(v) for k, v in DEFAULT_CATEGORY_DIRS.items()}
        if category_dirs:
            for k, v in category_dirs.items():
                merged[str(k)] = Path(v)
        self._category_dirs: Mapping[str, Path] = merged

        self._history: list[WriteRecord] = []

    # ------------------------------------------------------------------ #
    # Paths / config
    # ------------------------------------------------------------------ #
    def category_dir(self, category: str) -> Path:
        """Return the absolute directory for *category*, creating it on demand."""
        key = category.lower()
        if key not in self._category_dirs:
            raise ValueError(
                f"Unknown output category {category!r}. "
                f"Expected one of: {sorted(self._category_dirs)}."
            )
        sub = self._category_dirs[key]
        path = self.root / sub if not sub.is_absolute() else sub
        if not self.dry_run:
            path.mkdir(parents=True, exist_ok=True)
        return path

    def resolve(
        self,
        stem: str,
        ext: str,
        *,
        category: str,
        chapter: Optional[Union[int, str]] = None,
    ) -> Path:
        """Resolve a target path without writing anything.

        Parameters
        ----------
        stem:
            Filename stem (extension-less).  Passed through
            :func:`_normalise_stem` before use.
        ext:
            File extension, with or without leading dot (e.g. ``"png"``).
        category:
            One of the known categories (``"altair"``, ``"plotly"``, …).
        chapter:
            Optional chapter prefix.  When provided, the final filename
            becomes ``ch<N>_<stem>.<ext>`` for integer chapters, or
            ``<chapter>_<stem>.<ext>`` for string ones.
        """
        ext_norm = _normalise_ext(ext)
        stem_norm = _normalise_stem(stem)
        if not _is_valid_stem(stem_norm):
            raise ValueError(
                f"Refusing to write file with normalised stem {stem_norm!r} "
                f"(original stem: {stem!r})."
            )
        if chapter is not None:
            if isinstance(chapter, int):
                prefix = f"ch{chapter:02d}"
            else:
                prefix = _normalise_stem(str(chapter))
            stem_norm = f"{prefix}_{stem_norm}"
        known = _KNOWN_EXTS.get(category.lower())
        if known is not None and ext_norm not in known:
            warnings.warn(
                f"Extension {ext_norm} is unusual for category {category!r} "
                f"(expected one of {sorted(known)}).",
                stacklevel=2,
            )
        return self.category_dir(category) / f"{stem_norm}{ext_norm}"

    # ------------------------------------------------------------------ #
    # Overwrite handling
    # ------------------------------------------------------------------ #
    def _handle_existing(self, target: Path) -> Optional[bool]:
        """Apply overwrite policy.

        Returns
        -------
        True  -> proceed with the write (file may or may not have existed).
        False -> skip (caller should record skipped and bail out).
        None  -> not applicable (dry run).

        Raises
        ------
        FileExistsError
            If policy is ``ERROR`` and *target* exists.
        """
        if not target.exists():
            return True
        policy = self.overwrite
        if policy is OverwritePolicy.ERROR:
            raise FileExistsError(
                f"Refusing to overwrite {target} (overwrite policy = 'error')."
            )
        if policy is OverwritePolicy.SKIP:
            return False
        if policy is OverwritePolicy.WARN:
            warnings.warn(
                f"Overwriting existing output file: {target}",
                stacklevel=3,
            )
        return True

    # ------------------------------------------------------------------ #
    # Low-level writers
    # ------------------------------------------------------------------ #
    def write_bytes(
        self,
        data: bytes,
        stem: str,
        ext: str,
        *,
        category: str,
        chapter: Optional[Union[int, str]] = None,
    ) -> WriteRecord:
        """Write raw bytes to the resolved path."""
        target = self.resolve(stem, ext, category=category, chapter=chapter)
        action = self._handle_existing(target)
        if action is False:
            rec = WriteRecord(
                category=category, stem=stem, ext=ext,
                path=target, status="skipped",
            )
            self._history.append(rec)
            return rec
        status = "overwritten" if target.exists() else "written"
        try:
            if not self.dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            size = len(data)
            rec = WriteRecord(
                category=category, stem=stem, ext=ext,
                path=target, status=status, bytes_written=size,
            )
        except Exception as exc:  # pragma: no cover - IO edge cases
            rec = WriteRecord(
                category=category, stem=stem, ext=ext,
                path=target, status="failed", error=str(exc),
            )
        self._history.append(rec)
        return rec

    def write_text(
        self,
        text: str,
        stem: str,
        ext: str,
        *,
        category: str,
        chapter: Optional[Union[int, str]] = None,
        encoding: str = "utf-8",
    ) -> WriteRecord:
        """Write *text* to the resolved path using *encoding*."""
        target = self.resolve(stem, ext, category=category, chapter=chapter)
        action = self._handle_existing(target)
        if action is False:
            rec = WriteRecord(
                category=category, stem=stem, ext=ext,
                path=target, status="skipped",
            )
            self._history.append(rec)
            return rec
        status = "overwritten" if target.exists() else "written"
        try:
            raw = text.encode(encoding)
            if not self.dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            rec = WriteRecord(
                category=category, stem=stem, ext=ext,
                path=target, status=status, bytes_written=len(raw),
            )
        except Exception as exc:  # pragma: no cover - IO edge cases
            rec = WriteRecord(
                category=category, stem=stem, ext=ext,
                path=target, status="failed", error=str(exc),
            )
        self._history.append(rec)
        return rec

    def copy_file(
        self,
        source: PathLike,
        stem: str,
        ext: str,
        *,
        category: str,
        chapter: Optional[Union[int, str]] = None,
    ) -> WriteRecord:
        """Copy an existing file into the output layer."""
        src = Path(source)
        if not src.exists():
            rec = WriteRecord(
                category=category, stem=stem, ext=ext,
                path=self.resolve(stem, ext, category=category, chapter=chapter),
                status="failed", error=f"source not found: {src}",
            )
            self._history.append(rec)
            return rec
        target = self.resolve(stem, ext, category=category, chapter=chapter)
        action = self._handle_existing(target)
        if action is False:
            rec = WriteRecord(
                category=category, stem=stem, ext=ext,
                path=target, status="skipped",
            )
            self._history.append(rec)
            return rec
        status = "overwritten" if target.exists() else "written"
        try:
            if not self.dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, target)
            size = target.stat().st_size if (not self.dry_run and target.exists()) else src.stat().st_size
            rec = WriteRecord(
                category=category, stem=stem, ext=ext,
                path=target, status=status, bytes_written=size,
            )
        except Exception as exc:  # pragma: no cover
            rec = WriteRecord(
                category=category, stem=stem, ext=ext,
                path=target, status="failed", error=str(exc),
            )
        self._history.append(rec)
        return rec

    # ------------------------------------------------------------------ #
    # High-level helpers (chart / notebook / readme)
    # ------------------------------------------------------------------ #
    def save_altair(
        self,
        chart: Any,
        stem: str,
        *,
        chapter: Optional[Union[int, str]] = None,
        formats: Iterable[str] = ("png", "svg", "html"),
        scale_factor: float = 2.0,
    ) -> Dict[str, WriteRecord]:
        """Save an Altair chart in one or more *formats*.

        HTML always uses the active renderer.  PNG/SVG temporarily switch
        to ``vl-convert`` when available so vegafusion-backed charts can
        still produce static assets — if ``vl-convert`` is missing we
        fall back to the active renderer and record a warning on the
        record itself.
        """
        # Local import to keep the module importable without altair.
        import altair as alt  # noqa: WPS433

        results: Dict[str, WriteRecord] = {}
        for fmt in formats:
            ext = f".{fmt.lstrip('.')}"
            target = self.resolve(stem, ext, category="altair", chapter=chapter)
            action = self._handle_existing(target)
            if action is False:
                rec = WriteRecord(
                    category="altair", stem=stem, ext=ext,
                    path=target, status="skipped",
                )
                self._history.append(rec)
                results[fmt] = rec
                continue
            status = "overwritten" if target.exists() else "written"
            error: Optional[str] = None
            written = 0
            try:
                if fmt == "html":
                    if not self.dry_run:
                        chart.save(str(target))
                else:
                    # Prefer vl-convert for static assets so we stay
                    # independent of the vegafusion backend; degrade
                    # gracefully otherwise.
                    ctx: Any
                    if "vl-convert" in alt.renderers.names():
                        ctx = alt.renderers.enable(
                            "vl-convert", ppi=int(72 * scale_factor),
                        )
                    else:
                        error = (
                            "vl-convert not available; static export used "
                            "the active renderer and may be empty for "
                            "vegafusion-backed charts."
                        )
                        ctx = _NullContext()
                    with ctx:
                        if not self.dry_run:
                            chart.save(str(target))
                if not self.dry_run and target.exists():
                    written = target.stat().st_size
            except Exception as exc:
                status = "failed"
                error = f"{type(exc).__name__}: {exc}"
            rec = WriteRecord(
                category="altair", stem=stem, ext=ext,
                path=target, status=status, bytes_written=written, error=error,
            )
            if error and status != "failed":
                warnings.warn(error, stacklevel=2)
            self._history.append(rec)
            results[fmt] = rec
        return results

    def save_plotly(
        self,
        fig: Any,
        stem: str,
        *,
        chapter: Optional[Union[int, str]] = None,
        formats: Iterable[str] = ("png", "html"),
        width: Optional[int] = None,
        height: Optional[int] = None,
        scale: float = 2.0,
    ) -> Dict[str, WriteRecord]:
        """Save a Plotly figure in one or more *formats*.

        Static formats (png / svg / pdf / jpeg) go through
        ``fig.write_image``.  ``html`` uses ``fig.write_html``.
        """
        results: Dict[str, WriteRecord] = {}
        static_exts = {".png", ".svg", ".pdf", ".jpg", ".jpeg", ".webp"}
        for fmt in formats:
            ext = f".{fmt.lstrip('.').lower()}"
            if ext == ".jpg":
                ext = ".jpeg"
            target = self.resolve(stem, ext, category="plotly", chapter=chapter)
            action = self._handle_existing(target)
            if action is False:
                rec = WriteRecord(
                    category="plotly", stem=stem, ext=ext,
                    path=target, status="skipped",
                )
                self._history.append(rec)
                results[fmt] = rec
                continue
            status = "overwritten" if target.exists() else "written"
            error: Optional[str] = None
            written = 0
            try:
                if ext == ".html":
                    if not self.dry_run:
                        fig.write_html(str(target), include_plotlyjs="cdn")
                elif ext in static_exts:
                    if not self.dry_run:
                        fig.write_image(
                            str(target),
                            width=width,
                            height=height,
                            scale=scale,
                        )
                else:
                    status = "failed"
                    error = f"Unsupported plotly format: {fmt}"
                if not self.dry_run and target.exists():
                    written = target.stat().st_size
            except Exception as exc:
                status = "failed"
                error = f"{type(exc).__name__}: {exc}"
            rec = WriteRecord(
                category="plotly", stem=stem, ext=ext,
                path=target, status=status, bytes_written=written, error=error,
            )
            if error and status != "failed":
                warnings.warn(error, stacklevel=2)
            self._history.append(rec)
            results[fmt] = rec
        return results

    def save_notebook(
        self,
        source: PathLike,
        stem: str,
        ext: str = "ipynb",
        *,
        chapter: Optional[Union[int, str]] = None,
    ) -> WriteRecord:
        """Copy a rendered/converted notebook artefact into the output layer."""
        return self.copy_file(
            source, stem, ext, category="notebook", chapter=chapter,
        )

    def save_readme(
        self,
        text: str,
        stem: str,
        *,
        chapter: Optional[Union[int, str]] = None,
        ext: str = "md",
    ) -> WriteRecord:
        """Save a README fragment / generated markdown section."""
        return self.write_text(
            text, stem, ext, category="readme", chapter=chapter,
        )

    # ------------------------------------------------------------------ #
    # History / reporting
    # ------------------------------------------------------------------ #
    @property
    def history(self) -> Tuple[WriteRecord, ...]:
        """All write records in the order they were issued."""
        return tuple(self._history)

    def failures(self) -> Tuple[WriteRecord, ...]:
        """Return records whose status is ``failed``."""
        return tuple(r for r in self._history if r.status == "failed")

    def report(self) -> str:
        """Return a human-readable summary of the write history."""
        if not self._history:
            return "OutputManager: nothing written yet."
        total = len(self._history)
        counts: Dict[str, int] = {}
        for rec in self._history:
            counts[rec.status] = counts.get(rec.status, 0) + 1
        parts = [f"OutputManager: {total} write(s)"]
        for status in ("written", "overwritten", "skipped", "failed"):
            if status in counts:
                parts.append(f"{status}={counts[status]}")
        return ", ".join(parts)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"OutputManager(root={str(self.root)!r}, "
            f"overwrite={self.overwrite.value}, "
            f"dry_run={self.dry_run})"
        )


class _NullContext:
    """Context manager that does nothing — used as a renderer fallback."""

    def __enter__(self) -> "_NullContext":
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False


# --------------------------------------------------------------------------- #
# Module-level singleton + convenience helpers
# --------------------------------------------------------------------------- #
_DEFAULT_MANAGER: Optional[OutputManager] = None


def get_output_manager(
    *,
    reset: bool = False,
    root: Optional[PathLike] = None,
    overwrite: Union[str, OverwritePolicy, None] = None,
    dry_run: bool = False,
) -> OutputManager:
    """Return (and lazily construct) the module-level :class:`OutputManager`.

    Pass ``reset=True`` to replace the existing singleton.  The remaining
    keyword arguments mirror :class:`OutputManager`'s constructor and are
    only honoured when a new instance is being created.
    """
    global _DEFAULT_MANAGER
    if reset or _DEFAULT_MANAGER is None:
        kwargs: Dict[str, Any] = {"dry_run": dry_run}
        if root is not None:
            kwargs["root"] = root
        if overwrite is not None:
            kwargs["overwrite"] = overwrite
        _DEFAULT_MANAGER = OutputManager(**kwargs)
    return _DEFAULT_MANAGER


# Default exports -- kept alphabetical.
__all__ = [
    "DEFAULT_CATEGORY_DIRS",
    "OutputManager",
    "OverwritePolicy",
    "WriteRecord",
    "get_output_manager",
]
