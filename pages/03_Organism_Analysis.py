"""Organism Intelligence page for AMR RADAR."""

import streamlit as st

from modules.analytics import compute_grouped_resistance, compute_overall_sir
from modules.session_state import apply_amr_radar_theme, render_brand_banner, render_sidebar_filters
from modules.visualizations import plot_resistance_bars, plot_sir_stacked

st.set_page_config(page_title="Organism Analysis · AMR RADAR", layout="wide")
apply_amr_radar_theme()
render_brand_banner()
st.title("Organism Intelligence")

filtered_df, _, summary = render_sidebar_filters()

if filtered_df.empty:
    st.warning("No valid records match the active filters.")
    st.stop()

if summary.get("format") == "aggregated":
    orgs = sorted(filtered_df["Organism"].unique())
    selected = st.selectbox("Select Organism", orgs)
    sub = filtered_df[filtered_df["Organism"] == selected]
    st.dataframe(sub, use_container_width=True)
    st.stop()

orgs = sorted(filtered_df["Organism"].unique())
search = st.text_input("Search organism", value="")
matching = [o for o in orgs if search.strip().lower() in o.lower()] if search.strip() else orgs

if not matching:
    st.info("No organism matches your search.")
    st.stop()

selected_org = st.selectbox("Select Organism", matching)
org_df = filtered_df[filtered_df["Organism"] == selected_org]
overall = compute_overall_sir(org_df)

c1, c2, c3 = st.columns(3)
c1.metric("Tested Records (n)", overall["total_tested"])
c2.metric("Overall Resistance %", f"{overall['resistance_pct']:.1f}%")
c3.metric("Antibiotics Tested", org_df["Antibiotic"].nunique())

ab_df = compute_grouped_resistance(org_df, "Antibiotic")
loc_df = compute_grouped_resistance(org_df, "Location")

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(
        plot_resistance_bars(ab_df, "Antibiotic", f"{selected_org} — Resistance % by Antibiotic"),
        use_container_width=True,
    )
with col2:
    st.plotly_chart(
        plot_sir_stacked(ab_df, "Antibiotic", f"{selected_org} — S/I/R Distribution"),
        use_container_width=True,
    )

st.subheader(f"Location-Wise Comparison — {selected_org}")
st.dataframe(loc_df, use_container_width=True)
