"""Data Upload & Validation page for AMR RADAR (CSV, XLSX, XLS, Stata .dta)."""

from pathlib import Path
import streamlit as st

from modules.data_loader import detect_dataset_format, load_tabular_file
from modules.data_processing import (
    process_aggregated_dataset,
    process_individual_dataset,
    suggest_individual_mapping,
)
from modules.session_state import apply_amr_radar_theme, render_brand_banner, render_sidebar_filters

st.set_page_config(page_title="Data Upload · AMR RADAR", layout="wide")
apply_amr_radar_theme()
render_brand_banner()
st.title("Data Upload & Validation")

_, full_df, summary = render_sidebar_filters()

template_path = Path(__file__).resolve().parent.parent / "data" / "amr_template.csv"
if template_path.exists():
    st.download_button(
        label="Download Standard CSV Template",
        data=template_path.read_bytes(),
        file_name="amr_radar_template.csv",
        mime="text/csv",
    )

uploaded = st.file_uploader(
    "Upload laboratory dataset (.csv, .xlsx, .xls, or .dta)",
    type=["csv", "xlsx", "xls", "dta"],
)

if uploaded is not None:
    try:
        raw_df, file_meta = load_tabular_file(uploaded, uploaded.name)
        st.success(f"Loaded '{uploaded.name}' with {len(raw_df)} rows and {len(raw_df.columns)} columns.")
        detected_format = detect_dataset_format(list(raw_df.columns))
        fmt_choice = st.radio(
            "Dataset Format",
            options=["individual", "aggregated"],
            index=0 if detected_format == "individual" else 1,
            format_func=lambda x: (
                "Format A: Individual Susceptibility Records"
                if x == "individual"
                else "Format B: Aggregated Surveillance Statistics (e.g., ICMR Summary)"
            ),
            horizontal=True,
        )

        source_label = st.text_input("Dataset Source Attribution", value=f"Uploaded File ({uploaded.name})")

        if fmt_choice == "individual":
            suggested = suggest_individual_mapping(list(raw_df.columns))
            cols_opts = ["(Not mapped)"] + list(raw_df.columns)

            def select_col(label: str, key: str):
                default_val = suggested.get(key)
                idx = cols_opts.index(default_val) if default_val in cols_opts else 0
                choice = st.selectbox(label, cols_opts, index=idx, key=f"map_{key}")
                return None if choice == "(Not mapped)" else choice

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                m_org = select_col("Organism *", "Organism")
                m_sid = select_col("Sample_ID", "Sample_ID")
            with c2:
                m_ab = select_col("Antibiotic *", "Antibiotic")
                m_date = select_col("Date", "Date")
            with c3:
                m_res = select_col("Result (S/I/R) *", "Result")
                m_loc = select_col("Location", "Location")
            with c4:
                m_lab = select_col("Laboratory", "Laboratory")
                m_std = select_col("Standard", "Standard")

            if st.button("Validate & Load Dataset", type="primary"):
                mapping = {
                    "Sample_ID": m_sid,
                    "Organism": m_org,
                    "Antibiotic": m_ab,
                    "Result": m_res,
                    "Date": m_date,
                    "Location": m_loc,
                    "Laboratory": m_lab,
                    "Standard": m_std,
                }
                processed, new_summary = process_individual_dataset(
                    raw_df, mapping, dataset_name=uploaded.name
                )
                st.session_state["raw_df"] = raw_df
                st.session_state["processed_df"] = processed
                st.session_state["summary"] = new_summary
                st.session_state["source_label"] = source_label
                st.success(
                    f"Accepted: {new_summary['accepted_count']} · Rejected: {new_summary['rejected_count']} · Duplicates: {new_summary['flagged_duplicate_count']}"
                )
        else:
            if st.button("Validate & Load Format B Aggregated Dataset", type="primary"):
                processed, new_summary = process_aggregated_dataset(
                    raw_df, dataset_name=uploaded.name
                )
                st.session_state["raw_df"] = raw_df
                st.session_state["processed_df"] = processed
                st.session_state["summary"] = new_summary
                st.session_state["source_label"] = source_label
                st.success(f"Loaded {new_summary['accepted_count']} aggregated rows.")

        st.subheader("Raw Upload Preview (First 20 rows)")
        st.dataframe(raw_df.head(20), use_container_width=True)
    except Exception as exc:
        st.error(f"Upload error: {exc}")

st.divider()
st.subheader("Active Dataset Audit & Cleaned Export")
st.write(
    f"Active dataset: **{summary.get('dataset_name')}** · Accepted: {summary.get('accepted_count')} · "
    f"Rejected: {summary.get('rejected_count')} · Duplicates: {summary.get('flagged_duplicate_count')}"
)
st.download_button(
    label="Download Cleaned Dataset CSV (with Validation Status)",
    data=full_df.to_csv(index=False).encode("utf-8"),
    file_name="amr_radar_cleaned.csv",
    mime="text/csv",
)
st.dataframe(full_df.head(50), use_container_width=True)
