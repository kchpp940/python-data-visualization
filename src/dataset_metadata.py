"""Dataset metadata module for python-data-visualization.

Centralizes dataset information so notebooks, Dash apps, and README
can all reference the same authoritative source.

Architecture:
- **Static metadata** (hardcoded, never drifts):
  - Field names, types, and human-readable descriptions
  - Chapter/exercise usage mappings with key fields
  - Dataset notes and special considerations
- **Runtime profile** (computed on demand from actual files):
  - Row count, column count, missing value counts
  - Cached by file mtime to avoid re-reading large files

Usage::

    from src.dataset_metadata import (
        DATASETS, get_dataset_metadata, get_dataset_profile,
        print_dataset_summary, generate_readme_section,
    )

    # Static info (no I/O)
    meta = get_dataset_metadata("epa_fuel_economy")

    # Runtime profile (reads file once, caches)
    profile = get_dataset_profile("epa_fuel_economy")
    print(f"Rows: {profile.row_count}, Missing: {profile.total_missing}")

    # Pretty-print summary (combines static + profile)
    print_dataset_summary("amazon_books")

    # Generate README dataset section (writes to stdout or file)
    generate_readme_section()
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

import pandas as pd

from data_paths import RAW_DATA_DIR


# ---------------------------------------------------------------------------
# Markers for README auto-update
# ---------------------------------------------------------------------------

README_START_MARKER = "<!-- DATASET_METADATA_START -->"
README_END_MARKER = "<!-- DATASET_METADATA_END -->"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FieldInfo:
    """Static metadata for a single dataset column."""

    name: str
    dtype: str
    description: str
    nullable: bool = False


@dataclass(frozen=True)
class ChapterInfo:
    """Static information about which chapters/exercises use a dataset."""

    chapter: int
    exercises: list[int]
    purpose: str
    key_fields: list[str]


@dataclass
class DatasetStatic:
    """Static (non-drifting) metadata for a dataset.

    This is the *authoritative* description that never changes unless
    the dataset schema itself changes.  Row counts, missing-value
    tallies, and other runtime-derived numbers live in
    :class:`DatasetProfile` instead.
    """

    key: str
    name: str
    filename: str
    description: str
    file_type: str
    fields: list[FieldInfo]
    chapters: list[ChapterInfo]
    notes: list[str] = field(default_factory=list)

    @property
    def path(self) -> Path:
        return RAW_DATA_DIR / self.filename

    @property
    def field_names(self) -> list[str]:
        return [f.name for f in fields]


@dataclass
class DatasetProfile:
    """Runtime profile computed from the actual data file.

    Cached on disk keyed by file mtime so repeated calls are cheap.
    """

    row_count: int
    column_count: int
    missing_values: dict[str, int]
    sample_data: list[dict[str, Any]] = field(default_factory=list)

    @property
    def total_missing(self) -> int:
        return sum(self.missing_values.values())

    @property
    def missing_pct(self) -> float:
        total_cells = self.row_count * self.column_count
        if total_cells == 0:
            return 0.0
        return (self.total_missing / total_cells) * 100


@dataclass
class DatasetInfo:
    """Combined view: static metadata + runtime profile."""

    static: DatasetStatic
    profile: DatasetProfile

    @property
    def key(self) -> str:
        return self.static.key

    @property
    def name(self) -> str:
        return self.static.name

    @property
    def filename(self) -> str:
        return self.static.filename

    @property
    def row_count(self) -> int:
        return self.profile.row_count

    @property
    def column_count(self) -> int:
        return self.profile.column_count

    @property
    def total_missing(self) -> int:
        return self.profile.total_missing

    @property
    def missing_pct(self) -> float:
        return self.profile.missing_pct

    @property
    def fields(self) -> list[FieldInfo]:
        return self.static.fields

    @property
    def chapters(self) -> list[ChapterInfo]:
        return self.static.chapters

    @property
    def missing_values(self) -> dict[str, int]:
        return self.profile.missing_values

    @property
    def notes(self) -> list[str]:
        return self.static.notes

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.static.key,
            "name": self.static.name,
            "filename": self.static.filename,
            "description": self.static.description,
            "file_type": self.static.file_type,
            "row_count": self.profile.row_count,
            "column_count": self.profile.column_count,
            "total_missing": self.profile.total_missing,
            "missing_pct": self.profile.missing_pct,
            "fields": [
                {
                    "name": f.name,
                    "dtype": f.dtype,
                    "description": f.description,
                    "nullable": f.nullable,
                    "missing": self.profile.missing_values.get(f.name, 0),
                }
                for f in self.static.fields
            ],
            "chapters": [
                {
                    "chapter": c.chapter,
                    "exercises": c.exercises,
                    "purpose": c.purpose,
                    "key_fields": c.key_fields,
                }
                for c in self.static.chapters
            ],
            "notes": self.static.notes,
        }


# ---------------------------------------------------------------------------
# Static dataset definitions (schema only — no runtime numbers here)
# ---------------------------------------------------------------------------

DATASETS: dict[str, DatasetStatic] = {
    "epa_fuel_economy": DatasetStatic(
        key="epa_fuel_economy",
        name="EPA Fuel Economy (Full)",
        filename="EPA_fuel_economy.csv",
        description="US Environmental Protection Agency (EPA) vehicle fuel economy data spanning 2000-2020. Contains detailed technical specifications and fuel efficiency metrics for various makes and models.",
        file_type="CSV",
        fields=[
            FieldInfo("make", "object", "Vehicle manufacturer brand (e.g., Acura, BMW, Toyota)"),
            FieldInfo("model", "object", "Specific vehicle model name"),
            FieldInfo("year", "int64", "Model year (2000-2020)"),
            FieldInfo("cylinders", "float64", "Number of engine cylinders", nullable=True),
            FieldInfo("trany", "object", "Transmission type with gear count (e.g., 'Automatic 4-spd')", nullable=True),
            FieldInfo("displ", "float64", "Engine displacement in liters", nullable=True),
            FieldInfo("VClass", "object", "Vehicle class (e.g., 'Two Seaters', 'Compact Cars')"),
            FieldInfo("co2", "int64", "CO2 emissions in grams per mile (-1 indicates unavailable)"),
            FieldInfo("barrels08", "float64", "Annual petroleum consumption in barrels"),
            FieldInfo("fuelCost08", "int64", "Estimated annual fuel cost in USD"),
            FieldInfo("fuelType", "object", "Fuel type (e.g., 'Premium', 'Regular', 'Diesel')"),
            FieldInfo("highway08", "int64", "Highway MPG"),
            FieldInfo("city08", "int64", "City MPG"),
            FieldInfo("comb08", "int64", "Combined (city+highway) MPG"),
        ],
        chapters=[
            ChapterInfo(
                chapter=3,
                exercises=[1, 2, 3],
                purpose="Matplotlib basics: histograms, scatter plots, bar charts, and custom styling",
                key_fields=["fuelCost08", "comb08", "make", "year", "displ"],
            ),
            ChapterInfo(
                chapter=4,
                exercises=[1, 2],
                purpose="Pandas visualization: built-in plotting methods, time series analysis",
                key_fields=["year", "fuelCost08", "comb08", "highway08", "city08"],
            ),
            ChapterInfo(
                chapter=5,
                exercises=[1, 2, 3, 4],
                purpose="Seaborn: statistical visualizations, distribution plots, regression analysis",
                key_fields=["displ", "comb08", "cylinders", "fuelType", "VClass"],
            ),
        ],
        notes=[
            "co2 = -1 indicates emissions data not available",
            "Most missing values in 'cylinders' and 'displ' are from electric vehicles",
        ],
    ),
    "epa_fuel_economy_summary": DatasetStatic(
        key="epa_fuel_economy_summary",
        name="EPA Fuel Economy (Summary)",
        filename="EPA_fuel_economy_summary.csv",
        description="Simplified version of EPA fuel economy data with aggregated categorical fields for easier visualization. Derived from the full EPA dataset.",
        file_type="CSV",
        fields=[
            FieldInfo("make", "object", "Vehicle manufacturer brand"),
            FieldInfo("model", "object", "Specific vehicle model name"),
            FieldInfo("year", "int64", "Model year (2000-2020)"),
            FieldInfo("transmission", "object", "Simplified transmission: 'Automatic' or 'Manual'"),
            FieldInfo("drive", "object", "Drive type: '2WD' or '4WD'"),
            FieldInfo("date_range", "object", "Year range group (e.g., '2000-2010')"),
            FieldInfo("fuel_type_summary", "object", "Fuel category: 'Gas', 'Diesel', 'Electric', 'Other'"),
            FieldInfo("class_summary", "object", "Vehicle category: 'Car', 'SUV', 'Pickup', 'Wagon', 'Other'"),
            FieldInfo("cylinders", "float64", "Number of engine cylinders", nullable=True),
            FieldInfo("displ", "float64", "Engine displacement in liters", nullable=True),
            FieldInfo("co2", "int64", "CO2 emissions in grams per mile"),
            FieldInfo("barrels08", "float64", "Annual petroleum consumption in barrels"),
            FieldInfo("fuelCost08", "int64", "Estimated annual fuel cost in USD"),
            FieldInfo("highway08", "int64", "Highway MPG"),
            FieldInfo("city08", "int64", "City MPG"),
            FieldInfo("comb08", "int64", "Combined (city+highway) MPG"),
        ],
        chapters=[
            ChapterInfo(
                chapter=6,
                exercises=[1, 2, 3],
                purpose="Altair: declarative statistical visualizations, interactive charts",
                key_fields=["fuelCost08", "displ", "class_summary", "transmission", "year"],
            ),
            ChapterInfo(
                chapter=7,
                exercises=[1, 2, 3, 4],
                purpose="Plotly: interactive plotting, dashboards, and Dash applications",
                key_fields=["fuelCost08", "displ", "year", "transmission", "drive", "class_summary"],
            ),
        ],
        notes=[
            "Aggregated fields simplify faceting and coloring in visualizations",
            "Used in Dash full app for vehicle comparison features",
        ],
    ),
    "amazon_books": DatasetStatic(
        key="amazon_books",
        name="Amazon Books",
        filename="AmazonBooks.xlsx",
        description="Top 50 selling books on Amazon from 2009-2019, including user ratings, review counts, prices, and genre classifications.",
        file_type="Excel (XLSX)",
        fields=[
            FieldInfo("Name", "object", "Book title"),
            FieldInfo("Author", "object", "Book author name"),
            FieldInfo("User Rating", "float64", "Average user rating (out of 5)"),
            FieldInfo("Reviews", "int64", "Number of user reviews"),
            FieldInfo("Price", "int64", "Book price in USD"),
            FieldInfo("Year", "int64", "Year the book appeared in the top 50"),
            FieldInfo("Genre", "object", "Book genre: 'Fiction' or 'Non Fiction'"),
        ],
        chapters=[
            ChapterInfo(
                chapter=6,
                exercises=[2, 3],
                purpose="Altair: categorical data visualization, heatmaps, multi-panel charts",
                key_fields=["Genre", "User Rating", "Year", "Reviews", "Price"],
            ),
        ],
        notes=[
            "Complete dataset with no missing values — excellent for teaching basic visualization without data cleaning",
            "Genre is binary: Fiction / Non Fiction",
            "Prices range from $0 to ~$100",
        ],
    ),
}


# ---------------------------------------------------------------------------
# Cache management
# ---------------------------------------------------------------------------

_CACHE_DIR = Path(__file__).resolve().parent.parent / ".metadata_cache"
_CACHE_DIR.mkdir(exist_ok=True)


def _cache_path(key: str) -> Path:
    return _CACHE_DIR / f"{key}.json"


def _get_file_mtime(path: Path) -> float:
    """Return file modification time (0 if file doesn't exist)."""
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _load_profile_from_cache(key: str, expected_mtime: float) -> Optional[DatasetProfile]:
    """Load profile from disk cache if it matches the current file mtime."""
    cp = _cache_path(key)
    if not cp.exists():
        return None
    try:
        with open(cp) as f:
            cached = json.load(f)
        if cached.get("mtime") == expected_mtime:
            return DatasetProfile(
                row_count=cached["row_count"],
                column_count=cached["column_count"],
                missing_values=cached["missing_values"],
                sample_data=cached.get("sample_data", []),
            )
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def _save_profile_to_cache(key: str, profile: DatasetProfile, mtime: float) -> None:
    """Persist profile to disk cache."""
    cp = _cache_path(key)
    data = {
        "mtime": mtime,
        "row_count": profile.row_count,
        "column_count": profile.column_count,
        "missing_values": profile.missing_values,
        "sample_data": profile.sample_data,
    }
    with open(cp, "w") as f:
        json.dump(data, f, indent=2)


def _compute_profile(
    static: DatasetStatic,
    sample_rows: int = 0,
) -> DatasetProfile:
    """Read the actual data file and compute the runtime profile.

    For CSV files, ``usecols`` and ``nrows`` are used to keep the read
    lightweight — we only need the shape and null counts.
    """
    path = static.path

    if static.file_type.startswith("CSV"):
        df = pd.read_csv(path)
    elif static.file_type.startswith("Excel"):
        try:
            df = pd.read_excel(path)
        except ImportError:
            raise ImportError(
                "Reading Excel files requires openpyxl. "
                "Install it with: pip install openpyxl"
            )
    else:
        raise ValueError(f"Unsupported file type: {static.file_type}")

    missing = {col: int(df[col].isnull().sum()) for col in df.columns}

    sample = []
    if sample_rows > 0:
        sample = df.head(sample_rows).to_dict(orient="records")

    return DatasetProfile(
        row_count=len(df),
        column_count=len(df.columns),
        missing_values=missing,
        sample_data=sample,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def list_datasets() -> list[str]:
    """Return list of available dataset keys."""
    return sorted(DATASETS.keys())


def get_dataset_metadata(key: str) -> DatasetStatic:
    """Get static metadata for a dataset by key.

    This is a pure in-memory lookup — no file I/O.

    Raises
    ------
    KeyError
        If key is not found in DATASETS.
    """
    if key not in DATASETS:
        raise KeyError(
            f"Unknown dataset '{key}'. Available: {list_datasets()}"
        )
    return DATASETS[key]


def get_dataset_profile(
    key: str,
    sample_rows: int = 0,
    force_refresh: bool = False,
) -> DatasetProfile:
    """Get (or compute) the runtime profile for a dataset.

    The profile is cached on disk keyed by the file's mtime.  If the
    file hasn't changed since the last computation, the cached copy is
    returned instantly.

    Parameters
    ----------
    key:
        Dataset key from ``list_datasets()``.
    sample_rows:
        Number of sample rows to include in the profile (default 0).
    force_refresh:
        If True, re-read the file even if a cached profile exists.

    Returns
    -------
    DatasetProfile
    """
    static = get_dataset_metadata(key)
    path = static.path
    mtime = _get_file_mtime(path)

    if not force_refresh:
        cached = _load_profile_from_cache(key, mtime)
        if cached is not None:
            return cached

    profile = _compute_profile(static, sample_rows=sample_rows)
    _save_profile_to_cache(key, profile, mtime)
    return profile


def get_dataset_info(
    key: str,
    load_data: bool = False,
    sample_rows: int = 0,
    force_refresh: bool = False,
    **read_kwargs: Any,
) -> tuple[Optional[pd.DataFrame], DatasetInfo]:
    """Get combined static+profile metadata and optionally load the data.

    Parameters
    ----------
    key:
        Dataset key from ``list_datasets()``.
    load_data:
        If True, also load and return the full DataFrame.
    sample_rows:
        Number of sample rows to include in profile (default 0).
    force_refresh:
        Re-read profile from file even if cached.
    **read_kwargs:
        Extra kwargs passed to ``pd.read_csv`` or ``pd.read_excel``.

    Returns
    -------
    tuple
        (DataFrame or None, DatasetInfo)
    """
    static = get_dataset_metadata(key)
    profile = get_dataset_profile(key, sample_rows=sample_rows, force_refresh=force_refresh)
    info = DatasetInfo(static=static, profile=profile)

    df = None
    if load_data:
        path = static.path
        if static.file_type.startswith("CSV"):
            df = pd.read_csv(path, **read_kwargs)
        elif static.file_type.startswith("Excel"):
            try:
                df = pd.read_excel(path, **read_kwargs)
            except ImportError:
                from src.ch6_init import read_excel_safe
                df = read_excel_safe(path, **read_kwargs)
        else:
            raise ValueError(f"Unsupported file type: {static.file_type}")

    return df, info


def invalidate_cache(key: Optional[str] = None) -> None:
    """Clear the profile cache for one or all datasets.

    Parameters
    ----------
    key:
        Dataset key, or None to clear all caches.
    """
    if key is None:
        for cp in _CACHE_DIR.glob("*.json"):
            cp.unlink()
    else:
        cp = _cache_path(key)
        if cp.exists():
            cp.unlink()


def print_dataset_summary(key: str, max_fields: int = 20) -> None:
    """Pretty-print a dataset summary to stdout.

    Combines static field descriptions with runtime profile numbers.
    Useful in notebook initialization cells.
    """
    static = get_dataset_metadata(key)
    profile = get_dataset_profile(key)

    print(f"📊 Dataset: {static.name}")
    print(f"   File: {static.filename} ({static.file_type})")
    print(f"   Rows: {profile.row_count:,} | Columns: {profile.column_count}")
    print(
        f"   Missing values: {profile.total_missing:,} "
        f"({profile.missing_pct:.2f}%)"
    )
    print()
    print(f"📝 Description: {static.description}")
    print()
    print("🔍 Fields:")
    for f in static.fields[:max_fields]:
        nullable = " (nullable)" if f.nullable else ""
        miss = profile.missing_values.get(f.name, 0)
        miss_str = f" [missing: {miss}]" if miss > 0 else ""
        print(f"   • {f.name:<20} {f.dtype:<10} {f.description}{nullable}{miss_str}")
    print()
    print("📚 Used in chapters:")
    for ch in static.chapters:
        ex = ", ".join(f"Ex{i}" for i in ch.exercises)
        key_fields = ", ".join(ch.key_fields[:4])
        print(f"   • Ch{ch.chapter} ({ex}): {ch.purpose}")
        print(f"     Key fields: {key_fields}")
    if static.notes:
        print()
        print("💡 Notes:")
        for note in static.notes:
            print(f"   • {note}")


def get_chapter_datasets(chapter: int) -> list[DatasetStatic]:
    """Return all datasets used in a given chapter."""
    return [
        meta for meta in DATASETS.values()
        if any(ch.chapter == chapter for ch in meta.chapters)
    ]


def get_field_datasets(field_name: str) -> list[DatasetStatic]:
    """Return all datasets containing a given field name."""
    return [
        meta for meta in DATASETS.values()
        if any(f.name == field_name for f in meta.fields)
    ]


# ---------------------------------------------------------------------------
# README generation
# ---------------------------------------------------------------------------


def _generate_dataset_markdown(static: DatasetStatic, profile: DatasetProfile) -> str:
    """Generate Markdown for a single dataset."""
    parts: list[str] = []

    parts.append(f"### {static.name}")
    parts.append("")
    parts.append(
        f"**File:** `{static.filename}` ({static.file_type})  "
    )
    parts.append(
        f"**Rows:** {profile.row_count:,} | "
        f"**Columns:** {profile.column_count}  "
    )
    parts.append(
        f"**Missing values:** {profile.total_missing:,} "
        f"({profile.missing_pct:.2f}%)  "
    )
    parts.append("")
    parts.append(static.description)
    parts.append("")
    parts.append("#### Fields")
    parts.append("")
    parts.append("| Field | Type | Description | Missing |")
    parts.append("|-------|------|-------------|---------|")
    for f in static.fields:
        miss = profile.missing_values.get(f.name, 0)
        miss_str = f"{miss:,}" if miss > 0 else "-"
        parts.append(f"| `{f.name}` | {f.dtype} | {f.description} | {miss_str} |")
    parts.append("")
    parts.append("#### Usage by Chapter")
    parts.append("")
    parts.append("| Chapter | Exercises | Purpose | Key Fields |")
    parts.append("|---------|-----------|---------|------------|")
    for ch in static.chapters:
        ex = ", ".join(str(i) for i in ch.exercises)
        key_fields = ", ".join(f"`{k}`" for k in ch.key_fields)
        parts.append(f"| {ch.chapter} | {ex} | {ch.purpose} | {key_fields} |")
    parts.append("")
    if static.notes:
        parts.append("#### Notes")
        parts.append("")
        for note in static.notes:
            parts.append(f"- {note}")
        parts.append("")

    return "\n".join(parts)


def generate_readme_section(
    output_path: Optional[Union[str, Path]] = None,
    force_refresh: bool = False,
    include_markers: bool = True,
) -> str:
    """Generate the full "Datasets" section of the README.

    Parameters
    ----------
    output_path:
        If provided, write the markdown to this file.  If None, return
        the markdown as a string.
    force_refresh:
        Re-compute profiles even if cached.
    include_markers:
        If True (default), wrap the output in ``README_START_MARKER`` and
        ``README_END_MARKER`` so ``update_readme()`` can find and replace
        only this section.

    Returns
    -------
    str
        The generated markdown.
    """
    # Ensure profiles are fresh
    for key in DATASETS:
        get_dataset_profile(key, force_refresh=force_refresh)

    lines: list[str] = []

    if include_markers:
        lines.append(README_START_MARKER)

    # Overview table
    lines.append("---")
    lines.append("")
    lines.append("## Datasets")
    lines.append("")
    lines.append(
        "This repository includes three datasets used throughout the course "
        "exercises. All dataset metadata is centralized in "
        "[src/dataset_metadata.py](src/dataset_metadata.py) for easy reference "
        "in notebooks, Dash apps, and documentation."
    )
    lines.append("")
    lines.append(
        "> **Note:** The row counts, column counts, and missing-value statistics "
        "below are computed from the actual data files at generation time. "
        "Re-run `python -m src.dataset_metadata --write-readme` to refresh."
    )
    lines.append("")
    lines.append("### Quick Usage in Notebooks")
    lines.append("")
    lines.append("```python")
    lines.append("import sys; sys.path.insert(0, '..')")
    lines.append("from src.dataset_metadata import notebook_init")
    lines.append("")
    lines.append("# Load data and print summary")
    lines.append('df, meta = notebook_init("epa_fuel_economy")')
    lines.append("```")
    lines.append("")
    lines.append("### Available Datasets")
    lines.append("")
    lines.append("| Dataset | File | Rows | Columns | Missing Values | Chapters |")
    lines.append("|---------|------|------|---------|----------------|----------|")
    for key in sorted(DATASETS.keys()):
        static = DATASETS[key]
        profile = get_dataset_profile(key)
        chapters_str = ", ".join(
            f"Ch{ch.chapter}" for ch in static.chapters
        )
        lines.append(
            f"| {static.name} | `{static.filename}` | "
            f"{profile.row_count:,} | {profile.column_count} | "
            f"{profile.total_missing:,} ({profile.missing_pct:.2f}%) | "
            f"{chapters_str} |"
        )
    lines.append("")

    # Per-dataset detail
    for key in sorted(DATASETS.keys()):
        static = DATASETS[key]
        profile = get_dataset_profile(key)
        lines.append("---")
        lines.append("")
        lines.append(_generate_dataset_markdown(static, profile))

    # Interactive explorer section
    lines.append("---")
    lines.append("")
    lines.append("## Interactive Dataset Explorer")
    lines.append("")
    lines.append("Launch the Dash application to browse datasets interactively:")
    lines.append("")
    lines.append("```bash")
    lines.append("cd code")
    lines.append("python dash_full_app.py")
    lines.append("```")
    lines.append("")
    lines.append("Then navigate to the \"📊 数据集信息\" tab to explore:")
    lines.append("- Field descriptions and data types")
    lines.append("- Missing value statistics")
    lines.append("- Chapter usage examples")
    lines.append("- Dataset notes and special considerations")
    lines.append("")

    if include_markers:
        lines.append(README_END_MARKER)
        lines.append("")

    markdown = "\n".join(lines)

    if output_path is not None:
        Path(output_path).write_text(markdown, encoding="utf-8")

    return markdown


def update_readme(
    readme_path: Optional[Union[str, Path]] = None,
    force_refresh: bool = False,
    verbose: bool = True,
) -> Path:
    """Update the dataset section in an existing README in-place.

    Finds the block between ``README_START_MARKER`` and
    ``README_END_MARKER`` and replaces it with freshly generated content.
    Everything outside these markers is preserved untouched.

    If the markers are not found, appends the new section at the end
    (with markers so future runs can find it).

    Parameters
    ----------
    readme_path:
        Path to README.md.  Defaults to ``<repo_root>/README.md``.
    force_refresh:
        Re-compute profiles even if cached.
    verbose:
        Print status messages to stdout.

    Returns
    -------
    Path
        The path to the updated README.

    Raises
    ------
    FileNotFoundError
        If the README file does not exist.
    """
    readme_path = readme_path or Path(__file__).resolve().parent.parent / "README.md"
    readme_path = Path(readme_path)

    if not readme_path.exists():
        raise FileNotFoundError(f"README not found: {readme_path}")

    existing = readme_path.read_text(encoding="utf-8")
    new_content = generate_readme_section(force_refresh=force_refresh, include_markers=True)

    if README_START_MARKER in existing and README_END_MARKER in existing:
        # Replace the existing block
        before = existing.split(README_START_MARKER)[0]
        after = existing.split(README_END_MARKER)[1]
        output = before.rstrip() + "\n\n" + new_content.rstrip() + "\n\n" + after.lstrip()
        if verbose:
            print(f"Replacing existing dataset section in {readme_path}")
    else:
        # Append to end
        output = existing.rstrip() + "\n\n" + new_content
        if verbose:
            print(f"No markers found — appending dataset section to {readme_path}")

    readme_path.write_text(output, encoding="utf-8")
    if verbose:
        print(f"README updated successfully: {readme_path}")

    return readme_path


# ---------------------------------------------------------------------------
# Notebook initialization helpers
# ---------------------------------------------------------------------------


def notebook_init(
    key: str,
    load_data: bool = True,
    sample_rows: int = 0,
) -> tuple[Optional[pd.DataFrame], DatasetInfo]:
    """Convenience function for notebook first cells.

    Loads data (optionally) and prints summary information.

    Usage (first cell of notebook)::

        import sys; sys.path.insert(0, '..')
        from src.dataset_metadata import notebook_init
        df, meta = notebook_init("epa_fuel_economy")
    """
    df, info = get_dataset_info(key, load_data=load_data, sample_rows=sample_rows)
    print_dataset_summary(key)
    return df, info


# ---------------------------------------------------------------------------
# CLI entry point: python -m src.dataset_metadata [--refresh] [--write-readme]
# ---------------------------------------------------------------------------


def _main() -> None:
    """Refresh all profile caches and optionally update the README dataset section."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Refresh dataset profile caches and/or update README dataset section"
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force re-read of all data files",
    )
    parser.add_argument(
        "--write-readme",
        action="store_true",
        help=f"Update the README section between {README_START_MARKER} and {README_END_MARKER}",
    )
    parser.add_argument(
        "--readme-path",
        type=str,
        default=None,
        help="Path to README.md (default: auto-detect from repo root)",
    )
    args = parser.parse_args()

    keys = list_datasets()
    print(f"Refreshing {len(keys)} dataset{'s' if len(keys) != 1 else ''}...")
    for key in keys:
        print(f"  • {key}...", end=" ")
        profile = get_dataset_profile(key, force_refresh=args.refresh)
        print(
            f"ok ({profile.row_count:,} rows, "
            f"{profile.column_count} cols, "
            f"{profile.total_missing:,} missing)"
        )

    if args.write_readme:
        update_readme(
            readme_path=args.readme_path,
            force_refresh=args.refresh,
        )
    else:
        print(
            f"\nTip: add --write-readme to update the README dataset section "
            f"({README_START_MARKER} ... {README_END_MARKER})"
        )


if __name__ == "__main__":
    _main()


# ---------------------------------------------------------------------------
# __all__
# ---------------------------------------------------------------------------

__all__ = [
    "DATASETS",
    "DatasetStatic",
    "DatasetProfile",
    "DatasetInfo",
    "FieldInfo",
    "ChapterInfo",
    "README_START_MARKER",
    "README_END_MARKER",
    "list_datasets",
    "get_dataset_metadata",
    "get_dataset_profile",
    "get_dataset_info",
    "invalidate_cache",
    "print_dataset_summary",
    "get_chapter_datasets",
    "get_field_datasets",
    "generate_readme_section",
    "update_readme",
    "notebook_init",
]
