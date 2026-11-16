"""Antibiotic Resistance Analytics and Interactive Resistance Heatmap page."""

import streamlit as st

from modules.analytics import compute_grouped_resistance, compute_resistance_heatmap
from modules.session_state import apply_amr_radar_theme, render_brand_banner, render_sidebar_filters
from modules.visualizations import (
    plot_resistance_bars,
    plot_resistance_heatmap,
    plot_sir_stacked,
)

st.set_page_config(page_title="Resistance Analytics · AMR RADAR", layout="wide")
apply_amr_radar_theme()
render_brand_banner()
st.title("Antibiotic Resistance Analytics & Heatmap")

filtered_df, _, summary = render_sidebar_filters()

if filtered_df.empty:
    st.warning("No valid records match the active filters.")
    st.stop()

st.info(
    "Formula: Resistance % = Resistant / (Susceptible + Intermediate + Resistant) × 100. "
    "Missing or invalid results are never treated as Susceptible."
)

if summary.get("format") == "aggregated":
    st.dataframe(filtered_df, use_container_width=True)
    st.stop()

min_n = st.slider("Minimum sample size (n) filter", min_value=1, max_value=50, value=1)
ab_df = compute_grouped_resistance(filtered_df, "Antibiotic")
ab_df_filtered = ab_df[ab_df["Total_Tested"] >= min_n]
org_df = compute_grouped_resistance(filtered_df, "Organism")
org_df_filtered = org_df[org_df["Total_Tested"] >= min_n]

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(
        plot_resistance_bars(ab_df_filtered, "Antibiotic", "Antibiotic-Wise Resistance %"),
        use_container_width=True,
    )
with c2:
    st.plotly_chart(
        plot_resistance_bars(org_df_filtered, "Organism", "Organism-Wise Resistance %"),
        use_container_width=True,
    )

st.plotly_chart(
    plot_sir_stacked(ab_df_filtered, "Antibiotic", "S / I / R Distribution by Antibiotic"),
    use_container_width=True,
)

st.divider()
st.subheader("Interactive Organism × Antibiotic Resistance Heatmap")
pct_mat, count_mat = compute_resistance_heatmap(filtered_df)
if pct_mat.empty:
    st.warning("Insufficient data to generate the Resistance Heatmap.")
else:
    if (count_mat.values[(count_mat.values > 0) & (count_mat.values < 30)]).size > 0:
        st.warning("Cells marked with * have sample sizes n < 30; interpret percentages with caution.")
    st.plotly_chart(plot_resistance_heatmap(pct_mat, count_mat), use_container_width=True)

st.subheader("Comparison Table with Sample-Size Indicators")
st.dataframe(ab_df_filtered, use_container_width=True)
