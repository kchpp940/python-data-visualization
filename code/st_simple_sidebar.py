import streamlit as st

from st_charts import render_charts, show_empty_result, show_summary_metrics
from st_filters import apply_filters, is_empty, load_data, render_filter_widgets

df = load_data()

st.title("Simple Sidebar Example")

with st.sidebar:
    st.header("Filters")
    filter_state = render_filter_widgets(df, container=st.sidebar)

plot_df = apply_filters(df, filter_state)

if is_empty(plot_df):
    show_empty_result()
else:
    show_summary_metrics(plot_df, container=st)
    render_charts(plot_df)
