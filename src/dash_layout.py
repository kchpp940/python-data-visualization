"""Dash 应用的页面组件组装层。

把散点图、筛选器、按钮组、对比面板等 UI 子树从 ``dash_full_app.py``
里拆出来，便于在不触碰回调逻辑的情况下调整布局。

组件 builder 接受运行时所需的数据（年份列表、变速箱列表等），返回
``dash`` 的组件实例，完全不依赖 ``app`` 本身。
"""

from __future__ import annotations

from dash import dash_table, dcc, html


DEFAULT_STYLES = {"pre": {"border": "thin lightgrey solid", "overflowX": "scroll"}}

DEFAULT_COLUMNS = [
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


def build_stores() -> list:
    """顶部 dcc.Store，承载跨回调共享的轻量状态。

    - pinned-vehicles: 已固定用于对比的 pin_id 列表
    - last-reset-click: 最近一次 "Reset selections" 按钮的点击计数
    - reset-baseline: 回调侧已处理过的 reset 计数，用于判断"是否有新的 reset"
    """
    return [
        dcc.Store(id="pinned-vehicles", data=[]),
        dcc.Store(id="last-reset-click", data=0),
        dcc.Store(id="reset-baseline", data=0),
    ]


def build_filter_panel(all_years, transmission_types, min_year, max_year) -> list:
    """散点图 + 直方图 + 年份滑条 + 变速箱多选。"""
    return [
        html.P("Talk Python Training Example"),
        dcc.Graph(id="histogram-with-slider", config={"displayModeBar": False}),
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
    ]


def build_action_buttons() -> html.Div:
    """Reset / Pin scatter / Pin table 三个动作按钮。"""
    return html.Div(
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
    )


def build_data_table(columns=None) -> tuple[dash_table.DataTable, html.H3]:
    """选中计数标题 + 可多选的数据表。"""
    cols = columns if columns is not None else DEFAULT_COLUMNS
    title = html.H3(id="selected_count")
    table = dash_table.DataTable(
        id="data-table",
        data=[],
        page_size=10,
        row_selectable="multi",
        selected_rows=[],
        columns=[{"name": i, "id": i} for i in cols],
    )
    return title, table


def build_comparison_panel() -> html.Div:
    """右侧对比面板：提示 + 清空按钮 + 消息 + 对比表。"""
    return html.Div(
        [
            html.H3("车型对比面板"),
            html.Div(
                '从散点图或表格中选中车型，点击"Pin"按钮加入对比。',
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
    )


def build_left_panel(all_years, transmission_types, min_year, max_year) -> html.Div:
    """左侧主面板：筛选器 + 按钮 + 数据表。"""
    title, table = build_data_table()
    return html.Div(
        build_filter_panel(all_years, transmission_types, min_year, max_year)
        + [html.Hr(), build_action_buttons(), title, table],
        style={"width": "60%", "display": "inline-block", "vertical-align": "top"},
    )


def build_full_layout(all_years, transmission_types, min_year, max_year) -> html.Div:
    """组装整页布局，供 ``app.layout`` 直接使用。"""
    return html.Div(
        [
            html.H1("Fuel Cost Analysis"),
            *build_stores(),
            html.Div(
                [
                    build_left_panel(
                        all_years, transmission_types, min_year, max_year
                    ),
                    build_comparison_panel(),
                ]
            ),
        ],
        style={"margin-bottom": "150px"},
    )


__all__ = [
    "DEFAULT_STYLES",
    "DEFAULT_COLUMNS",
    "build_stores",
    "build_filter_panel",
    "build_action_buttons",
    "build_data_table",
    "build_comparison_panel",
    "build_left_panel",
    "build_full_layout",
]
