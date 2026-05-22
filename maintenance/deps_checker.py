"""Dependency lock-file validation — compare requirements.piptools vs requirements.txt.

The ``pip check`` sub-check is special: it classifies each reported issue as
either a project-relevant FAIL (the affected package is in requirements.txt) or
an external-environment WARN (the package is not part of this project).  This
prevents noise from globally-installed packages from masking real problems in
this repo's own dependency tree.
"""

from __future__ import annotations

import subprocess
import sys

from maintenance import (
    FAIL, PASS, SKIP, WARN,
    REQS_PIPTOOLS, REQS_TXT,
    CheckResult, make_result,
)


def _parse_piptools(path) -> set[str]:
    pkgs: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        pkg = (line
               .split(">=")[0].split("<=")[0].split("==")[0]
               .split("<")[0].split(">")[0].split("~=")[0].split("!=")[0]
               .strip())
        pkg = pkg.lower()
        if pkg:
            pkgs.add(pkg)
    return pkgs


def _parse_requirements_txt(path) -> set[str]:
    pkgs: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        pkg = (line
               .split("==")[0].split(">=")[0].split("<=")[0]
               .split("<")[0].split(">")[0].split("~=")[0].split("!=")[0]
               .strip())
        pkg = pkg.lower().replace("_", "-")
        if pkg:
            pkgs.add(pkg)
    return pkgs


def _extract_problem_package(pip_check_line: str) -> str:
    """Pull the package name from a ``pip check`` output line.

    Typical lines look like::

        some-pkg 1.0 has requirement other>=2, but you have other 1.5.

    Returns the first token (``some-pkg``) lowercased.
    """
    return pip_check_line.strip().split()[0].lower() if pip_check_line.strip() else ""


def _classify_pip_issue(line: str, project_pkgs: set[str]) -> tuple[str, str]:
    """Return (status, message) for a single pip-check line.

    * FAIL if the reported package belongs to this project.
    * WARN with an "(external)" tag otherwise.
    """
    pkg = _extract_problem_package(line)
    msg = line.strip()
    if pkg in project_pkgs:
        return FAIL, f"pip check [project]: {msg}"
    return WARN, f"pip check [external]: {msg}"


def run() -> list[CheckResult]:
    """Verify requirements.txt is consistent with requirements.piptools."""
    results: list[CheckResult] = []

    if not REQS_PIPTOOLS.exists():
        results.append(make_result(FAIL, f"{REQS_PIPTOOLS.name} missing"))
        return results

    if not REQS_TXT.exists():
        results.append(make_result(
            FAIL, f"{REQS_TXT.name} missing — run `pip-compile requirements.piptools`",
        ))
        return results

    piptools_pkgs = _parse_piptools(REQS_PIPTOOLS)
    txt_pkgs = _parse_requirements_txt(REQS_TXT)

    for pkg in sorted(piptools_pkgs):
        if pkg not in txt_pkgs:
            alt = pkg.replace("-", "_")
            if alt not in txt_pkgs:
                results.append(make_result(
                    WARN,
                    f"top-level pkg '{pkg}' in .piptools but not in requirements.txt",
                ))

    results.append(make_result(
        PASS, f"{REQS_PIPTOOLS.name}: {len(piptools_pkgs)} top-level deps",
    ))
    results.append(make_result(
        PASS, f"{REQS_TXT.name}: {len(txt_pkgs)} pinned packages",
    ))

    # ------------------------------------------------------------------
    # pip check — classify each issue as project-relevant or external
    # ------------------------------------------------------------------
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            capture_output=True, text=True, timeout=30,
        )
    except FileNotFoundError:
        results.append(make_result(SKIP, "pip not available — skipping pip check"))
        return results
    except subprocess.TimeoutExpired:
        results.append(make_result(WARN, "pip check timed out"))
        return results

    if proc.returncode == 0:
        results.append(make_result(PASS, "pip check: no broken dependencies"))
    else:
        project_pkgs = txt_pkgs | piptools_pkgs
        for line in proc.stdout.strip().splitlines():
            if not line.strip():
                continue
            status, msg = _classify_pip_issue(line, project_pkgs)
            results.append(make_result(status, msg))

    return results
