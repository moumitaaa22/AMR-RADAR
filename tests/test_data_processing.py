"""Pytest suite for data validation, S/I/R normalization, duplicate detection, and Format B."""

import pandas as pd

from modules.data_loader import detect_dataset_format
from modules.data_processing import (
    filter_records,
    process_aggregated_dataset,
    process_individual_dataset,
    suggest_individual_mapping,
)


def test_validation_rejects_invalid_sir_and_flags_duplicates():
    raw = pd.DataFrame(
        [
            {"Sample_ID": "1", "Organism": "E. coli", "Antibiotic": "Cip", "Result": "R", "Date": "2025-01-10", "Location": "L1", "Laboratory": "Lab1"},
            {"Sample_ID": "1", "Organism": "E. coli", "Antibiotic": "Cip", "Result": "R", "Date": "2025-01-10", "Location": "L1", "Laboratory": "Lab1"},
            {"Sample_ID": "2", "Organism": "E. coli", "Antibiotic": "Cip", "Result": "Susceptible", "Date": "2025-01-12", "Location": "L1", "Laboratory": "Lab1"},
            {"Sample_ID": "3", "Organism": "E. coli", "Antibiotic": "Cip", "Result": "MIC<=0.5", "Date": "2025-01-14", "Location": "L1", "Laboratory": "Lab1"},
            {"Sample_ID": "4", "Organism": "", "Antibiotic": "Cip", "Result": "R", "Date": "2025-01-15", "Location": "L1", "Laboratory": "Lab1"},
        ]
    )
    mapping = suggest_individual_mapping(list(raw.columns))
    processed, summary = process_individual_dataset(raw, mapping, dataset_name="Unit Test")

    assert summary["accepted_count"] == 2
    assert summary["flagged_duplicate_count"] == 1
    assert summary["rejected_count"] == 2
    assert processed.loc[2, "Result"] == "S"
    assert processed.loc[3, "Validation_Status"] == "rejected"
    assert processed.loc[4, "Validation_Status"] == "rejected"

    deduped = filter_records(processed, exclude_duplicates=True)
    assert len(deduped) == 2


def test_format_b_detection_and_preservation():
    raw = pd.DataFrame(
        [
            {"Organism": "K. pneumoniae", "Antibiotic": "Meropenem", "Tested_Count": "100", "Resistant_Pct": "45.0", "Year": "2024", "Location": "Network"}
        ]
    )
    assert detect_dataset_format(list(raw.columns)) == "aggregated"
    processed, summary = process_aggregated_dataset(raw, dataset_name="ICMR Test")
    assert summary["format"] == "aggregated"
    assert summary["accepted_count"] == 1
    assert processed.loc[0, "Tested_Count"] == 100
    assert processed.loc[0, "Resistant_Pct"] == 45.0
