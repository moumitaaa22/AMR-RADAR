"""Explainable Surveillance Alerts page for AMR RADAR."""

import streamlit as st

from modules.alerts import generate_surveillance_alerts
from modules.session_state import apply_amr_radar_theme, render_brand_banner, render_sidebar_filters

st.set_page_config(page_title="Surveillance Alerts · AMR RADAR", layout="wide")
apply_amr_radar_theme()
render_brand_banner()
st.title("Surveillance Alert System")

st.info(
    "Analytical Surveillance Flags Only: These flags highlight statistical patterns and data-quality "
    "warnings for laboratory investigation. They are NOT patient emergencies or treatment advice."
)

filtered_df, full_df, summary = render_sidebar_filters()

if summary.get("format") == "aggregated":
    st.warning("Surveillance threshold alerts for Format B:")
    thresh = st.slider("Resistance threshold (%)", 10, 90, 50, 5)
    flagged = filtered_df[filtered_df["Resistant_Pct"] >= thresh]
    st.dataframe(flagged, use_container_width=True)
    st.stop()

c1, c2, c3 = st.columns(3)
with c1:
    thresh = st.slider("Resistance threshold (%)", 10, 90, 50, 5)
with c2:
    min_n = st.slider("Minimum isolates for threshold alert", 3, 40, 10, 1)
with c3:
    trend_pp = st.slider("Temporal upward shift (pp)", 5, 40, 15, 5)

alerts = generate_surveillance_alerts(
    filtered_df,
    full_df,
    resistance_threshold_pct=float(thresh),
    min_sample_for_threshold=int(min_n),
    trend_delta_threshold_pct=float(trend_pp),
)

if not alerts:
    st.success("No surveillance alerts triggered under the active thresholds.")
else:
    for a in alerts:
        with st.container(border=True):
            st.markdown(
                f"**[{a['severity']}] {a['category']}** · `{a['id']}` · "
                f"**{a['organism']} / {a['antibiotic']}** (n = {a['supporting_n']})"
            )
            st.write(f"**Detected:** {a['what_detected']}")
            st.caption(f"**Why flagged:** {a['why_generated']}")
