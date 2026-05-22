"""文档生成模块 - 仅支持 README 标记区块替换。

安全原则：
- 只允许替换 `<!-- DATASET_INFO_START -->` 和 `<!-- DATASET_INFO_END -->` 之间的内容
- 不允许全量生成或覆盖整个文件
- 不提供 `generate_full_readme` 等危险方法

使用方式::

    from src.dataset_docs import DatasetDocsGenerator

    docs = DatasetDocsGenerator()
    docs.update_readme_markdown_block("README.md")  # 原地替换标记区块
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from src.dataset_metadata import DATASETS, get_dataset
from src.dataset_profile import DatasetProfiler


DATASET_MARKER_START = "<!-- DATASET_INFO_START -->"
DATASET_MARKER_END = "<!-- DATASET_INFO_END -->"


class DatasetDocsGenerator:
    """文档生成器 - 仅支持标记区块替换。"""

    def __init__(self, profiler: DatasetProfiler | None = None) -> None:
        self._profiler = profiler or DatasetProfiler()

    def _get_full_info(self, dataset_id: str) -> dict[str, Any]:
        """获取数据集的完整信息（元数据 + Profile）。"""
        meta = get_dataset(dataset_id)
        profile = self._profiler.get_profile(dataset_id)

        field_info = []
        for field in meta.fields:
            missing = profile.missing_values.get(field.name, 0)
            field_info.append({
                **asdict(field),
                "missing_count": missing,
                "missing_percent": round(missing / profile.row_count * 100, 2) if profile.row_count > 0 else 0,
            })

        return {
            "id": meta.id,
            "name": meta.name,
            "description": meta.description,
            "source": meta.source,
            "file_name": meta.file_name,
            "file_type": meta.file_type,
            "tags": meta.tags,
            "row_count": profile.row_count,
            "column_count": profile.column_count,
            "fields": field_info,
            "default_display_fields": meta.default_display_fields,
            "metric_fields": meta.metric_fields,
            "filter_fields": meta.filter_fields,
        }

    def generate_readme_section(self, dataset_id: str,
                                include_field_details: bool = True) -> str:
        """生成单个数据集的 README 文档片段。

        输出格式为 Markdown，可直接插入 README.md。
        """
        info = self._get_full_info(dataset_id)

        lines = []

        lines.append(f"### {info['name']}")
        lines.append("")
        lines.append(f"- **来源**: {info['source']}")
        lines.append(f"- **文件**: `{info['file_name']}`")
        lines.append(f"- **行数**: {info['row_count']:,}")
        lines.append(f"- **列数**: {info['column_count']}")
        lines.append(f"- **标签**: {', '.join(info['tags'])}")
        lines.append("")
        lines.append(info["description"])
        lines.append("")

        if include_field_details and info["fields"]:
            lines.append("#### 字段说明")
            lines.append("")
            lines.append("| 字段名 | 显示名称 | 类型 | 单位 | 说明 | 缺失值 |")
            lines.append("|--------|----------|------|------|------|--------|")

            for field in info["fields"]:
                unit = field.get("unit") or "-"
                missing = field["missing_count"]
                missing_str = f"{missing} ({field['missing_percent']}%)" if missing > 0 else "0"
                lines.append(
                    f"| `{field['name']}` | {field['label']} | "
                    f"`{field['dtype']}` | {unit} | "
                    f"{field['description']} | {missing_str} |"
                )
            lines.append("")

        return "\n".join(lines)

    def generate_markdown_block(self) -> str:
        """生成完整的数据集说明 Markdown 区块内容（不包含标记）。

        用于填充到 README 的标记区块之间。
        """
        lines = ["## 数据集说明", "", "> 本区块由 DatasetDocsGenerator 自动生成，请勿手动编辑。", ""]
        for dataset_id in sorted(DATASETS.keys()):
            lines.append(self.generate_readme_section(dataset_id))
            lines.append("")
            lines.append("---")
            lines.append("")
        return "\n".join(lines)

    def update_readme_markdown_block(self, readme_path: str | Path) -> bool:
        """更新 README 文件中的标记区块。

        只替换 `<!-- DATASET_INFO_START -->` 和 `<!-- DATASET_INFO_END -->` 之间的内容。

        Parameters
        ----------
        readme_path: README 文件路径

        Returns
        -------
        bool: 是否成功更新

        Raises
        ------
        ValueError: 如果标记不存在
        """
        readme_path = Path(readme_path)
        if not readme_path.exists():
            raise FileNotFoundError(f"README 文件不存在: {readme_path}")

        existing = readme_path.read_text(encoding="utf-8")

        if DATASET_MARKER_START not in existing or DATASET_MARKER_END not in existing:
            raise ValueError(
                f"README 文件中未找到标记区块，请确保包含以下标记：\n"
                f"  {DATASET_MARKER_START}\n"
                f"  {DATASET_MARKER_END}"
            )

        content = self.generate_markdown_block()

        start_idx = existing.index(DATASET_MARKER_START)
        end_idx = existing.index(DATASET_MARKER_END) + len(DATASET_MARKER_END)
        new_content = (
            existing[:start_idx]
            + f"{DATASET_MARKER_START}\n{content}\n{DATASET_MARKER_END}"
            + existing[end_idx:]
        )

        readme_path.write_text(new_content, encoding="utf-8")
        return True


__all__ = [
    "DatasetDocsGenerator",
    "DATASET_MARKER_START",
    "DATASET_MARKER_END",
]
