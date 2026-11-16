"""Data validation, column mapping, cleaning audit trail, and filtering for AMR RADAR."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from config import VALID_SIR_VALUES


def normalize_col_token(name: str) -> str:
    return name.strip().lower().replace("_", "").replace("-", "").replace(" ", "")


def suggest_individual_mapping(columns: List[str]) -> Dict[str, Optional[str]]:
    """Suggest best column mapping from source headers without assuming fixed names."""
    norm_lookup = {normalize_col_token(c): c for c in columns}

    def find(candidates: List[str]) -> Optional[str]:
        for cand in candidates:
            if cand in norm_lookup:
                return norm_lookup[cand]
        for cand in candidates:
            for token, orig in norm_lookup.items():
                if cand in token:
                    return orig
        return None

    return {
        "Sample_ID": find(["sampleid", "isolateid", "specimenid", "labid", "id"]),
        "Organism": find(["organism", "pathogen", "bacteria", "species", "microorganism"]),
        "Antibiotic": find(["antibiotic", "antimicrobial", "drug", "agent"]),
        "Result": find(["result", "sir", "interpretation", "susceptibility", "astresult"]),
        "Date": find(["date", "sampledate", "collectiondate", "testdate", "specimendate"]),
        "Location": find(["location", "site", "city", "state", "region", "hospital"]),
        "Laboratory": find(["laboratory", "lab", "center", "centre", "facility"]),
        "Standard": find(["standard", "guideline", "aststandard"]),
        "Standard_Version": find(["standardversion", "version", "edition"]),
    }


def normalize_sir_value(val: Any) -> Tuple[Optional[str], bool]:
    """Normalize explicit S/I/R or Susceptible/Intermediate/Resistant. Never impute missing/MIC as S."""
    if val is None:
        return None, False
    token = str(val).strip().upper()
    if not token:
        return None, False
    if token in VALID_SIR_VALUES:
        return token, False
    mapping = {
        "SUSCEPTIBLE": "S",
        "INTERMEDIATE": "I",
        "RESISTANT": "R",
    }
    if token in mapping:
        return mapping[token], True
    return None, False


def process_individual_dataset(
    raw_df: pd.DataFrame,
    column_mapping: Dict[str, Optional[str]],
    dataset_name: str = "Laboratory Dataset",
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Validate and clean Format A individual records while preserving original data."""
    required = ["Organism", "Antibiotic", "Result"]
    for req in required:
        if not column_mapping.get(req):
            raise ValueError(f"Required column mapping missing for: {req}")

    df = raw_df.copy()
    original_columns = list(df.columns)
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def extract_col(target: str, default: str = "") -> pd.Series:
        src = column_mapping.get(target)
        if src and src in df.columns:
            return df[src].astype(str).str.strip()
        return pd.Series([default] * len(df), index=df.index)

    out = pd.DataFrame(index=df.index)
    out["Row_Number"] = range(1, len(df) + 1)
    sample_series = extract_col("Sample_ID", "")
    out["Sample_ID"] = [
        s if s else f"ROW-{i}" for i, s in zip(out["Row_Number"], sample_series)
    ]
    out["Organism"] = extract_col("Organism", "")
    out["Antibiotic"] = extract_col("Antibiotic", "")
    raw_result = extract_col("Result", "")
    out["Raw_Result"] = raw_result
    raw_date = extract_col("Date", "")
    out["Location"] = extract_col("Location", "Unspecified").replace("", "Unspecified")
    out["Laboratory"] = extract_col("Laboratory", "Unspecified").replace("", "Unspecified")
    out["Standard"] = extract_col("Standard", "Not Recorded").replace("", "Not Recorded")
    out["Standard_Version"] = extract_col("Standard_Version", "")

    norm_results: List[str] = []
    word_normalized_count = 0
    invalid_sir_count = 0
    invalid_date_count = 0
    missing_req_count = 0
    parsed_dates: List[str] = []
    statuses: List[str] = []
    issues_col: List[str] = []

    seen_signatures = set()
    accepted_count = 0
    rejected_count = 0
    duplicate_count = 0
    warning_count = 0

    for idx in out.index:
        row_issues: List[str] = []
        org = out.at[idx, "Organism"]
        ab = out.at[idx, "Antibiotic"]
        res_raw = raw_result.at[idx]
        dt_raw = raw_date.at[idx]

        if not org:
            row_issues.append("Missing required field: Organism")
        if not ab:
            row_issues.append("Missing required field: Antibiotic")
        if not org or not ab:
            missing_req_count += 1

        sir, was_word = normalize_sir_value(res_raw)
        if was_word:
            word_normalized_count += 1
        if sir is None:
            label = res_raw if res_raw else "(blank)"
            row_issues.append(
                f"Invalid S/I/R value '{label}' (never imputed as Susceptible)"
            )
            invalid_sir_count += 1
            norm_results.append(res_raw)
        else:
            norm_results.append(sir)

        dt_iso = ""
        if dt_raw:
            dt_parsed = pd.to_datetime(dt_raw, errors="coerce")
            if pd.isna(dt_parsed):
                row_issues.append(f"Invalid date '{dt_raw}'")
                invalid_date_count += 1
                warning_count += 1
            else:
                dt_iso = dt_parsed.strftime("%Y-%m-%d")
        parsed_dates.append(dt_iso)

        if out.at[idx, "Location"] == "Unspecified":
            row_issues.append("Missing Location")
            warning_count += 1

        has_fatal = (not org) or (not ab) or (sir is None)
        sig = (
            out.at[idx, "Sample_ID"],
            org.lower(),
            ab.lower(),
            sir or res_raw,
            dt_iso,
            out.at[idx, "Location"].lower(),
            out.at[idx, "Laboratory"].lower(),
        )

        if has_fatal:
            statuses.append("rejected")
            rejected_count += 1
        elif sig in seen_signatures:
            statuses.append("flagged_duplicate")
            duplicate_count += 1
            warning_count += 1
            row_issues.append("Exact duplicate record flagged")
        else:
            seen_signatures.add(sig)
            statuses.append("valid")
            accepted_count += 1

        issues_col.append("; ".join(row_issues))

    out["Result"] = norm_results
    out["Date"] = parsed_dates
    out["YearMonth"] = [d[:7] if d else "" for d in parsed_dates]
    out["Year"] = [d[:4] if d else "" for d in parsed_dates]
    out["Validation_Status"] = statuses
    out["Issues"] = issues_col

    audit_log = [
        {
            "timestamp": now_iso,
            "operation": "Column Mapping",
            "details": f"Mapped {len(original_columns)} source columns for {dataset_name}.",
            "affected": len(df),
        }
    ]
    if word_normalized_count:
        audit_log.append(
            {
                "timestamp": now_iso,
                "operation": "S/I/R Label Standardization",
                "details": "Converted explicit Susceptible/Intermediate/Resistant words to S/I/R.",
                "affected": word_normalized_count,
            }
        )
    if invalid_sir_count:
        audit_log.append(
            {
                "timestamp": now_iso,
                "operation": "Result Validation",
                "details": "Rejected unrecognised/blank S/I/R interpretations without imputing S.",
                "affected": invalid_sir_count,
            }
        )
    if missing_req_count:
        audit_log.append(
            {
                "timestamp": now_iso,
                "operation": "Required Field Check",
                "details": "Rejected rows missing Organism or Antibiotic.",
                "affected": missing_req_count,
            }
        )
    if invalid_date_count:
        audit_log.append(
            {
                "timestamp": now_iso,
                "operation": "Date Validation",
                "details": "Flagged invalid dates; excluded from time-series only.",
                "affected": invalid_date_count,
            }
        )
    if duplicate_count:
        audit_log.append(
            {
                "timestamp": now_iso,
                "operation": "Duplicate Detection",
                "details": "Flagged exact duplicate laboratory rows for analyst review.",
                "affected": duplicate_count,
            }
        )

    valid_dates = sorted([d for d, s in zip(parsed_dates, statuses) if d and s != "rejected"])
    summary = {
        "dataset_name": dataset_name,
        "format": "individual",
        "original_columns": original_columns,
        "total_raw_rows": len(df),
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "flagged_duplicate_count": duplicate_count,
        "warning_count": warning_count,
        "date_range": f"{valid_dates[0]} to {valid_dates[-1]}" if valid_dates else "No valid dates",
        "audit_log": audit_log,
    }
    return out, summary


