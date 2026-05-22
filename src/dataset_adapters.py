"""适配器模块：为 Dash、Plotly 和 Notebook 提供适配层。

将数据集元数据适配到各框架的格式要求，避免业务代码重复处理。

使用方式::

    from src.dataset_adapters import DatasetAdapters

    adapters = DatasetAdapters()
    dash_cols = adapters.get_dash_table_columns("epa_fuel_economy_summary")
    plotly_labels = adapters.get_plotly_labels("epa_fuel_economy_summary")
    df, info = adapters.notebook_init("epa_fuel_economy_summary")
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.dataset_loader import DatasetLoader
from src.dataset_metadata import get_dataset
from src.dataset_profile import DatasetProfiler
from src.dataset_docs import DatasetDocsGenerator


class DatasetAdapters:
    """各框架的适配器。"""

    def __init__(
        self,
        loader: DatasetLoader | None = None,
        profiler: DatasetProfiler | None = None,
        docs: DatasetDocsGenerator | None = None,
    ) -> None:
        self._loader = loader or DatasetLoader()
        self._profiler = profiler or DatasetProfiler()
        self._docs = docs or DatasetDocsGenerator()

    def get_dash_table_columns(self, dataset_id: str) -> list[dict[str, str]]:
        """获取 Dash DataTable 可用的列定义。"""
        meta = get_dataset(dataset_id)
        return [
            {"name": meta.get_field_label(f), "id": f}
            for f in meta.default_display_fields
        ]

    def get_dash_filter_options(self, dataset_id: str, field_name: str) -> list[dict[str, str]]:
        """获取 Dash 筛选器的选项列表。"""
        df = self._loader.load(dataset_id)
        values = sorted(df[field_name].dropna().unique().tolist())
        return [{"label": str(v), "value": v} for v in values]

    def get_plotly_labels(self, dataset_id: str) -> dict[str, str]:
        """获取 Plotly 可用的 labels 字典。"""
        return get_dataset(dataset_id).get_labels_dict()

    def notebook_init(self, dataset_id: str, **kwargs) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Notebook 一键初始化：加载数据集并返回完整信息。

        在 Notebook 中使用::

            from src.dataset_service import get_service
            df, info = get_service().notebook_init("epa_fuel_economy_summary")

        Parameters
        ----------
        dataset_id: 数据集 ID
        **kwargs: 传递给 load 的额外参数

        Returns
        -------
        (df, info)
        """
        df = self._loader.load(dataset_id, **kwargs)
        info = self._docs._get_full_info(dataset_id)

        try:
            from IPython.display import display, Markdown

            display(Markdown(f"### {info['name']}"))
            display(Markdown(f"**{info['description']}**"))
            display(Markdown(
                f"- **行数**: {info['row_count']:,}  "
                f"- **列数**: {info['column_count']}  "
                f"- **文件**: `{info['file_name']}`"
            ))
        except ImportError:
            pass

        return df, info


__all__ = ["DatasetAdapters"]
