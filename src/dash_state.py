"""筛选条件 / 散点选中 / 数据表 — 与 pin_manager 对应的另一块"纯业务"。

本模块只负责：

1. 按 ``year_range`` + ``transmission_list`` 过滤原始 DataFrame；
2. 从散点图 ``selectedData`` 或 DataTable 的 ``selected_rows`` 中
   解析出原始 ``pin_id``；
3. 构建 histogram / scatter figure、DataTable records 及选中标签。

回调函数不直接写判断逻辑，而是把 UI 事件的原始参数丢给本模块的纯函数。
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd
import plotly.express as px


# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------

def filter_by(df: pd.DataFrame,
              year_range: tuple[int, int],
              transmission_list: Iterable[str]) -> pd.DataFrame:
    """按年份区间和变速箱多选筛选。"""
    return df[
        df["year"].between(year_range[0], year_range[1])
        & df["transmission"].isin(set(transmission_list))
    ]


def pin_ids_from_scatter(selected_data) -> list[int]:
    """从 plotly 散点图 ``selectedData`` 中解析 pin_id 列表。

    约定：散点的 ``customdata[0]`` 为原始 DataFrame 的行索引。
    ``selected_data`` 为空 / None 时返回空列表。
    """
    if not selected_data:
        return []
    points = selected_data.get("points") or []
    ids: list[int] = []
    seen: set[int] = set()
    for pt in points:
        cd = pt.get("customdata") or []
        if not cd:
            continue
        try:
            pid = int(cd[0])
        except (TypeError, ValueError):
            continue
        if pid in seen:
            continue
        seen.add(pid)
        ids.append(pid)
    return ids


def pin_ids_from_table(selected_rows: list[int] | None,
                       table_data: list[dict]) -> list[int]:
    """从 DataTable 的 ``selected_rows`` 中解析 pin_id。

    DataTable 的行号只代表当前页面内的相对位置，真正的身份来自
    每行记录里的 ``pin_id`` 字段（由 :func:`build_table_records` 注入）。
    """
    if not selected_rows:
        return []
    ids: list[int] = []
    seen: set[int] = set()
    for i in selected_rows:
        if i < 0 or i >= len(table_data):
            continue
        pid = table_data[i].get("pin_id")
        if pid is None:
            continue
        try:
            pid = int(pid)
        except (TypeError, ValueError):
            continue
        if pid in seen:
            continue
        seen.add(pid)
        ids.append(pid)
    return ids


# ---------------------------------------------------------------------------
# 图表 + 数据表
# ---------------------------------------------------------------------------

def build_histogram(filtered_df: pd.DataFrame):
    return px.histogram(
        filtered_df,
        x="fuelCost08",
        color="class_summary",
        labels={"fuelCost08": "Annual Fuel Cost"},
        nbins=40,
    )


def build_scatter(filtered_df: pd.DataFrame):
    fig = px.scatter(
        filtered_df,
        x="displ",
        y="fuelCost08",
        hover_data=[filtered_df.index, "make", "model", "year"],
    )
    fig.update_layout(clickmode="event", uirevision=True)
    fig.update_traces(selected_marker_color="red")
    return fig


def build_table_records(table_df: pd.DataFrame) -> list[dict]:
    """把要展示的 DataFrame 转为 DataTable 记录，额外注入 ``pin_id``。"""
    return (
        table_df.reset_index()
        .rename(columns={"index": "pin_id"})
        .to_dict("records")
    )


def choose_table_source(df: pd.DataFrame,
                        filtered_df: pd.DataFrame,
                        selected_pin_ids: list[int]):
    """决定 DataTable 展示的行及提示文案。"""
    if selected_pin_ids:
        valid = [pid for pid in selected_pin_ids if 0 <= pid < len(df)]
        return df.iloc[valid], f"Showing {len(valid)} selected points:"
    return filtered_df.head(10), "No points selected - showing top 10 only"


# ---------------------------------------------------------------------------
# 整体渲染决策（供 update_figure 回调一次性调用）
# ---------------------------------------------------------------------------

def build_main_view(df: pd.DataFrame,
                    year_range: tuple[int, int],
                    transmission_list: Iterable[str],
                    selected_data,
                    last_reset: int | None,
                    baseline: int | None) -> tuple:
    """统一构建 histogram / scatter / table / label / 新 baseline。

    回调侧只需一行调用，无需再写任何 reset 判断或表格源选择逻辑。

    Parameters
    ----------
    df : 原始完整 DataFrame
    year_range, transmission_list : 当前筛选条件
    selected_data : 散点图的 ``selectedData``
    last_reset : ``last-reset-click`` Store 的当前值
    baseline : ``reset-baseline`` Store 的当前值

    Returns
    -------
    (fig_hist, fig_scatter, table_records, label, new_baseline)
    """
    last_reset = int(last_reset or 0)
    baseline = int(baseline or 0)

    filtered_df = filter_by(df, year_range, transmission_list)
    fig_hist = build_histogram(filtered_df)
    fig_scatter = build_scatter(filtered_df)

    new_baseline = baseline
    if last_reset > baseline:
        fig_scatter.update_traces(selected_marker_color=None)
        selected_data = None
        new_baseline = last_reset

    selected_pin_ids = pin_ids_from_scatter(selected_data)
    table_df, label = choose_table_source(df, filtered_df, selected_pin_ids)

    return (
        fig_hist,
        fig_scatter,
        build_table_records(table_df),
        label,
        new_baseline,
    )


# ---------------------------------------------------------------------------
# pinned-vehicles Store 同步决策（供 sync_pinned_store 回调一次性调用）
# ---------------------------------------------------------------------------

def sync_pinned(df: pd.DataFrame,
                triggered_sources: list[str],
                selected_data,
                selected_rows: list[int] | None,
                table_data: list[dict] | None,
                pinned: list[int] | None,
                year_range: tuple[int, int],
                transmission_list: Iterable[str]) -> list[int] | None:
    """统一决策 pinned-vehicles Store 的新值。

    回调侧只需把 ``dash.callback_context.triggered`` 解析成触发源列表传入，
    无需再写任何分支判断或 pin_id 提取逻辑。

    Parameters
    ----------
    df : 原始完整 DataFrame
    triggered_sources : 触发本次回调的组件 id 列表（不含 prop）
    selected_data : 散点图 selectedData
    selected_rows : DataTable selected_rows
    table_data : DataTable data
    pinned : 当前 pinned-vehicles Store 值
    year_range, transmission_list : 当前筛选条件

    Returns
    -------
    更新后的 pinned 列表，或 ``None`` 表示不需要更新。
    """
    from pin_manager import add_pins, remove_invalid

    if not triggered_sources:
        return None

    if "clear-pinned" in triggered_sources:
        return []

    pinned = list(pinned or [])

    if "pin-from-scatter" in triggered_sources:
        new_ids = pin_ids_from_scatter(selected_data)
        pinned = add_pins(df, pinned, new_ids, year_range, transmission_list)

    if "pin-from-table" in triggered_sources:
        new_ids = pin_ids_from_table(selected_rows, table_data or [])
        pinned = add_pins(df, pinned, new_ids, year_range, transmission_list)

    pinned, _ = remove_invalid(df, pinned, year_range, transmission_list)
    return pinned


__all__ = [
    "filter_by",
    "pin_ids_from_scatter",
    "pin_ids_from_table",
    "build_histogram",
    "build_scatter",
    "build_table_records",
    "choose_table_source",
    "build_main_view",
    "sync_pinned",
]
