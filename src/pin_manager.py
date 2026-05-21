"""车型对比面板：pin / 去重 / 失效清理 / 对比表构建。

将与"已固定车型"相关的状态逻辑从 Dash 回调中抽离，
使得 dash_full_app.py 的回调只负责把 UI 事件映射到本模块的纯函数。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VehicleKey:
    """唯一标识一辆车型的复合键。"""

    make: str
    model: str
    year: int
    transmission: str

    @classmethod
    def from_row(cls, row: pd.Series | dict) -> "VehicleKey":
        return cls(
            make=str(row["make"]),
            model=str(row["model"]),
            year=int(row["year"]),
            transmission=str(row["transmission"]),
        )

    def as_list(self) -> list:
        return [self.make, self.model, self.year, self.transmission]


METRIC_COLS: dict[str, str] = {
    "city08": "城市油耗 (MPG)",
    "highway08": "高速油耗 (MPG)",
    "fuelCost08": "年燃油成本 ($)",
    "co2": "CO2 排放 (g/mi)",
}


# ---------------------------------------------------------------------------
# 辅助
# ---------------------------------------------------------------------------

def _matches_filters(
    row: pd.Series,
    year_range: tuple[int, int],
    transmission_list: Iterable[str],
) -> bool:
    return (
        year_range[0] <= row["year"] <= year_range[1]
        and row["transmission"] in transmission_list
    )


def _lookup(df: pd.DataFrame, key: VehicleKey) -> pd.Series | None:
    mask = (
        (df["make"] == key.make)
        & (df["model"] == key.model)
        & (df["year"] == key.year)
        & (df["transmission"] == key.transmission)
    )
    hits = df[mask]
    if hits.empty:
        return None
    return hits.iloc[0]


# ---------------------------------------------------------------------------
# 公共 API
# ---------------------------------------------------------------------------

def add_pins(
    df: pd.DataFrame,
    pinned: list[dict],
    new_keys: Iterable[VehicleKey],
    year_range: tuple[int, int],
    transmission_list: Iterable[str],
) -> list[dict]:
    """向已固定列表追加新车，自动去重并跳过当前筛选下失效的项。

    Parameters
    ----------
    df : 原始完整 DataFrame
    pinned : 当前已固定列表（每项形如 {"key": [make, model, year, transmission]}）
    new_keys : 本次要加入的键集合
    year_range, transmission_list : 当前筛选条件

    Returns
    -------
    更新后的 pinned 列表（新建 list，不修改入参）
    """
    existing = {
        VehicleKey(*p["key"]) for p in pinned if isinstance(p, dict) and "key" in p
    }
    result = list(pinned)

    for key in new_keys:
        if key in existing:
            continue
        row = _lookup(df, key)
        if row is None or not _matches_filters(row, year_range, transmission_list):
            continue
        existing.add(key)
        result.append({"key": key.as_list()})

    return result


def remove_invalid(
    df: pd.DataFrame,
    pinned: list[dict],
    year_range: tuple[int, int],
    transmission_list: Iterable[str],
) -> tuple[list[dict], int]:
    """从 pinned 中移除不再匹配当前筛选条件的项。

    Returns
    -------
    (新列表, 被移除的数量)
    """
    kept: list[dict] = []
    removed = 0
    for p in pinned:
        if not isinstance(p, dict) or "key" not in p:
            removed += 1
            continue
        key = VehicleKey(*p["key"])
        row = _lookup(df, key)
        if row is None or not _matches_filters(row, year_range, transmission_list):
            removed += 1
            continue
        kept.append({"key": key.as_list()})
    return kept, removed


def build_comparison(
    df: pd.DataFrame,
    pinned: list[dict],
    year_range: tuple[int, int],
    transmission_list: Iterable[str],
) -> tuple[list[dict], list[dict], str]:
    """构建对比表的数据、列定义和提示消息。

    对比表为"转置"形态：每行为一项指标，每列为一辆车型。
    失效项**不会**出现在表中（调用方应确保已先调用 remove_invalid 清理 Store）。

    Returns
    -------
    (data, columns, message)
    """
    if not pinned:
        return [], [], "暂无对比车型"

    records: list[pd.Series] = []
    for p in pinned:
        if not isinstance(p, dict) or "key" not in p:
            continue
        key = VehicleKey(*p["key"])
        row = _lookup(df, key)
        if row is None or not _matches_filters(row, year_range, transmission_list):
            continue
        records.append(row)

    if not records:
        return [], [], "筛选条件变化后，没有可用的对比项。"

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
