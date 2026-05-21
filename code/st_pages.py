import streamlit as st
from st_filters import load_data, FilterState, render_filters, filter_data
from st_charts import (
    calc_avg_fuel_cost,
    render_metric,
    create_histogram,
    create_altair_chart,
)


def build_page(filter_target):
    df = load_data()
    filter_state = FilterState(df)

    make, year_range = render_filters(filter_state, target=filter_target)
    plot_df = filter_data(df, make, year_range)

    avg = calc_avg_fuel_cost(plot_df)
    render_metric(avg, target=filter_target)

    histogram = create_histogram(plot_df)
    altair_chart = create_altair_chart(plot_df)

    st.title("Fuel Economy Explorer")
    st.write(histogram)
    st.write(altair_chart)
    st.write("Sample data", plot_df.head(10))
