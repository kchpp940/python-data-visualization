"""Launcher self-check — validate launch_schema.json, examples_manifest.json, and launcher.py syntax."""

from __future__ import annotations

import json

from maintenance import (
    FAIL, PASS, WARN,
    REPO_ROOT, MANIFEST_PATH, LAUNCH_SCHEMA_PATH,
    CheckResult, make_result, check_python_syntax,
)


def run() -> list[CheckResult]:
    """Validate the launcher stack: schema + manifest + launcher.py."""
    results: list[CheckResult] = []

    if not LAUNCH_SCHEMA_PATH.exists():
        results.append(make_result(FAIL, f"launch schema missing: {LAUNCH_SCHEMA_PATH}"))
        return results

    try:
        schema = json.loads(LAUNCH_SCHEMA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        results.append(make_result(FAIL, f"launch schema JSON parse error: {exc}"))
        return results

    if not isinstance(schema, dict):
        results.append(make_result(FAIL, "launch schema must be a JSON object"))
        return results

    results.append(make_result(
        PASS,
        f"launch schema: {len(schema)} types defined ({', '.join(sorted(schema.keys()))})",
    ))

    for type_name, rules in schema.items():
        for field in ("command", "args_template", "cwd", "check_package", "fallbacks"):
            if field not in rules:
                results.append(make_result(
                    FAIL, f"launch schema '{type_name}': missing field '{field}'",
                ))

    if not MANIFEST_PATH.exists():
        results.append(make_result(FAIL, f"manifest missing: {MANIFEST_PATH}"))
        return results

    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        results.append(make_result(FAIL, f"manifest JSON parse error: {exc}"))
        return results

    type_usage: dict[str, int] = {}
    for entry in manifest.values():
        t = entry.get("type", "unknown")
        type_usage[t] = type_usage.get(t, 0) + 1

    for t, count in sorted(type_usage.items()):
        if t in schema:
            results.append(make_result(PASS, f"type '{t}': {count} entries"))
        else:
            results.append(make_result(
                WARN, f"type '{t}': {count} entries but not in launch schema",
            ))

    launcher_py = REPO_ROOT / "launcher.py"
    if launcher_py.exists():
        err = check_python_syntax(launcher_py)
        if err is None:
            results.append(make_result(PASS, "launcher.py syntax OK"))
        else:
            results.append(make_result(FAIL, f"launcher.py: {err}"))
    else:
        results.append(make_result(
            WARN, "launcher.py not found — create it or check README for setup",
        ))

    launcher_dir = REPO_ROOT / "launcher"
    if launcher_dir.exists() and launcher_dir.is_dir():
        for py_file in sorted(launcher_dir.rglob("*.py")):
            err = check_python_syntax(py_file)
            rel = py_file.relative_to(REPO_ROOT)
            if err is None:
                results.append(make_result(PASS, f"{rel} syntax OK"))
            else:
                results.append(make_result(FAIL, f"{rel}: {err}"))

    results.append(make_result(PASS, f"manifest entries: {len(manifest)}"))

    return results
