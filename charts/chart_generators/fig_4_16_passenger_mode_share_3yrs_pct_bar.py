# charts/chart_generators/fig_4_16_passenger_mode_share_3yrs_pct_bar.py
"""
Passenger mode share (percent of total pkm) for 2024, 2030, 2035.
Input : data/processed/4_16_transport_pass_demand_mode_share_3yrs.csv
Output: outputs/charts_and_data/fig_4_16_passenger_mode_share_3yrs_pct_bar/{png,svg}
"""

from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go

# --- project path bootstrap ----------------------------------------------------
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures

# --- toggles -------------------------------------------------------------------
YEARS = [2024, 2030, 2035]

# font sizes
FONTS = dict(
    title=20,            # (not used; title kept empty)
    axis_title=20,       # x- and y-axis title size
    axis_tick=20,        # tick label size
    legend=20,           # legend font size
    legend_itemwidth=80, # legend colour square size
    annotation=20,       # % labels on bars
)

# colours (match previous charts exactly)
COLORS = {
    "Private":       "#b1d79b",
    "MBT":           "#a1d6c7",
    "Bus/BRT":       "#9dbfe8",
    "PassengerRail": "#ea9daa",
}

# labels
X_TITLE = "Share of total annual passenger-kilometers (% pkm)"
Y_TITLE = ""  # years shown on the axis, so keep empty

# --- helpers -------------------------------------------------------------------
def _read_percent(v) -> float:
    """Convert '12.34%' -> 12.34 (float)."""
    if pd.isna(v):
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    return float(s[:-1]) if s.endswith("%") else float(s)

def _prep(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate rows into the four buckets, returning a DataFrame indexed by Year
    with columns [Private, MBT, Bus/BRT, PassengerRail] containing percentages.
    """
    df = df.copy()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df = df[df["Year"].isin(YEARS)]

    # Parse percent column robustly
    # Source column name can be exactly '% of Total SATIMGE' (with spaces/percent sign).
    # Fall back to 'Percent' if needed.
    percent_col = None
    for c in df.columns:
        if "of Total" in c and "%" in c:
            percent_col = c
            break
    if percent_col is None:
        # graceful fallback if user renamed column
        percent_col = "% of Total SATIMGE"
    df["pct"] = df[percent_col].map(_read_percent)

    # bucket masks
    sub = df["Subsubsector"].astype(str)
    m_private = sub.str.contains(r"^(?:Car|SUV|Moto)", case=False, na=False)
    m_busbrt  = sub.str.contains(r"^(?:Bus|BRT)",     case=False, na=False)
    m_mbt     = sub.str.contains(r"^(?:Minibus)",     case=False, na=False)
    m_rail    = sub.str.contains(r"^(?:PassengerRail)", case=False, na=False)

    def sum_pct(mask):
        return df[mask].groupby("Year")["pct"].sum()

    out = pd.DataFrame({
        "Private":       sum_pct(m_private),
        "MBT":           sum_pct(m_mbt),
        "Bus/BRT":       sum_pct(m_busbrt),
        "PassengerRail": sum_pct(m_rail),
    }).reindex(YEARS).fillna(0.0)

    # small numeric tidy so bars always sum exactly 100 within rounding noise
    row_sums = out.sum(axis=1).replace(0, 1.0)
    out = out.mul(100.0 / row_sums, axis=0)
    return out

# --- generator -----------------------------------------------------------------
def generate_fig_4_16_passenger_mode_share(df: pd.DataFrame, output_dir: str, fonts: dict | None = None):
    fonts = {**FONTS, **(fonts or {})}
    data_pct = _prep(df)

    # Horizontal stacked bars: one bar per year (y), percentages along x (0..100)
    fig = go.Figure()
    for cat in ["Bus/BRT", "MBT", "Private", "PassengerRail"]:
        fig.add_trace(
            go.Bar(
                y=data_pct.index.astype(str),
                x=data_pct[cat],
                orientation="h",
                name=cat,
                marker=dict(color=COLORS[cat]),
                text=data_pct[cat].map(lambda v: f"{v:.1f}%"),
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(size=fonts["annotation"], color="#222"),
                hovertemplate=f"{cat}<br>%={{x:.1f}}%<extra></extra>",
                showlegend=True,
            )
        )

    # Apply global layout first, then specific overrides (so nothing gets overwritten)
    apply_common_layout(fig)

    fig.update_layout(
        title="",
        barmode="stack",
        bargap=0.25,
        margin=dict(l=80, r=260, t=300, b=100),
        legend=dict(
            orientation="v",
            yanchor="top", y=1.0,
            xanchor="left", x=1.02,
            bgcolor="rgba(255,255,255,0)",
            font=dict(size=fonts["legend"]),
            itemwidth=fonts["legend_itemwidth"],
        ),
        width=900, height=160,
    )

    # Axes
    fig.update_xaxes(
        title_text=X_TITLE,
        title_font=dict(size=fonts["axis_title"]),
        tickfont=dict(size=fonts["axis_tick"]),
        range=[0, 100],
        ticks="outside",
        dtick=10,
        showgrid=True,
        gridcolor="rgba(0,0,0,0.08)",
        zeroline=False,
    )
    fig.update_yaxes(
        title_text=Y_TITLE,
        title_font=dict(size=fonts["axis_title"]),
        tickfont=dict(size=fonts["axis_tick"]),
        categoryorder="array",
        categoryarray=[str(y) for y in YEARS],  # keep 2024->2035 top->bottom
    )

    # Save + data
    out_dir = Path(output_dir); out_dir.mkdir(parents=True, exist_ok=True)
    base = "fig_4_16_passenger_mode_share_3yrs_pct_bar"
    save_figures(fig, str(out_dir), name=base)
    data_pct.to_csv(out_dir / f"{base}_data.csv")

# --- CLI -----------------------------------------------------------------------
if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "4_16_transport_pass_demand_mode_share_3yrs.csv"
    out = project_root / "outputs" / "charts_and_data" / "fig_4_16_passenger_mode_share_3yrs_pct_bar"
    df_in = pd.read_csv(data_path)
    generate_fig_4_16_passenger_mode_share(df_in, str(out))
