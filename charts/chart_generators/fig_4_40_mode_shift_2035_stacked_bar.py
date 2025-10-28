# charts/chart_generators/fig_4_40_mode_shift_2035_stacked_bar.py
"""
Passenger & Freight mode shifting (2035).
Input : data/processed/4_40_transport_mode_shift_2035_stacked_bar.csv
Output: outputs/charts_and_data/fig_4_40_mode_shift_2035_stacked_bar/{png,svg}
"""

from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- project path bootstrap ----------------------------------------------------
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures

# --- labels / toggles ----------------------------------------------------------
YEAR = 2035
Y_LABEL_LEFT  = "Passenger-kilometers (billion pkm)"
Y_LABEL_RIGHT = "Tonne-kilometers (billion tkm)"

# % labels inside segments
TEXT_SIZE = 18
# y-axis title sizes
YAXIS_LABEL_SIZE = 20

# NEW: subplot title size
SUBPLOT_TITLE_SIZE = 22
# NEW: x-axis label texts (kept like your current figure; right shows the year)
XAXIS_LABEL_LEFT  = ""          # left subplot x-axis title
XAXIS_LABEL_RIGHT = ""   # right subplot x-axis title
# NEW: x-axis label font size
XAXIS_LABEL_SIZE  = 16
# NEW: x-axis tick angle
X_TICK_ANGLE = 0
# NEW: optional renaming of scenario tick labels
XTICK_RENAME = {
    "NDC_BASE-RG": "WEM",
    "NDC_BASE-PassM-RG": "WEM with Passenger<br>Modeshifting",
    "NDC_BASE-FreiM-RG": "WEM with Freight<br>Modeshifting",
}

# Keep colours EXACT
PAX_COLORS = {
    "Private":       "#b1d79b",
    "MBT":           "#a1d6c7",
    "Bus/BRT":       "#9dbfe8",
    "PassengerRail": "#ea9daa",
}
FREIGHT_COLORS = {
    "Freight rail":  "#a678b4",
    "Freight road":  "#d8b6d9",
}

# RHS legend (with toggles)
LEGEND_FONT_SIZE = 20        # NEW
LEGEND_ITEMWIDTH = 80        # NEW (controls the colour square width)
LEGEND_KW = dict(
    orientation="v",
    yanchor="top", y=1.0,
    xanchor="left", x=1.02,
    bgcolor="rgba(255,255,255,0)",
    font=dict(size=LEGEND_FONT_SIZE),
    itemwidth=LEGEND_ITEMWIDTH,
    itemsizing="constant",
)

