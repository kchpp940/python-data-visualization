from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import streamlit as st
import plotly.express as px

from src.dataset_service import get_service

DATASET_ID = "epa_fuel_economy_summary"
dataset_service = get_service()
plotly_labels = dataset_service.get_plotly_labels(DATASET_ID)


@st.cache_data()
def load_data():
    return dataset_service.load(DATASET_ID)


df = load_data()

fig = px.histogram(
    df,
    x="fuelCost08",
    color="class_summary",
    labels=plotly_labels,
    nbins=40,
    title="Fuel Cost Distribution",
)

st.title("Simple Example")
st.write(fig)
