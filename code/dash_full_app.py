from pathlib import Path
import sys

import pandas as pd

from dash import Dash, html, dcc, Input, Output, State, dash_table, no_update
import plotly.express as px

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pin_manager import (  # noqa: E402
    add_pins,
    build_comparison,
    remove_invalid,
)
from src.dataset_service import get_service  # noqa: E402
from src.dataset_metadata import get_dataset  # noqa: E402

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = Dash(__name__, external_stylesheets=external_stylesheets)

styles = {"pre": {"border": "thin lightgrey solid", "overflowX": "scroll"}}

DATASET_ID = "epa_fuel_economy_summary"
dataset_service = get_service()
dataset_meta = get_dataset(DATASET_ID)

df = dataset_service.load(DATASET_ID)
plotly_labels = dataset_service.get_plotly_labels(DATASET_ID)
data_table_columns = dataset_service.get_dash_table_columns(DATASET_ID)

# Define the input parameters
min_year = int(df["year"].min())
max_year = int(df["year"].max())
all_years = sorted(df["year"].unique())
transmission_types = df["transmission"].unique()

data_table_cols = dataset_meta.default_display_fields

# Need to keep track of button clicks to see if there is a change
total_clicks = 0

app.layout = html.Div(
    [
        html.H1("Fuel Cost Analysis"),
        dcc.Store(id="pinned-vehicles", data=[]),
        dcc.Store(id="last-reset-click", data=0),
        html.Div(
            [
                html.Div(
                    [
                        html.P("Talk Python Training Example"),
                        dcc.Graph(
                            id="histogram-with-slider",
                            config={"displayModeBar": False},
                        ),
                        dcc.Graph(id="scatter-plot"),
                        html.Label("Year Range"),
                        dcc.RangeSlider(
                            id="year-slider",
                            min=min_year,
                            max=max_year,
                            value=(min_year, max_year),
                            marks={str(y): str(y) for y in all_years},
                        ),
                        html.Label("Transmission type"),
                        dcc.Checklist(
                            id="transmission-list",
                            options=[{"label": i, "value": i} for i in transmission_types],
                            value=list(transmission_types),
                            labelStyle={"display": "inline-block"},
                        ),
                        html.Hr(),
                        html.Div(
                            [
                                html.Button(
                                    "Reset selections",
                                    id="reset",
                                    n_clicks=0,
                                    style={"margin-right": "10px"},
                                ),
                                html.Button(
                                    "Pin selected scatter points",
                                    id="pin-from-scatter",
                                    n_clicks=0,
                                    style={"margin-right": "10px"},
                                ),
                                html.Button(
                                    "Pin selected table rows",
                                    id="pin-from-table",
                                    n_clicks=0,
                                ),
                            ]
                        ),
                        html.H3(id="selected_count"),
                        dash_table.DataTable(
                            id="data-table",
                            data=[],
                            page_size=10,
                            row_selectable="multi",
                            selected_rows=[],
                            columns=data_table_columns,
                        ),
                    ],
                    style={"width": "60%", "display": "inline-block", "vertical-align": "top"},
                ),
                html.Div(
                    [
                        html.H3("车型对比面板"),
                        html.Div(
                            "从散点图或表格中选中车型，点击“Pin”按钮加入对比。",
                            style={"font-size": "12px", "color": "#666", "margin-bottom": "10px"},
                        ),
                        html.Button(
                            "Clear all pinned",
                            id="clear-pinned",
                            n_clicks=0,
                            style={"margin-bottom": "10px"},
                        ),
                        html.Div(
                            id="comparison-message",
                            style={"font-size": "12px", "color": "#888", "margin-bottom": "8px"},
                        ),
                        dash_table.DataTable(
                            id="comparison-table",
                            data=[],
                            columns=[],
                            style_cell={"padding": "6px 10px", "textAlign": "center"},
                            style_header={"fontWeight": "bold"},
                        ),
                    ],
                    style={
                        "width": "38%",
                        "display": "inline-block",
                        "vertical-align": "top",
                        "margin-left": "2%",
                    },
                ),
            ],
        ),
    ],
    style={"margin-bottom": "150px"},
)


# ---------------------------------------------------------------------------
# 回调 1：记录 Reset 点击
# ---------------------------------------------------------------------------

@app.callback(
    Output("last-reset-click", "data"),
    Input("reset", "n_clicks"),
    prevent_initial_call=True,
)
def record_reset(n_clicks):
    return n_clicks if n_clicks is not None else 0


