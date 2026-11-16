"""Trends and Geography page for AMR RADAR."""

import streamlit as st

from modules.analytics import compute_grouped_resistance, compute_time_trends
from modules.session_state import apply_amr_radar_theme, render_brand_banner, render_sidebar_filters
from modules.visualizations import plot_resistance_bars, plot_trend_line

st.set_page_config(page_title="Trends & Geography · AMR RADAR", layout="wide")
apply_amr_radar_theme()
render_brand_banner()
st.title("Trends and Geography")

filtered_df, _, summary = render_sidebar_filters()

if filtered_df.empty:
    st.warning("No valid records match the active filters.")
    st.stop()

if summary.get("format") == "aggregated":
    st.info("Aggregated Format B active. Temporal coordinate mapping is unavailable in summary tables.")
    st.dataframe(filtered_df, use_container_width=True)
    st.stop()

granularity = st.radio("Trend Granularity", options=["month", "year"], horizontal=True)
orgs = ["ALL"] + sorted(filtered_df["Organism"].unique())
abs_list = ["ALL"] + sorted(filtered_df["Antibiotic"].unique())

c1, c2 = st.columns(2)
with c1:
    sel_org = st.selectbox("Scope Organism", orgs)
with c2:
    sel_ab = st.selectbox("Scope Antibiotic", abs_list)

scoped = filtered_df.copy()
if sel_org != "ALL":
    scoped = scoped[scoped["Organism"] == sel_org]
if sel_ab != "ALL":
    scoped = scoped[scoped["Antibiotic"] == sel_ab]

trend_df = compute_time_trends(scoped, granularity=granularity)
st.plotly_chart(
    plot_trend_line(trend_df, f"{granularity.title()}ly Resistance Trend ({sel_org} / {sel_ab})"),
    use_container_width=True,
)

st.divider()
st.subheader("Location-Wise Resistance Comparison")
st.caption(
    "Geographic map policy: AMR RADAR renders maps only when genuine latitude/longitude coordinates "
    "exist in the uploaded dataset. Site labels without coordinates are compared quantitatively below."
)
loc_df = compute_grouped_resistance(scoped, "Location")
st.plotly_chart(
    plot_resistance_bars(loc_df, "Location", "Resistance % by Sentinel Location"),
    use_container_width=True,
)
st.dataframe(loc_df, use_container_width=True)
