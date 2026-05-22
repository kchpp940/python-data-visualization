"""数据集 Profile 生成与缓存。

负责生成数据集的运行时 Profile（行数、列数、缺失值等），并管理磁盘缓存。

使用方式::

    from src.dataset_profile import DatasetProfiler

    profiler = DatasetProfiler()
    profile = profiler.get_profile("epa_fuel_economy_summary")
    print(f"行数: {profile.row_count}, 缺失值: {profile.missing_values}")
"""

from __future__ import annotations

import json
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from data_paths import REPO_ROOT
from src.dataset_metadata import DATASETS, get_dataset
from src.dataset_loader import DatasetLoader


METADATA_CACHE_DIR = REPO_ROOT / ".metadata_cache"


@dataclass
class DatasetProfile:
    """数据集运行时 Profile。"""

    mtime: float
    row_count: int
    column_count: int
    missing_values: dict[str, int]
    sample_data: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DatasetProfiler:
    """数据集 Profile 生成器与缓存管理器。"""

    def __init__(self, cache_dir: Path | None = None, loader: DatasetLoader | None = None) -> None:
        self.cache_dir = cache_dir or METADATA_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._loader = loader or DatasetLoader()
        self._profile_cache: dict[str, DatasetProfile] = {}

    def _get_cache_path(self, dataset_id: str) -> Path:
        return self.cache_dir / f"{dataset_id}.json"

    def _cache_is_fresh(self, dataset_id: str, data_path: Path) -> bool:
        cache_path = self._get_cache_path(dataset_id)
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                return cached.get("mtime") == data_path.stat().st_mtime
            except (json.JSONDecodeError, KeyError):
                pass
        return False

    def generate_profile(self, dataset_id: str, df: pd.DataFrame | None = None,
                        include_sample: bool = False) -> DatasetProfile:
        """生成数据集 Profile。

        Parameters
        ----------
        dataset_id: 数据集 ID
        df: 可选的 DataFrame（如果已加载）
        include_sample: 是否包含样本数据（默认 False，避免缓存过大）
        """
        if df is None:
            df = self._loader.load(dataset_id, use_cache=True)

        data_path = self._loader.get_data_path(dataset_id)

        return DatasetProfile(
            mtime=data_path.stat().st_mtime,
            row_count=len(df),
            column_count=len(df.columns),
            missing_values=df.isnull().sum().to_dict(),
            sample_data=df.head(5).to_dict("records") if include_sample else [],
        )

    def save_profile(self, dataset_id: str, profile: DatasetProfile) -> None:
        """保存 Profile 到缓存。"""
        cache_path = self._get_cache_path(dataset_id)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2)

    def load_profile(self, dataset_id: str) -> DatasetProfile | None:
        """从缓存加载 Profile。"""
        cache_path = self._get_cache_path(dataset_id)
        if not cache_path.exists():
            return None
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return DatasetProfile(**data)
        except (json.JSONDecodeError, TypeError, KeyError):
            warnings.warn(f"Profile 缓存损坏，将重新生成: {cache_path}")
            return None

    def get_profile(self, dataset_id: str, refresh: bool = False) -> DatasetProfile:
        """获取数据集 Profile，优先使用缓存。

        Parameters
        ----------
        dataset_id: 数据集 ID
        refresh: 是否强制刷新缓存
        """
        data_path = self._loader.get_data_path(dataset_id)

        if not refresh and dataset_id in self._profile_cache:
            return self._profile_cache[dataset_id]

        if not refresh and self._cache_is_fresh(dataset_id, data_path):
            profile = self.load_profile(dataset_id)
            if profile:
                self._profile_cache[dataset_id] = profile
                return profile

        profile = self.generate_profile(dataset_id)
        self.save_profile(dataset_id, profile)
        self._profile_cache[dataset_id] = profile
        return profile

    def refresh_all_profiles(self) -> dict[str, DatasetProfile]:
        """刷新所有数据集的 Profile 缓存。"""
        results = {}
        for dataset_id in DATASETS.keys():
            try:
                results[dataset_id] = self.get_profile(dataset_id, refresh=True)
            except Exception as e:
                warnings.warn(f"刷新 {dataset_id} Profile 失败: {e}")
        return results


__all__ = ["DatasetProfile", "DatasetProfiler"]
