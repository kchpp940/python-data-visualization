"""车型对比面板：pin / 去重 / 失效清理 / 对比表构建。

所有对外 API 统一以 ``pin_id``（原始 DataFrame 的行索引，int）
作为一条车型记录的唯一身份，保证同一款车型的不同 trim 也能被
独立固定。筛选 / 去重 / 对比表渲染等纯业务逻辑集中在此，Dash
回调只负责把 UI 事件翻译成 ``pin_id`` 列表并调用本模块的纯函数。
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd

METRIC_COLS: dict[str, str] = {
    "city08": "城市油耗 (MPG)",
    "highway08": "高速油耗 (MPG)",
    "fuelCost08": "年燃油成本 ($)",
    "co2": "CO2 排放 (g/mi)",
}

LABEL_COLS = ["make", "model", "year", "transmission"]


# ---------------------------------------------------------------------------
# 内部辅助
# ---------------------------------------------------------------------------

def _matches_filters(
    row: pd.Series,
    year_range: tuple[int, int],
    transmission_list: Iterable[str],
) -> bool:
    return (
        year_range[0] <= row["year"] <= year_range[1]
        and row["transmission"] in set(transmission_list)
    )


def _safe_pin_id(pid) -> int | None:
    try:
        return int(pid)
    except (TypeError, ValueError):
        return None


def _valid_ids(df: pd.DataFrame, pin_ids: Iterable) -> list[int]:
    n = len(df)
    out: list[int] = []
    seen: set[int] = set()
    for pid in pin_ids:
        i = _safe_pin_id(pid)
        if i is None or i < 0 or i >= n or i in seen:
            continue
        seen.add(i)
        out.append(i)
    return out


# ---------------------------------------------------------------------------
# 公共 API
# ---------------------------------------------------------------------------

def add_pins(
    df: pd.DataFrame,
    pinned: list[int],
    new_pin_ids: Iterable[int],
    year_range: tuple[int, int],
    transmission_list: Iterable[str],
) -> list[int]:
    """向已固定列表追加新的 pin_id，自动去重并跳过当前筛选下失效的项。

    Parameters
    ----------
    df : 原始完整 DataFrame（索引即为 pin_id）
    pinned : 当前已固定的 pin_id 列表
    new_pin_ids : 本次要加入的 pin_id 集合
    year_range, transmission_list : 当前筛选条件

    Returns
    -------
    更新后的 pinned 列表（新建 list，不修改入参）
    """
    existing = set(int(p) for p in pinned)
    result = list(pinned)
    t_set = set(transmission_list)

    for pid in _valid_ids(df, new_pin_ids):
        if pid in existing:
            continue
        row = df.iloc[pid]
        if not _matches_filters(row, year_range, t_set):
            continue
        existing.add(pid)
        result.append(pid)

    return result


def remove_invalid(
    df: pd.DataFrame,
    pinned: Iterable[int],
    year_range: tuple[int, int],
    transmission_list: Iterable[str],
) -> tuple[list[int], int]:
    """从 pinned 中移除不再匹配当前筛选条件或越界的项。

    Returns
    -------
    (新列表, 被移除的数量)
    """
    kept: list[int] = []
    removed = 0
    t_set = set(transmission_list)
    for pid in pinned:
        i = _safe_pin_id(pid)
        if i is None or i < 0 or i >= len(df):
            removed += 1
            continue
        if not _matches_filters(df.iloc[i], year_range, t_set):
            removed += 1
            continue
        kept.append(i)
    return kept, removed


def build_comparison(
    df: pd.DataFrame,
    pinned: Iterable[int],
    year_range: tuple[int, int],
    transmission_list: Iterable[str],
) -> tuple[list[dict], list[dict], str]:
    """构建对比表的数据、列定义和提示消息。

    对比表为"转置"形态：每行为一项指标，每列为一辆车型。
    失效项**不会**出现在表中（调用方应确保已先调用 remove_invalid
    清理 Store）。

    Returns
    -------
    (data, columns, message)
    """
    t_set = set(transmission_list)
    valid = _valid_ids(df, pinned)
    records = [
        df.iloc[pid]
        for pid in valid
        if _matches_filters(df.iloc[pid], year_range, t_set)
    ]

    if not records:
        return [], [], "暂无对比车型"

    def _label(r: pd.Series) -> str:
        return f"{r['make']} {r['model']} ({int(r['year'])}, {r['transmission']})"

    transposed: list[dict] = []
    for metric_id, metric_name in METRIC_COLS.items():
        item = {"指标": metric_name}
        for row in records:
            item[_label(row)] = row[metric_id]
        transposed.append(item)

    columns: list[dict] = [{"name": "指标", "id": "指标"}] + [
        {"name": _label(r), "id": _label(r)} for r in records
    ]

    msg = f"对比车型: {len(records)}"
    return transposed, columns, msg


__all__ = [
    "add_pins",
    "remove_invalid",
    "build_comparison",
    "METRIC_COLS",
    "LABEL_COLS",
]
