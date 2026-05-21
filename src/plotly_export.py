"""Plotly 静态导出: 生成图表并保存为 PNG/JPEG/PDF。

直接依赖: plotly, kaleido, pandas
"""

import pandas as pd
import plotly.express as px


def make_figure(df):
    return px.bar(
        df,
        x="category",
        y="value",
        color="category",
        title="Static Plotly Export",
    )


if __name__ == "__main__":
    df = pd.DataFrame({
        "category": ["Alpha", "Beta", "Gamma", "Delta"],
        "value": [28, 55, 43, 91],
    })
    fig = make_figure(df)

    # 静态导出 —— 需要 kaleido
    fig.write_image("../data/plotly_chart.png")
    fig.write_image("../data/plotly_chart.jpeg")
    fig.write_image("../data/plotly_chart.pdf")
    fig.write_html("../data/plotly_chart.html")

    print("Exported plotly_chart.png/.jpeg/.pdf/.html to ../data/")
