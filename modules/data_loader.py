"""File ingestion module supporting CSV, XLSX, XLS, and optional Stata .dta files."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd


def load_tabular_file(
    file_obj: Any, filename: str
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Read CSV, XLSX, XLS, or .dta into a DataFrame while preserving original columns."""
    ext = Path(filename).suffix.lower()
    metadata: Dict[str, Any] = {
        "filename": filename,
        "extension": ext,
        "notes": [],
    }

    if ext == ".csv":
        df = pd.read_csv(file_obj, dtype=str, keep_default_na=False)
    elif ext in {".xlsx", ".xls"}:
        engine = "openpyxl" if ext == ".xlsx" else None
        df = pd.read_excel(file_obj, dtype=str, keep_default_na=False, engine=engine)
    elif ext == ".dta":
        try:
            import pyreadstat  # type: ignore

            if hasattr(file_obj, "read"):
                raw_bytes = file_obj.read()
                buf = io.BytesIO(raw_bytes)
                df, stata_meta = pyreadstat.read_dta(buf)
                metadata["notes"].append(
                    f"Loaded Stata .dta file via pyreadstat ({len(stata_meta.column_names)} columns)."
                )
            else:
                df, stata_meta = pyreadstat.read_dta(str(file_obj))
                metadata["notes"].append(
                    f"Loaded Stata .dta file via pyreadstat ({len(stata_meta.column_names)} columns)."
                )
            df = df.fillna("").astype(str)
        except ImportError as exc:
            raise ImportError(
                "Stata .dta support requires pyreadstat. Install it with: pip install pyreadstat"
            ) from exc
    else:
        raise ValueError(
            f"Unsupported file format '{ext}'. Supported formats: .csv, .xlsx, .xls, .dta"
        )

    metadata["original_columns"] = list(df.columns)
    metadata["raw_row_count"] = len(df)
    return df, metadata


def load_csv_path(path: str | Path) -> pd.DataFrame:
    """Load a local CSV file path safely as strings without silent NA coercion."""
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def detect_dataset_format(columns: List[str]) -> str:
    """Detect Format A (individual records) vs Format B (aggregated counts/percentages)."""
    normalized = {c.strip().lower().replace("_", "").replace(" ", "") for c in columns}
    has_denominator = bool(
        normalized.intersection({"testedcount", "totaltested", "isolatestested", "denominator", "n"})
    )
    has_pct_or_rcount = bool(
        normalized.intersection(
            {"resistantpct", "resistancepct", "resistantpercent", "pctresistant", "resistantcount", "rcount"}
        )
    )
    if has_denominator and has_pct_or_rcount:
        return "aggregated"
    return "individual"
