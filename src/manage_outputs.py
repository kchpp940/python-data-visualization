"""Unified output layer management CLI.

Provides a single entry point for inspecting, generating, and cleaning
artefacts produced by the unified output layer (``<repo>/output/``).

Commands
--------
list
    Scan ``output/`` and print a tree of all generated artefacts grouped by
    category, along with file sizes and timestamps.

export
    Run a minimal export demo for each category (Altair, Plotly, README)
    so the output layer can be inspected without launching Jupyter.

status
    Print the :class:`OutputManager` write history and any failures.
    Requires a prior export to have run in the same process.

failures
    Print only the failed records from the OutputManager history.

clean
    Remove ``output/`` entirely.  **This is the only way to delete artefacts**
    — no other command in this module (or in ``generate_readme_section.py`` /
    ``export_notebooks.py``) removes files from ``output/``.

readme
    Run ``generate_readme_section`` to produce README fragments (and, with
    ``--in-place``, update the repo root ``README.md``).

notebooks
    Run ``export_notebooks`` for one or more notebooks.

Run from the repo root::

    python -m src.manage_outputs list
    python -m src.manage_outputs export
    python -m src.manage_outputs status
    python -m src.manage_outputs failures
    python -m src.manage_outputs clean
    python -m src.manage_outputs readme --in-place
    python -m src.manage_outputs notebooks code/ch6-exercise-1.ipynb --to html
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from data_paths import OUTPUT_DIR, REPO_ROOT

from src.output_manager import (
    OutputManager,
    OverwritePolicy,
    WriteRecord,
    get_output_manager,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _format_size(nbytes: int) -> str:
    """Human-readable file size."""
    if nbytes < 1024:
        return f"{nbytes} B"
    if nbytes < 1024 ** 2:
        return f"{nbytes / 1024:.1f} KB"
    if nbytes < 1024 ** 3:
        return f"{nbytes / (1024 ** 2):.1f} MB"
    return f"{nbytes / (1024 ** 3):.2f} GB"


def _collect_tree(root: Path) -> dict[str, list[tuple[Path, int, datetime]]]:
    """Walk *root* and return files grouped by category directory."""
    groups: dict[str, list[tuple[Path, int, datetime]]] = {}
    if not root.exists():
        return groups
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        category = rel.parts[0] if len(rel.parts) > 1 else "(root)"
        st = p.stat()
        ts = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
        groups.setdefault(category, []).append((p, st.st_size, ts))
    return groups


# --------------------------------------------------------------------------- #
# Command implementations
# --------------------------------------------------------------------------- #
def cmd_list(args: argparse.Namespace) -> int:
    """Print the artefact tree under ``output/``."""
    root = Path(args.output_root) if args.output_root else OUTPUT_DIR
    if not root.exists():
        print(f"Output directory does not exist: {root}")
        print("Run `python -m src.manage_outputs export` to generate artefacts.")
        return 0

    groups = _collect_tree(root)
    total_files = sum(len(v) for v in groups.values())
    total_size = sum(st for files in groups.values() for _, st, _ in files)

    print(f"Output root: {root}")
    print(f"Total: {total_files} file(s), {_format_size(total_size)}")
    print()

    if not groups:
        print("  (no artefacts)")
        return 0

    for category in sorted(groups):
        files = groups[category]
        cat_size = sum(st for _, st, _ in files)
        print(f"[{category}]  {len(files)} file(s), {_format_size(cat_size)}")
        for p, size, ts in files:
            rel = p.relative_to(root)
            ts_str = ts.strftime("%Y-%m-%d %H:%M")
            print(f"  {rel.as_posix():50s}  {_format_size(size):>8s}  {ts_str}")
        print()

    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Run minimal demo exports for Altair, Plotly, and README."""
    manager = get_output_manager(
        reset=True,
        overwrite=OverwritePolicy.OVERWRITE,
        dry_run=args.dry_run,
    )

    if args.dry_run:
        print("[DRY RUN] No files will be written.")

    # --- Altair demo ---
    try:
        import altair as alt
        import pandas as pd

        df = pd.DataFrame({"x": [1, 2, 3, 4], "y": [10, 20, 15, 30]})
        chart = alt.Chart(df).mark_bar().encode(x="x", y="y")
        records = manager.save_altair(
            chart,
            "demo_scatter",
            chapter=6,
            formats=("html",),
        )
        for fmt, rec in records.items():
            _print_record(rec, prefix="  altair ")
    except ImportError as exc:
        print(f"  [SKIP] Altair demo: {exc}")

    # --- Plotly demo ---
    try:
        import plotly.graph_objects as go

        fig = go.Figure(data=go.Bar(x=[1, 2, 3, 4], y=[10, 20, 15, 30]))
        records = manager.save_plotly(
            fig,
            "demo_bar",
            chapter=7,
            formats=("html",),
        )
        for fmt, rec in records.items():
            _print_record(rec, prefix="  plotly ")
    except ImportError as exc:
        print(f"  [SKIP] Plotly demo: {exc}")

    # --- README fragment demo ---
    from src.generate_readme_section import generate_readme_section

    records = generate_readme_section(manager=manager)
    for rec in records:
        _print_record(rec, prefix="  readme ")

    print()
    print(manager.report())

    failures = manager.failures()
    if failures:
        print(f"\n{len(failures)} failure(s):")
        for rec in failures:
            print(f"  - {rec.path}: {rec.error}")
        return 1
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Print the OutputManager report."""
    manager = get_output_manager()
    print(manager.report())
    if manager.history:
        print(f"\nHistory ({len(manager.history)} record(s)):")
        for rec in manager.history:
            _print_record(rec, prefix="  ")
    return 0


def cmd_failures(args: argparse.Namespace) -> int:
    """Print only failed records."""
    manager = get_output_manager()
    failures = manager.failures()
    if not failures:
        print("No failures recorded.")
        return 0
    print(f"{len(failures)} failure(s):")
    for rec in failures:
        print(f"  [{rec.category}] {rec.path}")
        print(f"    stem={rec.stem!r}  ext={rec.ext}")
        print(f"    error: {rec.error}")
    return 1


def cmd_clean(args: argparse.Namespace) -> int:
    """Remove the output directory."""
    root = Path(args.output_root) if args.output_root else OUTPUT_DIR
    if not root.exists():
        print(f"Nothing to clean — {root} does not exist.")
        return 0

    if not args.yes:
        response = input(f"Remove {root}? [y/N] ").strip().lower()
        if response not in ("y", "yes"):
            print("Aborted.")
            return 0

    shutil.rmtree(root)
    print(f"Removed {root}")

    # Reset the singleton so subsequent operations start fresh.
    get_output_manager(reset=True)
    return 0


def cmd_readme(args: argparse.Namespace) -> int:
    """Run generate_readme_section."""
    from src.generate_readme_section import (
        generate_readme_section,
        update_readme_in_place,
    )

    manager = get_output_manager(reset=True, overwrite=args.overwrite, dry_run=args.dry_run)

    if args.in_place:
        result = update_readme_in_place(
            readme_path=Path(args.readme),
            manager=manager,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
            insert_if_missing=args.insert_if_missing,
        )
        status = "CHANGED" if result["changed"] else "UNCHANGED"
        print(f"README {status}: {result['readme']}")
        for rec in result["written"]:
            _print_record(rec, prefix="  ")
    else:
        recs = generate_readme_section(manager=manager, overwrite=args.overwrite)
        for rec in recs:
            _print_record(rec, prefix="  ")

    print()
    print(manager.report())
    return 0


def cmd_notebooks(args: argparse.Namespace) -> int:
    """Run export_notebooks for the given notebook files."""
    from src.export_notebooks import export_notebook

    manager = get_output_manager(
        reset=True,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
    )

    all_records: list[WriteRecord] = []
    for nb_path in args.notebooks:
        nb = Path(nb_path)
        if not nb.exists():
            print(f"[SKIP] {nb} (not found)")
            continue
        try:
            recs = export_notebook(
                nb,
                formats=args.formats,
                manager=manager,
                overwrite=args.overwrite,
                execute=args.execute,
            )
            all_records.extend(recs)
            for rec in recs:
                _print_record(rec, prefix="  ")
        except Exception as exc:
            print(f"[ERROR] {nb}: {exc}")

    print()
    print(manager.report())
    failures = [r for r in all_records if r.status == "failed"]
    return 1 if failures else 0


def _print_record(rec: WriteRecord, prefix: str = "") -> None:
    status = rec.status.upper()
    size = f" ({_format_size(rec.bytes_written)})" if rec.bytes_written else ""
    err = f" — {rec.error}" if rec.error else ""
    print(f"{prefix}[{status}] {rec.path}{size}{err}")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manage_outputs",
        description="Unified output layer management (list / export / status / failures / clean / readme / notebooks).",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Override the default output root (default: <repo>/output).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = sub.add_parser("list", help="List all artefacts under output/.")
    p_list.set_defaults(func=cmd_list)

    # export
    p_export = sub.add_parser("export", help="Run minimal demo exports.")
    p_export.add_argument("--dry-run", action="store_true", help="Resolve paths but do not write.")
    p_export.set_defaults(func=cmd_export)

    # status
    p_status = sub.add_parser("status", help="Print OutputManager history and report.")
    p_status.set_defaults(func=cmd_status)

    # failures
    p_fail = sub.add_parser("failures", help="Print only failed records.")
    p_fail.set_defaults(func=cmd_failures)

    # clean
    p_clean = sub.add_parser("clean", help="Remove the output directory.")
    p_clean.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt.")
    p_clean.set_defaults(func=cmd_clean)

    # readme
    p_readme = sub.add_parser("readme", help="Generate README auto-section.")
    p_readme.add_argument("--in-place", action="store_true", help="Update README.md in place.")
    p_readme.add_argument("--insert-if-missing", action="store_true", help="Append blocks when markers missing.")
    p_readme.add_argument("--dry-run", action="store_true", help="Do not write anything.")
    p_readme.add_argument(
        "--readme",
        type=Path,
        default=REPO_ROOT / "README.md",
        help="Path to README file.",
    )
    p_readme.add_argument(
        "--overwrite",
        choices=[p.value for p in OverwritePolicy],
        default=OverwritePolicy.OVERWRITE.value,
        help="Overwrite policy (default: overwrite).",
    )
    p_readme.set_defaults(func=cmd_readme)

    # notebooks
    p_nb = sub.add_parser("notebooks", help="Export notebook(s) via nbconvert.")
    p_nb.add_argument("notebooks", nargs="+", type=Path, help="Notebook files to export.")
    p_nb.add_argument(
        "--to",
        dest="formats",
        action="append",
        choices=["html", "pdf", "script", "slides", "latex", "markdown", "asciidoc", "rst"],
        default=[],
        help="Output format (repeatable). Default: html.",
    )
    p_nb.add_argument("--no-execute", dest="execute", action="store_false", help="Do not re-execute notebooks.")
    p_nb.add_argument("--dry-run", action="store_true", help="Resolve paths but do not write.")
    p_nb.add_argument(
        "--overwrite",
        choices=[p.value for p in OverwritePolicy],
        default=OverwritePolicy.WARN.value,
        help="Overwrite policy (default: warn).",
    )
    p_nb.set_defaults(func=cmd_notebooks, execute=True)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
