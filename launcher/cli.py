"""Command-line entry point for the manifest-driven launcher.

Commands:

* ``python launcher.py list`` — 列出所有已注册示例
* ``python launcher.py check [id ...]`` — 检查环境（缺依赖 / 缺数据 / 缺脚本 / 缺启动器）
* ``python launcher.py run <id> [-- ...]`` — 启动指定示例
* ``python launcher.py`` — 交互式选择并启动

All behaviour is driven by ``examples_manifest.json`` and
``launch_schema.json`` — the CLI layer does not know about any specific
example or startup rule.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional, Sequence

from .checker import check_entries
from .manifest_loader import LaunchSchema, ManifestEntry, ManifestError, load_launch_schema, load_manifest
from .runner import NoLauncherAvailable, run_entry


def _type_label(entry_type: str) -> str:
    return {
        "dash": "Dash",
        "streamlit": "Streamlit",
        "notebook": "Notebook",
        "script": "Script",
    }.get(entry_type, entry_type)


def _print_list(entries: List[ManifestEntry]) -> None:
    width = max((len(e.example_id) for e in entries), default=0)
    for entry in entries:
        tag = _type_label(entry.type).ljust(10)
        print(f"  {entry.example_id.ljust(width)}  {tag}  {entry.title}")
        if entry.desc:
            print(f"  {' ' * width}            {entry.desc}")


def _print_check(results) -> int:
    exit_code = 0
    for example_id, result in sorted(results.items()):
        status = "✓ 就绪" if result.ok else "✗ 未就绪"
        print(f"[{result.entry.example_id}] {result.entry.title} — {status}")
        for line in result.summary_lines():
            print(line)
        if not result.ok:
            exit_code = 1
    return exit_code


def _interactive_pick(entries: List[ManifestEntry]) -> Optional[ManifestEntry]:
    print("可用示例：\n")
    for idx, entry in enumerate(entries, start=1):
        tag = _type_label(entry.type)
        print(f"  {idx:>2}. [{entry.example_id}] {tag:<10} {entry.title}")
    print()

    raw = input("请输入编号或示例 ID（留空退出）: ").strip()
    if not raw:
        return None

    if raw.isdigit():
        index = int(raw) - 1
        if 0 <= index < len(entries):
            return entries[index]
        print(f"⚠ 编号 {raw} 超出范围", file=sys.stderr)
        return None

    for entry in entries:
        if entry.example_id == raw:
            return entry
    print(f"⚠ 未找到示例 {raw!r}", file=sys.stderr)
    return None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="launcher.py",
        description="统一的示例启动入口（由 manifest + launch_schema 驱动）",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="列出所有可用示例")

    check_parser = subparsers.add_parser("check", help="检查环境就绪状态")
    check_parser.add_argument(
        "ids", nargs="*", help="示例 ID，留空则检查全部"
    )

    run_parser = subparsers.add_parser("run", help="启动指定示例")
    run_parser.add_argument("id", help="示例 ID")
    run_parser.add_argument(
        "extra",
        nargs=argparse.REMAINDER,
        help="透传给启动命令的额外参数（通常接在 -- 之后）",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        manifest = load_manifest()
        launch_schemas = load_launch_schema()
    except ManifestError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 3

    parser = _build_parser()
    args = parser.parse_args(argv)

    ordered_entries = [
        manifest[key]
        for key in sorted(
            manifest,
            key=lambda k: ({"dash": 0, "streamlit": 1, "notebook": 2, "script": 3}.get(manifest[k].type, 99), k),
        )
    ]

    command = args.command

    if command is None:
        entry = _interactive_pick(ordered_entries)
        if entry is None:
            return 0
        try:
            return run_entry(entry, launch_schemas)
        except NoLauncherAvailable as exc:
            print(f"错误：{exc}", file=sys.stderr)
            return 5

    if command == "list":
        _print_list(ordered_entries)
        return 0

    if command == "check":
        selected_ids: List[str] = list(args.ids or [])
        if selected_ids:
            unknown = [i for i in selected_ids if i not in manifest]
            if unknown:
                print(
                    "警告：以下 ID 在 manifest 中不存在: "
                    + ", ".join(unknown),
                    file=sys.stderr,
                )
            targets = [manifest[i] for i in selected_ids if i in manifest]
        else:
            targets = ordered_entries
        results = check_entries(targets, launch_schemas)
        return _print_check(results)

    if command == "run":
        if args.id not in manifest:
            print(
                f"错误：未知示例 ID {args.id!r}；运行 `python launcher.py list` 查看可用列表",
                file=sys.stderr,
            )
            return 4
        extra = list(args.extra or [])
        if extra and extra[0] == "--":
            extra = extra[1:]
        try:
            return run_entry(manifest[args.id], launch_schemas, extra_args=extra)
        except NoLauncherAvailable as exc:
            print(f"错误：{exc}", file=sys.stderr)
            return 5

    parser.print_help()
    return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
