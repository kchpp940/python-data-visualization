"""统一的数据集元数据定义。

集中管理所有数据集的静态字段说明、业务含义、显示名称和使用场景，
避免在文档、页面和代码中各自维护。

使用方式::

    from src.dataset_metadata import DATASETS, get_dataset, get_field_label

    epa_meta = get_dataset("epa_fuel_economy_summary")
    label = get_field_label("epa_fuel_economy_summary", "fuelCost08")

数据集中的字段说明可以用于：
- README 文档自动生成
- Dash/Streamlit 页面标签和 tooltip
- Notebook 数据探索辅助
- Plotly/Altair 图表 labels 参数
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FieldMetadata:
    """单个字段的元数据定义。"""

    name: str
    label: str
    description: str
    dtype: str
    unit: str | None = None
    category: str | None = None


@dataclass(frozen=True)
class DatasetMetadata:
    """数据集的完整元数据定义。"""

    id: str
    name: str
    description: str
    source: str
    file_name: str
    file_type: str
    fields: list[FieldMetadata]
    default_display_fields: list[str] = field(default_factory=list)
    metric_fields: list[str] = field(default_factory=list)
    filter_fields: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def get_field(self, field_name: str) -> FieldMetadata | None:
        """根据字段名获取字段元数据。"""
        for f in self.fields:
            if f.name == field_name:
                return f
        return None

    def get_field_label(self, field_name: str) -> str:
        """获取字段的显示标签，找不到则返回原始字段名。"""
        f = self.get_field(field_name)
        return f.label if f else field_name

    def get_labels_dict(self) -> dict[str, str]:
        """获取 Plotly/Altair 可用的 labels 字典。"""
        return {f.name: f.label for f in self.fields}

    def get_metric_cols(self) -> dict[str, str]:
        """获取指标字段的中英文字典（兼容旧代码）。"""
        return {f.name: f.label for f in self.fields if f.name in self.metric_fields}


def _field(name: str, label: str, description: str, dtype: str,
          unit: str | None = None, category: str | None = None) -> FieldMetadata:
    """辅助函数，简化 FieldMetadata 创建。"""
    return FieldMetadata(
        name=name,
        label=label,
        description=description,
        dtype=dtype,
        unit=unit,
        category=category,
    )


DATASETS: dict[str, DatasetMetadata] = {
    "epa_fuel_economy_summary": DatasetMetadata(
        id="epa_fuel_economy_summary",
        name="EPA 燃油经济性数据集（摘要版）",
        description="美国环保署发布的车辆燃油经济性测试数据摘要，包含各车型的油耗、排放、成本等指标。",
        source="https://www.fueleconomy.gov/",
        file_name="EPA_fuel_economy_summary.csv",
        file_type="csv",
        tags=["燃油经济", "汽车", "环境"],
        default_display_fields=[
            "make", "model", "year", "transmission", "drive",
            "class_summary", "cylinders", "displ", "fuelCost08",
        ],
        metric_fields=["city08", "highway08", "fuelCost08", "co2"],
        filter_fields=["year", "transmission", "make", "class_summary"],
        fields=[
            _field("make", "品牌", "车辆制造商", "str", category="基本信息"),
            _field("model", "型号", "车型名称", "str", category="基本信息"),
            _field("year", "年份", "生产年份", "int", category="基本信息"),
            _field("transmission", "变速箱", "变速器类型", "str", category="车辆参数"),
            _field("drive", "驱动方式", "驱动轮配置（前驱/后驱/四驱）", "str", category="车辆参数"),
            _field("date_range", "日期范围", "数据覆盖的时间范围", "str", category="元信息"),
            _field("fuel_type_summary", "燃料类型", "使用的燃料类型摘要", "str", category="车辆参数"),
            _field("class_summary", "车型分类", "EPA 车型分类摘要", "str", category="分类信息"),
            _field("cylinders", "气缸数", "发动机气缸数量", "int", category="发动机参数"),
            _field("displ", "排量", "发动机排量（升）", "float", unit="L", category="发动机参数"),
            _field("co2", "CO2 排放", "二氧化碳排放量", "float", unit="g/mi", category="排放指标"),
            _field("barrels08", "年耗油量", "年度燃油消耗（桶）", "float", unit="桶/年", category="油耗指标"),
            _field("fuelCost08", "年燃油成本", "年度预计燃油成本", "float", unit="$", category="成本指标"),
            _field("highway08", "高速油耗", "高速工况燃油经济性", "int", unit="MPG", category="油耗指标"),
            _field("city08", "城市油耗", "城市工况燃油经济性", "int", unit="MPG", category="油耗指标"),
            _field("comb08", "综合油耗", "综合工况燃油经济性", "int", unit="MPG", category="油耗指标"),
        ],
    ),
    "epa_fuel_economy": DatasetMetadata(
        id="epa_fuel_economy",
        name="EPA 燃油经济性数据集（完整版）",
        description="美国环保署发布的完整车辆燃油经济性测试数据，包含更详细的传动系统和燃油类型信息。",
        source="https://www.fueleconomy.gov/",
        file_name="EPA_fuel_economy.csv",
        file_type="csv",
        tags=["燃油经济", "汽车", "环境", "原始数据"],
        default_display_fields=[
            "make", "model", "year", "trany", "VClass",
            "cylinders", "displ", "fuelCost08",
        ],
        metric_fields=["city08", "highway08", "fuelCost08", "co2"],
        filter_fields=["year", "fuelType", "make"],
        fields=[
            _field("make", "品牌", "车辆制造商", "str", category="基本信息"),
            _field("model", "型号", "车型名称", "str", category="基本信息"),
            _field("year", "年份", "生产年份", "int", category="基本信息"),
            _field("cylinders", "气缸数", "发动机气缸数量", "int", category="发动机参数"),
            _field("trany", "变速箱", "变速器类型（原始字段名）", "str", category="车辆参数"),
            _field("displ", "排量", "发动机排量（升）", "float", unit="L", category="发动机参数"),
            _field("VClass", "车型分类", "EPA 车型分类", "str", category="分类信息"),
            _field("co2", "CO2 排放", "二氧化碳排放量", "float", unit="g/mi", category="排放指标"),
            _field("barrels08", "年耗油量", "年度燃油消耗（桶）", "float", unit="桶/年", category="油耗指标"),
            _field("fuelCost08", "年燃油成本", "年度预计燃油成本", "float", unit="$", category="成本指标"),
            _field("fuelType", "燃料类型", "使用的燃料类型", "str", category="车辆参数"),
            _field("highway08", "高速油耗", "高速工况燃油经济性", "int", unit="MPG", category="油耗指标"),
            _field("city08", "城市油耗", "城市工况燃油经济性", "int", unit="MPG", category="油耗指标"),
            _field("comb08", "综合油耗", "综合工况燃油经济性", "int", unit="MPG", category="油耗指标"),
        ],
    ),
    "amazon_books": DatasetMetadata(
        id="amazon_books",
        name="Amazon 畅销书排行榜",
        description="Amazon 图书畅销榜数据，包含书名、作者、评分、评论数、价格、年份和 genre 分类。",
        source="Kaggle - Amazon Top 50 Bestselling Books",
        file_name="AmazonBooks.xlsx",
        file_type="xlsx",
        tags=["图书", "电商", "评分"],
        default_display_fields=[
            "Name", "Author", "User Rating", "Reviews", "Price", "Year", "Genre",
        ],
        metric_fields=["User Rating", "Reviews", "Price"],
        filter_fields=["Year", "Genre", "Author"],
        fields=[
            _field("Name", "书名", "图书名称", "str", category="基本信息"),
            _field("Author", "作者", "图书作者", "str", category="基本信息"),
            _field("User Rating", "用户评分", "Amazon 用户平均评分", "float", unit="星", category="评分指标"),
            _field("Reviews", "评论数", "用户评论数量", "int", category="热度指标"),
            _field("Price", "价格", "图书售价", "float", unit="$", category="价格指标"),
            _field("Year", "年份", "上榜年份", "int", category="时间信息"),
            _field("Genre", "分类", "图书类别（小说/非小说）", "str", category="分类信息"),
        ],
    ),
}


def get_dataset(dataset_id: str) -> DatasetMetadata:
    """根据 ID 获取数据集元数据。

    Raises
    ------
    KeyError
        如果指定的数据集不存在。
    """
    if dataset_id not in DATASETS:
        raise KeyError(
            f"未知数据集: {dataset_id}. "
            f"可用数据集: {sorted(DATASETS.keys())}"
        )
    return DATASETS[dataset_id]


def get_field_label(dataset_id: str, field_name: str) -> str:
    """快捷函数：获取指定数据集指定字段的显示标签。"""
    return get_dataset(dataset_id).get_field_label(field_name)


def get_labels_dict(dataset_id: str) -> dict[str, str]:
    """快捷函数：获取指定数据集的 labels 字典，用于 Plotly/Altair。"""
    return get_dataset(dataset_id).get_labels_dict()


def list_datasets() -> list[dict[str, Any]]:
    """列出所有可用数据集的摘要信息。"""
    return [
        {
            "id": ds.id,
            "name": ds.name,
            "description": ds.description,
            "tags": ds.tags,
            "row_count": ds.fields,  # placeholder, will be filled by service
        }
        for ds in DATASETS.values()
    ]


__all__ = [
    "FieldMetadata",
    "DatasetMetadata",
    "DATASETS",
    "get_dataset",
    "get_field_label",
    "get_labels_dict",
    "list_datasets",
]
