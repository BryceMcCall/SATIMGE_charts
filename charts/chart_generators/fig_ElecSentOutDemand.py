# double chart for electricity sent out and consumed

import sys
from pathlib import Path
import math

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.graph_objects as go
from charts.common.style import apply_common_layout, color_for
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
                       y=-0.26, per_row=6, swatch_w=0.015, swatch_h=0.02, gap=0.006,
                       font_size=14):
    """Draw a legend-like footer under a subplot (wrapping by per_row)."""
    x0, x1 = float(domain[0]), float(domain[1])
    width = x1 - x0
    cols = max(1, min(per_row, len(items)))
    cell_w = width / cols

    row = 0
    col = 0
    for name, color in items:
        rect_x0 = x0 + col * cell_w
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

        fig.add_annotation(
            xref="paper", yref="paper",
            x=rect_x1 + gap, y=rect_y0 + swatch_h / 2.0,
            xanchor="left", yanchor="middle",
            text=name,
            showarrow=False,
            font=dict(size=font_size)
        )

        col += 1
        if col >= cols:
            col = 0
            row += 1


def _compute_losses(df: pd.DataFrame, subsectors, years=(2024, 2035)) -> pd.DataFrame:
    """LossTWh = max(FlowIn - FlowOut, 0) for specified power subsectors."""
    filt = (
        (df["Scenario"] == "NDC_BASE-RG")
        & (df["Sector"] == "Power")
        & (df["Year"].between(years[0], years[1]))
        & (df["Commodity"] == "ELCC")
        & (df["Subsector"].isin(subsectors))
        & (df["Indicator"].isin(["FlowIn", "FlowOut"]))
    )
    d = df.loc[filt, ["Year", "Indicator", "SATIMGE"]].copy()
    agg = d.groupby(["Year", "Indicator"], as_index=False)["SATIMGE"].sum()
    wide = agg.pivot(index="Year", columns="Indicator", values="SATIMGE").fillna(0.0)
    wide["LossTWh"] = (wide.get("FlowIn", 0.0) - wide.get("FlowOut", 0.0)).clip(lower=0) / 3.6
    return wide.reset_index()[["Year", "LossTWh"]]


def generate_ElecTWh_chart(df: pd.DataFrame, output_dir: str) -> go.Figure:
    # ── LEFT: Sent out (Power output by technology)
    pwr_exclude = ["ETrans", "EDist", "EBattery", "EPumpStorage", "Demand", "AutoGen-Chemcials"]
    left_src = df[
        (df["Scenario"] == "NDC_BASE-RG")
        & (df["Sector"] == "Power")
        & (df["Year"].between(2024, 2035))
        & (~df["Subsector"].isin(pwr_exclude))
        & (df["Indicator"] == "FlowOut")
        & (df["Commodity"] == "ELCC")
    ].copy()

    df_pwr_out = left_src.groupby(["Year", "Subsector"], as_index=False)["SATIMGE"].sum()
    df_pwr_out["SATIMGE"] /= 3.6  # to TWh

    # Stable palette from style.py (fuel palette, handles E‑aliases)
    left_categories = list(df_pwr_out["Subsector"].dropna().astype(str).unique())
    left_color_map = {c: color_for("fuel", c) for c in left_categories}

    fig_left = px.area(
        df_pwr_out, x="Year", y="SATIMGE", color="Subsector",
        color_discrete_map=left_color_map,
        category_orders={"Subsector": left_categories}
    )

    # ── RIGHT: Electricity use (sectors) + losses from Power
    use_keep = ["Agriculture", "Commerce", "Industry", "Residential", "Transport", "Supply"]
    use_src = df[
        (df["Scenario"] == "NDC_BASE-RG")
        & (df["Sector"].isin(use_keep))
        & (df["Year"].between(2024, 2035))
        & (df["Indicator"] == "FlowIn")
        & (df["Short Description"] == "Electricity")
    ].copy()
    use_src["SATIMGE"] /= 3.6
    df_use = use_src.groupby(["Year", "Sector"], as_index=False)["SATIMGE"].sum()

    grid_losses = _compute_losses(df, subsectors=["ETrans", "EDist"])
    stor_losses = _compute_losses(df, subsectors=["EBattery", "EPumpStorage"])
    add_grid = grid_losses.assign(Sector="Losses-Grid").rename(columns={"LossTWh": "SATIMGE"})
    add_stor = stor_losses.assign(Sector="Losses-Storage").rename(columns={"LossTWh": "SATIMGE"})
    df_use_plus = pd.concat([df_use, add_grid, add_stor], ignore_index=True)

    right_categories = use_keep + ["Losses-Grid", "Losses-Storage"]
    right_color_map = {s: color_for("sector", s) for s in use_keep}
    right_color_map.update({"Losses-Grid": "#8A8A8A", "Losses-Storage": "#C9C9C9"})

    fig_right = px.bar(
        df_use_plus, x="Year", y="SATIMGE", color="Sector",
        color_discrete_map=right_color_map,
        category_orders={"Sector": right_categories}
    )

    # ── Compose subplots
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Sent out", "Electricity use"),
        shared_yaxes=False
    )

    for tr in fig_left.data:
        tr.showlegend = False
        fig.add_trace(tr, row=1, col=1)

    for tr in fig_right.data:
        tr.showlegend = False
        fig.add_trace(tr, row=1, col=2)

    fig = apply_common_layout(fig)

    # layout tweaks
    fig.update_layout(
        barmode="stack",
        width=1200, height=650,
        showlegend=False,
        xaxis=dict(tickmode="linear", dtick=1, tickangle=45, title=""),
        xaxis2=dict(tickmode="linear", dtick=1, tickangle=45, title=""),
        # y-axis labels just "TWh" and same size as subplot titles
        yaxis=dict(title="TWh",  title_font=dict(size=18), title_standoff=8),
        yaxis2=dict(title="TWh", title_font=dict(size=18), title_standoff=8),
        margin=dict(l=80, r=50, t=70, b=220)  # extra bottom for 2-line legends
    )

    # Footer legends (two rows)
    left_domain = fig.layout.xaxis.domain
    right_domain = fig.layout.xaxis2.domain
    left_items = [(k, left_color_map[k]) for k in left_categories]
    right_items = [(k, right_color_map[k]) for k in right_categories]

    left_per_row = max(1, math.ceil(len(left_items) / 2))   # force ~2 lines
    right_per_row = max(1, math.ceil(len(right_items) / 2)) # force ~2 lines

    _add_footer_legend(fig, left_items, left_domain,  y=-0.28, per_row=left_per_row,  font_size=14)
    _add_footer_legend(fig, right_items, right_domain, y=-0.28, per_row=right_per_row, font_size=14)

    # Subplot titles font (kept at 18)
    for ann in fig.layout.annotations:
        if getattr(ann, "text", "") in ("Sent out", "Electricity use"):
            ann.font.size = 18

    if dev_mode:
        print("👩‍💻 dev_mode ON — showing chart only (no export)")
    else:
        print("💾 saving figure and data")
        save_figures(fig, output_dir, name="ElecTWh_sentOut_consumed")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        df_pwr_out.to_csv(Path(output_dir) / "data_left_sentout.csv", index=False)
        df_use_plus.to_csv(Path(output_dir) / "data_right_use_losses.csv", index=False)

    return fig


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    df = pd.read_parquet(project_root / "data/processed/processed_dataset.parquet")
    out = project_root / "outputs/charts_and_data/ElecTWhsentuse_chart"
    out.mkdir(parents=True, exist_ok=True)
    generate_ElecTWh_chart(df, str(out))