# ---------------------------------------------------------------------------
# 回调 2：图表 + 数据表
# ---------------------------------------------------------------------------

@app.callback(
    Output("histogram-with-slider", "figure"),
    Output("scatter-plot", "figure"),
    Output("data-table", "data"),
    Output("selected_count", "children"),
    Input("year-slider", "value"),
    Input("transmission-list", "value"),
    Input("scatter-plot", "selectedData"),
    Input("last-reset-click", "data"),
)
def update_figure(year_range, transmission_list, selectedData, last_reset):
    global total_clicks
    filtered_df = df[
        df["year"].between(year_range[0], year_range[1])
        & df["transmission"].isin(transmission_list)
    ]

    fig_hist = px.histogram(
        filtered_df,
        x="fuelCost08",
        color="class_summary",
        labels=plotly_labels,
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

    if last_reset is not None and last_reset > total_clicks:
        fig_scatter.update_traces(selected_marker_color=None)
        total_clicks = last_reset
        selectedData = None

    if selectedData:
        points = selectedData["points"]
        index_list = [points[x]["customdata"][0] for x in range(len(points))]
        table_df = df[df.index.isin(index_list)]
        num_points_label = f"Showing {len(points)} selected points:"
    else:
        num_points_label = "No points selected - showing top 10 only"
        table_df = filtered_df.head(10)

    # pin_id 列用于从表格反查原始行索引（DataFrame 的原始 index）
    table_records = (
        table_df.reset_index().rename(columns={"index": "pin_id"}).to_dict("records")
    )
    return fig_hist, fig_scatter, table_records, num_points_label


# ---------------------------------------------------------------------------
# 回调 3：同步 pinned-vehicles Store（唯一写入方）
#
# 触发源：
#   - 筛选器变化（year-slider / transmission-list）：仅做失效清理
#   - Pin 按钮：先追加 pin_id，再做失效清理
#   - Clear 按钮：清空
#
# pin_id 即原始 DataFrame 的行索引，作为记录的唯一身份，
# 保证同一款车型的不同 trim 也能被独立固定。
# ---------------------------------------------------------------------------

@app.callback(
    Output("pinned-vehicles", "data"),
    Input("pin-from-scatter", "n_clicks"),
    Input("pin-from-table", "n_clicks"),
    Input("clear-pinned", "n_clicks"),
    Input("year-slider", "value"),
    Input("transmission-list", "value"),
    State("scatter-plot", "selectedData"),
    State("data-table", "selected_rows"),
    State("data-table", "data"),
    State("pinned-vehicles", "data"),
)
def sync_pinned_store(
    pin_scatter_n,
    pin_table_n,
    clear_n,
    year_range,
    transmission_list,
    selectedData,
    selected_rows,
    table_data,
    pinned,
):
    ctx = dash.callback_context

    if not ctx.triggered:
        return no_update

    triggered = [t["prop_id"].split(".")[0] for t in ctx.triggered]

    if "clear-pinned" in triggered:
        return []

    pinned = list(pinned or [])

    for source in triggered:
        if source == "pin-from-scatter" and selectedData:
            new_pin_ids = []
            for pt in selectedData["points"]:
                pid = pt["customdata"][0]
                if 0 <= pid < len(df):
                    new_pin_ids.append(int(pid))
            pinned = add_pins(df, pinned, new_pin_ids, year_range, transmission_list)

        elif source == "pin-from-table" and selected_rows:
            new_pin_ids = []
            for i in selected_rows:
                if i < len(table_data):
                    pid = table_data[i]["pin_id"]
                    new_pin_ids.append(int(pid))
            pinned = add_pins(df, pinned, new_pin_ids, year_range, transmission_list)

    # 统一按当前筛选条件失效清理，确保 Store 与页面显示一致
    pinned, _ = remove_invalid(df, pinned, year_range, transmission_list)
    return pinned


# ---------------------------------------------------------------------------
# 回调 4：渲染对比表
# ---------------------------------------------------------------------------

@app.callback(
    Output("comparison-table", "data"),
    Output("comparison-table", "columns"),
    Output("comparison-message", "children"),
    Input("pinned-vehicles", "data"),
    Input("year-slider", "value"),
    Input("transmission-list", "value"),
)
def render_comparison(pinned, year_range, transmission_list):
    data, columns, msg = build_comparison(df, pinned, year_range, transmission_list)
    return data, columns, msg


if __name__ == "__main__":
    app.run_server(debug=True)
