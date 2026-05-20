import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from dash import Dash, html, dcc
import plotly.express as px

from data_paths import epa_fuel_economy_summary

app = Dash(__name__)

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

app.layout = html.Div(children=[
    html.H1("Simple Histogram"),
    html.Div("Annual Fuel Cost Plot."),
    dcc.Graph(id="example-histogram", figure=fig),
])

if __name__ == "__main__":
    app.run_server(debug=True)


