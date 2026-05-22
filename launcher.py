"""Unified launcher for python-data-visualization.

Commands
--------
``python launcher.py list``
    Print every example from ``examples_manifest.json``.

``python launcher.py check [<id>]``
    Run :func:`env_check.check_environment` and render the report.

``python launcher.py run <id>``
    Run check first; only launch if no problems are found.

``python launcher.py``
    Interactive menu — prompts the user to pick an example id.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path

from env_check import (
    EnvReport,
    check_environment,
    load_manifest,
    load_schema,
    render_report,
)

REPO_ROOT = Path(__file__).resolve().parent


def _render_usage() -> str:
    return (
        "用法:\n"
        "  python launcher.py                  # 交互式选择\n"
        "  python launcher.py list             # 列出所有示例\n"
        "  python launcher.py check [<id>]     # 检查环境\n"
        "  python launcher.py run <id>         # 启动指定示例\n"
    )


def cmd_list() -> int:
    manifest = load_manifest()
    if not manifest:
        print("examples_manifest.json 为空或不存在。")
        return 1
    for eid, info in manifest.items():
        print(f"  {eid:<15} [{info.get('type','?')}]  {info.get('title','')}")
        print(f"                 {info.get('desc','')}")
    return 0


def cmd_check(example_id: str | None) -> int:
    report = check_environment(example_id)
    print(render_report(report))
    return 0 if report.ok else 1


def _pick_args(example: dict, schema: dict, python: str) -> tuple[list[str], Path] | None:
    ex_type = example.get("type")
    rule = schema.get(ex_type) if ex_type else None
    if not rule:
        return None

    cwd_rel = rule.get("cwd", ".")
    cwd = (REPO_ROOT / cwd_rel).resolve()
    file_name = example.get("file", "")

    def _format(args_template: list[str]) -> list[str]:
        return [
            (a.format(python=python, file=file_name) if isinstance(a, str) else a)
            for a in args_template
        ]

    primary_cmd = rule.get("command", "{python}").format(python=python)
    primary_args = _format(rule.get("args_template", []))

    return [primary_cmd, *primary_args], cwd


def _can_run_type(example: dict, schema: dict) -> tuple[bool, str]:
    ex_type = example.get("type")
    rule = schema.get(ex_type) if ex_type else None
    if not rule:
        return False, f"launch_schema.json 中缺少类型 '{ex_type}' 的启动规则"

    check_pkg = rule.get("check_package", "")
    if check_pkg:
        from env_check import installed_version

        if installed_version(check_pkg) is None:
            for fb in rule.get("fallbacks", []) or []:
                fb_pkg = fb.get("check_package", "")
                if fb_pkg and installed_version(fb_pkg) is not None:
                    return True, ""
            return False, f"缺少 '{check_pkg}' 启动器（pip install {check_pkg}）"
    return True, ""


def cmd_run(example_id: str) -> int:
    manifest = load_manifest()
    schema = load_schema()
    example = manifest.get(example_id)
    if not example:
        print(f"未知示例 id: {example_id}")
        print("运行 `python launcher.py list` 查看所有可用示例。")
        return 2

    report = check_environment(example_id)
    if not report.ok:
        print(render_report(report))

        # Extra, in-your-face "what should I do next?" summary when consistency
        # issues are blocking — render_report already shows details, but we
        # collapse unique fix_steps here so the user can copy-paste one block.
        if report.consistency_issues:
            seen: set[str] = set()
            print("")
            print("=" * 72)
            print("清单未同步 —— 统一修复步骤（去重后）")
            print("=" * 72)
            for ci in report.consistency_issues:
                if ci.fix_steps and ci.fix_steps not in seen:
                    seen.add(ci.fix_steps)
                    print(f"# 影响文件: {ci.target_file}  ({ci.package})")
                    print(ci.fix_steps)
                    print("")

        print("")
        print("检查未通过，已取消启动。请按上面的步骤修复后重试。")
        return 1

    ready, reason = _can_run_type(example, schema)
    if not ready:
        print(f"无法启动 '{example_id}': {reason}")
        return 1

    picked = _pick_args(example, schema, sys.executable)
    if picked is None:
        print("启动规则不完整。")
        return 1
    argv, cwd = picked

    print(f"执行: {' '.join(shlex.quote(a) for a in argv)}")
    print(f"工作目录: {cwd}")
    print("-" * 72)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    result = subprocess.run(argv, cwd=str(cwd), env=env)
    return result.returncode


def cmd_interactive() -> int:
    manifest = load_manifest()
    if not manifest:
        print("examples_manifest.json 为空或不存在。")
        return 1
    print("可用示例:")
    for eid, info in manifest.items():
        print(f"  {eid:<15} [{info.get('type','?')}]  {info.get('title','')}")
    print("")
    try:
        choice = input("请输入示例 id 运行，留空退出: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("")
        return 0
    if not choice:
        return 0
    if choice not in manifest:
        print(f"未知 id: {choice}")
        return 2
    return cmd_run(choice)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    if not argv:
        return cmd_interactive()

    verb = argv[0]
    rest = argv[1:]

    if verb == "list":
        return cmd_list()
    if verb == "check":
        return cmd_check(rest[0] if rest else None)
    if verb == "run":
        if not rest:
            print("错误: `run` 需要指定示例 id。")
            print(_render_usage())
            return 2
        return cmd_run(rest[0])
    if verb in ("-h", "--help", "help"):
        print(_render_usage())
        return 0

    print(f"未知命令: {verb}")
    print(_render_usage())
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
