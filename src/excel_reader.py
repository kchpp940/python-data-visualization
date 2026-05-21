"""Excel 读取工具: 批量读取 xlsx/xls 文件并做基础汇总。

直接依赖: pandas, openpyxl
"""

import pandas as pd


def read_excel_safe(path, sheet_name=0):
    """读取 Excel；xlsx 用 openpyxl，xls 用 xlrd (若可用)。"""
    if str(path).lower().endswith(".xlsx"):
        return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")
    return pd.read_excel(path, sheet_name=sheet_name)


if __name__ == "__main__":
    import sys
    for f in sys.argv[1:]:
        df = read_excel_safe(f)
        print(f"--- {f} ---")
        print(df.describe())
