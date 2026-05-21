"""Altair 静态导出: 生成图表并保存为 PNG/SVG/HTML。

直接依赖: altair, vl-convert-python, pandas
"""

import altair as alt
import pandas as pd


def make_chart(df):
    return alt.Chart(df).mark_bar().encode(
        x="category",
        y="value",
        color="category",
    ).properties(title="Static Altair Export")


if __name__ == "__main__":
    df = pd.DataFrame({
        "category": ["Alpha", "Beta", "Gamma", "Delta"],
        "value": [28, 55, 43, 91],
    })
    chart = make_chart(df)

    # 静态导出 —— 需要 vl-convert-python
    chart.save("../data/chart.png")   # PNG
    chart.save("../data/chart.svg")   # SVG
    chart.save("../data/chart.html")  # interactive HTML

    print("Exported chart.png / chart.svg / chart.html to ../data/")
