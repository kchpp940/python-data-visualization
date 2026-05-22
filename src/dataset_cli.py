"""数据集元数据 CLI 工具。

提供命令行接口来：
1. 列出所有数据集
2. 刷新 Profile 缓存
3. 查看数据集详情
4. 安全更新 README 标记区块

**安全原则**：readme 命令只允许替换 `<!-- DATASET_INFO_START -->` 与 `<!-- DATASET_INFO_END -->`
之间的内容，不支持全量生成或覆盖。

使用方式::

    python -m src.dataset_cli list
    python -m src.dataset_cli readme --file README.md
    python -m src.dataset_cli refresh
    python -m src.dataset_cli info epa_fuel_economy_summary
"""

from __future__ import annotations

import argparse
import sys

from src.dataset_service import get_service
from src.dataset_docs import DatasetDocsGenerator


def cmd_list() -> None:
    """列出所有数据集。"""
    service = get_service()
    datasets = service.list_datasets()

    print("\n可用数据集:")
    print("-" * 80)
    for ds in datasets:
        print(f"  {ds['id']:30s} {ds['name']}")
    print()


def cmd_readme(file: str, show_preview: bool = False) -> None:
    """安全更新 README 文件中的标记区块。

    只替换 `<!-- DATASET_INFO_START -->` 和 `<!-- DATASET_INFO_END -->` 之间的内容。
    """
    docs = DatasetDocsGenerator()

    if show_preview:
        content = docs.generate_markdown_block()
        print(content)
        return

    try:
        docs.update_readme_markdown_block(file)
        print(f"✅ README 标记区块已更新: {file}")
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


def cmd_refresh() -> None:
    """刷新所有 Profile 缓存。"""
    service = get_service()
    results = service.refresh_all_profiles()

    print("\n已刷新 Profile 缓存:")
    print("-" * 80)
    for dataset_id, profile in results.items():
        print(f"  {dataset_id:30s} {profile.row_count:>8,} 行, {profile.column_count} 列")
    print()


def cmd_info(dataset_id: str) -> None:
    """查看数据集详细信息。"""
    service = get_service()
    info = service.get_full_info(dataset_id)

    print(f"\n数据集: {info['name']}")
    print(f"ID: {info['id']}")
    print(f"描述: {info['description']}")
    print(f"来源: {info['source']}")
    print(f"文件: {info['file_name']} ({info['file_type']})")
    print(f"行数: {info['row_count']:,}")
    print(f"列数: {info['column_count']}")
    print(f"标签: {', '.join(info['tags'])}")
    print(f"\n字段详情:")
    print("-" * 100)
    print(f"  {'字段名':20s} {'类型':6s} {'单位':8s} {'分类':12s} {'缺失值':12s} 说明")
    print("-" * 100)
    for field in info['fields']:
        unit = field.get('unit') or '-'
        category = field.get('category') or '-'
        missing = field['missing_count']
        missing_str = f"{missing} ({field['missing_percent']}%)" if missing > 0 else "0"
        print(f"  {field['name']:20s} {field['dtype']:6s} {unit:8s} {category:12s} {missing_str:12s} {field['description']}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="数据集元数据管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m src.dataset_cli list                  列出所有数据集
  python -m src.dataset_cli info <dataset_id>     查看数据集详情
  python -m src.dataset_cli readme --file README.md  安全更新 README 标记区块
  python -m src.dataset_cli readme --preview      预览 README 区块内容（不写入）
  python -m src.dataset_cli refresh               刷新 Profile 缓存
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # list 命令
    subparsers.add_parser("list", help="列出所有数据集")

    # readme 命令（安全模式）
    readme_parser = subparsers.add_parser(
        "readme",
        help="安全更新 README 标记区块（仅替换标记之间的内容）",
    )
    readme_parser.add_argument(
        "--file", "-f",
        default="README.md",
        help="README 文件路径（默认: README.md）",
    )
    readme_parser.add_argument(
        "--preview",
        action="store_true",
        help="预览生成的内容但不写入文件",
    )

    # refresh 命令
    subparsers.add_parser("refresh", help="刷新所有 Profile 缓存")

    # info 命令
    info_parser = subparsers.add_parser("info", help="查看数据集详情")
    info_parser.add_argument("dataset_id", help="数据集 ID")

    args = parser.parse_args()

    if args.command == "list":
        cmd_list()
    elif args.command == "readme":
        cmd_readme(args.file, args.preview)
    elif args.command == "refresh":
        cmd_refresh()
    elif args.command == "info":
        cmd_info(args.dataset_id)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
