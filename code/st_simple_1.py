import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st
import plotly.express as px

from data_paths import epa_fuel_economy_summary

src_file = epa_fuel_economy_summary()
df = pd.read_csv(src_file)

fig = px.histogram(
    df,
    x="fuelCost08",
    color="class_summary",
    labels={"fuelCost08": "Annual Fuel Cost"},
    nbins=40,
    title="Fuel Cost Distribution",
)

st.title("Simple Example")
st.write(fig)

