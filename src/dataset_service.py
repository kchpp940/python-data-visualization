"""数据集服务门面（Facade）。

**重要**：此类仅作为统一入口，所有具体逻辑委托给子模块：
- 数据加载 → `dataset_loader.DatasetLoader`
- Profile 生成 → `dataset_profile.DatasetProfiler`
- 文档生成 → `dataset_docs.DatasetDocsGenerator`
- 框架适配 → `dataset_adapters.DatasetAdapters`

使用方式::

    from src.dataset_service import get_service

    service = get_service()
    df = service.load("epa_fuel_economy_summary")
    profile = service.get_profile("epa_fuel_economy_summary")
    info = service.get_full_info("epa_fuel_economy_summary")

    # 生成单个数据集的 README 片段（可用于文档，但不允许全量覆盖）
    readme = service.generate_readme_section("epa_fuel_economy_summary")

    # 安全地更新 README 标记区块
    service.update_readme_markdown_block("README.md")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.dataset_loader import DatasetLoader
from src.dataset_metadata import (
    DatasetMetadata,
    get_dataset,
    list_datasets,
)
from src.dataset_profile import DatasetProfile, DatasetProfiler
from src.dataset_docs import DatasetDocsGenerator
from src.dataset_adapters import DatasetAdapters


class DatasetService:
    """数据集服务门面（Facade）。

    所有具体操作委托给子模块，确保单一职责。
    """

    def __init__(
        self,
        loader: DatasetLoader | None = None,
        profiler: DatasetProfiler | None = None,
        docs: DatasetDocsGenerator | None = None,
        adapters: DatasetAdapters | None = None,
    ) -> None:
        self._loader = loader or DatasetLoader()
        self._profiler = profiler or DatasetProfiler(loader=self._loader)
        self._docs = docs or DatasetDocsGenerator(profiler=self._profiler)
        self._adapters = adapters or DatasetAdapters(
            loader=self._loader,
            profiler=self._profiler,
            docs=self._docs,
        )

    # ------------------------------------------------------------------
    # 元数据访问
    # ------------------------------------------------------------------

    @staticmethod
    def get_metadata(dataset_id: str) -> DatasetMetadata:
        """获取数据集静态元数据。"""
        return get_dataset(dataset_id)

    @staticmethod
    def list_datasets() -> list[dict[str, Any]]:
        """列出所有可用数据集。"""
        return list_datasets()

    # ------------------------------------------------------------------
    # 数据加载（委托给 DatasetLoader）
    # ------------------------------------------------------------------

    def get_data_path(self, dataset_id: str) -> Path:
        """获取数据集文件路径。"""
        return self._loader.get_data_path(dataset_id)

    def load(self, dataset_id: str, use_cache: bool = True, **kwargs) -> pd.DataFrame:
        """加载数据集为 DataFrame。"""
        return self._loader.load(dataset_id, use_cache=use_cache, **kwargs)

    # ------------------------------------------------------------------
    # Profile 管理（委托给 DatasetProfiler）
    # ------------------------------------------------------------------

    def generate_profile(self, dataset_id: str, df: pd.DataFrame | None = None,
                        include_sample: bool = False) -> DatasetProfile:
        """生成数据集 Profile。"""
        return self._profiler.generate_profile(dataset_id, df=df, include_sample=include_sample)

    def save_profile(self, dataset_id: str, profile: DatasetProfile) -> None:
        """保存 Profile 到缓存。"""
        self._profiler.save_profile(dataset_id, profile)

    def load_profile(self, dataset_id: str) -> DatasetProfile | None:
        """从缓存加载 Profile。"""
        return self._profiler.load_profile(dataset_id)

    def get_profile(self, dataset_id: str, refresh: bool = False) -> DatasetProfile:
        """获取数据集 Profile，优先使用缓存。"""
        return self._profiler.get_profile(dataset_id, refresh=refresh)

    def refresh_all_profiles(self) -> dict[str, DatasetProfile]:
        """刷新所有数据集的 Profile 缓存。"""
        return self._profiler.refresh_all_profiles()

    # ------------------------------------------------------------------
    # 综合信息
    # ------------------------------------------------------------------

    def get_full_info(self, dataset_id: str) -> dict[str, Any]:
        """获取数据集的完整信息（元数据 + Profile）。"""
        return self._docs._get_full_info(dataset_id)

    # ------------------------------------------------------------------
    # README 生成（委托给 DatasetDocsGenerator，仅安全方法）
    # ------------------------------------------------------------------

    def generate_readme_section(self, dataset_id: str,
                                include_field_details: bool = True) -> str:
        """生成单个数据集的 README 文档片段。

        注意：不提供全量生成方法，使用 update_readme_markdown_block 安全更新。
        """
        return self._docs.generate_readme_section(dataset_id, include_field_details=include_field_details)

    def update_readme_markdown_block(self, readme_path: str | Path) -> bool:
        """安全更新 README 文件中的标记区块。

        只替换 `<!-- DATASET_INFO_START -->` 和 `<!-- DATASET_INFO_END -->` 之间的内容。
        """
        return self._docs.update_readme_markdown_block(readme_path)

    # ------------------------------------------------------------------
    # Notebook 辅助（委托给 DatasetAdapters）
    # ------------------------------------------------------------------

    def notebook_init(self, dataset_id: str, **kwargs) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Notebook 一键初始化：加载数据集并返回完整信息。"""
        return self._adapters.notebook_init(dataset_id, **kwargs)

    # ------------------------------------------------------------------
    # Dash/Plotly 辅助（委托给 DatasetAdapters）
    # ------------------------------------------------------------------

    def get_dash_table_columns(self, dataset_id: str) -> list[dict[str, str]]:
        """获取 Dash DataTable 可用的列定义。"""
        return self._adapters.get_dash_table_columns(dataset_id)

    def get_dash_filter_options(self, dataset_id: str, field_name: str) -> list[dict[str, str]]:
        """获取 Dash 筛选器的选项列表。"""
        return self._adapters.get_dash_filter_options(dataset_id, field_name)

    def get_plotly_labels(self, dataset_id: str) -> dict[str, str]:
        """获取 Plotly 可用的 labels 字典。"""
        return self._adapters.get_plotly_labels(dataset_id)


# ---------------------------------------------------------------------------
# 便捷函数
# ---------------------------------------------------------------------------

_DEFAULT_SERVICE: DatasetService | None = None


def get_service() -> DatasetService:
    """获取全局单例 DatasetService。"""
    global _DEFAULT_SERVICE
    if _DEFAULT_SERVICE is None:
        _DEFAULT_SERVICE = DatasetService()
    return _DEFAULT_SERVICE


def load_dataset(dataset_id: str, **kwargs) -> pd.DataFrame:
    """便捷函数：加载数据集。"""
    return get_service().load(dataset_id, **kwargs)


def get_dataset_profile(dataset_id: str) -> DatasetProfile:
    """便捷函数：获取数据集 Profile。"""
    return get_service().get_profile(dataset_id)


def get_dataset_full_info(dataset_id: str) -> dict[str, Any]:
    """便捷函数：获取数据集完整信息。"""
    return get_service().get_full_info(dataset_id)


__all__ = [
    "DatasetProfile",
    "DatasetService",
    "get_service",
    "load_dataset",
    "get_dataset_profile",
    "get_dataset_full_info",
]
