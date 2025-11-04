## charts/chart_generators/fig3_economic_growth_rates.py
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures


def _load_growth_data(csv_hint: str | Path | None = None) -> pd.DataFrame:
    if csv_hint:
        p = Path(csv_hint)
        if p.exists():
            return pd.read_csv(p)
    for candidate in [
        PROJECT_ROOT / "data" / "raw" / "3_economic_growth_rates.csv",
        PROJECT_ROOT / "data" / "processed" / "3_economic_growth_rates.csv",
    ]:
        if candidate.exists():
            return pd.read_csv(candidate)

    data = {
        "Year": list(range(2024, 2041)),
        "Low": [
            0.51, 0.22, 1.15, 1.10, 1.04, 0.85, 1.01, 0.99, 0.77, 1.22, 1.23, 1.33,
            1.23, 1.18, 1.38, 1.10, 1.29
        ],
        "Reference": [
            0.51, 1.69, 1.70, 1.91, 2.06, 2.15, 2.09, 2.13, 2.09, 2.17, 2.51, 2.72,
            2.72, 2.76, 2.92, 2.72, 3.00
        ],
        "High": [
            0.51, 2.63, 2.39, 2.42, 2.61, 2.72, 2.56, 2.62, 2.62, 2.73, 2.81, 3.43,
            3.49, 3.56, 3.79, 3.64, 3.97
        ],
    }
    return pd.DataFrame(data)


def generate_fig3_economic_growth_rates(_df_unused: pd.DataFrame | None, output_dir: str,
                                        csv_hint: str | Path | None = None) -> None:
    df = _load_growth_data(csv_hint)

    # Ensure numeric if a CSV had % strings
    for col in ["Low", "Reference", "High"]:
        df[col] = df[col].astype(str).str.replace("%", "", regex=False).astype(float)

    colors = {"Low": "#1F77B4", "Reference": "#FF7F0E", "High": "#2CA02C"}
    fig = go.Figure()

    def add_line(series: str):
        fig.add_trace(
            go.Scatter(
                x=df["Year"],
                y=df[series],
                mode="lines+markers+text",
                name=series,
                line=dict(color=colors[series], width=3),
                marker=dict(size=6),
                text=[f"{v:.2f}%" for v in df[series]],
                textposition="top center",
                textfont=dict(size=14),  # smaller on-plot labels
                hovertemplate="%{x}: " + series + " %{y:.2f}%<extra></extra>",
            )
        )

    for s in ["Low", "Reference", "High"]:
        add_line(s)

    apply_common_layout(fig, image_type="report")

    # Layout tweaks per your notes
    fig.update_layout(
        title_text="",  # remove title
        margin=dict(l=100, r=20, t=70, b=70),  # more space on the left
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,   # slightly higher than before (-0.25)
            xanchor="center",
            x=0.5,
        ),
    )

    fig.update_xaxes(title="", tickmode="linear", dtick=1, tickangle=-45, range=[2024, 2040])

    fig.update_yaxes(
        title="% GDP growth",
        tickformat=".1f",
        range=[0, 4.5],
        title_font=dict(size=22),  # larger y-axis title
        tickfont=dict(size=20),    # larger y-axis ticks
        title_standoff=18,
    )

    save_figures(fig, output_dir, name="fig3_economic_growth_rates")


if __name__ == "__main__":
    outdir = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig3_economic_growth_rates"
    outdir.mkdir(parents=True, exist_ok=True)
    generate_fig3_economic_growth_rates(None, str(outdir))
