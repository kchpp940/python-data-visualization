from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st


@dataclass
class FilterState:
    makes: list[str]
    year_range: tuple[int, int]
    transmissions: list[str]
    fuel_types: list[str]


@st.cache_data
def load_data() -> pd.DataFrame:
    src_file = Path.cwd() / "data" / "raw" / "EPA_fuel_economy_summary.csv"
    return pd.read_csv(src_file)


@st.cache_data
def get_filter_options(_df: pd.DataFrame) -> dict:
    return {
        "makes": sorted(_df["make"].unique()),
        "transmissions": sorted(_df["transmission"].unique()),
        "fuel_types": sorted(_df["fuel_type_summary"].unique()),
        "min_year": int(_df["year"].min()),
        "max_year": int(_df["year"].max()),
    }


def _normalize(values: list[str]) -> list[str]:
    if not values:
        return ["ALL"]
    if "ALL" in values:
        return ["ALL"]
    return values


def _sync_state(key: str) -> None:
    normalized = _normalize(st.session_state[key])
    if st.session_state[key] != normalized:
        st.session_state[key] = normalized


def _ensure_defaults(options: dict) -> None:
    if "filter_makes" not in st.session_state:
        st.session_state["filter_makes"] = ["ALL"]
    if "filter_transmissions" not in st.session_state:
        st.session_state["filter_transmissions"] = ["ALL"]
    if "filter_fuel_types" not in st.session_state:
        st.session_state["filter_fuel_types"] = ["ALL"]
    if "filter_year_range" not in st.session_state:
        st.session_state["filter_year_range"] = (options["min_year"], options["max_year"])


def render_filter_widgets(df: pd.DataFrame, container=st) -> FilterState:
    options = get_filter_options(df)
    _ensure_defaults(options)

    makes = container.multiselect(
        "Select make(s):",
        ["ALL"] + options["makes"],
        key="filter_makes",
        on_change=_sync_state,
        args=("filter_makes",),
    )

    year_range = container.slider(
        label="Year range",
        min_value=options["min_year"],
        max_value=options["max_year"],
        key="filter_year_range",
    )

    transmissions = container.multiselect(
        "Select transmission(s):",
        ["ALL"] + options["transmissions"],
        key="filter_transmissions",
        on_change=_sync_state,
        args=("filter_transmissions",),
    )

    fuel_types = container.multiselect(
        "Select fuel type(s):",
        ["ALL"] + options["fuel_types"],
        key="filter_fuel_types",
        on_change=_sync_state,
        args=("filter_fuel_types",),
    )

    return FilterState(
        makes=_normalize(makes),
        year_range=year_range,
        transmissions=_normalize(transmissions),
        fuel_types=_normalize(fuel_types),
    )


def apply_filters(df: pd.DataFrame, state: FilterState) -> pd.DataFrame:
    year_mask = df["year"].between(state.year_range[0], state.year_range[1])
    make_mask = True if "ALL" in state.makes else df["make"].isin(state.makes)
    tr_mask = True if "ALL" in state.transmissions else df["transmission"].isin(state.transmissions)
    fuel_mask = True if "ALL" in state.fuel_types else df["fuel_type_summary"].isin(state.fuel_types)
    return df[year_mask & make_mask & tr_mask & fuel_mask]


def is_empty(plot_df: pd.DataFrame) -> bool:
    return plot_df.empty
