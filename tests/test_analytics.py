"""Pytest suite for AMR resistance calculations, heatmaps, and trends."""

import pandas as pd
import pytest

from modules.analytics import (
    compute_grouped_resistance,
    compute_overall_sir,
    compute_resistance_heatmap,
    compute_time_trends,
)


def _sample_df():
    return pd.DataFrame(
        [
            {"Organism": "E. coli", "Antibiotic": "Ciprofloxacin", "Result": "R", "YearMonth": "2025-01", "Year": "2025", "Location": "Site A"},
            {"Organism": "E. coli", "Antibiotic": "Ciprofloxacin", "Result": "R", "YearMonth": "2025-01", "Year": "2025", "Location": "Site A"},
            {"Organism": "E. coli", "Antibiotic": "Ciprofloxacin", "Result": "I", "YearMonth": "2025-02", "Year": "2025", "Location": "Site A"},
            {"Organism": "E. coli", "Antibiotic": "Ciprofloxacin", "Result": "S", "YearMonth": "2025-02", "Year": "2025", "Location": "Site B"},
        ]
    )


def test_exact_resistance_formula_includes_intermediate_in_denominator():
    df = _sample_df()
    overall = compute_overall_sir(df)
    assert overall["S"] == 1
    assert overall["I"] == 1
    assert overall["R"] == 2
    assert overall["total_tested"] == 4
    # 2 / (1 + 1 + 2) * 100 = 50.0%
    assert overall["resistance_pct"] == pytest.approx(50.0)


def test_invalid_results_excluded_never_imputed_as_susceptible():
    df = pd.concat(
        [
            _sample_df(),
            pd.DataFrame(
                [
                    {"Organism": "E. coli", "Antibiotic": "Ciprofloxacin", "Result": "ND", "YearMonth": "2025-02", "Year": "2025", "Location": "Site B"},
                    {"Organism": "E. coli", "Antibiotic": "Ciprofloxacin", "Result": "", "YearMonth": "2025-02", "Year": "2025", "Location": "Site B"},
                ]
            ),
        ],
        ignore_index=True,
    )
    overall = compute_overall_sir(df)
    assert overall["total_tested"] == 4
    assert overall["resistance_pct"] == pytest.approx(50.0)


def test_grouped_resistance_flags_small_sample_sizes():
    df = _sample_df()
    grouped = compute_grouped_resistance(df, "Organism")
    assert len(grouped) == 1
    assert grouped.iloc[0]["Total_Tested"] == 4
    assert bool(grouped.iloc[0]["Low_Sample_Warning"]) is True
    assert bool(grouped.iloc[0]["Very_Low_Sample_Warning"]) is True


def test_heatmap_and_trends_alignment():
    df = _sample_df()
    pct_mat, count_mat = compute_resistance_heatmap(df)
    assert pct_mat.loc["E. coli", "Ciprofloxacin"] == pytest.approx(50.0)
    assert count_mat.loc["E. coli", "Ciprofloxacin"] == 4

    trends = compute_time_trends(df, "month")
    assert list(trends["Period"]) == ["2025-01", "2025-02"]
    assert trends.iloc[0]["Resistance_Pct"] == pytest.approx(100.0)
    assert trends.iloc[1]["Resistance_Pct"] == pytest.approx(0.0)
