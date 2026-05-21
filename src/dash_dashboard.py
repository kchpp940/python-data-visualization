"""Dash dashboard: 读取 Excel 数据并用 Plotly 图表展示。

直接依赖: dash, pandas, openpyxl, plotly
"""

import pandas as pd
from dash import Dash, dcc, html, Input, Output

try:
    df = pd.read_excel("../data/sample.xlsx")
except FileNotFoundError:
    df = pd.DataFrame({"category": ["A", "B", "C"], "value": [10, 20, 30]})

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Sales Dashboard"),
    dcc.Dropdown(
        id="category-filter",
        options=[{"label": c, "value": c} for c in df["category"].unique()],
        value=df["category"].unique().tolist(),
        multi=True,
    ),
    dcc.Graph(id="bar-chart"),
])

@app.callback(Output("bar-chart", "figure"), Input("category-filter", "value"))
def update_chart(selected):
    import plotly.express as px
    filtered = df[df["category"].isin(selected)]
    return px.bar(filtered, x="category", y="value", title="Sales by Category")

if __name__ == "__main__":
    app.run_server(debug=True)
