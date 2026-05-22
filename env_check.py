"""Unified environment-check module for python-data-visualization.

Public API
----------
- :func:`check_environment`   -> ``EnvReport`` (all examples or one id)
- :func:`check_example`       -> ``ExampleReport`` (single example)
- :func:`check_consistency`   -> list of ``ConsistencyIssue``
- :func:`parse_requirements`  -> dict[pkg]version from a requirements.txt
- :func:`parse_piptools`      -> list[pkg] from requirements.piptools top-level
- :func:`render_report`       -> pretty console output

The report splits problems into five independent buckets so that the launcher
can present one clear, actionable message per issue:

1. ``missing_deps``        -- Python packages that are not installed
2. ``version_conflicts``   -- installed version doesn't match requirements.txt
3. ``missing_data_files``  -- expected raw data files absent
4. ``missing_entry_files`` -- the script/notebook declared in manifest is missing
5. ``consistency_issues``  -- manifest/piptools/requirements lists out of sync
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:
    from importlib.metadata import PackageNotFoundError, version as _pkg_version
except ImportError:  # pragma: no cover - py<3.8 fallback
    from importlib_metadata import PackageNotFoundError, version as _pkg_version  # type: ignore

REPO_ROOT = Path(__file__).resolve().parent
CODE_DIR = REPO_ROOT / "code"
RAW_DATA_DIR = CODE_DIR / "data" / "raw"
REQUIREMENTS_TXT = REPO_ROOT / "requirements.txt"
REQUIREMENTS_PIPTOOLS = REPO_ROOT / "requirements.piptools"
MANIFEST_FILE = REPO_ROOT / "examples_manifest.json"
SCHEMA_FILE = REPO_ROOT / "launch_schema.json"


_REQ_LINE_RE = re.compile(r"^([A-Za-z0-9_.-]+)\s*(?:==|>=|<=|~=|!=|>|<)\s*([A-Za-z0-9_.*+!-]+)")
_PIPTOOLS_PKG_RE = re.compile(r"^([A-Za-z0-9_.-]+)(?:\s*[<>=!~].*)?$")


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_requirements(path: Path = REQUIREMENTS_TXT) -> dict[str, str]:
    """Parse a pinned requirements.txt into ``{package: version}``.

    Only ``pkg==X.Y.Z`` lines are recorded; comments and directives are skipped.
    """
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = _REQ_LINE_RE.match(line)
        if m:
            out[_norm(m.group(1))] = m.group(2)
    return out


def parse_piptools(path: Path = REQUIREMENTS_PIPTOOLS) -> list[str]:
    """Return the list of top-level package names declared in piptools file."""
    out: list[str] = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = _PIPTOOLS_PKG_RE.match(line)
        if m:
            out.append(_norm(m.group(1)))
    return out


def load_manifest(path: Path = MANIFEST_FILE) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_schema(path: Path = SCHEMA_FILE) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def installed_version(pkg: str) -> str | None:
    """Return the installed version of ``pkg`` or ``None`` if not installed."""
    try:
        return _pkg_version(pkg)
    except PackageNotFoundError:
        return None


@dataclass
class ExampleReport:
    example_id: str
    title: str
    type: str
    file: str
    missing_deps: list[str] = field(default_factory=list)
    version_conflicts: list[tuple[str, str, str]] = field(default_factory=list)  # (pkg, expected, actual)
    missing_data_files: list[str] = field(default_factory=list)
    missing_entry_files: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (
            self.missing_deps
            or self.version_conflicts
            or self.missing_data_files
            or self.missing_entry_files
        )

    @property
    def problems(self) -> int:
        return (
            len(self.missing_deps)
            + len(self.version_conflicts)
            + len(self.missing_data_files)
            + len(self.missing_entry_files)
        )


@dataclass
class ConsistencyIssue:
    """A single cross-list consistency problem.

    ``issue_type`` is one of:

    - ``"manifest_dep_not_in_piptools"``  -- dep in manifest, absent from piptools
    - ``"manifest_dep_not_in_requirements"`` -- dep in manifest, absent from requirements.txt
    - ``"piptools_dep_not_in_requirements"`` -- dep in piptools, absent from requirements.txt

    ``fix_steps`` is a short, copy-paste-ready sequence of shell commands (one per
    line) that the launcher surfaces when a ``run`` is blocked by this issue.
    """

    issue_type: str
    package: str
    details: str = ""
    fix_steps: str = ""

    @property
    def label(self) -> str:
        return {
            "manifest_dep_not_in_piptools": "清单未同步",
            "manifest_dep_not_in_requirements": "清单未同步",
            "piptools_dep_not_in_requirements": "清单未同步",
        }.get(self.issue_type, "清单未同步")

    @property
    def target_file(self) -> str:
        return {
            "manifest_dep_not_in_piptools": "requirements.piptools",
            "manifest_dep_not_in_requirements": "requirements.txt",
            "piptools_dep_not_in_requirements": "requirements.txt",
        }.get(self.issue_type, "?")


@dataclass
class EnvReport:
    examples: list[ExampleReport] = field(default_factory=list)
    consistency_issues: list[ConsistencyIssue] = field(default_factory=list)
    requirements_missing: bool = False
    piptools_missing: bool = False
    manifest_missing: bool = False
    schema_missing: bool = False

    @property
    def ok(self) -> bool:
        return (
            all(e.ok for e in self.examples)
            and not self.consistency_issues
            and not (
                self.requirements_missing
                or self.piptools_missing
                or self.manifest_missing
                or self.schema_missing
            )
        )

    def by_id(self, example_id: str) -> ExampleReport | None:
        for e in self.examples:
            if e.example_id == example_id:
                return e
        return None


def _check_entry_file(rel_path: str) -> str | None:
    abs_path = CODE_DIR / rel_path
    return None if abs_path.exists() else rel_path


def _check_data_file(rel_name: str) -> str | None:
    abs_path = RAW_DATA_DIR / rel_name
    return None if abs_path.exists() else rel_name


def check_example(
    example_id: str,
    manifest: dict | None = None,
    pinned: dict[str, str] | None = None,
    top_level: Iterable[str] | None = None,
) -> ExampleReport:
    """Run all four checks against a single example and return the report."""
    if manifest is None:
        manifest = load_manifest()
    if pinned is None:
        pinned = parse_requirements()
    if top_level is None:
        top_level = set(parse_piptools())
    else:
        top_level = set(_norm(p) for p in top_level)

    entry = manifest.get(example_id)
    if entry is None:
        return ExampleReport(
            example_id=example_id,
            title=f"<unknown: {example_id}>",
            type="unknown",
            file="",
            missing_entry_files=[f"<manifest missing id '{example_id}'>"],
        )

    report = ExampleReport(
        example_id=example_id,
        title=entry.get("title", example_id),
        type=entry.get("type", "unknown"),
        file=entry.get("file", ""),
    )

    entry_rel = entry.get("file")
    if entry_rel:
        miss = _check_entry_file(entry_rel)
        if miss:
            report.missing_entry_files.append(miss)

    for data_name in entry.get("data_files", []) or []:
        miss = _check_data_file(data_name)
        if miss:
            report.missing_data_files.append(miss)

    for dep in entry.get("deps", []) or []:
        dep_norm = _norm(dep)
        installed = installed_version(dep_norm)
        expected = pinned.get(dep_norm)
        if installed is None:
            report.missing_deps.append(dep)
        elif expected is not None and installed != expected and dep_norm in top_level:
            report.version_conflicts.append((dep, expected, installed))

    return report


def check_consistency(
    manifest: dict | None = None,
    pinned: dict[str, str] | None = None,
    top_level: Iterable[str] | None = None,
) -> list[ConsistencyIssue]:
    """Cross-check that manifest / piptools / requirements.txt are in sync.

    Returns a list of consistency issues. Each issue carries an ``issue_type``:

    - ``"manifest_dep_not_in_piptools"``  -- a dep declared in manifest is not
      a top-level dependency in piptools (and not in requirements.txt either)
    - ``"manifest_dep_not_in_requirements"`` -- a dep declared in manifest is
      not present in requirements.txt at all
    - ``"piptools_dep_not_in_requirements"`` -- a top-level piptools dep is
      not found in requirements.txt
    """
    if manifest is None:
        manifest = load_manifest()
    if pinned is None:
        pinned = parse_requirements()
    if top_level is None:
        top_level = set(parse_piptools())
    else:
        top_level = set(_norm(p) for p in top_level)

    issues: list[ConsistencyIssue] = []

    # 1. piptools top-level deps must appear in requirements.txt
    for pkg in sorted(top_level):
        if pkg not in pinned:
            issues.append(
                ConsistencyIssue(
                    issue_type="piptools_dep_not_in_requirements",
                    package=pkg,
                    details=(
                        f"requirements.piptools 顶层依赖 '{pkg}' "
                        f"未在 requirements.txt 中找到锁定版本"
                    ),
                    fix_steps=(
                        "# 重新生成锁文件\n"
                        "pip install pip-tools\n"
                        "pip-compile requirements.piptools\n"
                        "pip install -r requirements.txt"
                    ),
                )
            )

    # 2. manifest deps must be in piptools or requirements.txt at minimum
    all_manifest_deps: set[str] = set()
    for eid, entry in manifest.items():
        for dep in entry.get("deps", []) or []:
            all_manifest_deps.add(_norm(dep))

    for pkg in sorted(all_manifest_deps):
        in_piptools = pkg in top_level
        in_requirements = pkg in pinned
        if not in_piptools and not in_requirements:
            issues.append(
                ConsistencyIssue(
                    issue_type="manifest_dep_not_in_piptools",
                    package=pkg,
                    details=(
                        f"examples_manifest.json 依赖 '{pkg}' "
                        f"既不在 requirements.piptools 顶层，"
                        f"也不在 requirements.txt 中"
                    ),
                    fix_steps=(
                        f"# 1. 在 requirements.piptools 中添加一行\n"
                        f"#    {pkg}\n"
                        f"# 2. 重新生成锁文件\n"
                        f"pip install pip-tools\n"
                        f"pip-compile requirements.piptools\n"
                        f"pip install -r requirements.txt"
                    ),
                )
            )
        elif not in_requirements:
            issues.append(
                ConsistencyIssue(
                    issue_type="manifest_dep_not_in_requirements",
                    package=pkg,
                    details=(
                        f"examples_manifest.json 依赖 '{pkg}' "
                        f"未在 requirements.txt 中找到锁定版本"
                    ),
                    fix_steps=(
                        "# 重新生成锁文件\n"
                        "pip install pip-tools\n"
                        "pip-compile requirements.piptools\n"
                        "pip install -r requirements.txt"
                    ),
                )
            )

    return issues


def check_environment(example_id: str | None = None) -> EnvReport:
    """Run the full env check across all (or one) examples."""
    report = EnvReport()
    report.requirements_missing = not REQUIREMENTS_TXT.exists()
    report.piptools_missing = not REQUIREMENTS_PIPTOOLS.exists()
    report.manifest_missing = not MANIFEST_FILE.exists()
    report.schema_missing = not SCHEMA_FILE.exists()

    manifest = {} if report.manifest_missing else load_manifest()
    pinned = {} if report.requirements_missing else parse_requirements()
    top_level: set[str] = set() if report.piptools_missing else set(parse_piptools())

    if not (report.requirements_missing or report.piptools_missing or report.manifest_missing):
        report.consistency_issues = check_consistency(manifest, pinned, top_level)

    if example_id is not None:
        report.examples.append(check_example(example_id, manifest, pinned, top_level))
        return report

    for eid in manifest.keys():
        report.examples.append(check_example(eid, manifest, pinned, top_level))
    return report


def render_report(report: EnvReport, *, verbose: bool = False) -> str:
    """Render a human-readable summary suitable for the launcher output."""
    lines: list[str] = []
    sep = "=" * 72

    lines.append(sep)
    lines.append("python-data-visualization  环境检查报告")
    lines.append(sep)

    infra = []
    if report.requirements_missing:
        infra.append(f"  ! requirements.txt 缺失 ({REQUIREMENTS_TXT})")
    if report.piptools_missing:
        infra.append(f"  ! requirements.piptools 缺失 ({REQUIREMENTS_PIPTOOLS})")
    if report.manifest_missing:
        infra.append(f"  ! examples_manifest.json 缺失 ({MANIFEST_FILE})")
    if report.schema_missing:
        infra.append(f"  ! launch_schema.json 缺失 ({SCHEMA_FILE})")
    if infra:
        lines.append("基础设施:")
        lines.extend(infra)
    else:
        lines.append("基础设施: 全部就绪")

    if report.consistency_issues:
        lines.append("")
        lines.append("清单一致性:")
        for ci in report.consistency_issues:
            lines.append(f"  [{ci.label}] {ci.details}")
            if ci.fix_steps:
                lines.append(f"      → 修复文件: {ci.target_file}")
                for step in ci.fix_steps.splitlines():
                    lines.append(f"         {step}")
    else:
        lines.append("清单一致性: 已同步")

    ok_examples = [e for e in report.examples if e.ok]
    bad_examples = [e for e in report.examples if not e.ok]

    lines.append("")
    lines.append(
        f"示例总数: {len(report.examples)}  就绪: {len(ok_examples)}  有问题: {len(bad_examples)}"
    )
    lines.append("-" * 72)

    if not bad_examples and not report.consistency_issues:
        lines.append("所有示例环境就绪，可以运行。")
        return "\n".join(lines)

    for e in bad_examples:
        lines.append(f"[{e.example_id}] {e.title} ({e.type})")
        if e.missing_entry_files:
            for f in e.missing_entry_files:
                lines.append(f"  [入口缺失] code/{f}")
        if e.missing_deps:
            for pkg in e.missing_deps:
                lines.append(f"  [缺依赖]   {pkg}  —— pip install {pkg}")
        if e.version_conflicts:
            for pkg, expected, actual in e.version_conflicts:
                lines.append(
                    f"  [版本冲突] {pkg} 期望 {expected}, 实际 {actual}"
                    f"  —— pip install {pkg}=={expected}"
                )
        if e.missing_data_files:
            for f in e.missing_data_files:
                lines.append(f"  [数据缺失] code/data/raw/{f}")
        if verbose and e.ok:
            lines.append("  OK")
        lines.append("")

    lines.append("-" * 72)
    lines.append("提示: 请先处理上面列出的问题，再执行 `python launcher.py run <id>`。")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    verbose = "-v" in argv or "--verbose" in argv
    argv = [a for a in argv if a not in ("-v", "--verbose")]
    example_id = argv[0] if argv else None

    report = check_environment(example_id)
    print(render_report(report, verbose=verbose))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
