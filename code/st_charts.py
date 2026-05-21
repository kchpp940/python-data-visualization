import streamlit as st
import plotly.express as px
import altair as alt


# ---------------------------------------------------------------------------
# 1. 指标计算
# ---------------------------------------------------------------------------
def calc_avg_fuel_cost(plot_df):
    return plot_df["fuelCost08"].mean().round(0)


# ---------------------------------------------------------------------------
# 2. 指标渲染
# ---------------------------------------------------------------------------
def render_metric(value, target=st):
    target.metric("Average", value)


# ---------------------------------------------------------------------------
# 3. 图表创建 - 固定宽度，行为统一
# ---------------------------------------------------------------------------
def create_histogram(plot_df):
    return px.histogram(
        plot_df,
        x="fuelCost08",
        color="class_summary",
        labels={"fuelCost08": "Annual Fuel Cost"},
        nbins=40,
        title="Fuel Cost Distribution",
    )


def create_altair_chart(plot_df):
    return (
        alt.Chart(plot_df)
        .mark_tick()
        .encode(y="fuel_type_summary", x="barrels08")
        .properties(width=600)
    )
