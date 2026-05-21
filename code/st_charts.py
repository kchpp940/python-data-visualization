from __future__ import annotations

import altair as alt
import pandas as pd
import plotly.express as px
import streamlit as st


def show_empty_result() -> None:
    st.warning(
        "⚠️ No data matches the selected filters. "
        "Please adjust your filter criteria and try again."
    )


def show_summary_metrics(plot_df: pd.DataFrame, container=st) -> None:
    col1, col2, col3, col4 = container.columns(4)
    with col1:
        container.metric("Records", f"{len(plot_df):,}")
    with col2:
        avg_fuel_cost = plot_df["fuelCost08"].mean().round(0)
        container.metric("Avg Annual Fuel Cost", f"${avg_fuel_cost:,.0f}")
    with col3:
        avg_comb_mpg = plot_df["comb08"].mean().round(1)
        container.metric("Avg Combined MPG", f"{avg_comb_mpg}")
    with col4:
        container.metric("Unique Makes", f"{plot_df['make'].nunique()}")


def render_charts(plot_df: pd.DataFrame) -> None:
    fig_hist = px.histogram(
        plot_df,
        x="fuelCost08",
        color="class_summary",
        labels={"fuelCost08": "Annual Fuel Cost (USD)"},
        nbins=40,
        title="Fuel Cost Distribution by Vehicle Class",
    )
    fig_hist.update_layout(bargap=0.1)

    altair_chart = (
        alt.Chart(plot_df)
        .mark_tick()
        .encode(
            y=alt.Y("fuel_type_summary", title="Fuel Type"),
            x=alt.X("barrels08", title="Annual Petroleum Consumption (barrels)"),
            color=alt.Color("class_summary", title="Vehicle Class"),
        )
        .properties(width=600, height=300)
    )

    st.write(fig_hist)
    st.write(altair_chart)

    with st.expander("View Sample Data"):
        st.dataframe(
            plot_df[
                [
                    "make", "model", "year", "transmission",
                    "fuel_type_summary", "class_summary", "comb08", "fuelCost08",
                ]
            ].head(10),
            use_container_width=True,
        )
