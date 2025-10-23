# charts/chart_generators/fig_ndc_ghg_emission_cats_gen.py
#
# Facets: "NDC GHG emisssion cats gen"
# x-axis: Year (only 2024 & 2035), categorical; tick labels hidden
# y-axis: Emissions (MtCO2-eq), minor gridlines every 10
# Colors: 2024 blue, 2035 orange (no colorbar)
# Tight grouping; facet titles kept at TOP and rotated -90°; legend moved up

import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import yaml
import shutil

# ───────────────────────── Safe Import Path ─────────────────────────
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures

# ───────────────────────── Config ─────────────────────────
config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path) as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    print("⚠️ config.yaml not found — defaulting dev_mode = False")
    dev_mode = False


# ───────────────────────── Generator ─────────────────────────
def generate_fig_ndc_ghg_emission_cats_gen(df: pd.DataFrame, output_dir: str) -> None:
    print("generating figure: NDC GHG emission categories by Year (facet titles top, rotated)")
    print(f"🛠️ dev_mode = {dev_mode}")
    print(f"📂 Output directory: {output_dir}")

    # ── Prepare data
    df = df.copy()
    df.rename(columns={
        "NDC GHG emisssion cats gen": "Scenario",
        "MtCO2-eq": "Emissions",
        "Year": "Year",
    }, inplace=True)

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["Emissions"] = pd.to_numeric(df["Emissions"], errors="coerce")
    df = df.dropna(subset=["Scenario", "Year", "Emissions"])

    # Only 2024 & 2035; categorical for tight grouping
    df = df[df["Year"].isin([2024, 2035])]
    df["Year_str"] = df["Year"].astype(str)

    scenario_order = sorted(df["Scenario"].astype(str).unique())
    year_order = ["2024", "2035"]
    year_colors = {"2024": "#1f77b4", "2035": "#ff7f0e"}

    # ── Plot
    fig = px.bar(
        df,
        x="Year_str",                # categorical axis
        y="Emissions",
        color="Year_str",            # discrete legend (no colorbar)
        facet_col="Scenario",
        facet_col_wrap=len(scenario_order),
        category_orders={"Scenario": scenario_order, "Year_str": year_order},
        color_discrete_map=year_colors,
        barmode="group",
        labels={"Year_str": "", "Emissions": "", "Scenario": ""},
    )

    # ── Layout (tight spacing)
    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",
        bargap=0.0,          # no gap between categories
        bargroupgap=0.0,     # no gap within category
        margin=dict(l=110, r=60, t=60, b=140),
        width=1600,
        height=700,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.22,          # moved up
            xanchor="center",
            x=0.5,
            font=dict(size=18),
            title=None,
        ),
    )

    # Make bars fill most of the slot
    fig.update_traces(width=0.95, marker_line_width=0.3, marker_line_color="white")

    # ── Y-axis (minor gridlines every 10)
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(0,0,0,0.15)",
        zeroline=True,
        zerolinecolor="black",
        zerolinewidth=1.3,
        minor=dict(ticks="outside", showgrid=True, gridcolor="rgba(0,0,0,0.08)", dtick=10),
    )

    # ── X-axis: categorical; HIDE tick labels (2024/2035 shown in legend)
    fig.update_xaxes(
        type="category",
        showticklabels=False,
        title_text=None,
    )

    # Remove per-facet y titles; fixed left y-axis label
    for axis_name in fig.layout:
        if axis_name.startswith("yaxis"):
            getattr(fig.layout, axis_name).title.text = ""

    fig.add_annotation(
        text="Emissions (MtCO₂-eq)",
        xref="paper", yref="paper",
        x=-0.075, y=0.5,
        xanchor="left", yanchor="middle",
        textangle=-90,
        font=dict(size=18),
        showarrow=False
    )

    # ── Keep facet titles at TOP but rotate them -90° and make smaller
    for anno in fig.layout.annotations:
        if "Scenario=" in anno.text:
            anno.text = anno.text.replace("Scenario=", "")
            anno.font.size = 12
            anno.textangle = -90
            # nudge slightly upward so the tops don't crowd the plot area
            anno.y += 0.02

    if dev_mode:
        print("👩‍💻 dev_mode ON — preview only")
    else:
        print("💾 saving figure and data")
        save_figures(fig, output_dir, name="fig_ndc_ghg_emission_cats_gen")
        df.to_csv(Path(output_dir) / "fig_ndc_ghg_emission_cats_gen_data.csv", index=False)
        gallery_dir = project_root / "outputs" / "gallery"
        gallery_dir.mkdir(parents=True, exist_ok=True)
        src_img = Path(output_dir) / "fig_ndc_ghg_emission_cats_gen_report.png"
        if src_img.exists():
            shutil.copy(src_img, gallery_dir / src_img.name)


# ───────────────────────── Entry Point ─────────────────────────
if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "5.1_total_emissions_bar_ipcc_2024_35.csv"
    df = pd.read_csv(data_path)

    out = project_root / "outputs" / "charts_and_data" / "fig_ndc_ghg_emission_cats_gen"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig_ndc_ghg_emission_cats_gen(df, str(out))
