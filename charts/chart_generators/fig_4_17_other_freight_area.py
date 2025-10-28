# charts/chart_generators/fig_4_17_other_freight_area.py
"""
Other Freight — stacked area (tkm) with 3 vertical subplots:
1) LCVs           -> [LCV EV, LCV Oil]
2) Rail Export    -> [Rail Export (Bulk Mining) Electric, Rail Export (Bulk Mining) Diesel]
3) Rail Other     -> [Rail Other Electric, Rail Other Diesel]

Input : data/processed/4_17_transport_freight_rail_other_LCV_tkm_wem.csv
Output: outputs/charts_and_data/fig_4_17_other_freight_area/{png,svg}
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
from plotly.subplots import make_subplots
from charts.common.style import apply_common_layout
from charts.common.save import save_figures

# --- font toggles (kept consistent with your corridor chart) -------------------
DEFAULT_FONTS = dict(title=20, axis=22, tick=16, legend=22, annotation=16)

# --- softened colours (close to your style; distinct by tech) ------------------
COLORS = {
    "LCV EV":                                   "#7fbf7b",  # soft green
    "LCV Oil":                                  "#f4c69a",  # peach
    "Rail Export (Bulk Mining) Electric":       "#9ecae1",  # soft blue
    "Rail Export (Bulk Mining) Diesel":         "#6baed6",  # deeper blue
    "Rail Other Electric":                      "#b3cde3",  # light blue
    "Rail Other Diesel":                        "#8c96c6",  # blue-violet
}

ROW_TITLES = ["LCVs", "Rail Export (Bulk Mining)", "Rail Other"]
TITLE = ""
Y_LABEL = "Tonne-kilometers (billion tkm)"
Y_RANGE = (0, 30)   # <- fixed scale for all rows
DEFAULT_FONTS = dict(title=20, axis=16, tick=14, legend=18, annotation=16)


# ------------------------------ helpers ---------------------------------------
def _years_idx(df: pd.DataFrame) -> pd.Index:
    years = sorted(df["Year"].dropna().astype(int).unique())
    years = [y for y in years if 2024 <= y <= 2035]
    return pd.Index(years, name="Year")

def _sum_by_year(df: pd.DataFrame, mask: pd.Series, years_idx: pd.Index) -> pd.Series:
    return (df[mask].groupby("Year")["SATIMGE"].sum()
            .reindex(years_idx, fill_value=0.0))

def _is(df: pd.DataFrame, *, sub=None, tech_substr=None) -> pd.Series:
    ok = pd.Series(True, index=df.index)
    if sub is not None:
        ok &= df["Subsubsector"].fillna("").str.contains(sub, case=False, regex=False)
    if tech_substr is not None:
        ok &= df["TechDescription"].fillna("").str.contains(tech_substr, case=False, regex=False)
    return ok

def _build_series(df: pd.DataFrame) -> dict:
    """Return a dict: row -> {name: series} for 2024–2035."""
    idx = _years_idx(df)

    # --- Row 1: LCVs
    lcv_ev  = _sum_by_year(df, _is(df, sub="LCVElectric"), idx)
    # LCV Oil = everything LCV that is not Electric (diesel/gasoline/hybrid)
    lcv_oil = _sum_by_year(df, _is(df, sub="LCV") & ~_is(df, sub="LCVElectric"), idx)

    # --- Row 2: Rail Export (Bulk Mining)
    rex_ele = _sum_by_year(df, _is(df, sub="FreightRail", tech_substr="Rail Export (bulk mining)") &
                                _is(df, tech_substr="Elec"), idx)
    rex_dsl = _sum_by_year(df, _is(df, sub="FreightRail", tech_substr="Rail Export (bulk mining)") &
                                _is(df, tech_substr="Oil"), idx)

    # --- Row 3: Rail Other
    r_other_ele = _sum_by_year(df, _is(df, tech_substr="Rail Other") &
                                    _is(df, tech_substr="Electricity"), idx)
    r_other_dsl = _sum_by_year(df, _is(df, tech_substr="Rail Other") &
                                    _is(df, tech_substr="Oil Diesel"), idx)

    return {
        1: {
            "LCV EV":  lcv_ev,
            "LCV Oil": lcv_oil,
        },
        2: {
            "Rail Export (Bulk Mining) Electric": rex_ele,
            "Rail Export (Bulk Mining) Diesel":   rex_dsl,
        },
        3: {
            "Rail Other Electric": r_other_ele,
            "Rail Other Diesel":   r_other_dsl,
        },
    }

# ------------------------------ generator -------------------------------------
def generate_fig_4_17_other_freight(df: pd.DataFrame, output_dir: str, fonts: dict | None = None):
    fonts = {**DEFAULT_FONTS, **(fonts or {})}
    df = df.copy()

    # clean & restrict years
    df["SATIMGE"] = pd.to_numeric(df["SATIMGE"], errors="coerce").fillna(0.0)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype(int)
    df = df[df["Year"].between(2024, 2035)]

    series = _build_series(df)
    years = series[1]["LCV EV"].index.tolist()

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        row_heights=[0.34, 0.33, 0.33],
        vertical_spacing=0.08,
        subplot_titles=ROW_TITLES,
    )

    # --- draw stacked areas per row (unique stackgroup per row)
    for row in (1, 2, 3):
        stack = f"tkm_row_{row}"
        cumulative_first = True
        for name, ser in series[row].items():
            fig.add_trace(
                go.Scatter(
                    x=ser.index, y=ser.values,
                    mode="none",  # area only
                    line=dict(width=0, color=COLORS[name]),
                    name=name,
                    stackgroup=stack,
                    fill="tozeroy" if cumulative_first else "tonexty",
                    fillcolor=COLORS[name],
                    hovertemplate=f"{name}<br>Year=%{{x}}<br>tkm=%{{y:.2f}}<extra></extra>",
                    showlegend=False,   # legend built later with square markers
                ),
                row=row, col=1
            )
            cumulative_first = False

    # --- apply common layout FIRST
    apply_common_layout(fig)

    # --- x/y axes, legend, margins
    fig.update_layout(
        title=dict(text=TITLE, x=0.5, font=dict(size=fonts["title"])),
        margin=dict(l=90, r=280, t=50, b=90),
        hovermode="x unified",
    )
    # same y-scale for all 3 subplots
    for r in (1, 2, 3):
        fig.update_yaxes(
            range=list(Y_RANGE), 
            title=dict(text=Y_LABEL, font=dict(size=fonts["axis"])),        
            tick0=0, dtick=10,           # optional: consistent ticks
            row=r, col=1
        )


    # y-axis titles
    fig.update_yaxes(title_text=Y_LABEL, title_font=dict(size=fonts["axis"]),
                     tickfont=dict(size=fonts["tick"]), rangemode="tozero", row=1, col=1)
    fig.update_yaxes(title_text=Y_LABEL, title_font=dict(size=fonts["axis"]),
                     tickfont=dict(size=fonts["tick"]), rangemode="tozero", row=2, col=1)
    fig.update_yaxes(title_text=Y_LABEL, title_font=dict(size=fonts["axis"]),
                     tickfont=dict(size=fonts["tick"]), rangemode="tozero", row=3, col=1)

    # x-axis ticks (years only, -45°)
    fig.update_xaxes(
        title=None, tickmode="array",
        tickvals=years, ticktext=[str(y) for y in years],
        tickangle=-45, tickfont=dict(size=fonts["tick"]),
        row=3, col=1
    )
    # ensure top/middle rows have the same tick settings without labels crowding
    fig.update_xaxes(
        tickmode="array", tickvals=years, ticktext=[str(y) for y in years],
        tickangle=-45, tickfont=dict(size=fonts["tick"]),
        row=1, col=1
    )
    fig.update_xaxes(
        tickmode="array", tickvals=years, ticktext=[str(y) for y in years],
        tickangle=-45, tickfont=dict(size=fonts["tick"]),
        row=2, col=1
    )

    # --- build a RHS legend with square swatches (one entry per series name)
    for name in ["LCV EV", "LCV Oil",
                 "Rail Export (Bulk Mining) Electric", "Rail Export (Bulk Mining) Diesel",
                 "Rail Other Electric", "Rail Other Diesel"]:
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None], mode="markers",
                marker=dict(symbol="square", size=18, color=COLORS[name]),
                name=name, showlegend=True, hoverinfo="skip",
            )
        )
    fig.update_layout(
        legend=dict(
            orientation="v",
            x=1.02, xanchor="left",
            y=1.0, yanchor="top",
            bgcolor="rgba(255,255,255,0.0)",
            font=dict(size=fonts["legend"]),
            itemsizing="constant",
        )
    )

    out_dir = Path(output_dir); out_dir.mkdir(parents=True, exist_ok=True)
    save_figures(fig, str(out_dir), name="fig_4_17_other_freight_area")
    # export tidy CSV (stacked)
    tidy = []
    for row, mapping in series.items():
        section = ROW_TITLES[row-1]
        for name, ser in mapping.items():
            tidy.append(pd.DataFrame({"Section": section, "Category": name, "Year": ser.index, "SATIMGE": ser.values}))
    pd.concat(tidy).to_csv(out_dir / "fig_4_17_other_freight_area_data.csv", index=False)

# --- CLI -----------------------------------------------------------------------
if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "4_17_transport_freight_rail_other_LCV_tkm_wem.csv"
    out = project_root / "outputs" / "charts_and_data" / "fig_4_17_other_freight_area"
    df = pd.read_csv(data_path)
    generate_fig_4_17_other_freight(df, str(out))
