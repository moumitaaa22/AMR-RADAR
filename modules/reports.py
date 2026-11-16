"""PDF (ReportLab) and Excel (OpenPyXL) report generation for AMR RADAR."""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any, Dict, List

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config import APP_FULL_NAME, APP_TITLE, DISCLAIMER_TEXT
from modules.analytics import (
    compute_grouped_resistance,
    compute_overall_sir,
    compute_resistance_heatmap,
)


def build_excel_report(
    filtered_df: pd.DataFrame,
    full_df: pd.DataFrame,
    summary: Dict[str, Any],
    alerts: List[Dict[str, Any]],
) -> bytes:
    """Export multi-sheet Excel analytical workbook."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        meta_df = pd.DataFrame(
            [
                {"Field": "Platform", "Value": f"{APP_TITLE} — {APP_FULL_NAME}"},
                {"Field": "Dataset Name", "Value": summary.get("dataset_name", "Dataset")},
                {"Field": "Date Range", "Value": summary.get("date_range", "")},
                {"Field": "Total Raw Rows", "Value": summary.get("total_raw_rows", len(full_df))},
                {"Field": "Accepted Rows", "Value": summary.get("accepted_count", len(filtered_df))},
                {"Field": "Rejected Rows", "Value": summary.get("rejected_count", 0)},
                {"Field": "Flagged Duplicates", "Value": summary.get("flagged_duplicate_count", 0)},
            ]
        )
        meta_df.to_excel(writer, sheet_name="Dataset_Summary", index=False)
        full_df.to_excel(writer, sheet_name="All_Records_With_Audit", index=False)

        if not filtered_df.empty and "Result" in filtered_df.columns:
            compute_grouped_resistance(filtered_df, "Organism").to_excel(
                writer, sheet_name="Organism_Analysis", index=False
            )
            compute_grouped_resistance(filtered_df, "Antibiotic").to_excel(
                writer, sheet_name="Antibiotic_Analysis", index=False
            )
            pct_mat, _ = compute_resistance_heatmap(filtered_df)
            if not pct_mat.empty:
                pct_mat.round(1).to_excel(writer, sheet_name="Heatmap_Matrix_Pct")

        pd.DataFrame(alerts).to_excel(writer, sheet_name="Surveillance_Alerts", index=False)

    return buf.getvalue()


def build_pdf_report(
    filtered_df: pd.DataFrame,
    full_df: pd.DataFrame,
    summary: Dict[str, Any],
    alerts: List[Dict[str, Any]],
) -> bytes:
    """Generate a structured PDF surveillance report using ReportLab."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"<b>{APP_TITLE}</b> — Surveillance Analytics Report", styles["Title"]))
    story.append(Paragraph(APP_FULL_NAME, styles["Normal"]))
    story.append(
        Paragraph(
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Disclaimer:</b> {DISCLAIMER_TEXT}", styles["Normal"]))
    story.append(Spacer(1, 14))

    overall = compute_overall_sir(filtered_df)
    is_agg = summary.get("format") == "aggregated"
    story.append(Paragraph("<b>1. Dataset &amp; Data-Quality Summary</b>", styles["Heading2"]))
    summary_rows = [
        ["Attribute", "Value"],
        ["Dataset Name", str(summary.get("dataset_name", ""))],
        ["Format", "Format B (Aggregated)" if is_agg else "Format A (Individual)"],
        ["Date Range", str(summary.get("date_range", ""))],
        ["Total Raw Rows", str(summary.get("total_raw_rows", len(full_df)))],
        ["Accepted Valid Rows", str(summary.get("accepted_count", 0))],
        ["Rejected Rows", str(summary.get("rejected_count", 0))],
        ["Flagged Duplicates", str(summary.get("flagged_duplicate_count", 0))],
        *(
            []
            if is_agg
            else [
                ["Filtered Tested Denominator (S+I+R)", str(overall["total_tested"])],
                [
                    "Overall Resistance %",
                    f"{overall['resistance_pct']:.1f}% (R={overall['R']}, I={overall['I']}, S={overall['S']})",
                ],
            ]
        ),
    ]
    tbl = Table(summary_rows, colWidths=[210, 300])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111111")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D5CEC2")),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ]
        )
    )
    story.append(tbl)
    story.append(Spacer(1, 14))

    org_df = compute_grouped_resistance(filtered_df, "Organism")
    if not org_df.empty:
        story.append(Paragraph("<b>2. Organism Analysis</b>", styles["Heading2"]))
        org_rows = [["Organism", "Tested (n)", "S", "I", "R", "Resistance %"]]
        for _, r in org_df.iterrows():
            org_rows.append(
                [
                    str(r["Organism"]),
                    str(int(r["Total_Tested"])),
                    str(int(r["S"])),
                    str(int(r["I"])),
                    str(int(r["R"])),
                    f"{r['Resistance_Pct']:.1f}%",
                ]
            )
        t_org = Table(org_rows, colWidths=[180, 65, 50, 50, 50, 95])
        t_org.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111111")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D5CEC2")),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(t_org)
        story.append(Spacer(1, 14))

    ab_df = compute_grouped_resistance(filtered_df, "Antibiotic")
    if not ab_df.empty:
        story.append(Paragraph("<b>3. Antibiotic Resistance Analysis</b>", styles["Heading2"]))
        ab_rows = [["Antibiotic", "Tested (n)", "S", "I", "R", "Resistance %"]]
        for _, r in ab_df.iterrows():
            ab_rows.append(
                [
                    str(r["Antibiotic"]),
                    str(int(r["Total_Tested"])),
                    str(int(r["S"])),
                    str(int(r["I"])),
                    str(int(r["R"])),
                    f"{r['Resistance_Pct']:.1f}%",
                ]
            )
        t_ab = Table(ab_rows, colWidths=[180, 65, 50, 50, 50, 95])
        t_ab.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111111")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D5CEC2")),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(t_ab)
        story.append(Spacer(1, 14))

    pct_mat, count_mat = compute_resistance_heatmap(filtered_df)
    if not pct_mat.empty:
        story.append(Paragraph("<b>4. Organism × Antibiotic Matrix Summary</b>", styles["Heading2"]))
        cols_shown = list(pct_mat.columns)[:6]
        hm_rows = [["Organism"] + cols_shown]
        for org in pct_mat.index[:10]:
            row_vals = [str(org)]
            for ab in cols_shown:
                v = pct_mat.at[org, ab]
                n = int(count_mat.at[org, ab])
                row_vals.append("—" if pd.isna(v) or n == 0 else f"{v:.0f}% (n={n})")
            hm_rows.append(row_vals)
        t_hm = Table(hm_rows)
        t_hm.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#262626")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D5CEC2")),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                ]
            )
        )
        story.append(t_hm)
        story.append(Spacer(1, 14))

    story.append(Paragraph("<b>5. Important Surveillance Flags</b>", styles["Heading2"]))
    if alerts:
        al_rows = [["Severity", "Category", "Organism / Antibiotic", "n", "Finding"]]
        for a in alerts[:12]:
            al_rows.append(
                [
                    str(a["severity"]),
                    str(a["category"]),
                    f"{a['organism']} / {a['antibiotic']}",
                    str(a["supporting_n"]),
                    str(a["what_detected"]),
                ]
            )
        t_al = Table(al_rows, colWidths=[55, 80, 125, 35, 215])
        t_al.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111111")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D5CEC2")),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ]
            )
        )
        story.append(t_al)
    else:
        story.append(Paragraph("No surveillance flags triggered under active parameters.", styles["Normal"]))
    story.append(Spacer(1, 14))

    story.append(Paragraph("<b>6. Methodology &amp; Limitations</b>", styles["Heading2"]))
    story.append(
        Paragraph(
            "Resistance % = [R / (S + I + R)] × 100. Missing or un-interpreted results are never "
            "imputed as Susceptible. Sample sizes below 30 isolates are flagged as statistically unstable. "
            "Observed trends are descriptive and do not establish causation.",
            styles["Normal"],
        )
    )

    doc.build(story)
    return buf.getvalue()
