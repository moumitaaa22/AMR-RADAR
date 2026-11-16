"""Antimicrobial resistance analytics calculations for Format A and Format B datasets."""

from __future__ import annotations

from typing import Dict, Tuple

import pandas as pd

from config import LOW_SAMPLE_THRESHOLD, VERY_LOW_SAMPLE_THRESHOLD


def compute_overall_sir(df: pd.DataFrame) -> Dict[str, float | int]:
    """Compute overall S, I, R counts and exact Resistance % = R / (S + I + R) * 100."""
    if df.empty or "Result" not in df.columns:
        return {"S": 0, "I": 0, "R": 0, "total_tested": 0, "resistance_pct": 0.0}

    valid = df[df["Result"].isin(["S", "I", "R"])]
    counts = valid["Result"].value_counts()
    s = int(counts.get("S", 0))
    i = int(counts.get("I", 0))
    r = int(counts.get("R", 0))
    total = s + i + r
    pct = (r / total * 100.0) if total > 0 else 0.0
    return {
        "S": s,
        "I": i,
        "R": r,
        "total_tested": total,
        "resistance_pct": round(pct, 2),
    }


def compute_grouped_resistance(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Group valid S/I/R records by group_col and compute exact resistance metrics and sample warnings."""
    cols = [
        group_col,
        "S",
        "I",
        "R",
        "Total_Tested",
        "Resistance_Pct",
        "Susceptible_Pct",
        "Intermediate_Pct",
        "Low_Sample_Warning",
        "Very_Low_Sample_Warning",
    ]
    if df.empty or group_col not in df.columns or "Result" not in df.columns:
        return pd.DataFrame(columns=cols)

    valid = df[df["Result"].isin(["S", "I", "R"])].copy()
    if valid.empty:
        return pd.DataFrame(columns=cols)

    pivot = pd.crosstab(valid[group_col], valid["Result"])
    for sir in ["S", "I", "R"]:
        if sir not in pivot.columns:
            pivot[sir] = 0

    pivot = pivot[["S", "I", "R"]].copy()
    pivot["Total_Tested"] = pivot["S"] + pivot["I"] + pivot["R"]
    pivot = pivot[pivot["Total_Tested"] > 0]
    pivot["Resistance_Pct"] = (pivot["R"] / pivot["Total_Tested"]) * 100.0
    pivot["Susceptible_Pct"] = (pivot["S"] / pivot["Total_Tested"]) * 100.0
    pivot["Intermediate_Pct"] = (pivot["I"] / pivot["Total_Tested"]) * 100.0
    pivot["Low_Sample_Warning"] = pivot["Total_Tested"] < LOW_SAMPLE_THRESHOLD
    pivot["Very_Low_Sample_Warning"] = pivot["Total_Tested"] < VERY_LOW_SAMPLE_THRESHOLD

    res = pivot.reset_index().sort_values(by="Total_Tested", ascending=False)
    return res[cols]


def compute_resistance_heatmap(
    df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Return (resistance_pct_matrix, tested_count_matrix) for Organism x Antibiotic."""
    if df.empty or "Result" not in df.columns:
        return pd.DataFrame(), pd.DataFrame()

    valid = df[df["Result"].isin(["S", "I", "R"])].copy()
    if valid.empty:
        return pd.DataFrame(), pd.DataFrame()

    valid["Is_R"] = (valid["Result"] == "R").astype(int)
    grouped = (
        valid.groupby(["Organism", "Antibiotic"], as_index=False)
        .agg(R_Count=("Is_R", "sum"), Total_Tested=("Result", "count"))
    )
    grouped["Resistance_Pct"] = (grouped["R_Count"] / grouped["Total_Tested"]) * 100.0

    pct_matrix = grouped.pivot(index="Organism", columns="Antibiotic", values="Resistance_Pct")
    count_matrix = grouped.pivot(index="Organism", columns="Antibiotic", values="Total_Tested").fillna(0).astype(int)
    return pct_matrix, count_matrix


def compute_time_trends(df: pd.DataFrame, granularity: str = "month") -> pd.DataFrame:
    """Compute monthly or yearly resistance percentage trends across dated valid S/I/R records."""
    period_col = "YearMonth" if granularity == "month" else "Year"
    cols = ["Period", "S", "I", "R", "Total_Tested", "Resistance_Pct"]
    if df.empty or period_col not in df.columns:
        return pd.DataFrame(columns=cols)

    valid = df[df["Result"].isin(["S", "I", "R"]) & (df[period_col] != "")].copy()
    if valid.empty:
        return pd.DataFrame(columns=cols)

    pivot = pd.crosstab(valid[period_col], valid["Result"])
    for sir in ["S", "I", "R"]:
        if sir not in pivot.columns:
            pivot[sir] = 0

    pivot = pivot[["S", "I", "R"]].copy()
    pivot["Total_Tested"] = pivot["S"] + pivot["I"] + pivot["R"]
    pivot["Resistance_Pct"] = (pivot["R"] / pivot["Total_Tested"]) * 100.0
    res = pivot.reset_index().rename(columns={period_col: "Period"}).sort_values("Period")
    return res[cols]
