# charts/chart_generators/fig_4_17_freight_corridor_area.py
"""
Freight Corridor area chart (tkm).
Input : data/processed/4_17_transport_freight_rail_corridor_HCV_tkm_wem.csv
Output: outputs/charts_and_data/fig_4_17_freight_corridor_area/{png,svg}
"""
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))
else:
    project_root = Path(__file__).resolve().parents[2]

import pandas as pd
import plotly.graph_objects as go
from charts.common.style import apply_common_layout
from charts.common.save import save_figures

# --- font toggles --------------------------------------------------------------
DEFAULT_FONTS = dict(title=20, axis=22, tick=16, legend=22, annotation=16)

# --- softened colours ----------------------------------------------------------
COLORS = {
    "HCV EV":                 "#7fbf7b",  # softer green
    "HCV Diesel":             "#f4c69a",  # peach
    "Rail Corridor Electric": "#a69bd6",  # light lavender
    "Rail Corridor Diesel":   "#e58b85",  # muted red
}
ORDER_BOTTOM_TO_TOP = [
    "Rail Corridor Electric",
    "Rail Corridor Diesel",
    "HCV Diesel",
    "HCV EV",
]
TITLE = ""
Y_LABEL = "Freight tonne-kilometers (billion tkm)"

# --- helpers -------------------------------------------------------------------
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
    out = {k: (v.groupby("Year")["SATIMGE"].sum().reindex(idx, fill_value=0.0)) for k, v in parts.items()}
    return pd.DataFrame(out)[ORDER_BOTTOM_TO_TOP]

# --- generator -----------------------------------------------------------------
def generate_fig_4_17_freight_corridor(df: pd.DataFrame, output_dir: str, fonts: dict | None = None):
    fonts = {**DEFAULT_FONTS, **(fonts or {})}

    df = df.copy()
    df["SATIMGE"] = pd.to_numeric(df["SATIMGE"], errors="coerce").fillna(0.0)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype(int)
    # keep only 2024–2035
    df = df[df["Year"].between(2024, 2035)]
    plot_df = _aggregate_four_categories(df)


    fig = go.Figure()

    # --- stacked areas (legend off – we’ll add square legend markers separately)
    for i, col in enumerate(plot_df.columns):
        fig.add_trace(
            go.Scatter(
                x=plot_df.index,
                y=plot_df[col].values,
                mode="none",                         # area only
                line=dict(width=0, color=COLORS[col]),
                name=col,
                stackgroup="tkm",
                fill="tozeroy" if i == 0 else "tonexty",
                fillcolor=COLORS[col],
                hovertemplate=f"{col}<br>Year=%{{x}}<br>tkm=%{{y:.2f}}<extra></extra>",
                showlegend=False,
            )
        )

    # --- apply common layout FIRST so our updates aren’t overwritten
    apply_common_layout(fig)

    # --- axis & page layout
    years = [int(y) for y in plot_df.index]
    fig.update_layout(
        title=dict(text=TITLE, x=0.5, font=dict(size=fonts["title"])),
        xaxis=dict(
            title=None,
            tickmode="array",
            tickvals=years,
            ticktext=[str(y) for y in years],
            tickangle=-45,
            tickfont=dict(size=fonts["tick"]),
        ),
        yaxis=dict(
            title=dict(text=Y_LABEL, font=dict(size=fonts["axis"])),
            tickfont=dict(size=fonts["tick"]),
            rangemode="tozero",
        ),
        margin=dict(l=90, r=250, t=40, b=90),
        hovermode="x unified",
    )

    # --- square legend on RHS (legend-only marker traces)
    for col in ORDER_BOTTOM_TO_TOP:
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(symbol="square", size=18, color=COLORS[col]),
                name=col,
                showlegend=True,
                hoverinfo="skip",
            )
        )
    fig.update_layout(
        legend=dict(
            orientation="v",
            x=1.02, xanchor="left",
            y=1.0, yanchor="top",
            bgcolor="rgba(255,255,255,0.0)",
            font=dict(size=fonts["legend"]),
            itemsizing="constant"
        )
    )

    # --- knobs ---------------------------------------------------------
    HCV_EV_LABEL = dict(x=0.78, y=0.75)  # paper coords (0..1), tweak these
    HCV_EV_LABEL_SHIFT = dict(xshift=0, yshift=0)  # pixel nudge if needed

    # after apply_common_layout(fig) and fig.update_layout(...)
    fig.add_annotation(
        x=HCV_EV_LABEL["x"], y=HCV_EV_LABEL["y"],
        xref="paper", yref="paper",
        text="HCV EV",
        showarrow=False,
        xanchor="center", yanchor="middle",
        font=dict(size=fonts["annotation"]),
        **HCV_EV_LABEL_SHIFT
    )

    idx_re = int(len(plot_df) * 0.40)
    fig.add_annotation(
        x=plot_df.index[idx_re],
        y=(plot_df["Rail Corridor Electric"].iloc[idx_re] * 0.6),
        text="Rail Corridor Electric",
        showarrow=False,
        font=dict(size=fonts["annotation"]),
    )
    idx_dsl = int(len(plot_df) * 0.35)
    fig.add_annotation(
        x=plot_df.index[idx_dsl],
        y=(plot_df["Rail Corridor Electric"] + plot_df["Rail Corridor Diesel"] + plot_df["HCV Diesel"]).iloc[idx_dsl] * 0.55,
        text="HCV Diesel",
        showarrow=False,
        font=dict(size=fonts["annotation"]),
    )

    out_dir = Path(output_dir); out_dir.mkdir(parents=True, exist_ok=True)
    save_figures(fig, str(out_dir), name="fig_4_17_freight_corridor_area")
    plot_df.to_csv(out_dir / "fig_4_17_freight_corridor_data.csv")

# --- CLI -----------------------------------------------------------------------
if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "4_17_transport_freight_rail_corridor_HCV_tkm_wem.csv"
    out = project_root / "outputs" / "charts_and_data" / "fig_4_17_freight_corridor_area"
    df = pd.read_csv(data_path)
    generate_fig_4_17_freight_corridor(df, str(out))
