"""Example manifest validation — check examples_manifest.json against the filesystem."""

from __future__ import annotations

import json

from maintenance import (
    FAIL, PASS, WARN,
    CODE_DIR, RAW_DATA_DIR, MANIFEST_PATH, LAUNCH_SCHEMA_PATH,
    CheckResult, make_result,
)


def run() -> list[CheckResult]:
    """Validate examples_manifest.json against the filesystem."""
    results: list[CheckResult] = []

    if not MANIFEST_PATH.exists():
        results.append(make_result(FAIL, f"manifest file missing: {MANIFEST_PATH}"))
        return results

    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        results.append(make_result(FAIL, f"manifest JSON parse error: {exc}"))
        return results

    if not isinstance(manifest, dict):
        results.append(make_result(FAIL, "manifest must be a JSON object (id -> entry)"))
        return results

    if not LAUNCH_SCHEMA_PATH.exists():
        results.append(make_result(FAIL, f"launch schema missing: {LAUNCH_SCHEMA_PATH}"))
        return results

    try:
        schema = json.loads(LAUNCH_SCHEMA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        results.append(make_result(FAIL, f"launch schema JSON parse error: {exc}"))
        return results

    valid_types = set(schema.keys()) if isinstance(schema, dict) else set()

    entries_ok = 0
    for eid, entry in manifest.items():
        entry_ok = True
        for field in ("type", "file", "title", "desc", "data_files", "deps"):
            if field not in entry:
                results.append(make_result(FAIL, f"{eid}: missing field '{field}'"))
                entry_ok = False
        if not entry_ok:
            continue

        if entry["type"] not in valid_types:
            results.append(make_result(
                FAIL,
                f"{eid}: type '{entry['type']}' not in launch_schema "
                f"({', '.join(sorted(valid_types))})",
            ))
            entry_ok = False

        script_path = CODE_DIR / entry["file"]
        if not script_path.exists():
            results.append(make_result(FAIL, f"{eid}: script not found -> {script_path}"))
            entry_ok = False

        for df in entry.get("data_files", []):
            df_path = RAW_DATA_DIR / df
            if not df_path.exists():
                results.append(make_result(FAIL, f"{eid}: data file missing -> {df_path}"))
                entry_ok = False

        if entry_ok:
            entries_ok += 1

    results.append(make_result(
        PASS, f"manifest entries: {entries_ok}/{len(manifest)} valid",
    ))

    known_files = {entry.get("file") for entry in manifest.values()}
    for py_file in sorted(CODE_DIR.glob("*.py")):
        if py_file.name not in known_files:
            results.append(make_result(
                WARN, f"undeclared script: {py_file.name} (not in manifest)",
            ))

    for nb_file in sorted(CODE_DIR.glob("ch*-exercise-*.ipynb")):
        if nb_file.name not in known_files:
            results.append(make_result(
                WARN, f"undeclared notebook: {nb_file.name} (not in manifest)",
            ))

    return results
