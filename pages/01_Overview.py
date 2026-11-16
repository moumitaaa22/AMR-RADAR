"""Overview Dashboard page for AMR RADAR."""

import streamlit as st

from modules.analytics import (
    compute_grouped_resistance,
    compute_overall_sir,
    compute_time_trends,
)
from modules.session_state import apply_amr_radar_theme, render_brand_banner, render_sidebar_filters
from modules.visualizations import plot_resistance_bars, plot_sir_stacked, plot_trend_line

st.set_page_config(page_title="Overview · AMR RADAR", layout="wide")
apply_amr_radar_theme()
render_brand_banner()
st.title("Overview Dashboard")

filtered_df, full_df, summary = render_sidebar_filters()

if summary.get("format") == "aggregated":
    st.info("Format B (Aggregated Surveillance Summary) active. Showing published denominators and percentages.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Summary Rows", len(filtered_df))
    c2.metric("Reported Isolates (Sum n)", int(filtered_df["Tested_Count"].sum()))
    c3.metric("Organisms", filtered_df["Organism"].nunique())
    c4.metric("Antibiotics", filtered_df["Antibiotic"].nunique())
    st.dataframe(filtered_df, use_container_width=True)
    st.stop()

overall = compute_overall_sir(filtered_df)
org_df = compute_grouped_resistance(filtered_df, "Organism")
ab_df = compute_grouped_resistance(filtered_df, "Antibiotic")
loc_count = filtered_df["Location"].replace("Unspecified", "").loc[lambda s: s != ""].nunique()
quality_warnings = (
    int(summary.get("rejected_count", 0))
    + int(summary.get("flagged_duplicate_count", 0))
    + int(summary.get("warning_count", 0))
)

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Valid Records", overall["total_tested"])
m2.metric("Organisms", len(org_df))
m3.metric("Antibiotics", len(ab_df))
m4.metric("Locations", int(loc_count))
m5.metric("Overall Resistance %", f"{overall['resistance_pct']:.1f}%")
m6.metric("Data-Quality Warnings", quality_warnings)

col_left, col_right = st.columns(2)
with col_left:
    st.plotly_chart(
        plot_sir_stacked(org_df, "Organism", "Most Frequently Recorded Organisms (S/I/R)"),
        use_container_width=True,
    )
with col_right:
    st.plotly_chart(
        plot_resistance_bars(ab_df, "Antibiotic", "Resistance % by Antibiotic"),
        use_container_width=True,
    )

trend_df = compute_time_trends(filtered_df, "month")
st.plotly_chart(
    plot_trend_line(trend_df, "Monthly Resistance Trajectory (%)"),
    use_container_width=True,
)

with st.expander("Data-Quality Overview & Audit Summary"):
    st.write(
        f"**Raw rows:** {summary.get('total_raw_rows', len(full_df))} · "
        f"**Accepted:** {summary.get('accepted_count', 0)} · "
        f"**Rejected:** {summary.get('rejected_count', 0)} · "
        f"**Flagged Duplicates:** {summary.get('flagged_duplicate_count', 0)}"
    )
    st.dataframe(full_df[full_df["Validation_Status"] != "valid"], use_container_width=True)
