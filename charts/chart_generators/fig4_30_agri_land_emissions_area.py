# charts/chart_generators/fig4_30_agri_land_emissions_area.py
#
# Figure 4.30 — Agriculture (non-energy) & Land emissions
# Stacked areas, shared y-axis, years 2024–2035
#
# Expected CSV columns:
#   "IPCC_Category_L1", "IPCC_Category_L2", "Year", "MtCO2-eq"
#
# CLI:
#   python charts/chart_generators/fig4_30_agri_land_emissions_area.py

from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import yaml
import shutil
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── project root on path ────────────────────────────────────────────
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures

# ── config (dev mode) ───────────────────────────────────────────────
config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    dev_mode = False

YEAR_ORDER = list(range(2024, 2036))
Y_LABEL = "CO₂-eq Emissions (Mt)"

# Colours matched to the reference figure
AGRI_COLORS = {
    "3A Enteric fermentation":        "#2A6FB9",  # clear blue
    "3B Manure management":           "#6FB1E7",  # light azure
    "3D Agricultural soils":          "#F0A22A",  # amber
    "3F Field burning of agricultural residues": "#2BA24D",  # green
    "3G Liming":                      "#8FD26B",  # light green
    "3H Urea application":            "#F6C29F",  # peach
}
LAND_COLORS = {
    "4A Forest land":                 "#D34B3F",  # brick red (negative)
    "4B Cropland":                    "#F87EB9",  # pink
    "4C Grassland":                   "#2A6FB9",  # blue
    "4D Wetlands":                    "#6B6BD6",  # violet-blue
    "4E Settlements":                 "#BFBFBF",  # grey
    "4F Other land":                  "#6D4F2B",  # brown
    "4G Harvested wood products":     "#E7A8C5",  # rose (small negative)
}

AGRI_ORDER = [
    "3H Urea application",
    "3G Liming",
    "3F Field burning of agricultural residues",
    "3D Agricultural soils",
    "3B Manure management",
    "3A Enteric fermentation",
]
LAND_ORDER = [
    "4G Harvested wood products",
    "4F Other land",
    "4E Settlements",
    "4D Wetlands",
    "4C Grassland",
    "4B Cropland",
    "4A Forest land",
]

# Categories that should stack downward from zero
NEGATIVE_LAND = {"4A Forest land", "4G Harvested wood products"}

# ── helpers ─────────────────────────────────────────────────────────
def _tidy(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={
        "IPCC_Category_L1": "L1",
        "IPCC_Category_L2": "L2",
        "MtCO2-eq": "MtCO2eq",
    }).copy()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["MtCO2eq"] = pd.to_numeric(df["MtCO2eq"], errors="coerce")
    df = df[df["Year"].isin(YEAR_ORDER)].copy()
    df = (
        df.groupby(["L1", "L2", "Year"], as_index=False)["MtCO2eq"].sum()
          .sort_values(["L1", "L2", "Year"])
    )
    return df

def _stack_area(
    fig: go.Figure,
    frame: pd.DataFrame,
    row: int, col: int,
    order: list[str],
    colors: dict[str, str],
    title_text: str,
    negative_cats: set[str] | None = None,
) -> None:
    """Add a stacked area set into the given subplot.

    If `negative_cats` is provided, those series are stacked below zero
    using a separate stackgroup so they start at 0 and go downward.
    """
    negative_cats = negative_cats or set()
    x_vals = [str(y) for y in YEAR_ORDER]

    # Separate stackgroups for + and - so they each build from 0.
    first_added = {"pos": False, "neg": False}

    for cat in order:
        series = (
            frame[frame["L2"] == cat]
            .set_index("Year")["MtCO2eq"]
            .reindex(YEAR_ORDER)
            .fillna(0.0)
        )
        y_vals = series.values.tolist()

        is_negative_group = cat in negative_cats
        group_key = "neg" if is_negative_group else "pos"
        stackgroup_name = f"{group_key}-g-{row}-{col}"
        fillmode = "tozeroy" if not first_added[group_key] else "tonexty"
        first_added[group_key] = True

        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="lines",
                line=dict(width=0, color=colors.get(cat, "#999")),
                fill=fillmode,
                stackgroup=stackgroup_name,
                name=cat,
                hovertemplate=f"{cat}<br>%{{x}}: %{{y:.2f}} Mt<extra></extra>",
                showlegend=False,
            ),
            row=row, col=col
        )

    # Centered subplot title
    ax = "" if (row, col) == (1, 1) else "2"
    fig.add_annotation(
        text=title_text,
        xref=f"x{ax} domain", yref=f"y{ax} domain",
        x=0.5, y=1.08, showarrow=False,
        font=dict(size=20, color="#222", family="Inter, Arial, sans-serif"),
    )

