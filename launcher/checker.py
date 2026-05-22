"""Environment checks for manifest entries.

A check returns a :class:`CheckResult` describing whether a single example
is ready to run.  Four categories of problems are reported:

* missing Python packages (``missing_deps``)
* missing data files under ``code/data/raw`` (``missing_data``)
* missing entry script / notebook (``missing_entry``)
* missing launch runner (``missing_launcher``) — when neither the primary
  launch schema nor any fallback can be imported
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from .manifest_loader import LaunchSchema, ManifestEntry


@dataclass
class CheckResult:
    """Result of checking a single example."""

    entry: ManifestEntry
    missing_deps: List[str] = field(default_factory=list)
    missing_data: List[str] = field(default_factory=list)
    missing_entry: List[str] = field(default_factory=list)
    missing_launcher: Optional[str] = None

    @property
    def ok(self) -> bool:
        return not (
            self.missing_deps
            or self.missing_data
            or self.missing_entry
            or self.missing_launcher
        )

    def summary_lines(self) -> List[str]:
        lines: List[str] = []
        if self.missing_deps:
            lines.append(
                "  缺依赖: "
                + ", ".join(self.missing_deps)
                + f"  → pip install {' '.join(self.missing_deps)}"
            )
        if self.missing_data:
            lines.append(
                "  缺数据文件: " + ", ".join(self.missing_data)
                + "  → 请下载到 code/data/raw/"
            )
        if self.missing_entry:
            lines.append(
                "  缺入口脚本: " + ", ".join(self.missing_entry)
                + "  → 请检查 code/ 目录"
            )
        if self.missing_launcher:
            lines.append(
                f"  缺启动器: {self.missing_launcher}"
                + "  → 请在 launch_schema.json 中添加对应类型的启动规则"
            )
        return lines


def _package_available(package: Optional[str]) -> bool:
    """Return True when *package* can be imported, or always True when None."""

    if package is None:
        return True
    return importlib.util.find_spec(package) is not None


def _check_launcher(
    entry: ManifestEntry,
    launch_schemas: Optional[dict[str, LaunchSchema]],
) -> Optional[str]:
    """Return an error string if no usable launcher is found, else None."""

    if launch_schemas is None:
        return None

    if entry.type not in launch_schemas:
        return (
            f"type={entry.type!r} 在 launch_schema.json 中未定义"
        )

    primary = launch_schemas[entry.type]
    candidates = [primary, *primary.fallbacks]

    for candidate in candidates:
        if _package_available(candidate.check_package):
            return None

    tried = ", ".join(
        f"{c.check_package}" for c in candidates if c.check_package
    )
    return f"尝试了 {tried} 均不可用"


def check_entry(
    entry: ManifestEntry,
    launch_schemas: Optional[dict[str, LaunchSchema]] = None,
) -> CheckResult:
    """Run dependency / data / entry-script / launcher checks on a single entry.

    When *launch_schemas* is provided, the check also verifies that at least
    one launcher (primary or fallback) is importable.
    """

    result = CheckResult(entry=entry)

    for dep in entry.deps:
        if not _package_available(dep):
            result.missing_deps.append(dep)

    for data_path in entry.data_paths:
        if not data_path.is_file():
            result.missing_data.append(data_path.name)

    if not entry.script_path.is_file():
        result.missing_entry.append(entry.script_path.name)

    result.missing_launcher = _check_launcher(entry, launch_schemas)

    return result


def check_entries(
    entries: Sequence[ManifestEntry],
    launch_schemas: Optional[dict[str, LaunchSchema]] = None,
) -> Dict[str, CheckResult]:
    """Check a collection of entries keyed by example id."""

    return {
        entry.example_id: check_entry(entry, launch_schemas)
        for entry in entries
    }
