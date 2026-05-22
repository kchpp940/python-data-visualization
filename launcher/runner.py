"""Build startup commands and execute them — entirely schema-driven.

The runner contains **zero** hardcoded rules for any example type.  Every
aspect of how an example starts (command, arguments, working directory,
availability check, fallback chain) is declared in ``launch_schema.json``.

Resolution order for a single entry:

1. Look up the entry's ``type`` in the launch schema.
2. Check if the schema's ``check_package`` is importable.
3. If not, walk ``fallbacks`` and pick the first whose ``check_package``
   is importable.
4. If nothing matches, raise :class:`NoLauncherAvailable`.
5. Render ``command`` and ``args_template`` with ``{python}`` / ``{file}`` /
   ``{cwd}`` placeholders.
"""

from __future__ import annotations

import importlib.util
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

from data_paths import CODE_DIR, REPO_ROOT

from .checker import CheckResult, check_entry
from .manifest_loader import LaunchSchema, ManifestEntry


@dataclass(frozen=True)
class LaunchCommand:
    """A prepared command ready to execute."""

    argv: List[str]
    cwd: Path
    entry: ManifestEntry
    schema: LaunchSchema

    @property
    def display(self) -> str:
        return " ".join(shlex.quote(part) for part in self.argv)

    @property
    def launcher_label(self) -> str:
        """Human-readable label for the launcher being used (e.g. 'jupyter lab')."""
        args = self.schema.args_template
        if len(args) >= 3 and args[0] == "-m" and args[1] in (
            "streamlit",
            "jupyter",
            "notebook",
        ):
            return f"{args[1]} {' '.join(args[2:-1])}".strip()
        if len(args) == 1:
            return "python"
        return self.schema.command


# ---------------------------------------------------------------------------
# Package-availability helper (shared with checker)
# ---------------------------------------------------------------------------

def _package_available(package: Optional[str]) -> bool:
    """Return True when *package* can be imported, or always True when None."""

    if package is None:
        return True
    return importlib.util.find_spec(package) is not None


# ---------------------------------------------------------------------------
# Schema resolution
# ---------------------------------------------------------------------------

class NoLauncherAvailable(ValueError):
    """Raised when none of the schema's check_packages are importable."""


def _resolve_schema(
    entry: ManifestEntry,
    launch_schemas: dict[str, LaunchSchema],
) -> LaunchSchema:
    """Find the first usable launch schema for *entry*."""

    if entry.type not in launch_schemas:
        raise NoLauncherAvailable(
            f"[{entry.example_id}] 在 launch_schema.json 中"
            f"未找到 type={entry.type!r} 的启动定义"
        )

    primary = launch_schemas[entry.type]

    candidates: list[LaunchSchema] = [primary, *primary.fallbacks]

    for candidate in candidates:
        if _package_available(candidate.check_package):
            return candidate

    tried = ", ".join(
                f"{c.type_name}({c.check_package})" for c in candidates
            )
    raise NoLauncherAvailable(
        f"[{entry.example_id}] 没有可用的启动器；尝试了: {tried}"
    )


# ---------------------------------------------------------------------------
# Command rendering
# ---------------------------------------------------------------------------

def _render(template: str, *, python_exe: str, entry: ManifestEntry, cwd: Path) -> str:
    """Render a single template string with placeholders."""

    return template.format(
        python=python_exe,
        file=str(CODE_DIR / entry.file),
        cwd=str(cwd),
    )


def build_command(
    entry: ManifestEntry,
    launch_schemas: dict[str, LaunchSchema],
    python_exe: str | None = None,
) -> LaunchCommand:
    """Build the argv for *entry* using the launch schema.

    Raises:
        NoLauncherAvailable: When no schema (including fallbacks) is usable.
    """

    schema = _resolve_schema(entry, launch_schemas)
    exe = python_exe or sys.executable
    cwd = REPO_ROOT / schema.cwd

    command = _render(schema.command, python_exe=exe, entry=entry, cwd=cwd)
    argv: List[str] = [command]
    for tpl in schema.args_template:
        argv.append(_render(tpl, python_exe=exe, entry=entry, cwd=cwd))

    return LaunchCommand(argv=argv, cwd=cwd, entry=entry, schema=schema)


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def run_entry(
    entry: ManifestEntry,
    launch_schemas: dict[str, LaunchSchema],
    python_exe: str | None = None,
    check_first: bool = True,
    extra_args: Sequence[str] = (),
) -> int:
    """Build and execute the startup command for *entry*.

    Returns the subprocess exit code.
    """

    if check_first:
        result: CheckResult = check_entry(entry)
        if not result.ok:
            sys.stderr.write(
                f"[{entry.example_id}] 环境检查失败，无法启动：\n"
            )
            for line in result.summary_lines():
                sys.stderr.write(line + "\n")
            return 2

    try:
        command = build_command(entry, launch_schemas, python_exe=python_exe)
    except NoLauncherAvailable as exc:
        sys.stderr.write(f"错误：{exc}\n")
        return 5

    argv = list(command.argv) + list(extra_args)

    print(f"→ 启动 {entry.title} ({entry.example_id})")
    print(f"   启动器: {command.launcher_label}")
    print(f"   $ {command.display}", end="")
    if extra_args:
        print(" " + " ".join(shlex.quote(a) for a in extra_args), end="")
    print()

    completed = subprocess.run(argv, cwd=command.cwd, env={**os.environ})
    return completed.returncode
