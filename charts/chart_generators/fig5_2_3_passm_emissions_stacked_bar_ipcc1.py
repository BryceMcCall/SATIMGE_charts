# charts/chart_generators/fig5_2_3_passm_emissions_stacked_bar_ipcc1.py

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
    s = str(code).replace("NDC_BASE-", "").replace("-RG", "")
    if "PassM" in s:
        return "WEM + PassM"
    return "WEM"


# ───────────────────────── Generator ─────────────────────────
def generate_fig5_2_3_passm_emissions_stacked_bar_ipcc1(df: pd.DataFrame, output_dir: str) -> None:
    """
    Generate stacked bar chart comparing WEM vs WEM + PassM emissions (MtCO₂-eq)
    for all years (2025–2035), faceted by year horizontally.
    Legend placed below (same style as Carbon Tax figure).
    """
    print("generating figure 5.2.3: Passenger M Emissions comparison (WEM vs WEM + PassM)")
    print(f"🛠️ dev_mode = {dev_mode}")
    print(f"📂 Output directory: {output_dir}")

    # Ensure numeric types
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["MtCO2-eq"] = pd.to_numeric(df["MtCO2-eq"], errors="coerce").fillna(0)
    df = df[df["Year"].between(2025, 2035)]
    df = df[df["IPCC_Category_L1"].notna()]
    df = df[df["IPCC_Category_L1"] != "nan"]
    df["IPCC_Category_L1"] = df["IPCC_Category_L1"].astype(str)
    df["ScenarioLabel"] = df["Scenario"].apply(_short_scenario_label)

    # Consistent IPCC color palette and stacking order
    color_map = {
        "1 Energy": "#1f77b4",
        "2 Industrial Processes and Product Use": "#ff7f0e",
        "3 Agriculture": "#2ca02c",
        "4 LULUCF": "#9467bd",
        "5 Waste": "#8c564b",
    }
    stack_order = list(color_map.keys())

    # Plot
    fig = px.bar(
        df,
        x="ScenarioLabel",
        y="MtCO2-eq",
        color="IPCC_Category_L1",
        facet_col="Year",
        facet_col_wrap=None,
        barmode="relative",
        category_orders={
            "ScenarioLabel": ["WEM", "WEM + PassM"],
            "IPCC_Category_L1": stack_order,
        },
        color_discrete_map=color_map,
        labels={"MtCO2-eq": "MtCO₂-eq", "ScenarioLabel": ""},
    )

    # Apply shared style
    fig = apply_common_layout(fig)

    # ───── Layout refinements (exactly as Carbon Tax) ─────
    fig.update_layout(
        title="",
        legend_title_text="IPCC category L1",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.4,       # adjust this to move legend up/down
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

    # Clean facet titles and match axes
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font=dict(size=18)))
    fig.update_xaxes(tickangle=-90, tickfont=dict(size=20))
    fig.update_yaxes(matches="y")
    fig.update_traces(marker_line_width=0.5, marker_line_color="white")

    # Save
    if not dev_mode:
        save_figures(fig, output_dir, name="fig5_2_3_passm_emissions_stacked_bar_ipcc1")
        df.to_csv(Path(output_dir) / "fig5_2_3_passm_emissions_stacked_bar_ipcc1_data.csv", index=False)


if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "5.2.1_PassM_emissions_stacked_bar_ipcc1.csv"
    out = project_root / "outputs" / "charts_and_data" / "fig5_2_3_passm_emissions_stacked_bar_ipcc1"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig5_2_3_passm_emissions_stacked_bar_ipcc1(pd.read_csv(data_path), str(out))
