#!/usr/bin/env python3
"""Developer maintenance command for python-data-visualization.

Consolidates five routine checks into one lightweight entry point::

    python maintenance.py all          # run every check (default, dry-run)
    python maintenance.py profile      # refresh data profile cache
    python maintenance.py readme       # dry-run: report sync status
    python maintenance.py readme --in-place   # update README.md blocks
    python maintenance.py manifest     # validate examples_manifest.json
    python maintenance.py deps         # verify dependency lock-file integrity
    python maintenance.py launcher     # self-check the launcher stack

This module is intentionally thin — it only dispatches to the checker
modules under ``maintenance/`` and aggregates their results.  Each
checker module is self-contained and can also be invoked directly::

    python -m maintenance.profile_checker
    python -m maintenance.readme_updater [--in-place]
    python -m maintenance.manifest_checker
    python -m maintenance.deps_checker
    python -m maintenance.launcher_checker

Exit status is 0 when every requested check passes, 1 otherwise.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from maintenance import (  # noqa: E402
    FAIL, PASS,
    CheckResult,
    colour,
    print_results,
    all_passed,
)

from maintenance import profile_checker  # noqa: E402
from maintenance import readme_updater   # noqa: E402
from maintenance import manifest_checker  # noqa: E402
from maintenance import deps_checker     # noqa: E402
from maintenance import launcher_checker  # noqa: E402


# ---------------------------------------------------------------------------
# Task registry — each entry maps a CLI name to (module, display_name, extra_kwargs)
# extra_kwargs is a dict that will be merged into the module.run() call.
# ---------------------------------------------------------------------------

TASKS: dict[str, tuple[object, str]] = {
    "profile": (profile_checker, "Data Profile Refresh"),
    "readme": (readme_updater, "README Section Update"),
    "manifest": (manifest_checker, "Example Manifest Check"),
    "deps": (deps_checker, "Dependency Lock-File Validation"),
    "launcher": (launcher_checker, "Launcher Self-Check"),
}


def _dispatch(task_key: str, *, in_place: bool = False) -> list[CheckResult]:
    """Call the ``run()`` entry point of the registered checker module.

    ``in_place`` is forwarded only to modules that accept it; others
    ignore the extra kwarg.
    """
    module, _ = TASKS[task_key]
    if task_key == "readme":
        return module.run(in_place=in_place)
    return module.run()


def _print_banner(requested: list[str]) -> None:
    print("=" * 60)
    print(f"  maintenance.py  |  task(s): {', '.join(requested)}")
    print("=" * 60)


def _print_summary(overall_ok: bool) -> None:
    print("\n" + "=" * 60)
    if overall_ok:
        print(f"  [{colour(PASS)}PASS{colour('reset')}] all checks passed")
    else:
        print(f"  [{colour(FAIL)}FAIL{colour('reset')}] some checks failed — review above")
    print("=" * 60)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    # Parse --in-place before task name so it works with 'readme' only
    in_place = "--in-place" in argv
    if in_place:
        argv.remove("--in-place")

    if not argv or argv[0] in ("-h", "--help", "help"):
        _print_banner(list(TASKS.keys()))
        print("\nUsage: python maintenance.py [task] [--in-place]")
        print("\nAvailable tasks:")
        for key, (_, name) in TASKS.items():
            flag = " [--in-place]" if key == "readme" else ""
            print(f"  {key:<10} {name}{flag}")
        print(f"  {'all':<10} run every check (default, dry-run)")
        print("\nOptions:")
        print("  --in-place  Apply README.md block updates (only valid with 'readme')")
        return 0

    task = argv[0]
    if task == "all":
        requested = list(TASKS.keys())
    elif task in TASKS:
        requested = [task]
    else:
        print(f"Unknown task: {task}", file=sys.stderr)
        print(f"Available: all, {', '.join(TASKS.keys())}", file=sys.stderr)
        return 2

    if in_place and "readme" not in requested:
        print("--in-place is only valid with the 'readme' task", file=sys.stderr)
        return 2

    _print_banner(requested)

    overall_ok = True
    for task_key in requested:
        results = _dispatch(task_key, in_place=in_place)
        display_name = TASKS[task_key][1]
        if task_key == "readme":
            display_name += " [--in-place]" if in_place else " [dry-run]"
        print_results(display_name, results)
        if not all_passed(results):
            overall_ok = False

    _print_summary(overall_ok)
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
