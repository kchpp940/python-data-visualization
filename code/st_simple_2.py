from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import streamlit as st
import plotly.express as px
import altair as alt

from src.dataset_service import get_service

DATASET_ID = "epa_fuel_economy_summary"
dataset_service = get_service()
plotly_labels = dataset_service.get_plotly_labels(DATASET_ID)


@st.cache_data()
def load_data():
    return dataset_service.load(DATASET_ID)


df = load_data()
min_year = int(df["year"].min())
max_year = int(df["year"].max())
valid_makes = sorted(df["make"].unique())

st.title("Simple Example")
make = st.multiselect("Select a make:", valid_makes)
year_range = st.slider(
    label="Year range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
)

year_filter = df["year"].between(year_range[0], year_range[1])
make_filter = df["make"].isin(make)

plot_df = df[make_filter & year_filter]

avg_fuel_economy = plot_df["fuelCost08"].mean().round(0)
st.metric("Average", avg_fuel_economy)

fig = px.histogram(
    plot_df,
    x="fuelCost08",
    color="class_summary",
    labels=plotly_labels,
    nbins=40,
    title="Fuel Cost Distribution",
)

altair_chart = (
    alt.Chart(plot_df).mark_tick().encode(y="fuel_type_summary", x="barrels08")
)

st.write(fig)
st.write(altair_chart)

st.write("Sample data", plot_df.head(10))
