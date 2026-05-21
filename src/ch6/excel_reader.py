"""Safe Excel file reading.

Automatically selects the appropriate engine based on file extension:
- ``.xlsx`` / ``.xlsm`` -> ``openpyxl``
- ``.xls``             -> ``xlrd`` (if installed) or ``openpyxl`` fallback
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import pandas as pd


def read_excel_safe(
    path: Union[str, Path],
    sheet_name: Union[int, str] = 0,
    **kwargs,
) -> pd.DataFrame:
    """Read an Excel file with an engine chosen automatically.

    * ``.xlsx`` / ``.xlsm`` -> ``openpyxl``
    * ``.xls``             -> ``xlrd`` (if installed) or ``openpyxl``
    """
    p = Path(path)
    suffix = p.suffix.lower()
    engine = kwargs.pop("engine", None)
    if engine is None:
        if suffix in (".xlsx", ".xlsm"):
            engine = "openpyxl"
        elif suffix == ".xls":
            try:
                import xlrd  # noqa: F401
                engine = "xlrd"
            except ImportError:  # pragma: no cover
                engine = "openpyxl"
    return pd.read_excel(p, sheet_name=sheet_name, engine=engine, **kwargs)
