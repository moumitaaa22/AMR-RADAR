"""AMR RADAR — Streamlit Home & Platform Entrypoint."""

from pathlib import Path
import streamlit as st

from config import APP_FULL_NAME, APP_TAGLINE, APP_TITLE, DISCLAIMER_TEXT
from modules.session_state import (
    apply_amr_radar_theme,
    ensure_session_data,
    load_icmr_demo_into_session,
)

st.set_page_config(
    page_title=f"{APP_TITLE} — {APP_FULL_NAME}",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_amr_radar_theme()
ensure_session_data()

logo_path = Path(__file__).parent / "assets" / "logo.png"

col_logo, col_head = st.columns([1, 6])
with col_logo:
    if logo_path.exists():
        st.image(str(logo_path), width=88)
with col_head:
    st.title(APP_TITLE)
    st.subheader(APP_TAGLINE)
    st.caption(APP_FULL_NAME)

st.warning(DISCLAIMER_TEXT)

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Open Overview Dashboard", type="primary", use_container_width=True):
        st.switch_page("pages/01_Overview.py")
with col2:
    if st.button("Load Synthetic Format A Demo", use_container_width=True):
        st.session_state.pop("processed_df", None)
        ensure_session_data()
        st.success("Synthetic Format A demonstration dataset loaded.")
with col3:
    if st.button("Load ICMR-Format B Demo", use_container_width=True):
        load_icmr_demo_into_session()
        st.success("Format B aggregated demonstration dataset loaded.")

st.divider()

c1, c2 = st.columns(2)
with c1:
    st.markdown("### What is Antimicrobial Resistance (AMR)?")
    st.write(
        "Antimicrobial resistance occurs when bacteria and other microorganisms evolve to "
        "withstand medicines designed to inhibit them. Surveillance platforms aggregate "
        "laboratory Susceptible (S), Intermediate (I), and Resistant (R) results to monitor "
        "resistance patterns across organisms, antibiotics, time, and sentinel sites."
    )
    st.markdown("### Project Objectives")
    st.markdown(
        "- Validate and audit uploaded laboratory CSV, Excel, and Stata `.dta` datasets\n"
        "- Compute verified Resistance % = `R / (S + I + R) × 100` without imputing missing values as Susceptible\n"
        "- Compare organisms, antibiotics, and sentinel locations\n"
        "- Surface explainable surveillance flags and export PDF/Excel/CSV reports"
    )

with c2:
    st.markdown("### Key Platform Capabilities")
    st.markdown(
        "1. **Dual-Format Support**: Individual susceptibility records (Format A) and published aggregated counts (Format B)\n"
        "2. **Interactive Resistance Heatmap**: Organism × Antibiotic resistance matrix with tested counts `n`\n"
        "3. **Explainable Alert System**: Threshold breaches, temporal drift, small-sample warnings (`n < 30`), and quality flags\n"
        "4. **ReportLab PDF & OpenPyXL Excel**: Structured surveillance briefs with methodology and limitations"
    )
    summary = st.session_state["summary"]
    st.info(
        f"**Active Dataset:** {summary['dataset_name']} · "
        f"{summary['accepted_count']} accepted · {summary['rejected_count']} rejected · "
        f"{summary['flagged_duplicate_count']} duplicates"
    )
