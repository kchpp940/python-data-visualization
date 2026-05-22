"""README auto-generation and drift-detection for python-data-visualization.

This module owns everything related to README.md's auto-generated blocks:
- Rendering block content from ``examples_manifest.json`` / ``launch_schema.json``
- Replacing the ``<!-- BEGIN ... -->`` / ``<!-- END ... -->`` delimited regions
- Byte-for-byte comparison to detect drift

``launcher.py`` calls into this module; it should not contain any README rules
of its own.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants (shared between this module and launcher.py)
# ---------------------------------------------------------------------------

TYPE_LABELS: dict[str, str] = {
    "dash": "Dash",
    "streamlit": "Streamlit",
    "notebook": "Notebook",
    "static": "Static",
}

TYPE_ID_PREFIX: dict[str, str] = {
    "dash": "dash",
    "streamlit": "st",
    "notebook": "nb-chX-Y",
    "static": "static",
}

AUTO_BLOCKS: tuple[str, ...] = (
    "EXAMPLE_INVENTORY",
    "ADD_EXAMPLE_TEMPLATES",
    "FIELD_REFERENCE",
    "TYPE_LAUNCH_REFERENCE",
)


# ---------------------------------------------------------------------------
# Block rendering
# ---------------------------------------------------------------------------

def render_example_inventory(manifest: dict) -> str:
    """Render the full example inventory table."""
    lines = [
        "<!-- BEGIN EXAMPLE_INVENTORY -->",
        "### 示例清单（自动生成，勿手动编辑）",
        "",
        "下表由 `examples_manifest.json` 自动生成，运行 `python launcher.py generate-readme` 更新。",
        "",
        "| ID | 类型 | 标题 | 入口脚本 | 数据 | 依赖 |",
        "|----|------|------|----------|------|------|",
    ]
    for eid, meta in sorted(manifest.items()):
        stype = meta.get("type", "")
        title = meta.get("title", "")
        file = meta.get("file", "")
        data = ", ".join(meta.get("data_files", [])) or "—"
        deps = ", ".join(meta.get("deps", [])) or "—"
        lines.append(f"| `{eid}` | {TYPE_LABELS.get(stype, stype)} | {title} | `{file}` | {data} | {deps} |")
    lines.append("<!-- END EXAMPLE_INVENTORY -->")
    return "\n".join(lines)


def render_add_example_templates(manifest: dict, schema: dict) -> str:
    """Render minimal-config templates for every type in schema."""
    lines = [
        "<!-- BEGIN ADD_EXAMPLE_TEMPLATES -->",
        "### 新增示例（最小配置，自动生成）",
        "",
        "每种类型的最小配置如下（由 `launch_schema.json` 自动生成）：",
    ]
    for t, _tmeta in sorted(schema.items()):
        label = TYPE_LABELS.get(t, t)
        rep = next(((eid, m) for eid, m in manifest.items() if m.get("type") == t), None)
        if rep:
            _, rep_meta = rep
            sample_file = rep_meta.get("file", "your_file.py")
            sample_data = rep_meta.get("data_files", [])
            sample_deps = rep_meta.get("deps", [])
        else:
            sample_file = "your_file.py"
            sample_data = []
            sample_deps = []
        data_json = json.dumps(sample_data, ensure_ascii=False)
        deps_json = json.dumps(sample_deps, ensure_ascii=False)

        prefix = TYPE_ID_PREFIX.get(t, t[:2])
        sample_id = f"{prefix}" if prefix.endswith("X-Y") else f"{prefix}-your-id"
        lines.extend([
            "",
            f"**{label}** (`type: {t}`)",
            "",
            "```json",
            f'"{sample_id}": {{',
            f'  "type": "{t}",',
            f'  "file": "{sample_file}",',
            '  "title": "简短标题",',
            '  "desc": "一句话描述",',
            f'  "data_files": {data_json},',
            f'  "deps": {deps_json}',
            "}",
            "```",
        ])
    lines.append("<!-- END ADD_EXAMPLE_TEMPLATES -->")
    return "\n".join(lines)


def render_field_reference(schema: dict) -> str:
    """Render field reference table."""
    known_types = " / ".join(f"`{t}`" for t in sorted(schema))
    lines = [
        "<!-- BEGIN FIELD_REFERENCE -->",
        "#### 字段说明（自动生成）",
        "",
        "| 字段 | 必填 | 说明 |",
        "|------|------|------|",
        f"| `type` | ✅ | {known_types}，对应 `launch_schema.json` 中的启动规则 |",
        "| `file` | ✅ | 脚本文件名，相对于 `code/` 目录 |",
        "| `title` | ✅ | 显示在列表中的简短名称 |",
        "| `desc` | ✅ | 补充说明 |",
        "| `data_files` | ✅ | 依赖的数据文件名（空数组为无依赖），相对于 `code/data/raw/` |",
        "| `deps` | ✅ | 需要检查的 Python 包列表（空数组为无依赖） |",
        "<!-- END FIELD_REFERENCE -->",
    ]
    return "\n".join(lines)


def render_type_launch_reference(schema: dict) -> str:
    """Render per-type launch command reference."""
    lines = [
        "<!-- BEGIN TYPE_LAUNCH_REFERENCE -->",
        "#### 启动命令速查（自动生成）",
        "",
        "| 类型 | 启动命令 | 工作目录 | 启动依赖 |",
        "|------|----------|----------|----------|",
    ]
    for t, tmeta in sorted(schema.items()):
        label = TYPE_LABELS.get(t, t)
        cmd_parts = [tmeta.get("command", "{python}")] + tmeta.get("args_template", [])
        cmd_str = " ".join(cmd_parts)
        cwd = tmeta.get("cwd", ".")
        pkgs = ", ".join(tmeta.get("launcher_packages", [])) or "—"
        lines.append(f"| {label} | `{cmd_str}` | `{cwd}` | {pkgs} |")
    lines.append("<!-- END TYPE_LAUNCH_REFERENCE -->")
    return "\n".join(lines)


def generate_all_blocks(manifest: dict, schema: dict) -> dict[str, str]:
    """Return a dict mapping block name -> rendered Markdown (including markers)."""
    return {
        "EXAMPLE_INVENTORY": render_example_inventory(manifest),
        "ADD_EXAMPLE_TEMPLATES": render_add_example_templates(manifest, schema),
        "FIELD_REFERENCE": render_field_reference(schema),
        "TYPE_LAUNCH_REFERENCE": render_type_launch_reference(schema),
    }


# ---------------------------------------------------------------------------
# README mutation
# ---------------------------------------------------------------------------

def write_generated_blocks(readme_path: Path, manifest: dict, schema: dict) -> None:
    """Replace every auto-generated block in *readme_path* with freshly-rendered
    content. Raises ``SystemExit`` on marker errors.
    """
    if not readme_path.exists():
        print(f"[ERROR] README not found: {readme_path}", file=sys.stderr)
        sys.exit(1)

    readme = readme_path.read_text(encoding="utf-8")
    blocks = generate_all_blocks(manifest, schema)

    missing_blocks: list[str] = []
    for name in AUTO_BLOCKS:
        begin = f"<!-- BEGIN {name} -->"
        end = f"<!-- END {name} -->"
        if begin not in readme or end not in readme:
            missing_blocks.append(name)

    if missing_blocks:
        print(
            f"[ERROR] README 缺少以下 auto-generated 区块标记：{missing_blocks}",
            file=sys.stderr,
        )
        print(
            "请先在 README.md 中插入相应的 <!-- BEGIN ... --> / <!-- END ... --> 标记。",
            file=sys.stderr,
        )
        sys.exit(1)

    updated = readme
    for name, block_content in blocks.items():
        begin = f"<!-- BEGIN {name} -->"
        end = f"<!-- END {name} -->"
        pattern = re.compile(
            rf"{re.escape(begin)}.*?{re.escape(end)}",
            re.DOTALL,
        )
        updated, n = pattern.subn(block_content, updated, count=1)
        if n != 1:
            print(f"[ERROR] 替换区块 '{name}' 失败（找到 {n} 处匹配）", file=sys.stderr)
            sys.exit(1)

    readme_path.write_text(updated, encoding="utf-8")
    print(f"✅ README.md 的 {len(AUTO_BLOCKS)} 个 auto-generated 区块已更新。")


# ---------------------------------------------------------------------------
# Drift detection
# ---------------------------------------------------------------------------

def check_readme_drift(readme_path: Path, manifest: dict, schema: dict) -> list[str]:
    """Return a list of human-readable drift warnings. Empty list = no drift.

    Strategy: re-render every block and compare byte-for-byte with the current
    README content. Any difference -> drift.
    """
    warnings: list[str] = []
    if not readme_path.exists():
        return [f"README not found at {readme_path}"]

    readme = readme_path.read_text(encoding="utf-8")

    # 1. Marker existence
    for block in AUTO_BLOCKS:
        begin = f"<!-- BEGIN {block} -->"
        end = f"<!-- END {block} -->"
        if begin not in readme:
            warnings.append(f"README 缺少 auto-generated 区块起始标记: {begin}")
        if end not in readme:
            warnings.append(f"README 缺少 auto-generated 区块结束标记: {end}")

    # 2. Byte-for-byte comparison of every block
    renderers: dict[str, Any] = {
        "EXAMPLE_INVENTORY": lambda: render_example_inventory(manifest),
        "ADD_EXAMPLE_TEMPLATES": lambda: render_add_example_templates(manifest, schema),
        "FIELD_REFERENCE": lambda: render_field_reference(schema),
        "TYPE_LAUNCH_REFERENCE": lambda: render_type_launch_reference(schema),
    }

    for block in AUTO_BLOCKS:
        begin = f"<!-- BEGIN {block} -->"
        end = f"<!-- END {block} -->"
        if begin not in readme or end not in readme:
            continue  # already reported in step 1

        pattern = re.compile(
            rf"{re.escape(begin)}.*?{re.escape(end)}",
            re.DOTALL,
        )
        match = pattern.search(readme)
        if not match:
            continue

        current = match.group(0)
        expected = renderers[block]()

        if current != expected:
            warnings.append(
                f"README auto-generated 区块 '{block}' 未同步 "
                f"— 请运行 `python launcher.py generate-readme`"
            )

    # 3. Inline `python launcher.py run X` reference validation
    #    (handwritten, outside auto-generated blocks)
    inline_refs = re.findall(r"`python launcher\.py run ([^`]+)`", readme)
    for ref in inline_refs:
        ref = ref.strip()
        if ref not in manifest:
            warnings.append(
                f"README 引用了不存在的示例 ID '{ref}'（在 `python launcher.py run ...` 中）"
            )

    return warnings
