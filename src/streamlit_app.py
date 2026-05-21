"""Streamlit app: Excel 数据交互式可视化。

直接依赖: streamlit, pandas, openpyxl, plotly
"""

import pandas as pd
import plotly.express as px
import streamlit as st

st.title("Data Explorer")

uploaded = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])

if uploaded is not None:
    df = pd.read_excel(uploaded)
else:
    df = pd.DataFrame({
        "category": ["A", "B", "C", "D"],
        "value": [12, 19, 7, 15],
        "region": ["N", "S", "E", "W"],
    })

st.dataframe(df)

chart_type = st.radio("Chart type", ["Bar", "Line", "Scatter"])
if chart_type == "Bar":
    st.plotly_chart(px.bar(df, x="category", y="value"))
elif chart_type == "Line":
    st.plotly_chart(px.line(df, x="category", y="value"))
else:
    st.plotly_chart(px.scatter(df, x="category", y="value", size="value"))
