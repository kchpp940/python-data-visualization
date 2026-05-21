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
from dataset_metadata import DATASETS, get_dataset_info  # noqa: E402

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = Dash(__name__, external_stylesheets=external_stylesheets)

styles = {"pre": {"border": "thin lightgrey solid", "overflowX": "scroll"}}

src_file = Path(__file__).resolve().parent / "data" / "raw" / "EPA_fuel_economy_summary.csv"
df = pd.read_csv(src_file)

min_year = int(df["year"].min())
max_year = int(df["year"].max())
all_years = sorted(df["year"].unique())
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

total_clicks = 0


def build_dataset_info_layout():
    """Build the dataset information tab layout."""
    dataset_options = [
        {"label": meta.name, "value": key} for key, meta in DATASETS.items()
    ]

    return html.Div(
        [
            html.H2("📊 数据集信息"),
            html.Div(
                [
                    html.P("选择数据集查看详细信息："),
                    dcc.Dropdown(
                        id="dataset-selector",
                        options=dataset_options,
                        value=list(DATASETS.keys())[0],
                        clearable=False,
                    ),
                ],
                style={"margin-bottom": "20px"},
            ),
            html.Div(
                [
                    html.Div(id="dataset-basic-info"),
                    html.Hr(),
                    html.H4("字段说明"),
                    dash_table.DataTable(
                        id="dataset-fields-table",
                        columns=[
                            {"name": "字段名", "id": "name"},
                            {"name": "类型", "id": "dtype"},
                            {"name": "说明", "id": "description"},
                            {"name": "缺失值", "id": "missing"},
                        ],
                        data=[],
                        style_cell={
                            "textAlign": "left",
                            "padding": "8px",
                            "whiteSpace": "normal",
                            "height": "auto",
                        },
                        style_header={"fontWeight": "bold", "backgroundColor": "#f5f5f5"},
                        style_data_conditional=[
                            {
                                "if": {"column_id": "missing", "filter_query": '{missing} > "0"'},
                                "color": "red",
                                "fontWeight": "bold",
                            }
                        ],
                    ),
                    html.Hr(),
                    html.H4("章节使用示例"),
                    dash_table.DataTable(
                        id="dataset-chapters-table",
                        columns=[
                            {"name": "章节", "id": "chapter"},
                            {"name": "练习", "id": "exercises"},
                            {"name": "用途", "id": "purpose"},
                            {"name": "关键字段", "id": "key_fields"},
                        ],
                        data=[],
                        style_cell={
                            "textAlign": "left",
                            "padding": "8px",
                            "whiteSpace": "normal",
                            "height": "auto",
                        },
                        style_header={"fontWeight": "bold", "backgroundColor": "#f5f5f5"},
                    ),
                    html.Hr(),
                    html.H4("备注"),
                    html.Div(id="dataset-notes"),
                ],
                style={"maxWidth": "900px"},
            ),
        ],
        style={"padding": "20px"},
    )


app.layout = html.Div(
    [
        html.H1("Python 数据可视化课程示例"),
        dcc.Tabs(
            id="app-tabs",
            value="fuel-analysis",
            children=[
                dcc.Tab(label="🚗 燃油成本分析", value="fuel-analysis"),
                dcc.Tab(label="📊 数据集信息", value="dataset-info"),
            ],
        ),
        html.Div(id="tabs-content"),
    ],
    style={"margin-bottom": "150px"},
)


fuel_analysis_layout = html.Div(
    [
        html.H2("Fuel Cost Analysis"),
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
                            columns=[{"name": i, "id": i} for i in data_table_cols],
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
    style={"padding": "20px"},
)


@app.callback(Output("tabs-content", "children"), Input("app-tabs", "value"))
def render_tab(tab_value):
    if tab_value == "fuel-analysis":
        return fuel_analysis_layout
    elif tab_value == "dataset-info":
        return build_dataset_info_layout()
    return html.Div()


@app.callback(
    Output("dataset-basic-info", "children"),
    Output("dataset-fields-table", "data"),
    Output("dataset-chapters-table", "data"),
    Output("dataset-notes", "children"),
    Input("dataset-selector", "value"),
)
def update_dataset_info(dataset_key):
    _, info = get_dataset_info(dataset_key, load_data=False)

    basic_info = html.Div(
        [
            html.H3(info.name),
            html.P(info.static.description),
            html.Div(
                [
                    html.Strong("文件名："),
                    html.Span(f"{info.filename} ({info.static.file_type})"),
                    html.Br(),
                    html.Strong("行数："),
                    html.Span(f"{info.row_count:,}"),
                    html.Br(),
                    html.Strong("列数："),
                    html.Span(f"{info.column_count}"),
                    html.Br(),
                    html.Strong("缺失值："),
                    html.Span(
                        f"{info.total_missing:,} ({info.missing_pct:.2f}%)",
                        style={"color": "red" if info.total_missing > 0 else "inherit"},
                    ),
                ],
                style={
                    "backgroundColor": "#f9f9f9",
                    "padding": "15px",
                    "borderRadius": "5px",
                },
            ),
        ]
    )

    fields_data = [
        {
            "name": f.name,
            "dtype": f.dtype,
            "description": f.description,
            "missing": str(info.missing_values.get(f.name, 0)),
        }
        for f in info.fields
    ]

    chapters_data = [
        {
            "chapter": f"第 {ch.chapter} 章",
            "exercises": ", ".join(str(e) for e in ch.exercises),
            "purpose": ch.purpose,
            "key_fields": ", ".join(ch.key_fields),
        }
        for ch in info.chapters
    ]

    if info.notes:
        notes = html.Ul([html.Li(note) for note in info.notes])
    else:
        notes = html.P("无备注")

    return basic_info, fields_data, chapters_data, notes


@app.callback(
    Output("last-reset-click", "data"),
    Input("reset", "n_clicks"),
    prevent_initial_call=True,
)
def record_reset(n_clicks):
    return n_clicks if n_clicks is not None else 0


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

    table_records = (
        table_df.reset_index().rename(columns={"index": "pin_id"}).to_dict("records")
    )
    return fig_hist, fig_scatter, table_records, num_points_label


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

    pinned, _ = remove_invalid(df, pinned, year_range, transmission_list)
    return pinned


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
