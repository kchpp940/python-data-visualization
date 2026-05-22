"""数据集加载器。

负责从磁盘读取数据集文件，支持 CSV 和 Excel 格式。

使用方式::

    from src.dataset_loader import DatasetLoader

    loader = DatasetLoader()
    df = loader.load("epa_fuel_economy_summary")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from data_paths import RAW_DATA_DIR
from src.dataset_metadata import DatasetMetadata, get_dataset


class DatasetLoader:
    """数据集文件加载器。"""

    def __init__(self) -> None:
        self._df_cache: dict[str, pd.DataFrame] = {}

    def get_data_path(self, dataset_id: str) -> Path:
        """获取数据集文件路径。"""
        meta = get_dataset(dataset_id)
        path = RAW_DATA_DIR / meta.file_name
        if not path.exists():
            raise FileNotFoundError(
                f"数据集文件不存在: {path}. "
                f"请确保 {meta.file_name} 位于 {RAW_DATA_DIR} 目录下。"
            )
        return path

    def load(self, dataset_id: str, use_cache: bool = True, **kwargs) -> pd.DataFrame:
        """加载数据集为 DataFrame。

        Parameters
        ----------
        dataset_id: 数据集 ID
        use_cache: 是否使用内存缓存
        **kwargs: 传递给 pandas 读取函数的额外参数
        """
        if use_cache and dataset_id in self._df_cache:
            return self._df_cache[dataset_id]

        meta = get_dataset(dataset_id)
        path = self.get_data_path(dataset_id)

        if meta.file_type == "csv":
            df = pd.read_csv(path, **kwargs)
        elif meta.file_type in ("xlsx", "xls", "xlsm"):
            from src.ch6_init import read_excel_safe
            df = read_excel_safe(path, **kwargs)
        else:
            raise ValueError(f"不支持的文件类型: {meta.file_type}")

        if use_cache:
            self._df_cache[dataset_id] = df

        return df

    def invalidate_cache(self, dataset_id: str | None = None) -> None:
        """清除缓存。

        Parameters
        ----------
        dataset_id: 数据集 ID，None 表示清除全部
        """
        if dataset_id is None:
            self._df_cache.clear()
        else:
            self._df_cache.pop(dataset_id, None)


__all__ = ["DatasetLoader"]