# --- prep helpers --------------------------------------------------------------
def _prep_passenger(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate to Private, MBT, Bus/BRT, PassengerRail for both scenarios."""
    df = df[(df["Year"] == YEAR) & df["Scenario"].isin(["NDC_BASE-PassM-RG", "NDC_BASE-RG"])].copy()

    # buckets
    private = df["Subsector"].str.contains(r"^(?:Car|SUV|Moto)", case=False, na=False)
    busbrt  = df["Subsector"].str.contains(r"^(?:Bus|BRT)", case=False, na=False)
    mbt     = df["Subsector"].str.contains(r"^(?:Minibus)", case=False, na=False)
    rail    = df["Subsector"].str.contains(r"^(?:PassengerRail)", case=False, na=False)

    def bucket_sum(mask): return df[mask].groupby("Scenario")["SATIMGE"].sum()

    out = pd.DataFrame({
        "Private":       bucket_sum(private),
        "MBT":           bucket_sum(mbt),
        "Bus/BRT":       bucket_sum(busbrt),
        "PassengerRail": bucket_sum(rail),
    }).fillna(0.0)

    # percentages per scenario
    totals = out.sum(axis=1).replace(0, 1.0)
    pct = out.div(totals, axis=0) * 100
    return out, pct

def _prep_freight(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate Freight rail/road for both scenarios."""
    df = df[(df["Year"] == YEAR) & df["Scenario"].isin(["NDC_BASE-FreiM-RG", "NDC_BASE-RG"])
           & df["Subsector"].str.contains("^Freight", na=False)].copy()
    df["Cat"] = df["Subsector"].map({"FreightRail": "Freight rail", "FreightRoad": "Freight road"}).fillna(df["Subsector"])
    out = df.pivot_table(index="Scenario", columns="Cat", values="SATIMGE", aggfunc="sum").fillna(0.0)
    totals = out.sum(axis=1).replace(0, 1.0)
    pct = out.div(totals, axis=0) * 100
    return out, pct

# --- generator -----------------------------------------------------------------
def generate_fig_4_40_mode_shift(df: pd.DataFrame, output_dir: str) -> None:
    pax_vals, pax_pct = _prep_passenger(df)
    frt_vals, frt_pct = _prep_freight(df)

    # Keep scenario order consistent with your examples
    pax_order = ["NDC_BASE-RG", "NDC_BASE-PassM-RG"]
    frt_order = ["NDC_BASE-RG", "NDC_BASE-FreiM-RG"]
    pax_vals = pax_vals.reindex(pax_order)
    pax_pct  = pax_pct.reindex(pax_order)
    frt_vals = frt_vals.reindex(frt_order)
    frt_pct  = frt_pct.reindex(frt_order)

    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.9, 0.9],
        horizontal_spacing=0.15,
        subplot_titles=("Passenger Mode shifting", "Freight Mode shifting"),
        shared_yaxes=False,
    )

    # --- Passenger subplot (left): raw SATIMGE with % labels -------------------
    for cat in ["Private", "MBT", "Bus/BRT", "PassengerRail"]:
        fig.add_trace(
            go.Bar(
                x=pax_vals.index,
                y=pax_vals[cat],
                text=pax_pct[cat].map(lambda v: f"{v:.1f}%"),
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(size=TEXT_SIZE, color="#333"),
                marker=dict(color=PAX_COLORS[cat]),
                name=cat,
                showlegend=True,
            ),
            row=1, col=1
        )

    # --- Freight subplot (right): raw SATIMGE with % labels --------------------
    for cat in ["Freight rail", "Freight road"]:
        fig.add_trace(
            go.Bar(
                x=frt_vals.index,
                y=frt_vals[cat],
                text=frt_pct[cat].map(lambda v: f"{v:.1f}%"),
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(size=TEXT_SIZE, color="#333"),
                marker=dict(color=FREIGHT_COLORS[cat]),
                name=cat,
                showlegend=True,
            ),
            row=1, col=2
        )

    # Common bar settings
    fig.update_traces(marker_line_width=0)

    # Apply global layout FIRST, then overrides
    apply_common_layout(fig)
    fig.update_layout(
        title="",
        barmode="stack",
        margin=dict(l=90, r=260, t=40, b=80),
        legend=dict(**LEGEND_KW),
        width=1100, height=720,
    )

    # Subplot title font sizes (toggle)
    for a in fig.layout.annotations:
        if a.text in ("Passenger Mode shifting", "Freight Mode shifting"):
            a.font.size = SUBPLOT_TITLE_SIZE

    # x-axis titles + font sizes (toggles)
    fig.update_xaxes(title_text=XAXIS_LABEL_LEFT,
                     title_font=dict(size=XAXIS_LABEL_SIZE),
                     row=1, col=1)
    fig.update_xaxes(title_text=XAXIS_LABEL_RIGHT,
                     title_font=dict(size=XAXIS_LABEL_SIZE),
                     row=1, col=2)

    # y-axes (raw totals) + sizes
    fig.update_yaxes(title_text=Y_LABEL_LEFT,  title_font=dict(size=YAXIS_LABEL_SIZE), row=1, col=1)
    fig.update_yaxes(title_text=Y_LABEL_RIGHT, title_font=dict(size=YAXIS_LABEL_SIZE), row=1, col=2)

    # Tick renaming + angle (toggles)
    pax_ticks = [XTICK_RENAME.get(s, s) for s in pax_vals.index]
    frt_ticks = [XTICK_RENAME.get(s, s) for s in frt_vals.index]
    fig.update_xaxes(tickmode="array", tickvals=list(pax_vals.index), ticktext=pax_ticks,
                     tickangle=X_TICK_ANGLE, row=1, col=1)
    fig.update_xaxes(tickmode="array", tickvals=list(frt_vals.index), ticktext=frt_ticks,
                     tickangle=X_TICK_ANGLE, row=1, col=2)

    # Save + data
    out_dir = Path(output_dir); out_dir.mkdir(parents=True, exist_ok=True)
    base = "fig_4_40_mode_shift_2035_stacked_bar"
    save_figures(fig, str(out_dir), name=base)
    pax_vals.assign(panel="Passenger").to_csv(out_dir / f"{base}_passenger_values.csv")
    pax_pct.assign(panel="Passenger").to_csv(out_dir / f"{base}_passenger_percent.csv")
    frt_vals.assign(panel="Freight").to_csv(out_dir / f"{base}_freight_values.csv")
    frt_pct.assign(panel="Freight").to_csv(out_dir / f"{base}_freight_percent.csv")

# --- CLI -----------------------------------------------------------------------
if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "4_40_transport_mode_shift_2035_stacked_bar.csv"
    df = pd.read_csv(data_path)
    out = project_root / "outputs" / "charts_and_data" / "fig_4_40_mode_shift_2035_stacked_bar"
    generate_fig_4_40_mode_shift(df, str(out))
