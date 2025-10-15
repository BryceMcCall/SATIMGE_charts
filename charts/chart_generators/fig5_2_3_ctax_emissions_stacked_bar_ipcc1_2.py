# charts/chart_generators/fig5_2_3_ctax_emissions_stacked_bar_ipcc1.py

import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import yaml
import shutil

# ────────────────────────── Safe Import Fallback ──────────────────────────
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures
from utils.mappings import map_scenario_key

# ────────────────────────── Config ────────────────────────────────
config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path) as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    print("⚠️ config.yaml not found — defaulting dev_mode = False")
    dev_mode = False


def _short_scenario_label(code: str) -> str:
    """Convert long scenario names to short readable labels."""
    s = str(code)
    s = s.replace("NDC_BASE-", "").replace("-RG", "")
    if "Ctax" in s:
        return "WEM + Ctax"
    return "WEM"


# ───────────────────────── Generator ─────────────────────────
def generate_fig5_2_3_ctax_emissions_stacked_bar_ipcc1(df: pd.DataFrame, output_dir: str) -> None:
    """
    Generate stacked bar chart comparing WEM vs WEM + Ctax emissions (MtCO₂-eq)
    for all years (2025–2035), faceted by year horizontally.
    Legend placed below.
    """
    print("generating figure 5.2.3: Carbon Tax Emissions comparison (WEM vs WEM + Ctax)")
    print(f"🛠️ dev_mode = {dev_mode}")
    print(f"📂 Output directory: {output_dir}")

    # Ensure numeric
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["MtCO2-eq"] = pd.to_numeric(df["MtCO2-eq"], errors="coerce").fillna(0)

    # Keep only model horizon (2025–2035)
    df = df[df["Year"].between(2025, 2035)]

    # Drop NaN or empty categories
    df = df[df["IPCC_Category_L1"].notna()]
    df = df[df["IPCC_Category_L1"] != "nan"]

    # Preserve original IPCC naming
    df["IPCC_Category_L1"] = df["IPCC_Category_L1"].astype(str)

    # Map short scenario names
    df["ScenarioLabel"] = df["Scenario"].apply(_short_scenario_label)

    # Colour palette (consistent IPCC order)
    color_map = {
        "1 Energy": "#1f77b4",
        "2 Industrial Processes and Product Use": "#ff7f0e",
        "3 Agriculture": "#2ca02c",
        "4 LULUCF": "#9467bd",
        "5 Waste": "#8c564b",
    }

    stack_order = [
        "1 Energy",
        "2 Industrial Processes and Product Use",
        "3 Agriculture",
        "4 LULUCF",
        "5 Waste",
    ]

    # Plot — facet by year horizontally
    fig = px.bar(
        df,
        x="ScenarioLabel",
        y="MtCO2-eq",
        color="IPCC_Category_L1",
        facet_col="Year",
        facet_col_wrap=None,  # single horizontal row
        barmode="relative",  # allows LULUCF below 0
        category_orders={
            "ScenarioLabel": ["WEM", "WEM + Ctax"],
            "IPCC_Category_L1": stack_order,
        },
        color_discrete_map=color_map,
        labels={"MtCO2-eq": "MtCO₂-eq", "ScenarioLabel": ""},
    )

    # Apply shared styling
    fig = apply_common_layout(fig)

    # ───── Visual refinements ─────
    fig.update_layout(
        title="",
        legend_title_text="IPCC category L1",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
            font=dict(size=20),
            title_font=dict(size=20),
            bgcolor="rgba(255,255,255,0.8)",
            itemsizing="constant",
            itemwidth=40,
            traceorder="normal",
        ),
        font=dict(size=20),
        margin=dict(l=50, r=50, t=40, b=160),
        yaxis=dict(
            dtick=50,
            title=dict(text="Emissions (MtCO₂-eq)", font=dict(size=20)),
            title_standoff=10,
            gridcolor="rgba(0,0,0,0.08)",
            zeroline=True,
            zerolinewidth=1.2,
            zerolinecolor="grey",
        ),
        bargap=0.45,
    )

    # Clean facet titles
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font=dict(size=18)))

    # Axis and bar refinements
    fig.update_xaxes(tickangle=-90, tickfont=dict(size=20))
    fig.update_yaxes(matches="y")
    fig.update_traces(marker_line_width=0.5, marker_line_color="white")



    # Save or show
    if dev_mode:
        print("👩‍💻 dev_mode ON — preview only")
    else:
        print("💾 saving figure and data")
        save_figures(fig, output_dir, name="fig5_2_3_ctax_emissions_stacked_bar_ipcc1")

        gallery_dir = project_root / "outputs" / "gallery"
        gallery_dir.mkdir(parents=True, exist_ok=True)
        src_img = Path(output_dir) / "fig5_2_3_ctax_emissions_stacked_bar_ipcc1_report.png"
        if src_img.exists():
            shutil.copy(src_img, gallery_dir / src_img.name)

        df.to_csv(Path(output_dir) / "fig5_2_3_ctax_emissions_stacked_bar_ipcc1_data.csv", index=False)


if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "5.2.1_ctax_emissions_stacked_bar_ipcc1.csv"
    df = pd.read_csv(data_path)
    out = project_root / "outputs" / "charts_and_data" / "fig5_2_3_ctax_emissions_stacked_bar_ipcc1"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig5_2_3_ctax_emissions_stacked_bar_ipcc1(df, str(out))
