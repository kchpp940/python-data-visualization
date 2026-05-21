"""Dash 完整应用：EPA Fuel Economy 分析 + 车型对比面板。

本文件仅作为"组装层"：

- 数据加载 / 常量  →  本文件顶部
- 页面 UI 组件   →  ``src.dash_layout``
- 筛选 + 选中解析 + 图表构建   →  ``src.dash_state``
- pin 去重 / 失效清理 / 对比表  →  ``src.pin_manager``

回调函数只做"把事件翻译为状态操作"这一件事，不再承担具体业务判断。

所有跨请求状态均托管于 ``dcc.Store``，不依赖模块级可变变量，
保证多会话场景下互不污染。
"""

from pathlib import Path
import sys

import pandas as pd

from dash import Dash, Input, Output, State, dash, no_update

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dash_layout import (  # noqa: E402
    DEFAULT_COLUMNS,
    build_full_layout,
)
from dash_state import (  # noqa: E402
    build_main_view,
    sync_pinned,
)
from pin_manager import (  # noqa: E402
    build_comparison,
)

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = Dash(__name__, external_stylesheets=external_stylesheets)

src_file = Path(__file__).resolve().parent / "data" / "raw" / "EPA_fuel_economy_summary.csv"
df = pd.read_csv(src_file)

min_year = int(df["year"].min())
max_year = int(df["year"].max())
all_years = sorted(df["year"].unique())
transmission_types = df["transmission"].unique()

app.layout = build_full_layout(
    all_years=all_years,
    transmission_types=transmission_types,
    min_year=min_year,
    max_year=max_year,
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
#
# 所有 reset 判断 / 图表构建 / 表格源选择均下沉到 build_main_view，
# 本回调只做参数传递和结果分发。
# ---------------------------------------------------------------------------


@app.callback(
    Output("histogram-with-slider", "figure"),
    Output("scatter-plot", "figure"),
    Output("data-table", "data"),
    Output("selected_count", "children"),
    Output("reset-baseline", "data"),
    Input("year-slider", "value"),
    Input("transmission-list", "value"),
    Input("scatter-plot", "selectedData"),
    Input("last-reset-click", "data"),
    State("reset-baseline", "data"),
)
def update_figure(year_range, transmission_list, selected_data, last_reset, baseline):
    return build_main_view(
        df, year_range, transmission_list, selected_data, last_reset, baseline
    )


# ---------------------------------------------------------------------------
# 回调 3：同步 pinned-vehicles Store（唯一写入方）
#
# 所有触发源解析 / pin_id 提取 / 失效清理均下沉到 sync_pinned，
# 本回调只做参数传递和 no_update 判断。
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
    selected_data,
    selected_rows,
    table_data,
    pinned,
):
    del pin_scatter_n, pin_table_n, clear_n

    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update

    triggered = [t["prop_id"].split(".")[0] for t in ctx.triggered]

    result = sync_pinned(
        df, triggered, selected_data, selected_rows, table_data, pinned,
        year_range, transmission_list,
    )
    return result if result is not None else no_update


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
    return build_comparison(df, pinned, year_range, transmission_list)


# 使 DEFAULT_COLUMNS 在外部也可引用（保持与旧版一致）
data_table_cols = DEFAULT_COLUMNS


if __name__ == "__main__":
    app.run_server(debug=True)
