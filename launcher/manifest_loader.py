"""Load and validate ``examples_manifest.json``.

The manifest is a JSON object mapping an example id (e.g. ``"st-2"``) to a
record that describes *what* the example is and *what it needs* to run:

.. code-block:: json

   {
     "st-2": {
       "type": "dash | streamlit | notebook | script",
       "file": "script_file.py",
       "title": "显示名",
       "desc": "一句话描述",
       "data_files": ["EPA_fuel_economy_summary.csv"],
       "deps": ["pandas", "plotly"]
     }
   }

All paths are relative to the project layout — see
:data:`data_paths.CODE_DIR` and :data:`data_paths.RAW_DATA_DIR`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from data_paths import CODE_DIR, RAW_DATA_DIR, REPO_ROOT

MANIFEST_PATH: Path = REPO_ROOT / "examples_manifest.json"
LAUNCH_SCHEMA_PATH: Path = REPO_ROOT / "launch_schema.json"

_REQUIRED_KEYS = ("type", "file", "title", "desc", "data_files", "deps")


class ManifestError(ValueError):
    """Raised when the manifest is missing or malformed."""


@dataclass(frozen=True)
class ManifestEntry:
    """A single example record from the manifest."""

    example_id: str
    type: str
    file: str
    title: str
    desc: str
    data_files: List[str] = field(default_factory=list)
    deps: List[str] = field(default_factory=list)

    @property
    def script_path(self) -> Path:
        return CODE_DIR / self.file

    @property
    def data_paths(self) -> List[Path]:
        return [RAW_DATA_DIR / name for name in self.data_files]

    def to_dict(self) -> Dict[str, object]:
        return {
            "type": self.type,
            "file": self.file,
            "title": self.title,
            "desc": self.desc,
            "data_files": list(self.data_files),
            "deps": list(self.deps),
        }


def _validate_record(example_id: str, raw: object) -> Dict[str, object]:
    if not isinstance(raw, dict):
        raise ManifestError(f"[{example_id}] 记录必须是对象")

    missing = [k for k in _REQUIRED_KEYS if k not in raw]
    if missing:
        raise ManifestError(
            f"[{example_id}] 缺少必填字段: {', '.join(missing)}"
        )

    if not isinstance(raw["type"], str) or not raw["type"]:
        raise ManifestError(f"[{example_id}] type 必须是非空字符串")

    for list_key in ("data_files", "deps"):
        value = raw[list_key]
        if not isinstance(value, list) or not all(
            isinstance(v, str) for v in value
        ):
            raise ManifestError(
                f"[{example_id}] {list_key} 必须是字符串数组"
            )

    return raw  # type: ignore[return-value]


def load_manifest(path: Path = MANIFEST_PATH) -> Dict[str, ManifestEntry]:
    """Load ``examples_manifest.json`` and return validated entries.

    Raises :class:`ManifestError` when the file is missing or malformed.
    """

    if not path.is_file():
        raise ManifestError(f"未找到 manifest 文件: {path}")

    with path.open("r", encoding="utf-8") as fh:
        raw_data = json.load(fh)

    if not isinstance(raw_data, dict):
        raise ManifestError("manifest 根节点必须是对象")

    entries: Dict[str, ManifestEntry] = {}
    for example_id, raw in raw_data.items():
        rec = _validate_record(example_id, raw)
        entries[example_id] = ManifestEntry(
            example_id=example_id,
            type=str(rec["type"]),
            file=str(rec["file"]),
            title=str(rec["title"]),
            desc=str(rec["desc"]),
            data_files=list(rec["data_files"]),
            deps=list(rec["deps"]),
        )

    return entries


@dataclass(frozen=True)
class LaunchSchema:
    """A resolved launch schema entry for a single example type.

    Attributes:
        type_name: The manifest ``type`` this schema applies to.
        command: The executable template (usually ``{python}``).
        args_template: Argument templates with ``{python}`` / ``{file}`` /
            ``{cwd}`` placeholders.
        cwd: Working directory relative to ``REPO_ROOT``.
        check_package: Python package that must be importable for this schema
            to be usable (``None`` means always usable).
        fallbacks: Alternative schemas tried when ``check_package`` is not
            available.
    """

    type_name: str
    command: str
    args_template: List[str]
    cwd: str
    check_package: Optional[str]
    fallbacks: List["LaunchSchema"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type_name": self.type_name,
            "command": self.command,
            "args_template": list(self.args_template),
            "cwd": self.cwd,
            "check_package": self.check_package,
            "fallbacks": [f.to_dict() for f in self.fallbacks],
        }


def _build_launch_schema(type_name: str, raw: Dict[str, Any]) -> LaunchSchema:
    """Construct a :class:`LaunchSchema` (recursively for fallbacks)."""

    for key in ("command", "args_template"):
        if key not in raw:
            raise ManifestError(
                f"[launch_schema:{type_name}] 缺少必填字段: {key}"
            )

    if not isinstance(raw["args_template"], list) or not all(
        isinstance(v, str) for v in raw["args_template"]
    ):
        raise ManifestError(
            f"[launch_schema:{type_name}] args_template 必须是字符串数组"
        )

    check_pkg = raw.get("check_package")
    if check_pkg is not None and not isinstance(check_pkg, str):
        raise ManifestError(
            f"[launch_schema:{type_name}] check_package 必须是字符串或 null"
        )

    fallbacks_raw = raw.get("fallbacks", [])
    if not isinstance(fallbacks_raw, list):
        raise ManifestError(
            f"[launch_schema:{type_name}] fallbacks 必须是数组"
        )

    fallbacks = [
        _build_launch_schema(f"{type_name}#fb{idx}", fb)
        for idx, fb in enumerate(fallbacks_raw)
    ]

    return LaunchSchema(
        type_name=type_name,
        command=str(raw["command"]),
        args_template=list(raw["args_template"]),
        cwd=str(raw.get("cwd", "code")),
        check_package=check_pkg,
        fallbacks=fallbacks,
    )


def load_launch_schema(path: Path = LAUNCH_SCHEMA_PATH) -> Dict[str, LaunchSchema]:
    """Load ``launch_schema.json`` and return validated schemas keyed by type.

    Raises :class:`ManifestError` when the file is missing or malformed.
    """

    if not path.is_file():
        raise ManifestError(f"未找到 launch schema 文件: {path}")

    with path.open("r", encoding="utf-8") as fh:
        raw_data = json.load(fh)

    if not isinstance(raw_data, dict):
        raise ManifestError("launch schema 根节点必须是对象")

    schemas: Dict[str, LaunchSchema] = {}
    for type_name, raw in raw_data.items():
        if not isinstance(raw, dict):
            raise ManifestError(f"[launch_schema:{type_name}] 必须是对象")
        schemas[type_name] = _build_launch_schema(type_name, raw)

    return schemas