# ── main ────────────────────────────────────────────────────────────
def generate_fig4_30_agri_land_emissions_area(df: pd.DataFrame, output_dir: str) -> None:
    print("generating figure 4.30: Agriculture & Land emissions (stacked areas, 2024–2035)")
    print(f"📂 Output directory: {output_dir}")

    df = _tidy(df)
    agri = df[df["L1"].str.startswith("3")].copy()
    land = df[df["L1"].str.startswith("4")].copy()

    fig = make_subplots(
        rows=1, cols=2,
        shared_yaxes=True,
        horizontal_spacing=0.10,
        specs=[[{"type": "xy"}, {"type": "xy"}]],
    )

    _stack_area(fig, agri, 1, 1, AGRI_ORDER, AGRI_COLORS,
                "3 · Agriculture (non-energy)")
    _stack_area(fig, land, 1, 2, LAND_ORDER, LAND_COLORS,
                "4 · Land", negative_cats=NEGATIVE_LAND)

    # ---- Standard legend at bottom, ordered: all 3* then all 4* ----
    legend_items = list(AGRI_COLORS.items()) + list(LAND_COLORS.items())
    for name, color in legend_items:
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(symbol="square", size=18, color=color, line=dict(width=0)),
                name=name,
                hoverinfo="skip",
                showlegend=True,
            ),
            row=1, col=2
        )

    # Layout & legend
    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",
        margin=dict(l=84, r=60, t=60, b=130),
        width=1600, height=1000,
        legend_title_text="",
        showlegend=True,
        legend=dict(
            orientation="h",
            xanchor="left", x=0.06,   # starts under the left panel
            yanchor="top",  y=-0.12,  # below the x axis labels
            traceorder="normal",
            font=dict(size=18),
            itemwidth=80,
            tracegroupgap=12,
        ),
    )

    # X-axes
    x_ticks = [str(y) for y in YEAR_ORDER]
    fig.update_xaxes(tickangle=-45, tickmode="array", tickvals=x_ticks, row=1, col=1)
    fig.update_xaxes(tickangle=-45, tickmode="array", tickvals=x_ticks, row=1, col=2)

    # Shared Y-axis: fixed range, ticks visible on both subplots
    fig.update_yaxes(
        title_text=Y_LABEL,
        title_font=dict(size=17),
        range=[-70, 60],
        row=1, col=1
    )
    fig.update_yaxes(matches="y", showticklabels=True, title_text="", row=1, col=2)

    if dev_mode:
        print("👩‍💻 dev_mode ON — preview only (no files written)")
        return

    out_dir = Path(output_dir); out_dir.mkdir(parents=True, exist_ok=True)
    base = "fig4_30_agri_land_emissions_area"
    save_figures(fig, str(out_dir), name=base)
    df.to_csv(out_dir / f"{base}_data.csv", index=False)

    # Optional gallery copy
    gallery_dir = project_root / "outputs" / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    src = out_dir / f"{base}_report.png"
    if src.exists():
        shutil.copy2(src, gallery_dir / src.name)

# ── CLI ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "4_30_agri_land_emissions_area.csv"
    if not data_path.exists():
        raise FileNotFoundError(
            f"Data file not found at {data_path}.\n"
            "Expected columns: 'IPCC_Category_L1', 'IPCC_Category_L2', 'Year', 'MtCO2-eq'."
        )
    df = pd.read_csv(data_path)
    out = project_root / "outputs" / "charts_and_data" / "fig4_30_agri_land_emissions_area"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig4_30_agri_land_emissions_area(df, str(out))
