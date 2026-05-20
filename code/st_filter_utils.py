"""Shared filtering logic for Streamlit example apps.

Keeps the make/ALL semantics clean:
- Default selection is ["ALL"] — show everything.
- "ALL" is mutually exclusive with specific brands; the direction of the
  user's latest change determines which one wins.
- An empty selection triggers a warning; no silent fallback to "ALL".
"""

from pathlib import Path
import pandas as pd


SRC_PATH = Path.cwd() / "data" / "raw" / "EPA_fuel_economy_summary.csv"

# Session-state keys shared by both Streamlit apps.
# * MAKE_SELECT_KEY  – bound to the multiselect widget via `key=`.
# * PREV_MAKE_KEY   – snapshot of the previous run's selection, used by
#                     `resolve_make_selection` to detect which side
#                     (ALL or a specific brand) was just added.
MAKE_SELECT_KEY = "_make_select"
PREV_MAKE_KEY = "_prev_make_select"


def load_data():
    return pd.read_csv(SRC_PATH)


def make_options(df):
    """Return ['ALL', ...unique makes...]."""
    return ["ALL"] + sorted(df["make"].unique())


def resolve_make_selection(current, previous):
    """Resolve make selection so "ALL" and specific brands are mutually exclusive.

    Parameters
    ----------
    current : list
        The current multiselect value from this run.
    previous : list or None
        The multiselect value from the previous run (stored in session state),
        or ``None`` if this is the first run.

    Returns
    -------
    resolved : list
        The normalized selection — either ``["ALL"]``, a list of specific
        brands, or ``[]``.
    explanation : str or None
        A short explanation for the caller to display if the value was
        mutated (so the UI can be updated via ``st.session_state``).

    How the resolution works
    ------------------------
    * **First run (``previous is None``)**: return ``current`` as-is.
    * **Addition of "ALL"** (``"ALL" in current`` and ``"ALL" not in previous``):
      strip every specific brand and return only ``["ALL"]``.  The user
      explicitly chose the "show everything" shortcut, so it should
      override any previous narrow selection.
    * **Addition of any specific brand** while "ALL" was previously
      selected: remove "ALL" and keep only the specific brands currently
      chosen.  The user explicitly narrowed the scope.
    * **Other cases** (removal only, no conflict): return ``current``.
    """
    if previous is None:
        return current, None

    cur = list(current)
    prev = list(previous)

    # Case 1 — "ALL" was just added → it wins, clear every specific brand.
    if "ALL" in cur and "ALL" not in prev:
        return ["ALL"], "ALL added → cleared specific brands"

    # Case 2 — a specific brand was just added while "ALL" was already on
    # → the user is narrowing the scope, so drop "ALL" and keep the
    # specific brands currently chosen.
    specifics_prev = [m for m in prev if m != "ALL"]
    specifics_cur = [m for m in cur if m != "ALL"]
    if "ALL" in prev and specifics_cur and set(specifics_cur) - set(specifics_prev):
        return specifics_cur, "specific added → removed ALL"

    # Case 3 — "ALL" was explicitly removed by the user (e.g. they
    # deselected it) → keep whatever specific brands remain.
    if "ALL" not in cur and "ALL" in prev:
        return specifics_cur, "ALL removed → kept specific brands"

    return cur, None


def year_range(df):
    return int(df["year"].min()), int(df["year"].max())


def build_make_filter(df, selected_makes):
    """Return a boolean Series for the make filter.

    Rules
    -----
    * If ``"ALL"`` is selected, ignore any other selections and return a
      Series of ``True`` (include every row).
    * If the selection is empty, return a Series of ``False`` so the caller
      can show a warning instead of silently showing all data.
    * Otherwise, keep only rows whose ``make`` is in the selection.
    """
    if "ALL" in selected_makes:
        return pd.Series(True, index=df.index)
    if len(selected_makes) == 0:
        return pd.Series(False, index=df.index)
    return df["make"].isin(selected_makes)


def build_year_filter(df, year_low, year_high):
    return df["year"].between(year_low, year_high)


def filter_data(df, selected_makes, year_low, year_high):
    make_filter = build_make_filter(df, selected_makes)
    year_filter = build_year_filter(df, year_low, year_high)
    return df[make_filter & year_filter]
