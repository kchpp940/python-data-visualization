"""Manifest-driven launcher for python-data-visualization examples.

Package public surface:

- :mod:`launcher.manifest_loader` — load & validate ``examples_manifest.json``
  and ``launch_schema.json``
- :mod:`launcher.checker` — dependency / data-file / entry-script checks
- :mod:`launcher.runner` — build & execute startup commands from manifest entries
  and launch schema
- :mod:`launcher.cli` — command-line entry point (``list`` / ``check`` / ``run``)
"""

from .manifest_loader import (  # noqa: F401
    LaunchSchema,
    ManifestEntry,
    load_launch_schema,
    load_manifest,
)

__all__ = ["LaunchSchema", "ManifestEntry", "load_launch_schema", "load_manifest"]
