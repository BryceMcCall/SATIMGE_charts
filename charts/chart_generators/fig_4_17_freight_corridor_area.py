# charts/chart_generators/fig_4_17_freight_corridor_area.py
"""
Freight Corridor area chart (tkm) — like Fig 4_14 but for freight.
Input  : data/4_17_transport_freight_rail_corridor_HCV_tkm_wem.csv
Output : outputs/charts_and_data/fig_4_17_freight_corridor_area/{png,svg}
"""

import sys
from pathlib import Path

# ── Project import path (same CLI pattern as fig_4_14) ─────────────────────────
if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))
else:
    project_root = Path(__file__).resolve().parents[2]

import pandas as pd
import plotly.graph_objects as go

from charts.common.style import apply_common_layout
from charts.common.save import save_figures

# ── Fonts: separate toggles (edit these or pass as kwargs) ─────────────────────
DEFAULT_FONTS = dict(
    title=18,       # main chart title
    axis=14,        # axis titles
    tick=12,        # tick labels
    legend=12,      # legend labels
    annotation=12,  # labels inside the plot
)

# ── Colours (tuned to match your reference more closely) ───────────────────────
COLORS = {
    "HCV EV":               "#58a65c",  # soft green
    "HCV Diesel":           "#f2b37a",  # warm orange/peach
    "Rail Corridor Electric":"#8c72d8", # light purple
    "Rail Corridor Diesel": "#d95b52",  # muted red
}

ORDER_BOTTOM_TO_TOP = [
    "Rail Corridor Electric",
    "Rail Corridor Diesel",
    "HCV Diesel",
    "HCV EV",
]

TITLE = "Freight Corridor"
Y_LABEL = "billion tkm"
X_LABEL = "Year"

# ───────────────────────── Data wrangling helpers ──────────────────────────────
def _is_rail_electric(s: pd.Series) -> pd.Series:
    return s.str.contains("Rail Corridor Electricity", case=False, na=False)

def _is_rail_diesel(s: pd.Series) -> pd.Series:
    return s.str.contains("Rail Corridor Oil Diesel", case=False, na=False)

def _is_hcv_electric(sub: pd.Series, tech: pd.Series) -> pd.Series:
    return sub.str.contains("HCV", na=False) & tech.str.contains("Electricity", na=False)

def _is_hcv_diesel(sub: pd.Series, tech: pd.Series) -> pd.Series:
    return sub.str.contains("HCV", na=False) & tech.str.contains("Oil Diesel", na=False)

def _aggregate_four_categories(df: pd.DataFrame) -> pd.DataFrame:
    years = sorted(df["Year"].dropna().astype(int).unique())
    idx = pd.Index(years, name="Year")
    parts = {
        "Rail Corridor Electric": df[_is_rail_electric(df["TechDescription"])],
        "Rail Corridor Diesel":   df[_is_rail_diesel(df["TechDescription"])],
        "HCV Diesel":             df[_is_hcv_diesel(df["Subsubsector"], df["TechDescription"])],
        "HCV EV":                 df[_is_hcv_electric(df["Subsubsector"], df["TechDescription"])],
    }
    out = {}
    for k, sub in parts.items():
        out[k] = (
            sub.groupby("Year")["SATIMGE"].sum()
               .reindex(idx, fill_value=0.0)
        )
    return pd.DataFrame(out)[ORDER_BOTTOM_TO_TOP]

# ────────────────────────── Figure generator ───────────────────────────────────
def generate_fig_4_17_freight_corridor(
    df: pd.DataFrame,
    output_dir: str,
    fonts: dict | None = None
):
    fonts = {**DEFAULT_FONTS, **(fonts or {})}

    # Clean/aggregate
    df = df.copy()
    df["SATIMGE"] = pd.to_numeric(df["SATIMGE"], errors="coerce").fillna(0.0)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype(int)
    plot_df = _aggregate_four_categories(df)

    # Build stacked area with go.Scatter so we control fill order
    fig = go.Figure()
    cumulative = None
    for i, col in enumerate(plot_df.columns):
        y = plot_df[col].values
        fig.add_trace(
            go.Scatter(
                x=plot_df.index,
                y=y,
                mode="lines",
                line=dict(width=0.0),  # no outline to match the soft style
                name=col,
                stackgroup="tkm",
                fill="tonexty" if i > 0 else "tonexty",
                fillcolor=COLORS[col],
                hovertemplate=f"{col}<br>Year=%{{x}}<br>tkm=%{{y:.2f}}<extra></extra>",
            )
        )

    # Axis titles, ticks & legend
    fig.update_layout(
        title=dict(text=TITLE, x=0.5, font=dict(size=fonts["title"])),
        xaxis=dict(
            title=dict(text=X_LABEL, font=dict(size=fonts["axis"])),
            tickfont=dict(size=fonts["tick"]),
            tickmode="array",
            tickvals=[int(y) for y in plot_df.index],
            ticktext=[str(int(y)) for y in plot_df.index],
        ),
        yaxis=dict(
            title=dict(text=Y_LABEL, font=dict(size=fonts["axis"])),
            tickfont=dict(size=fonts["tick"]),
            rangemode="tozero",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.18,
            xanchor="center",
            x=0.5,
            font=dict(size=fonts["legend"]),
            traceorder="normal",
        ),
        margin=dict(l=60, r=20, t=60, b=90),
        hovermode="x unified",
        showlegend=True,
    )

    # Project-wide styling hook (kept from original)
    apply_common_layout(fig)

    # Optional internal labels (comment out if not wanted)
    if plot_df["HCV EV"].sum() > 0:
        fig.add_annotation(
            x=plot_df.index[int(len(plot_df)*0.8)],
            y=(plot_df.sum(axis=1)).iloc[int(len(plot_df)*0.8)]*0.85,
            text="HCV EV",
            showarrow=False,
            font=dict(size=fonts["annotation"], color="#1f3b1f"),
        )
    fig.add_annotation(
        x=plot_df.index[int(len(plot_df)*0.45)],
        y=(plot_df["Rail Corridor Electric"].iloc[int(len(plot_df)*0.45)]*0.55),
        text="Rail Corridor Electric",
        showarrow=False,
        font=dict(size=fonts["annotation"]),
    )
    fig.add_annotation(
        x=plot_df.index[int(len(plot_df)*0.35)],
        y=(plot_df["Rail Corridor Electric"] + plot_df["Rail Corridor Diesel"] + plot_df["HCV Diesel"]).iloc[int(len(plot_df)*0.35)]*0.55,
        text="HCV Diesel",
        showarrow=False,
        font=dict(size=fonts["annotation"]),
    )

    # Save (keeps the same helper used elsewhere)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    save_figures(fig, str(out_dir), name="fig_4_17_freight_corridor_area")

    # Also save the aggregated data used to plot
    plot_df.to_csv(out_dir / "fig_4_17_freight_corridor_data.csv")

# ────────────────────────── Standalone CLI run ────────────────────────────────
if __name__ == "__main__":
    data_path = project_root / "data" / "processed" /"4_17_transport_freight_rail_corridor_HCV_tkm_wem.csv"
    out = project_root / "outputs" / "charts_and_data" / "fig_4_17_freight_corridor_area"
    df = pd.read_csv(data_path)
    generate_fig_4_17_freight_corridor(df, str(out))
