"""Reports and Exports page (PDF, Excel, CSV) for AMR RADAR."""

import streamlit as st

from modules.alerts import generate_surveillance_alerts
from modules.reports import build_excel_report, build_pdf_report
from modules.session_state import apply_amr_radar_theme, render_brand_banner, render_sidebar_filters

st.set_page_config(page_title="Reports · AMR RADAR", layout="wide")
apply_amr_radar_theme()
render_brand_banner()
st.title("Reports and Exports")

filtered_df, full_df, summary = render_sidebar_filters()
alerts = (
    generate_surveillance_alerts(filtered_df, full_df)
    if summary.get("format") != "aggregated"
    else []
)

c1, c2, c3 = st.columns(3)
with c1:
    pdf_bytes = build_pdf_report(filtered_df, full_df, summary, alerts)
    st.download_button(
        label="Download PDF Surveillance Report",
        data=pdf_bytes,
        file_name="AMR_RADAR_Surveillance_Report.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )
with c2:
    xlsx_bytes = build_excel_report(filtered_df, full_df, summary, alerts)
    st.download_button(
        label="Download Excel Analytical Workbook (.xlsx)",
        data=xlsx_bytes,
        file_name="AMR_RADAR_Analytical_Export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
with c3:
    st.download_button(
        label="Download Cleaned CSV",
        data=full_df.to_csv(index=False).encode("utf-8"),
        file_name="AMR_RADAR_Cleaned_Records.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.divider()
st.subheader("Report Metadata Summary")
st.json(summary)
