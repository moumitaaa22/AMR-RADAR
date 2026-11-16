"""Plotly visualizations styled with AMR RADAR black, white, and beige palette."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import (
    COLOR_BEIGE,
    COLOR_BLACK,
    COLOR_INTERMEDIATE,
    COLOR_RESISTANT,
    COLOR_SUSCEPTIBLE,
)


def plot_sir_stacked(grouped_df: pd.DataFrame, label_col: str, title: str) -> go.Figure:
    """Create horizontal stacked bar chart for S / I / R counts."""
    fig = go.Figure()
    if grouped_df.empty:
        fig.update_layout(font=dict(color="#111111"),title=f"{title} (No matching records)")
        return fig

    df = grouped_df.head(15).iloc[::-1]
    fig.add_trace(
        go.Bar(
            y=df[label_col],
            x=df["S"],
            name="Susceptible (S)",
            orientation="h",
            marker_color=COLOR_SUSCEPTIBLE,
        )
    )
    fig.add_trace(
        go.Bar(
            y=df[label_col],
            x=df["I"],
            name="Intermediate (I)",
            orientation="h",
            marker_color=COLOR_INTERMEDIATE,
        )
    )
    fig.add_trace(
        go.Bar(
            y=df[label_col],
            x=df["R"],
            name="Resistant (R)",
            orientation="h",
            marker_color=COLOR_RESISTANT,
        )
    )
    fig.update_layout(font=dict(color="#111111"),
        title=title,
        barmode="stack",
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        margin=dict(l=20, r=20, t=48, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis_title="Tested Records (n)",
    )
    return fig


def plot_resistance_bars(grouped_df: pd.DataFrame, label_col: str, title: str) -> go.Figure:
    """Create horizontal resistance percentage bar chart with sample size annotations."""
    if grouped_df.empty:
        fig = go.Figure()
        fig.update_layout(title=f"{title} (No matching records)")
        return fig

    df = grouped_df.head(15).iloc[::-1].copy()
    colors = [
        COLOR_RESISTANT if p >= 60 else (COLOR_INTERMEDIATE if p >= 30 else COLOR_SUSCEPTIBLE)
        for p in df["Resistance_Pct"]
    ]
    text_labels = [
        f"{p:.1f}% (n={n}{'*' if n < 30 else ''})"
        for p, n in zip(df["Resistance_Pct"], df["Total_Tested"])
    ]

    fig = go.Figure(
        go.Bar(
            x=df["Resistance_Pct"],
            y=df[label_col],
            orientation="h",
            marker_color=colors,
            text=text_labels,
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Resistance: %{x:.1f}%<br>Tested n: %{customdata[0]}<extra></extra>",
            customdata=df[["Total_Tested"]].values,
        )
    )
    fig.update_layout(font=dict(color="#111111"),
        title=title,
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        xaxis=dict(range=[0, 115], title="Resistance % [R / (S + I + R) × 100]"),
        margin=dict(l=20, r=40, t=48, b=30),
    )
    return fig


def plot_resistance_heatmap(pct_matrix: pd.DataFrame, count_matrix: pd.DataFrame) -> go.Figure:
    """Create interactive Organism x Antibiotic resistance heatmap with tested counts on hover."""
    if pct_matrix.empty:
        fig = go.Figure()
        fig.update_layout(title="Insufficient data for Resistance Heatmap")
        return fig

    z_vals = pct_matrix.values
    counts_aligned = count_matrix.reindex(index=pct_matrix.index, columns=pct_matrix.columns).fillna(0).astype(int)

    text_grid = []
    custom_grid = []
    for r_idx in range(len(pct_matrix.index)):
        row_txt = []
        row_cust = []
        for c_idx in range(len(pct_matrix.columns)):
            val = z_vals[r_idx][c_idx]
            n = int(counts_aligned.values[r_idx][c_idx])
            if pd.isna(val) or n == 0:
                row_txt.append("—")
                row_cust.append("Not tested")
            else:
                star = "*" if n < 30 else ""
                row_txt.append(f"{val:.1f}%{star}<br>(n={n})")
                row_cust.append(f"Tested n={n}")
        text_grid.append(row_txt)
        custom_grid.append(row_cust)

    colorscale = [
        [0.0, "#E6EFEA"],
        [0.25, "#EFECE6"],
        [0.5, "#E7D8BE"],
        [0.75, "#D49A6A"],
        [1.0, "#A63A3A"],
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=z_vals,
            x=list(pct_matrix.columns),
            y=list(pct_matrix.index),
            text=text_grid,
            texttemplate="%{text}",
            customdata=custom_grid,
            hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>Resistance: %{z:.1f}%<br>%{customdata}<extra></extra>",
            colorscale=colorscale,
            zmin=0,
            zmax=100,
            colorbar=dict(title="Resistance %"),
            xgap=2,
            ygap=2,
        )
    )
    fig.update_layout(font=dict(color="#111111"),
        title="Organism × Antibiotic Resistance Heatmap (* indicates n < 30)",
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        height=max(420, 62 * len(pct_matrix.index) + 120),
        margin=dict(l=20, r=20, t=55, b=40),
    )
    return fig


def plot_trend_line(trend_df: pd.DataFrame, title: str) -> go.Figure:
    """Create time-series resistance trend line chart."""
    if trend_df.empty:
        fig = go.Figure()
        fig.update_layout(title=f"{title} (No dated records)")
        return fig

    fig = px.line(
        trend_df,
        x="Period",
        y="Resistance_Pct",
        markers=True,
        title=title,
        hover_data=["Total_Tested", "R", "I", "S"],
    )
    fig.update_traces(line_color=COLOR_BLACK, marker_color=COLOR_BEIGE, marker_line_color=COLOR_BLACK, marker_line_width=1.5)
    fig.update_layout(font=dict(color="#111111"),
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        yaxis=dict(range=[0, 100], title="Resistance %"),
        xaxis_title="Period",
        margin=dict(l=20, r=20, t=48, b=30),
    )
    return fig
