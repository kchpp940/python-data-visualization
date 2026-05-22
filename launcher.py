"""Unified launcher for python-data-visualization examples.

This is a thin entry point — all logic lives in the ``launcher`` package:

* :mod:`launcher.manifest_loader` — reads ``examples_manifest.json`` and
  ``launch_schema.json``
* :mod:`launcher.checker` — dependency / data / entry-script / launcher checks
* :mod:`launcher.runner` — build & execute startup commands (100 % schema-driven)
* :mod:`launcher.cli` — command-line parsing and interactive picker

To add a new example, edit ``examples_manifest.json``.
To change how a type starts, edit ``launch_schema.json``.
No code changes needed in either case.
"""

from __future__ import annotations

import sys

from launcher.cli import main

if __name__ == "__main__":
    sys.exit(main())
