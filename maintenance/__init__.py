"""Shared constants, paths, and helpers for the maintenance package.

Each checker module (profile_checker, readme_updater, …) imports the
common building blocks from here so that ``maintenance.py`` stays a
thin CLI dispatcher.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TypedDict


# ---------------------------------------------------------------------------
# Paths — resolved relative to the repo root (parent of maintenance/)
# ---------------------------------------------------------------------------

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent
CODE_DIR = REPO_ROOT / "code"
RAW_DATA_DIR = CODE_DIR / "data" / "raw"
METADATA_CACHE = REPO_ROOT / ".metadata_cache"
MANIFEST_PATH = REPO_ROOT / "examples_manifest.json"
LAUNCH_SCHEMA_PATH = REPO_ROOT / "launch_schema.json"
REQS_PIPTOOLS = REPO_ROOT / "requirements.piptools"
REQS_TXT = REPO_ROOT / "requirements.txt"
OUTPUT_DIR = REPO_ROOT / "output"


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"
SKIP = "SKIP"


class CheckResult(TypedDict):
    status: str
    message: str


def make_result(status: str, message: str) -> CheckResult:
    return CheckResult(status=status, message=message)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

_COLORS: dict[str, str] = {
    PASS: "\033[32m",
    WARN: "\033[33m",
    FAIL: "\033[31m",
    SKIP: "\033[36m",
    "reset": "\033[0m",
}


def colour(tag: str) -> str:
    if not sys.stdout.isatty():
        return ""
    return _COLORS.get(tag, "")


def print_results(group: str, results: list[CheckResult]) -> None:
    print(f"\n--- {group} ---")
    for r in results:
        c = colour(r["status"])
        reset = colour("reset")
        print(f"  [{c}{r['status']:>4}{reset}] {r['message']}")


def all_passed(results: list[CheckResult]) -> bool:
    return all(r["status"] != FAIL for r in results)


# ---------------------------------------------------------------------------
# Python syntax check (shared by launcher_checker)
# ---------------------------------------------------------------------------

def check_python_syntax(file_path: Path) -> str | None:
    """Return an error string if *file_path* has syntax issues, else None."""
    try:
        source = file_path.read_text(encoding="utf-8")
        compile(source, str(file_path), "exec")
    except SyntaxError as exc:
        return f"syntax error: {exc}"
    except Exception as exc:
        return f"read error: {exc}"
    return None
