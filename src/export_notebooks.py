"""Export Jupyter notebook artefacts through the unified output layer.

Given a notebook (``.ipynb``), this script runs ``nbconvert`` to produce one
or more rendered formats (HTML, PDF, Python script) and then copies the
resulting file(s) into ``output/notebook/`` via
:class:`src.output_manager.OutputManager`.

The original notebook itself is also copied to ``output/notebook/`` as a
frozen snapshot, so the output directory is self-contained.

Run from the repo root::

    # Export a single notebook to HTML
    python -m src.export_notebooks code/ch6-exercise-1.ipynb --to html

    # Export to multiple formats
    python -m src.export_notebooks code/ch6-exercise-1.ipynb --to html --to script

    # Export all ch6 notebooks
    python -m src.export_notebooks code/ch6-exercise-*.ipynb --to html

    # Dry run (check paths without writing)
    python -m src.export_notebooks code/ch6-exercise-1.ipynb --to html --dry-run
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable, Optional, Union

from data_paths import CODE_DIR, REPO_ROOT

from src.output_manager import (
    OutputManager,
    OverwritePolicy,
    WriteRecord,
    get_output_manager,
)


PathLike = Union[str, Path]


# Mapping from nbconvert --to format -> file extension
_FORMAT_EXT: dict[str, str] = {
    "html": ".html",
    "pdf": ".pdf",
    "script": ".py",
    "slides": ".slides.html",
    "latex": ".tex",
    "markdown": ".md",
    "asciidoc": ".asciidoc",
    "rst": ".rst",
}


def _run_nbconvert(
    notebook: Path,
    fmt: str,
    output_dir: Path,
    timeout: int = 300,
) -> Path:
    """Execute ``jupyter nbconvert`` for a single format, return output path."""
    ext = _FORMAT_EXT.get(fmt)
    if ext is None:
        raise ValueError(
            f"Unsupported nbconvert format {fmt!r}. "
            f"Supported: {sorted(_FORMAT_EXT)}"
        )

    cmd = [
        sys.executable, "-m", "jupyter", "nbconvert",
        "--to", fmt,
        "--output-dir", str(output_dir),
        "--execute" if fmt in ("html", "pdf", "slides") else "",
        str(notebook),
    ]
    cmd = [c for c in cmd if c]  # filter empty strings

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"nbconvert failed for {notebook.name} (--to {fmt}):\n"
            f"STDERR: {result.stderr}\nSTDOUT: {result.stdout}"
        )

    # nbconvert writes to output_dir with the notebook stem + format ext
    expected = output_dir / f"{notebook.stem}{ext}"
    if not expected.exists():
        raise FileNotFoundError(
            f"nbconvert did not produce expected output: {expected}"
        )
    return expected


def export_notebook(
    notebook: PathLike,
    *,
    formats: Iterable[str] = ("html",),
    manager: Optional[OutputManager] = None,
    overwrite: Union[str, OverwritePolicy] = OverwritePolicy.WARN,
    execute: bool = True,
    chapter: Optional[Union[int, str]] = None,
) -> list[WriteRecord]:
    """Export a notebook to one or more formats, then copy to output layer.

    Parameters
    ----------
    notebook:
        Path to the ``.ipynb`` file.
    formats:
        nbconvert output formats (``"html"``, ``"pdf"``, ``"script"``, …).
    manager:
        OutputManager to use.  When ``None``, the module-level singleton is
        used (or created on demand).
    overwrite:
        Overwrite policy forwarded to the manager.
    execute:
        If ``True`` (default), pass ``--execute`` to nbconvert so the
        notebook is re-run before rendering.
    chapter:
        Optional chapter prefix (e.g. ``6`` → ``ch06_``).  When ``None``,
        an attempt is made to infer the chapter from the filename
        (``ch<N>-exercise-*.ipynb``).
    """
    nb_path = Path(notebook).resolve()
    if not nb_path.exists():
        raise FileNotFoundError(f"Notebook not found: {nb_path}")

    if manager is None:
        manager = get_output_manager()
    if overwrite != manager.overwrite:
        manager = OutputManager(
            root=manager.root,
            overwrite=overwrite,
            category_dirs=manager._category_dirs,
            dry_run=manager.dry_run,
        )

    # Infer chapter from filename like "ch6-exercise-1.ipynb"
    if chapter is None:
        stem = nb_path.stem
        if stem.startswith("ch") and "-" in stem:
            try:
                chapter = int(stem[2 : stem.index("-")])
            except ValueError:
                chapter = None

    records: list[WriteRecord] = []

    # 1. Copy the source notebook as a frozen snapshot
    records.append(
        manager.save_notebook(
            nb_path,
            stem=nb_path.stem,
            ext="ipynb",
            chapter=chapter,
        )
    )

    # 2. Render and copy each format
    with tempfile.TemporaryDirectory(prefix="nbexport_") as tmp:
        tmp_dir = Path(tmp)
        for fmt in formats:
            try:
                rendered = _run_nbconvert(nb_path, fmt, tmp_dir)
            except Exception as exc:
                # Record failure and continue with next format
                target = manager.resolve(
                    nb_path.stem,
                    _FORMAT_EXT.get(fmt, f".{fmt}"),
                    category="notebook",
                    chapter=chapter,
                )
                records.append(
                    WriteRecord(
                        category="notebook",
                        stem=nb_path.stem,
                        ext=_FORMAT_EXT.get(fmt, f".{fmt}"),
                        path=target,
                        status="failed",
                        error=str(exc),
                    )
                )
                continue

            ext = rendered.suffix
            records.append(
                manager.save_notebook(
                    rendered,
                    stem=nb_path.stem,
                    ext=ext.lstrip("."),
                    chapter=chapter,
                )
            )

    return records


def _cli(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export notebook artefacts through OutputManager",
    )
    parser.add_argument(
        "notebooks",
        nargs="+",
        type=Path,
        help="Notebook files to export (supports glob patterns via shell expansion).",
    )
    parser.add_argument(
        "--to",
        dest="formats",
        action="append",
        choices=sorted(_FORMAT_EXT),
        default=[],
        help="Output format (repeatable). Default: html.",
    )
    parser.add_argument(
        "--no-execute",
        dest="execute",
        action="store_false",
        help="Do not re-execute the notebook before rendering.",
    )
    parser.add_argument(
        "--overwrite",
        choices=[p.value for p in OverwritePolicy],
        default=OverwritePolicy.WARN.value,
        help="Overwrite policy (default: warn).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve paths and check policy but do not write anything.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Override the default output root (default: <repo>/output).",
    )
    args = parser.parse_args(argv)

    formats = args.formats or ["html"]

    manager_kwargs: dict = {}
    if args.output_root is not None:
        manager_kwargs["root"] = args.output_root
    if args.dry_run:
        manager_kwargs["dry_run"] = True
    manager_kwargs["overwrite"] = args.overwrite

    # Get or reset the singleton with our desired config
    mgr = get_output_manager(reset=True, **manager_kwargs)

    all_records: list[WriteRecord] = []
    for nb in args.notebooks:
        if not nb.exists():
            print(f"SKIP  {nb} (file not found)", file=sys.stderr)
            continue
        try:
            recs = export_notebook(
                nb,
                formats=formats,
                manager=mgr,
                overwrite=args.overwrite,
                execute=args.execute,
            )
            all_records.extend(recs)
            for rec in recs:
                status = rec.status.upper()
                suffix = f"  ({rec.error})" if rec.error else ""
                print(f"[{status}] {rec.path}{suffix}")
        except Exception as exc:
            print(f"ERROR {nb}: {exc}", file=sys.stderr)

    print()
    print(mgr.report())

    failures = [r for r in all_records if r.status == "failed"]
    return 1 if failures else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())
