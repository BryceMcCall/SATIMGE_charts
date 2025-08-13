# double chart for electricity sent out and consumed

import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.graph_objects as go
from charts.common.style import apply_common_layout
from charts.common.save import save_figures
import plotly.express as px
from plotly.subplots import make_subplots
import yaml


project_root = Path(__file__).resolve().parents[2]
config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path) as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    dev_mode = False


def _add_footer_legend(fig: go.Figure, items, domain, *,
                       y=-0.18, per_row=6, swatch_w=0.015, swatch_h=0.02, gap=0.006,
                       font_size=12):
    """
    Draw a legend-like footer under a subplot.
    - items: list[tuple(name, color)]
    - domain: (x0, x1) of the subplot (fig.layout.xaxis(N).domain)
    - y: vertical paper coordinate for the first row (negative places it below)
    """
    x0, x1 = float(domain[0]), float(domain[1])
    width = x1 - x0

    # horizontal cell size (swatch + gap + text space). We distribute evenly.
    cols = max(1, per_row)
    cell_w = width / cols

    row = 0
    col = 0
    for name, color in items:
        # left edge of this cell
        cell_left = x0 + col * cell_w
        # swatch rectangle position
        rect_x0 = cell_left
        rect_x1 = rect_x0 + swatch_w
        rect_y0 = y - row * (swatch_h + 0.05)
        rect_y1 = rect_y0 + swatch_h

        fig.add_shape(
            type="rect",
            xref="paper", yref="paper",
            x0=rect_x0, x1=rect_x1, y0=rect_y0, y1=rect_y1,
            line=dict(width=1, color=color),
            fillcolor=color,
            layer="above"
        )

        # label annotation (aligned left, a small gap after swatch)
        label_x = rect_x1 + gap
        label_y = rect_y0 + swatch_h / 2.0
        fig.add_annotation(
            xref="paper", yref="paper",
            x=label_x, y=label_y,
            xanchor="left", yanchor="middle",
            text=name,
            showarrow=False,
            font=dict(size=font_size)
        )

        col += 1
        if col >= cols:
            col = 0
            row += 1


def generate_ElecTWh_chart(df: pd.DataFrame, output_dir: str) -> go.Figure:
    # Colour mapping for subsectors (Sent out, left subplot)
    color_map_left = {
        "ECoal": "#505457",
        "ENuclear": "#ca1d90",
        "EHydro": "#8c564b",
        "EGas": "#ee2c4c",
        "EOil": "#e66177",
        "EBiomass": "#03ff2d",
        "EWind": "#3f1ae6",
        "EPV": "#e6e21a",
        "ECSP": "#fc5c34",
        "EHybrid": "#b39ddb",
        "Imports": "#9467bd",
    }

    # Colour mapping for consumption sectors (Electricity use, right subplot)
    color_map_right = {
        "Industry": "#f28e2b",
        "Residential": "#59a14f",
        "Commerce": "#4e79a7",
        "Transport": "#e15759",
        "Supply": "#76b7b2",
        "Agriculture": "#8cd17d",
    }

    # Exclude processes not needed
    pwr_exclude = ["ETrans", "EDist", "EBattery", "EPumpStorage", "Demand", "AutoGen-Chemcials"]

    # -------- Left subplot data (Sent out)
    filtered_pwr = df[
        (df["Scenario"] == "NDC_BASE-RG")
        & (df["Sector"] == "Power")
        & (df["Year"].between(2024, 2035))
        & (~df["Subsector"].isin(pwr_exclude))
    ].copy()

    df_pwr_out = (
        filtered_pwr[
            (filtered_pwr["Indicator"] == "FlowOut") & (filtered_pwr["Commodity"] == "ELCC")
        ]
        .groupby(["Year", "Subsector"], as_index=False)["SATIMGE"]
        .sum()
    )
    df_pwr_out["SATIMGE"] *= (1 / 3.6)  # to TWh

    fig_left = px.area(
        df_pwr_out,
        x="Year",
        y="SATIMGE",
        color="Subsector",
        color_discrete_map=color_map_left,
        category_orders={"Subsector": list(color_map_left.keys())}
    )

    # -------- Right subplot data (Electricity use)
    use_keep = ["Agriculture", "Commerce", "Industry", "Residential", "Transport", "Supply"]
    df_use = df[
        (df["Scenario"] == "NDC_BASE-RG")
        & (df["Sector"] != "Power")
        & (df["Year"].between(2024, 2035))
        & (df["Indicator"] == "FlowIn")
        & (df["Short Description"] == "Electricity")
        & (df["Sector"].isin(use_keep))
    ].copy()

    df_use["SATIMGE"] *= (1 / 3.6)  # to TWh
    df_use = df_use.groupby(["Year", "Sector"], as_index=False)["SATIMGE"].sum()

    fig_right = px.bar(
        df_use,
        x="Year",
        y="SATIMGE",
        color="Sector",
        color_discrete_map=color_map_right,
        category_orders={"Sector": list(color_map_right.keys())}
    )

    # -------- Compose subplots
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Sent out", "Electricity use"),
        shared_yaxes=True
    )

    for tr in fig_left.data:
        tr.showlegend = False  # we'll draw footer legends manually
        fig.add_trace(tr, row=1, col=1)

    for tr in fig_right.data:
        tr.showlegend = False
        fig.add_trace(tr, row=1, col=2)

    fig = apply_common_layout(fig)

    fig.update_layout(
        barmode="stack",
        width=1100,
        height=600,
        showlegend=False,          # ensure the default legend is off
        legend_title_text="",
        xaxis=dict(tickmode="linear", dtick=1, tickangle=45),
        xaxis2=dict(tickmode="linear", dtick=1, tickangle=45),
        margin=dict(l=70, r=30, t=70, b=120)  # extra bottom room for footer legends
    )

    # -------- Add footer legends under each subplot
    left_domain = fig.layout.xaxis.domain
    right_domain = fig.layout.xaxis2.domain

    # Build ordered lists of (name, color)
    left_items = [(k, color_map_left[k]) for k in color_map_left.keys()]
    right_items = [(k, color_map_right[k]) for k in color_map_right.keys()]

    _add_footer_legend(fig, left_items, left_domain, y=-0.16, per_row=6, font_size=12)
    _add_footer_legend(fig, right_items, right_domain, y=-0.16, per_row=6, font_size=12)

    if dev_mode:
        print("👩‍💻 dev_mode ON — showing chart only (no export)")
    else:
        print("💾 saving figure and data")
        save_figures(fig, output_dir, name="ElecTWh_sentOut_consumed")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        # also save the data used for sanity checks
        df_pwr_out.to_csv(Path(output_dir) / "data.csv", index=False)
        df_use.to_csv(Path(output_dir) / "data2.csv", index=False)

    return fig


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    df = pd.read_parquet(project_root / "data/processed/processed_dataset.parquet")
    out = project_root / "outputs/charts_and_data/ElecTWhsentuse_chart"
    out.mkdir(parents=True, exist_ok=True)
    generate_ElecTWh_chart(df, str(out))
