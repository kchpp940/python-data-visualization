"""README section updater — regenerate auto-generated markdown under output/readme/
and optionally update the root README.md in-place.

Three auto-generated blocks are managed:

* ``notebooks``  — the list of Jupyter notebooks under ``code/``
* ``artefacts``  — the list of output files under ``output/``
* ``datasets``   — a summary table built from ``.metadata_cache/*.json``

Each block is delimited in both ``README.md`` and the fragment files by::

    <!-- BEGIN auto-generated: BLOCK_NAME -->
    ...
    <!-- END auto-generated: BLOCK_NAME -->

The fragment files under ``output/readme/`` are always written (they serve as
a reference copy).  Writing to the root ``README.md`` is opt-in via
``--in-place``; by default the updater runs in **dry-run** mode and reports
whether each block is already in sync or needs updating.

The ``datasets`` block consumes the profile cache produced by
``maintenance.profile_checker``.  If the cache is stale or missing, the
updater still works (the table may be empty or out of date) — run
``python maintenance.py profile`` first to refresh it.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from maintenance import (
    FAIL, PASS, WARN,
    REPO_ROOT, CODE_DIR, OUTPUT_DIR, METADATA_CACHE, RAW_DATA_DIR,
    CheckResult, make_result,
)

README_MD = REPO_ROOT / "README.md"

_BEGIN_FMT = "<!-- BEGIN auto-generated: {name} -->"
_END_FMT = "<!-- END auto-generated: {name} -->"

BLOCK_NAMES = ("notebooks", "datasets", "artefacts")


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------

def _scan_notebooks() -> list[tuple[str, str]]:
    """Return (chapter_title, relative_path) for each notebook under code/."""
    notebooks: list[tuple[str, str]] = []
    for nb in sorted(CODE_DIR.glob("ch*-exercise-*.ipynb")):
        title = "Unknown"
        try:
            with open(nb, encoding="utf-8") as fh:
                data = json.load(fh)
            for cell in data.get("cells", []):
                if cell.get("cell_type") == "markdown" and cell.get("source"):
                    first_line = cell["source"][0].strip()
                    if first_line.startswith("#"):
                        title = first_line.lstrip("#").strip()
                        break
        except Exception:
            pass
        rel = f"code/{nb.name}"
        notebooks.append((title, rel))
    return notebooks


def _scan_output_files() -> dict[str, list[str]]:
    """Return {category: [relative_path, ...]} for files under output/."""
    grouped: dict[str, list[str]] = {}
    if not OUTPUT_DIR.exists():
        return grouped
    for item in sorted(OUTPUT_DIR.rglob("*")):
        if item.is_dir():
            continue
        rel = item.relative_to(OUTPUT_DIR)
        category = rel.parts[0] if len(rel.parts) > 1 else "misc"
        grouped.setdefault(category, []).append(str(Path("output") / rel))
    return grouped


def _scan_datasets() -> list[dict]:
    """Return a list of dataset summary dicts from the profile cache.

    Each dict has keys: file_name, row_count, column_count, missing_summary.
    Entries are ordered by the underlying raw-data file name so the table
    is stable across runs.
    """
    entries: list[dict] = []
    if not METADATA_CACHE.exists():
        return entries

    # Build a mapping from raw file stem -> profile cache
    cache_map: dict[str, Path] = {}
    for p in METADATA_CACHE.iterdir():
        if p.is_file() and p.suffix == ".json":
            cache_map[p.stem.lower()] = p

    # Iterate raw data files for a canonical ordering
    if RAW_DATA_DIR.exists():
        raw_files = sorted(
            [p for p in RAW_DATA_DIR.iterdir()
             if p.is_file() and p.suffix.lower() in (".csv", ".xlsx", ".xlsm")]
        )
    else:
        raw_files = []

    for raw in raw_files:
        cache_file = cache_map.get(raw.stem.lower())
        if cache_file is None:
            entries.append({
                "file_name": raw.name,
                "row_count": "?",
                "column_count": "?",
                "missing_summary": "(no cache — run `python maintenance.py profile`)",
            })
            continue
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            entries.append({
                "file_name": raw.name,
                "row_count": "?",
                "column_count": "?",
                "missing_summary": "(cache unreadable)",
            })
            continue

        missing = data.get("missing_values", {})
        nonzero = {k: v for k, v in missing.items() if v}
        if not nonzero:
            missing_summary = "0"
        else:
            missing_summary = ", ".join(
                f"{k}:{v}" for k, v in sorted(nonzero.items())
            )

        entries.append({
            "file_name": raw.name,
            "row_count": data.get("row_count", "?"),
            "column_count": data.get("column_count", "?"),
            "missing_summary": missing_summary,
        })

    return entries


# ---------------------------------------------------------------------------
# Block generation
# ---------------------------------------------------------------------------

def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")


def _generate_notebook_section() -> str:
    lines = [
        _BEGIN_FMT.format(name="notebooks"),
        "## Notebooks",
        "",
        "<!-- auto-generated by maintenance.py -->",
        "",
    ]
    for title, rel in _scan_notebooks():
        lines.append(f"- [{title}]({rel})")
    lines.append(_END_FMT.format(name="notebooks"))
    return "\n".join(lines) + "\n"


def _generate_artefacts_section() -> str:
    lines = [
        _BEGIN_FMT.format(name="artefacts"),
        "## Output artefacts",
        "",
        "<!-- auto-generated by maintenance.py -->",
        "",
    ]
    for category, files in sorted(_scan_output_files().items()):
        cap = category.capitalize()
        lines.append(f"### {cap}")
        lines.append("")
        for f in files:
            lines.append(f"- `{f}`")
        lines.append("")
    lines.append(_END_FMT.format(name="artefacts"))
    return "\n".join(lines) + "\n"


def _generate_datasets_section() -> str:
    lines = [
        _BEGIN_FMT.format(name="datasets"),
        "## Datasets",
        "",
        "<!-- auto-generated by maintenance.py -->",
        "",
        "| File | Rows | Cols | Missing |",
        "|------|------|------|---------|",
    ]
    datasets = _scan_datasets()
    if not datasets:
        lines.append("| _(no profile cache — run `python maintenance.py profile`)_ | | | |")
    else:
        for d in datasets:
            rc = d["row_count"]
            rc_fmt = f"{int(rc):,}" if isinstance(rc, int) else str(rc)
            lines.append(
                f"| `{d['file_name']}` | {rc_fmt} "
                f"| {d['column_count']} | {d['missing_summary']} |"
            )
    lines.append("")
    lines.append(_END_FMT.format(name="datasets"))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Block extraction / replacement in README.md
# ---------------------------------------------------------------------------

def _extract_block(content: str, block_name: str) -> str | None:
    """Return the block between BEGIN/END markers (inclusive), or None."""
    begin = _BEGIN_FMT.format(name=block_name)
    end = _END_FMT.format(name=block_name)
    start = content.find(begin)
    if start == -1:
        return None
    end_pos = content.find(end, start)
    if end_pos == -1:
        return None
    return content[start : end_pos + len(end)]


def _replace_block(content: str, block_name: str, new_block: str) -> str:
    """Replace the block in *content* with *new_block*.

    Returns the modified content.  Raises ValueError if the block is not found.
    """
    begin = _BEGIN_FMT.format(name=block_name)
    end = _END_FMT.format(name=block_name)
    start = content.find(begin)
    if start == -1:
        raise ValueError(f"Block '{block_name}' not found in README.md — "
                         f"missing marker: {begin}")
    end_pos = content.find(end, start)
    if end_pos == -1:
        raise ValueError(f"Block '{block_name}' has no END marker in README.md")

    before = content[:start]
    after = content[end_pos + len(end):]
    # Ensure single newline separation from surrounding content
    return before + new_block.rstrip("\n") + "\n" + after.lstrip("\n")


# ---------------------------------------------------------------------------
# Fragment file helpers
# ---------------------------------------------------------------------------

_FRAGMENT_FILES: dict[str, str] = {
    "notebooks": "auto_generated_section_notebooks.md",
    "datasets": "auto_generated_section_datasets.md",
    "artefacts": "auto_generated_section_artefacts.md",
}


def _write_fragment(block_name: str, content: str) -> None:
    readme_dir = OUTPUT_DIR / "readme"
    readme_dir.mkdir(parents=True, exist_ok=True)
    (readme_dir / _FRAGMENT_FILES[block_name]).write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run(*, in_place: bool = False) -> list[CheckResult]:
    """Regenerate fragment files and optionally update root README.md.

    Parameters
    ----------
    in_place:
        If ``False`` (default / dry-run), compare generated content against
        the blocks in ``README.md`` and report "synced" or "needs update"
        for each block.  The fragment files under ``output/readme/`` are
        always written.

        If ``True``, replace the blocks in ``README.md`` with the newly
        generated content and report "updated" for each block.

    Returns
    -------
    list[CheckResult]
    """
    results: list[CheckResult] = []
    generators: dict[str, object] = {
        "notebooks": _generate_notebook_section,
        "datasets": _generate_datasets_section,
        "artefacts": _generate_artefacts_section,
    }

    if not README_MD.exists():
        results.append(make_result(FAIL, f"README.md missing: {README_MD}"))
        return results

    readme_text = README_MD.read_text(encoding="utf-8")

    for block_name in BLOCK_NAMES:
        generated = generators[block_name]()

        # Always write the fragment file
        try:
            _write_fragment(block_name, generated)
            results.append(make_result(
                PASS,
                f"fragment written -> {_FRAGMENT_FILES[block_name]}",
            ))
        except Exception as exc:
            results.append(make_result(
                FAIL, f"{block_name} fragment write: {exc}",
            ))
            continue

        # Check or update the root README.md
        current = _extract_block(readme_text, block_name)
        if current is None:
            results.append(make_result(
                FAIL,
                f"{block_name}: markers not found in README.md "
                f"(expected {_BEGIN_FMT.format(name=block_name)} / "
                f"{_END_FMT.format(name=block_name)})",
            ))
            continue

        if in_place:
            try:
                readme_text = _replace_block(readme_text, block_name, generated)
                results.append(make_result(
                    PASS, f"{block_name}: README.md updated in-place",
                ))
            except ValueError as exc:
                results.append(make_result(FAIL, f"{block_name}: {exc}"))
            except Exception as exc:
                results.append(make_result(
                    FAIL, f"{block_name} in-place update: {exc}",
                ))
        else:
            # Dry-run: compare normalized content (ignoring timestamp in
            # BEGIN lines so the comparison is stable)
            def _normalize(s: str) -> str:
                # Strip the BEGIN line (which carries a timestamp) before compare
                lines = s.splitlines()
                # Remove the BEGIN marker line
                lines = [l for l in lines if not l.strip().startswith("<!-- BEGIN auto-generated:")]
                # Remove the END marker line
                lines = [l for l in lines if not l.strip().startswith("<!-- END auto-generated:")]
                return "\n".join(lines).strip()

            if _normalize(generated) == _normalize(current):
                results.append(make_result(
                    PASS, f"{block_name}: README.md in sync",
                ))
            else:
                results.append(make_result(
                    WARN,
                    f"{block_name}: README.md out of sync — "
                    f"run with --in-place to update",
                ))

    # Write updated README.md if in_place made changes
    if in_place:
        try:
            README_MD.write_text(readme_text, encoding="utf-8")
        except Exception as exc:
            results.append(make_result(FAIL, f"writing README.md: {exc}"))

    # Summary counts
    notebooks_count = len(_scan_notebooks())
    results.append(make_result(PASS, f"notebook count: {notebooks_count}"))
    datasets_count = len(_scan_datasets())
    results.append(make_result(PASS, f"dataset count: {datasets_count}"))
    art_count = sum(len(v) for v in _scan_output_files().values())
    results.append(make_result(PASS, f"output artefact count: {art_count}"))

    return results


# ---------------------------------------------------------------------------
# Standalone entry point (python -m maintenance.readme_updater)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    in_place = "--in-place" in sys.argv or "-i" in sys.argv
    from maintenance import print_results, all_passed
    results = run(in_place=in_place)
    print_results(
        "README Section Update" + (" [--in-place]" if in_place else " [dry-run]"),
        results,
    )
    sys.exit(0 if all_passed(results) else 1)
