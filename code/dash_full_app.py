from pathlib import Path
import pandas as pd

from dash import Dash, html, dcc, Input, Output, State, dash_table, callback_context
import plotly.express as px

from dash_selection_state import (
    build_default_state,
    filter_dataframe,
    resolve_selection_render,
    resolve_selection_update,
)

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = Dash(__name__, external_stylesheets=external_stylesheets)

styles = {"pre": {"border": "thin lightgrey solid", "overflowX": "scroll"}}

src_file = Path.cwd() / "data" / "raw" / "EPA_fuel_economy_summary.csv"
df = pd.read_csv(src_file)

min_year = df["year"].min()
max_year = df["year"].max()
all_years = df["year"].unique()
transmission_types = df["transmission"].unique()

data_table_cols = [
    "make",
    "model",
    "year",
    "transmission",
    "drive",
    "class_summary",
    "cylinders",
    "displ",
    "fuelCost08",
]

default_state = build_default_state(min_year, max_year, transmission_types)

app.layout = html.Div(
    [
        html.H1("Fuel Cost Analysis"),
        html.Div([
            html.P("Talk Python Training Example"),
            dcc.Graph(id="histogram-with-slider",
                      config={"displayModeBar": False}),
            dcc.Graph(id="scatter-plot"),
            html.Label("Year Range"),
            dcc.RangeSlider(
                id="year-slider",
                min=min_year,
                max=max_year,
                value=(min_year, max_year),
                marks={str(year): str(year)
                       for year in all_years},
            ),
            html.Label("Transmission type"),
            dcc.Checklist(
                id="transmission-list",
                options=[{
                    "label": i,
                    "value": i
                } for i in transmission_types],
                value=transmission_types,
                labelStyle={"display": "inline-block"},
            ),
            html.Hr(),
            html.Button("Reset selections", id="reset", n_clicks=0),
            html.H3(id="selected_count"),
            dash_table.DataTable(
                id="data-table",
                data=[],
                page_size=10,
                columns=[{
                    "name": i,
                    "id": i
                } for i in data_table_cols],
            ),
        ]),
        dcc.Store(id="selection_state", data=default_state),
    ],
    style={"margin-bottom": "150px"},
)


@app.callback(
    Output("selection_state", "data"),
    Output("scatter-plot", "selectedData"),
    Input("year-slider", "value"),
    Input("transmission-list", "value"),
    Input("reset", "n_clicks"),
    Input("scatter-plot", "selectedData"),
    State("selection_state", "data"),
)
def update_selection_state(year_range, transmission_list, n_clicks, selectedData, state):
    triggered = {t["prop_id"] for t in callback_context.triggered}
    return resolve_selection_update(
        df, triggered, year_range, transmission_list, selectedData, state
    )


@app.callback(
    Output("histogram-with-slider", "figure"),
    Output("scatter-plot", "figure"),
    Output("data-table", "data"),
    Output("selected_count", "children"),
    Input("year-slider", "value"),
    Input("transmission-list", "value"),
    Input("selection_state", "data"),
)
def update_figure(year_range, transmission_list, state):
    filtered_df = filter_dataframe(df, year_range, transmission_list)

    fig_hist = px.histogram(
        filtered_df,
        x="fuelCost08",
        color="class_summary",
        labels={"fuelCost08": "Annual Fuel Cost"},
        nbins=40,
    )

    fig_scatter = px.scatter(
        filtered_df,
        x="displ",
        y="fuelCost08",
        hover_data=[filtered_df.index, "make", "model", "year"],
    )
    fig_scatter.update_layout(clickmode="event", uirevision=True)
    fig_scatter.update_traces(selected_marker_color="red")

    table_df, selected_point_indices, label = resolve_selection_render(
        df, year_range, transmission_list, state
    )

    if selected_point_indices:
        fig_scatter.update_traces(selectedpoints=selected_point_indices)

    return fig_hist, fig_scatter, table_df.to_dict("records"), label


if __name__ == "__main__":
    app.run_server(debug=True)
