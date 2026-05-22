"""Dash 数据集信息页面组件。

提供可复用的 Dash 布局组件，用于展示数据集的完整元数据信息。
可嵌入任何 Dash 应用中，无需重复维护数据集描述。

使用方式::

    from src.dataset_info_page import create_dataset_info_layout

    app.layout = html.Div([
        create_dataset_info_layout("epa_fuel_economy_summary"),
        # ... 其他组件
    ])
"""

from __future__ import annotations

from typing import Any

from dash import html, dash_table

from src.dataset_service import get_service
from src.dataset_metadata import DATASETS


def _create_info_card(title: str, value: str, subtitle: str | None = None) -> html.Div:
    """创建信息卡片组件。"""
    children = [
        html.H4(title, style={"margin": "0", "fontSize": "12px", "color": "#666"}),
        html.P(value, style={"margin": "4px 0", "fontSize": "20px", "fontWeight": "bold"}),
    ]
    if subtitle:
        children.append(html.P(subtitle, style={"margin": "0", "fontSize": "11px", "color": "#999"}))

    return html.Div(
        children,
        style={
            "padding": "12px",
            "border": "1px solid #e0e0e0",
            "borderRadius": "6px",
            "backgroundColor": "#fafafa",
        },
    )


def _create_field_table(fields: list[dict[str, Any]], dataset_id: str) -> dash_table.DataTable:
    """创建字段说明表格。"""
    columns = [
        {"name": "字段名", "id": "name"},
        {"name": "显示名称", "id": "label"},
        {"name": "类型", "id": "dtype"},
        {"name": "单位", "id": "unit"},
        {"name": "分类", "id": "category"},
        {"name": "说明", "id": "description"},
        {"name": "缺失值", "id": "missing_str"},
    ]

    data = []
    for field in fields:
        missing = field.get("missing_count", 0)
        missing_str = f"{missing} ({field.get('missing_percent', 0)}%)" if missing > 0 else "0"
        data.append({
            "name": field["name"],
            "label": field["label"],
            "dtype": field["dtype"],
            "unit": field.get("unit") or "-",
            "category": field.get("category") or "-",
            "description": field["description"],
            "missing_str": missing_str,
        })

    return dash_table.DataTable(
        id=f"dataset-fields-{dataset_id}",
        columns=columns,
        data=data,
        page_size=15,
        style_cell={
            "textAlign": "left",
            "padding": "8px 12px",
            "whiteSpace": "normal",
            "height": "auto",
        },
        style_header={
            "backgroundColor": "#f0f0f0",
            "fontWeight": "bold",
        },
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#fafafa",
            }
        ],
    )


def create_dataset_info_layout(
    dataset_id: str,
    show_field_details: bool = True,
    title: str | None = None,
) -> html.Div:
    """创建数据集信息页面的完整布局。

    Parameters
    ----------
    dataset_id: 数据集 ID
    show_field_details: 是否显示字段详情表格
    title: 自定义标题，默认使用数据集名称

    Returns
    -------
    html.Div
        可直接嵌入 Dash 应用的布局组件
    """
    service = get_service()
    info = service.get_full_info(dataset_id)

    display_title = title or info["name"]

    # 概览卡片
    overview_cards = html.Div(
        [
            _create_info_card("行数", f"{info['row_count']:,}"),
            _create_info_card("列数", str(info["column_count"])),
            _create_info_card("文件", info["file_name"]),
            _create_info_card("标签", ", ".join(info["tags"])),
        ],
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(4, 1fr)",
            "gap": "12px",
            "marginBottom": "20px",
        },
    )

    # 描述区域
    description_section = html.Div([
        html.H3("数据集描述", style={"marginTop": "20px"}),
        html.P(info["description"], style={"lineHeight": "1.6"}),
        html.P(
            [html.Strong("来源: "), html.A(info["source"], href=info["source"], target="_blank")],
            style={"marginTop": "8px"},
        ),
    ])

    # 指标字段
    metric_fields_section = None
    if info.get("metric_fields"):
        metric_items = []
        for mf in info["metric_fields"]:
            field_meta = next((f for f in info["fields"] if f["name"] == mf), None)
            if field_meta:
                metric_items.append(
                    html.Li([
                        html.Strong(field_meta["label"]),
                        f" ({mf})",
                        html.Span(
                            f" - {field_meta['description']}",
                            style={"color": "#666"},
                        ),
                    ])
                )
        metric_fields_section = html.Div([
            html.H3("关键指标", style={"marginTop": "20px"}),
            html.Ul(metric_items),
        ])

    # 筛选字段
    filter_fields_section = None
    if info.get("filter_fields"):
        filter_items = []
        for ff in info["filter_fields"]:
            field_meta = next((f for f in info["fields"] if f["name"] == ff), None)
            label = field_meta["label"] if field_meta else ff
            filter_items.append(html.Li(f"{label} ({ff})"))

        filter_fields_section = html.Div([
            html.H3("常用筛选字段", style={"marginTop": "20px"}),
            html.Ul(filter_items),
        ])

    # 字段详情表格
    field_table_section = None
    if show_field_details:
        field_table_section = html.Div([
            html.H3("字段详情", style={"marginTop": "20px"}),
            _create_field_table(info["fields"], dataset_id),
        ])

    # 组合所有部分
    children = [
        html.H2(display_title, style={"marginBottom": "16px"}),
        overview_cards,
        description_section,
    ]

    if metric_fields_section:
        children.append(metric_fields_section)
    if filter_fields_section:
        children.append(filter_fields_section)
    if field_table_section:
        children.append(field_table_section)

    return html.Div(
        children,
        style={
            "padding": "20px",
            "backgroundColor": "#ffffff",
            "borderRadius": "8px",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.1)",
        },
    )


def create_all_datasets_summary_layout() -> html.Div:
    """创建所有数据集的摘要页面布局。

    Returns
    -------
    html.Div
        展示所有数据集概览的布局组件
    """
    service = get_service()

    cards = []
    for dataset_id in sorted(DATASETS.keys()):
        info = service.get_full_info(dataset_id)
        card = html.Div(
            [
                html.H4(info["name"], style={"margin": "0 0 8px 0"}),
                html.P(info["description"], style={
                    "margin": "0 0 12px 0",
                    "fontSize": "13px",
                    "color": "#666",
                    "lineHeight": "1.5",
                }),
                html.Div(
                    [
                        html.Span(f"📊 {info['row_count']:,} 行", style={"marginRight": "16px"}),
                        html.Span(f"📋 {info['column_count']} 列", style={"marginRight": "16px"}),
                        html.Span(f"📁 {info['file_name']}"),
                    ],
                    style={"fontSize": "12px", "color": "#888"},
                ),
            ],
            style={
                "padding": "16px",
                "border": "1px solid #e0e0e0",
                "borderRadius": "8px",
                "backgroundColor": "#fafafa",
            },
        )
        cards.append(card)

    return html.Div(
        [
            html.H2("数据集总览", style={"marginBottom": "20px"}),
            html.Div(
                cards,
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(auto-fill, minmax(350px, 1fr))",
                    "gap": "16px",
                },
            ),
        ],
        style={"padding": "20px"},
    )


__all__ = [
    "create_dataset_info_layout",
    "create_all_datasets_summary_layout",
]
