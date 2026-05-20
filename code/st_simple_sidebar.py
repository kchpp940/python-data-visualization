import streamlit as st
import plotly.express as px
import altair as alt

from st_filter_utils import (
    load_data,
    make_options,
    year_range,
    resolve_make_selection,
    filter_data,
    MAKE_SELECT_KEY,
    PREV_MAKE_KEY,
)


st.set_page_config(layout="wide")


@st.cache_data()
def _load():
    return load_data()


df = _load()
min_year, max_year = year_range(df)
valid_makes = make_options(df)

# Initialise the widget key on first run so the multiselect always reads
# from session state (and we can mutate it later via session state).
if MAKE_SELECT_KEY not in st.session_state:
    st.session_state[MAKE_SELECT_KEY] = ["ALL"]

# ---------- UI (sidebar) ----------
st.title("Simple Sidebar Example")

make = st.sidebar.multiselect(
    "Select a make:",
    valid_makes,
    key=MAKE_SELECT_KEY,
)

year_range_val = st.sidebar.slider(
    label="Year range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
)

# ---------- Normalise make selection (ALL ⇄ specific brands) ----------
previous = st.session_state.get(PREV_MAKE_KEY)
resolved, _ = resolve_make_selection(make, previous)

# If the resolution changed the selection, update session state and
# rerun so the widget reflects the new value.
if resolved != make:
    st.session_state[MAKE_SELECT_KEY] = resolved
    st.session_state[PREV_MAKE_KEY] = resolved
    st.rerun()

# Remember this run's selection for the next one.
st.session_state[PREV_MAKE_KEY] = resolved
make = resolved

# ---------- Filter ----------
plot_df = filter_data(df, make, year_range_val[0], year_range_val[1])

# ---------- Display ----------
if plot_df.empty:
    st.warning(
        "No data matches the current filters. "
        "Try selecting at least one make or adjusting the year range."
    )
    st.sidebar.metric("Average Annual Fuel Cost", "N/A")
else:
    avg_fuel_economy = plot_df["fuelCost08"].mean().round(0)
    st.sidebar.metric("Average Annual Fuel Cost", f"${avg_fuel_economy:,.0f}")

    fig = px.histogram(
        plot_df,
        x="fuelCost08",
        color="class_summary",
        labels={"fuelCost08": "Annual Fuel Cost"},
        nbins=40,
        title="Fuel Cost Distribution",
    )

    altair_chart = (
        alt.Chart(plot_df)
        .mark_tick()
        .encode(y="fuel_type_summary", x="barrels08")
        .properties(width=600)
    )

    st.write(fig)
    st.write(altair_chart)
