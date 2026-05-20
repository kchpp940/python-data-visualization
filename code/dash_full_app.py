from pathlib import Path
import pandas as pd

from dash import Dash, html, dcc, Input, Output, State, dash_table, no_update
from dash import callback_context as ctx
import plotly.express as px

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
        dcc.Store(
            id="selection-store",
            data={
                "selected_indices": None,
                "year_range": None,
                "transmissions": None,
                "reset_clicks": 0,
            },
        ),
    ],
    style={"margin-bottom": "150px"},
)


@app.callback(
    Output("selection-store", "data"),
    Output("scatter-plot", "selectedData"),
    Input("scatter-plot", "selectedData"),
    Input("reset", "n_clicks"),
    Input("year-slider", "value"),
    Input("transmission-list", "value"),
    State("selection-store", "data"),
)
def update_selection_store(selectedData, n_clicks, year_range, transmission_list, store):
    trigger_ids = {c["prop_id"] for c in ctx.triggered}
    store = store or {}

    if "reset.n_clicks" in trigger_ids:
        return {
            "selected_indices": None,
            "year_range": year_range,
            "transmissions": transmission_list,
            "reset_clicks": n_clicks or 0,
        }, None

    if "year-slider.value" in trigger_ids or "transmission-list.value" in trigger_ids:
        return {
            "selected_indices": None,
            "year_range": year_range,
            "transmissions": transmission_list,
            "reset_clicks": store.get("reset_clicks", 0),
        }, None

    if "scatter-plot.selectedData" in trigger_ids:
        if selectedData:
            points = selectedData.get("points", [])
            index_list = [
                p["customdata"][0] for p in points
                if p.get("customdata")
            ]
            return {
                "selected_indices": index_list,
                "year_range": year_range,
                "transmissions": transmission_list,
                "reset_clicks": store.get("reset_clicks", 0),
            }, no_update
        else:
            return {
                "selected_indices": None,
                "year_range": year_range,
                "transmissions": transmission_list,
                "reset_clicks": store.get("reset_clicks", 0),
            }, no_update

    return store, no_update


@app.callback(
    Output("histogram-with-slider", "figure"),
    Output("scatter-plot", "figure"),
    Output("data-table", "data"),
    Output("selected_count", "children"),
    Input("year-slider", "value"),
    Input("transmission-list", "value"),
    Input("selection-store", "data"),
)
def update_figure(year_range, transmission_list, store):
    filtered_df = df[df["year"].between(year_range[0], year_range[1])
                     & df["transmission"].isin(transmission_list)]

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

    store = store or {}
    store_year = store.get("year_range")
    store_trans = store.get("transmissions")
    selected_indices = store.get("selected_indices")

    year_match = (store_year is not None
                  and store_year[0] == year_range[0]
                  and store_year[1] == year_range[1])
    trans_match = (store_trans is not None
                   and sorted(store_trans) == sorted(transmission_list))

    if selected_indices and year_match and trans_match:
        valid_indices = [i for i in selected_indices if i in filtered_df.index]
        if valid_indices:
            table_df = df.loc[valid_indices, data_table_cols]
            num_points_label = f"Showing {len(valid_indices)} selected points:"
        else:
            table_df = filtered_df[data_table_cols].head(10)
            num_points_label = "No points selected - showing top 10 only"
    else:
        table_df = filtered_df[data_table_cols].head(10)
        num_points_label = "No points selected - showing top 10 only"

    return fig_hist, fig_scatter, table_df.to_dict(
        "records"), num_points_label


if __name__ == "__main__":
    app.run_server(debug=True)