def process_aggregated_dataset(
    raw_df: pd.DataFrame,
    dataset_name: str = "Aggregated Surveillance Dataset",
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Process Format B aggregated counts/denominators/percentages without fabricating isolates."""
    df = raw_df.copy()
    norm = {normalize_col_token(c): c for c in df.columns}

    def pick(cands: List[str]) -> Optional[str]:
        for c in cands:
            if c in norm:
                return norm[c]
        return None

    org_col = pick(["organism", "pathogen", "bacteria", "species"])
    ab_col = pick(["antibiotic", "antimicrobial", "drug", "agent"])
    n_col = pick(["testedcount", "totaltested", "isolatestested", "denominator", "n"])
    pct_col = pick(["resistantpct", "resistancepct", "resistantpercent", "pctresistant"])
    rcount_col = pick(["resistantcount", "rcount"])
    year_col = pick(["year", "period"])
    loc_col = pick(["location", "region", "site", "network"])
    src_col = pick(["source", "dataset"])

    if not org_col or not ab_col or not n_col:
        raise ValueError(
            "Aggregated Format B requires Organism, Antibiotic, and Tested_Count columns."
        )

    rows = []
    for idx, r in df.iterrows():
        n_val = pd.to_numeric(r[n_col], errors="coerce")
        pct_val = pd.to_numeric(str(r[pct_col]).replace("%", ""), errors="coerce") if pct_col else None
        r_val = pd.to_numeric(r[rcount_col], errors="coerce") if rcount_col else None
        if (pct_val is None or pd.isna(pct_val)) and r_val is not None and not pd.isna(r_val) and n_val > 0:
            pct_val = (r_val / n_val) * 100.0

        valid = bool(
            str(r[org_col]).strip()
            and str(r[ab_col]).strip()
            and pd.notna(n_val)
            and n_val > 0
            and pct_val is not None
            and pd.notna(pct_val)
            and 0 <= float(pct_val) <= 100
        )
        rows.append(
            {
                "Row_Number": idx + 1,
                "Organism": str(r[org_col]).strip(),
                "Antibiotic": str(r[ab_col]).strip(),
                "Tested_Count": int(n_val) if pd.notna(n_val) else 0,
                "Resistant_Count": int(r_val) if r_val is not None and pd.notna(r_val) else None,
                "Resistant_Pct": float(pct_val) if pct_val is not None and pd.notna(pct_val) else 0.0,
                "Year": str(r[year_col]).strip() if year_col else "Unspecified",
                "Location": str(r[loc_col]).strip() if loc_col else "Unspecified",
                "Source": str(r[src_col]).strip() if src_col else dataset_name,
                "Validation_Status": "valid" if valid else "rejected",
            }
        )

    out = pd.DataFrame(rows)
    summary = {
        "dataset_name": dataset_name,
        "format": "aggregated",
        "original_columns": list(df.columns),
        "total_raw_rows": len(df),
        "accepted_count": int((out["Validation_Status"] == "valid").sum()),
        "rejected_count": int((out["Validation_Status"] == "rejected").sum()),
        "flagged_duplicate_count": 0,
        "warning_count": int((out["Tested_Count"] < 30).sum()),
        "date_range": ", ".join(sorted(out["Year"].unique())),
        "audit_log": [
            {
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "operation": "Format B Aggregated Ingestion",
                "details": "Preserved published counts and percentages without fabricating isolate rows.",
                "affected": len(df),
            }
        ],
    }
    return out, summary


def filter_records(
    df: pd.DataFrame,
    organisms: Optional[List[str]] = None,
    antibiotics: Optional[List[str]] = None,
    locations: Optional[List[str]] = None,
    laboratories: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    exclude_duplicates: bool = True,
) -> pd.DataFrame:
    """Filter processed Format A records cleanly without mutating original DataFrame."""
    if df.empty:
        return df.copy()

    mask = df["Validation_Status"] != "rejected"
    if exclude_duplicates:
        mask = mask & (df["Validation_Status"] != "flagged_duplicate")
    if organisms:
        mask = mask & df["Organism"].isin(organisms)
    if antibiotics:
        mask = mask & df["Antibiotic"].isin(antibiotics)
    if locations:
        mask = mask & df["Location"].isin(locations)
    if laboratories:
        mask = mask & df["Laboratory"].isin(laboratories)
    if start_date:
        mask = mask & (df["Date"] != "") & (df["Date"] >= start_date)
    if end_date:
        mask = mask & (df["Date"] != "") & (df["Date"] <= end_date)
    return df.loc[mask].copy()
