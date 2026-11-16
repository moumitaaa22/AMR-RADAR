"""Explainable surveillance alert engine for AMR RADAR (non-clinical analytical flags)."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from config import LOW_SAMPLE_THRESHOLD, VERY_LOW_SAMPLE_THRESHOLD
from modules.analytics import compute_resistance_heatmap


def generate_surveillance_alerts(
    filtered_df: pd.DataFrame,
    full_df: pd.DataFrame,
    resistance_threshold_pct: float = 50.0,
    min_sample_for_threshold: int = 10,
    trend_delta_threshold_pct: float = 15.0,
) -> List[Dict[str, Any]]:
    """Generate explainable analytical flags with supporting counts and explicit rationale."""
    alerts: List[Dict[str, Any]] = []
    counter = 1

    pct_matrix, count_matrix = compute_resistance_heatmap(filtered_df)
    if not pct_matrix.empty:
        for org in pct_matrix.index:
            for ab in pct_matrix.columns:
                pct = pct_matrix.at[org, ab]
                n = int(count_matrix.at[org, ab])
                if pd.isna(pct) or n == 0:
                    continue

                if pct >= resistance_threshold_pct and n >= min_sample_for_threshold:
                    alerts.append(
                        {
                            "id": f"ALT-{counter}",
                            "category": "Threshold Breach",
                            "severity": "High" if pct >= 75 else "Moderate",
                            "organism": org,
                            "antibiotic": ab,
                            "supporting_n": n,
                            "resistance_pct": round(float(pct), 1),
                            "what_detected": f"{pct:.1f}% resistance across {n} valid S/I/R records for {org} tested against {ab}.",
                            "why_generated": f"Observed resistance >= {resistance_threshold_pct:.0f}% threshold with supporting sample size n={n} (>= {min_sample_for_threshold}).",
                        }
                    )
                    counter += 1

                if n < LOW_SAMPLE_THRESHOLD:
                    alerts.append(
                        {
                            "id": f"ALT-{counter}",
                            "category": "Small Sample Size",
                            "severity": "Caution",
                            "organism": org,
                            "antibiotic": ab,
                            "supporting_n": n,
                            "resistance_pct": round(float(pct), 1),
                            "what_detected": f"Small sample size (n={n}) for {org} vs {ab} ({pct:.1f}% R).",
                            "why_generated": (
                                "Very low isolate count (n < 10)."
                                if n < VERY_LOW_SAMPLE_THRESHOLD
                                else "Below CLSI M39 recommended minimum of 30 isolates per pair."
                            ),
                        }
                    )
                    counter += 1

    # Temporal trend check
    dated = filtered_df[
        filtered_df["Result"].isin(["S", "I", "R"]) & (filtered_df["YearMonth"] != "")
    ].copy()
    if not dated.empty:
        for (org, ab), grp in dated.groupby(["Organism", "Antibiotic"]):
            months = sorted(grp["YearMonth"].unique())
            if len(months) < 4 or len(grp) < 16:
                continue
            mid = len(months) // 2
            early = grp[grp["YearMonth"].isin(months[:mid])]
            late = grp[grp["YearMonth"].isin(months[mid:])]
            if len(early) < 6 or len(late) < 6:
                continue
            early_pct = (early["Result"] == "R").mean() * 100.0
            late_pct = (late["Result"] == "R").mean() * 100.0
            delta = late_pct - early_pct
            if delta >= trend_delta_threshold_pct:
                alerts.append(
                    {
                        "id": f"ALT-{counter}",
                        "category": "Upward Trend",
                        "severity": "High" if delta >= 25 else "Moderate",
                        "organism": org,
                        "antibiotic": ab,
                        "supporting_n": len(grp),
                        "resistance_pct": round(float(late_pct), 1),
                        "what_detected": f"Resistance rose from {early_pct:.1f}% (n={len(early)}) to {late_pct:.1f}% (n={len(late)}) (+{delta:.1f} pp).",
                        "why_generated": f"Exceeds +{trend_delta_threshold_pct:.0f} pp period-over-period shift threshold. Correlation does not prove causation.",
                    }
                )
                counter += 1

    # Data quality flags
    if not full_df.empty and "Validation_Status" in full_df.columns:
        rejected_n = int((full_df["Validation_Status"] == "rejected").sum())
        dupe_n = int((full_df["Validation_Status"] == "flagged_duplicate").sum())
        if rejected_n > 0:
            alerts.append(
                {
                    "id": f"ALT-{counter}",
                    "category": "Data Quality",
                    "severity": "Caution",
                    "organism": "Multiple",
                    "antibiotic": "Multiple",
                    "supporting_n": rejected_n,
                    "resistance_pct": None,
                    "what_detected": f"{rejected_n} raw row(s) rejected due to missing required fields or invalid S/I/R values.",
                    "why_generated": "Invalid or missing S/I/R results are quarantined and never imputed as Susceptible.",
                }
            )
            counter += 1
        if dupe_n > 0:
            alerts.append(
                {
                    "id": f"ALT-{counter}",
                    "category": "Data Quality",
                    "severity": "Caution",
                    "organism": "Multiple",
                    "antibiotic": "Multiple",
                    "supporting_n": dupe_n,
                    "resistance_pct": None,
                    "what_detected": f"{dupe_n} exact duplicate isolate-antibiotic row(s) flagged.",
                    "why_generated": "Exact duplicate entries can bias antibiogram percentages if not reviewed.",
                }
            )
            counter += 1

    sev_rank = {"High": 0, "Moderate": 1, "Caution": 2}
    alerts.sort(key=lambda a: sev_rank.get(a["severity"], 3))
    return alerts
