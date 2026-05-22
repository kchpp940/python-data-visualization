#!/usr/bin/env python3
"""Unified launcher for python-data-visualization examples.

Reads configuration from two JSON files (co-located with this script):

    examples_manifest.json   -- what examples exist (IDs, entry files, deps, data)
    launch_schema.json       -- how to launch each type (command, args, cwd, fallbacks)

README auto-generation and drift detection live in :mod:`launcher.docs`;
this file only dispatches CLI commands.

Usage:
    python launcher.py list                  # list all examples
    python launcher.py run <id>              # run a specific example
    python launcher.py check [<id>]          # check environment (and README drift)
    python launcher.py generate-readme       # regenerate auto-generated blocks in README
    python launcher.py                       # interactive picker (default)
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

from launcher.docs import (  # noqa: E402
    AUTO_BLOCKS,
    TYPE_LABELS,
    check_readme_drift,
    write_generated_blocks,
)

REPO_ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = REPO_ROOT / "examples_manifest.json"
SCHEMA_PATH = REPO_ROOT / "launch_schema.json"
README_PATH = REPO_ROOT / "README.md"


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_json(path: Path) -> dict:
    if not path.exists():
        print(f"[ERROR] Missing config file: {path}", file=sys.stderr)
        sys.exit(1)
    import json
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_manifest() -> dict[str, dict]:
    """Load examples_manifest.json, filtering out private keys (starting with '_')."""
    raw = load_json(MANIFEST_PATH)
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def load_schema() -> dict[str, dict]:
    """Load launch_schema.json, filtering out private keys."""
    raw = load_json(SCHEMA_PATH)
    return {k: v for k, v in raw.items() if not k.startswith("_")}


# ---------------------------------------------------------------------------
# Dependency checking helpers
# ---------------------------------------------------------------------------

def check_package(pkg: str) -> bool:
    """Check whether a Python package is importable (by import name)."""
    try:
        return importlib.util.find_spec(pkg) is not None
    except (ImportError, ValueError):
        return False


def resolve_path(base: Path, rel: str) -> Path:
    return (base / rel).resolve()


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

def cmd_list(manifest: dict, schema: dict) -> None:
    """Display all examples grouped by type."""
    by_type: dict[str, list[tuple[str, dict]]] = {}
    for eid, meta in manifest.items():
        t = meta.get("type", "unknown")
        by_type.setdefault(t, []).append((eid, meta))

    for t, items in sorted(by_type.items()):
        label = TYPE_LABELS.get(t, t)
        print(f"\n{'=' * 60}")
        print(f"  {label}  ({len(items)} example{'s' if len(items) != 1 else ''})")
        print(f"{'=' * 60}")
        for eid, meta in sorted(items):
            title = meta.get("title", "(no title)")
            desc = meta.get("desc", "")
            print(f"  {eid:<20s} {title}")
            if desc:
                print(f"  {'':20s}   {desc}")

    print(f"\nTotal: {len(manifest)} examples across {len(by_type)} types.")
    print(f"\nRun:  python launcher.py run <id>")
    print(f"Check: python launcher.py check <id>")
    print(f"Gen README: python launcher.py generate-readme")


# ---------------------------------------------------------------------------
# check (environment + README drift)
# ---------------------------------------------------------------------------

def _check_example(eid: str, meta: dict, schema: dict) -> dict[str, list[str]]:
    """Check a single example's environment.

    Returns a dict with keys: missing_deps, missing_data, missing_entry,
    missing_launcher.
    """
    issues: dict[str, list[str]] = {
        "missing_deps": [],
        "missing_data": [],
        "missing_entry": [],
        "missing_launcher": [],
    }

    entry_file = meta.get("file", "")
    if entry_file:
        entry_path = resolve_path(REPO_ROOT, f"code/{entry_file}")
        if not entry_path.exists():
            issues["missing_entry"].append(str(entry_path))

    for df in meta.get("data_files", []):
        df_path = resolve_path(REPO_ROOT, f"code/data/raw/{df}")
        if not df_path.exists():
            issues["missing_data"].append(str(df_path))

    for dep in meta.get("deps", []):
        if not check_package(dep):
            issues["missing_deps"].append(dep)

    stype = meta.get("type", "")
    type_schema = schema.get(stype, {})
    for pkg in type_schema.get("launcher_packages", []):
        if not check_package(pkg):
            issues["missing_launcher"].append(pkg)

    if issues["missing_launcher"]:
        for fb in type_schema.get("fallbacks", []):
            for pkg in fb.get("launcher_packages", []):
                if check_package(pkg):
                    issues["missing_launcher"] = [
                        p for p in issues["missing_launcher"] if p != pkg
                    ]

    return issues


def cmd_check(manifest: dict, schema: dict, target: str | None = None) -> bool:
    """Check environment readiness for one or all examples, plus README drift.

    Returns True if all checked examples pass and no README drift is found.
    """
    env_ok = True

    if target:
        if target not in manifest:
            print(f"[ERROR] Unknown example ID: {target}", file=sys.stderr)
            print(f"Run 'python launcher.py list' to see available IDs.", file=sys.stderr)
            return False
        items = [(target, manifest[target])]
    else:
        items = sorted(manifest.items())

    for eid, meta in items:
        issues = _check_example(eid, meta, schema)
        total_issues = sum(len(v) for v in issues.values())
        status = "OK" if total_issues == 0 else f"ISSUES ({total_issues})"
        icon = "✅" if total_issues == 0 else "⚠️"
        print(f"\n{icon} {eid}  [{status}]")

        if issues["missing_deps"]:
            env_ok = False
            print(f"   ❌ Missing deps: {', '.join(issues['missing_deps'])}")
            print(f"      → pip install {' '.join(issues['missing_deps'])}")
        if issues["missing_data"]:
            env_ok = False
            for p in issues["missing_data"]:
                print(f"   ❌ Missing data: {p}")
        if issues["missing_entry"]:
            env_ok = False
            for p in issues["missing_entry"]:
                print(f"   ❌ Missing entry: {p}")
        if issues["missing_launcher"]:
            env_ok = False
            print(f"   ❌ Missing launcher: {', '.join(issues['missing_launcher'])}")
            print(f"      → pip install {' '.join(issues['missing_launcher'])}")

    # README drift check (only when checking "all", not for a single target)
    if target is None:
        print(f"\n{'─' * 60}")
        print("📖 README 一致性检查")
        print(f"{'─' * 60}")
        drift = check_readme_drift(README_PATH, manifest, schema)
        if drift:
            env_ok = False
            print(f"⚠️  发现 {len(drift)} 项 README 与配置不一致：")
            for w in drift:
                print(f"   - {w}")
            print(f"\n   → 运行 `python launcher.py generate-readme` 重新生成 auto-generated 区块")
        else:
            print("✅ README 与 manifest/schema 保持一致。")

    if env_ok:
        print("\n✅ All checks passed.")
    else:
        print("\n⚠️  Some checks need attention. See above for details.")

    return env_ok


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

def _build_command(eid: str, meta: dict, schema: dict) -> tuple[list[str], Path, str | None]:
    """Build (argv, cwd, browse_hint) for an example."""
    stype = meta["type"]
    type_schema = schema[stype]

    python = sys.executable
    file_rel = meta["file"]

    launcher_pkgs = type_schema.get("launcher_packages", [])
    primary_available = all(check_package(p) for p in launcher_pkgs) if launcher_pkgs else True

    if primary_available:
        args_template = type_schema["args_template"]
    else:
        args_template = type_schema["args_template"]
        for fb in type_schema.get("fallbacks", []):
            fb_pkgs = fb.get("launcher_packages", [])
            if all(check_package(p) for p in fb_pkgs) if fb_pkgs else True:
                args_template = fb["args_template"]
                break

    command = type_schema.get("command", "{python}")
    cmd_parts = [command.replace("{python}", python)]
    for arg in args_template:
        cmd_parts.append(arg.replace("{file}", file_rel).replace("{python}", python))

    cwd = resolve_path(REPO_ROOT, type_schema.get("cwd", "."))
    browse_hint = type_schema.get("browse_hint")

    return cmd_parts, cwd, browse_hint


def cmd_run(manifest: dict, schema: dict, target: str) -> None:
    """Run a specific example."""
    if target not in manifest:
        print(f"[ERROR] Unknown example ID: {target}", file=sys.stderr)
        print(f"Run 'python launcher.py list' to see available IDs.", file=sys.stderr)
        sys.exit(1)

    meta = manifest[target]

    issues = _check_example(target, meta, schema)
    total_issues = sum(len(v) for v in issues.values())
    if total_issues > 0:
        print(f"⚠️  Pre-flight check found {total_issues} issue(s):")
        for category, items in issues.items():
            for item in items:
                print(f"   - {category}: {item}")
        print("   Attempting to launch anyway...\n")

    argv, cwd, browse_hint = _build_command(target, meta, schema)

    print(f"🚀 Launching '{target}' ({meta.get('title', '')})")
    print(f"   cwd: {cwd}")
    print(f"   cmd: {' '.join(argv)}")
    if browse_hint:
        print(f"   tip: {browse_hint}")
    print()

    cwd.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(argv, cwd=str(cwd), check=False)
    except KeyboardInterrupt:
        print("\n[Interrupted]")
    except FileNotFoundError:
        print(f"[ERROR] Command not found: {argv[0]}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# interactive
# ---------------------------------------------------------------------------

def cmd_interactive(manifest: dict, schema: dict) -> None:
    """Display the list and let the user pick an example to run."""
    cmd_list(manifest, schema)

    print("\n" + "-" * 60)
    try:
        choice = input("Enter example ID to run (or press Enter to quit): ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if not choice:
        return

    if choice in manifest:
        cmd_run(manifest, schema, choice)
    else:
        print(f"[ERROR] Unknown example ID: {choice}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# generate-readme (delegated to launcher.docs)
# ---------------------------------------------------------------------------

def cmd_generate_readme(manifest: dict, schema: dict) -> None:
    """Regenerate all auto-generated blocks in README.md."""
    write_generated_blocks(README_PATH, manifest, schema)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    manifest = load_manifest()
    schema = load_schema()

    args = sys.argv[1:]

    if not args:
        cmd_interactive(manifest, schema)
        return

    cmd = args[0].lower()

    if cmd == "list":
        cmd_list(manifest, schema)
    elif cmd == "check":
        target = args[1] if len(args) > 1 else None
        ok = cmd_check(manifest, schema, target)
        sys.exit(0 if ok else 1)
    elif cmd == "run":
        if len(args) < 2:
            print("Usage: python launcher.py run <id>", file=sys.stderr)
            sys.exit(1)
        cmd_run(manifest, schema, args[1])
    elif cmd == "generate-readme":
        cmd_generate_readme(manifest, schema)
    elif cmd in ("-h", "--help", "help"):
        print(__doc__)
    else:
        print(f"[ERROR] Unknown command: {cmd}", file=sys.stderr)
        print(f"Available: list, run, check, generate-readme, help", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
