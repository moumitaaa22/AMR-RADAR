"""Shared Streamlit session state initialization and UI helpers for AMR RADAR."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd
import streamlit as st

from config import APP_FULL_NAME, APP_TAGLINE, APP_TITLE, DISCLAIMER_TEXT
from modules.data_loader import load_csv_path
from modules.data_processing import (
    filter_records,
    process_aggregated_dataset,
    process_individual_dataset,
    suggest_individual_mapping,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"



def apply_amr_radar_theme() -> None:
    """Apply consistent, readable styling across AMR RADAR."""
    st.markdown(
        """
        <style>
        /* Main dashboard text */
        [data-testid="stMain"] {
            color: #111111 !important;
        }

        /* Metric labels and values */
        [data-testid="stMetricLabel"] *,
        [data-testid="stMetricValue"] *,
        [data-testid="stMetricDelta"] * {
            color: #111111 !important;
            -webkit-text-fill-color: #111111 !important;
        }

        /* Plotly chart text */
        .js-plotly-plot .plotly text {
            fill: #111111 !important;
        }

        /* White metric cards */
        div[data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #DCE3EA;
            padding: 14px 16px;
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )




def ensure_session_data() -> None:
    """Load the synthetic demonstration dataset on first run so all pages work immediately."""
    if "processed_df" in st.session_state and "summary" in st.session_state:
        return

    sample_path = DATA_DIR / "sample_amr.csv"
    raw_df = load_csv_path(sample_path)
    mapping = suggest_individual_mapping(list(raw_df.columns))
    processed_df, summary = process_individual_dataset(
        raw_df,
        mapping,
        dataset_name="Synthetic AMR Sentinel Demo (2024-2025)",
    )
    st.session_state["raw_df"] = raw_df
    st.session_state["processed_df"] = processed_df
    st.session_state["summary"] = summary
    st.session_state["source_label"] = "Synthetic Demonstration Dataset (Fictional — Non-Clinical)"


def load_icmr_demo_into_session() -> None:
    """Load the Format B aggregated demo dataset into session state."""
    icmr_path = DATA_DIR / "icmr_sample_aggregated.csv"
    raw_df = load_csv_path(icmr_path)
    processed_df, summary = process_aggregated_dataset(
        raw_df,
        dataset_name="ICMR-Style Aggregated Network Demo (Format B)",
    )
    st.session_state["raw_df"] = raw_df
    st.session_state["processed_df"] = processed_df
    st.session_state["summary"] = summary
    st.session_state["source_label"] = "Synthetic Format-B Demo (Modelled on Aggregated Summaries)"


def render_sidebar_filters() -> Tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Render standard sidebar provenance and filters; return (filtered_df, full_df, summary)."""
    ensure_session_data()
    full_df: pd.DataFrame = st.session_state["processed_df"]
    summary: dict = st.session_state["summary"]

    st.sidebar.markdown(f"### {APP_TITLE}")
    st.sidebar.caption(APP_TAGLINE)
    st.sidebar.markdown(f"**Active:** {summary.get('dataset_name', 'Dataset')}")
    st.sidebar.caption(st.session_state.get("source_label", ""))

    if summary.get("format") == "aggregated":
        return full_df[full_df["Validation_Status"] == "valid"].copy(), full_df, summary

    valid_pool = full_df[full_df["Validation_Status"] != "rejected"]
    orgs = sorted([o for o in valid_pool["Organism"].unique() if o])
    abs_list = sorted([a for a in valid_pool["Antibiotic"].unique() if a])
    locs = sorted([l for l in valid_pool["Location"].unique() if l])

    sel_orgs = st.sidebar.multiselect("Filter Organisms", orgs, default=[])
    sel_abs = st.sidebar.multiselect("Filter Antibiotics", abs_list, default=[])
    sel_locs = st.sidebar.multiselect("Filter Locations", locs, default=[])
    exclude_dupes = st.sidebar.checkbox("Exclude Flagged Duplicates", value=True)

    filtered = filter_records(
        full_df,
        organisms=sel_orgs or None,
        antibiotics=sel_abs or None,
        locations=sel_locs or None,
        exclude_duplicates=exclude_dupes,
    )
    st.sidebar.info(DISCLAIMER_TEXT)
    return filtered, full_df, summary


def render_brand_banner() -> None:
    st.caption(f"{APP_TITLE} · {APP_FULL_NAME} · Research & Surveillance Only")
