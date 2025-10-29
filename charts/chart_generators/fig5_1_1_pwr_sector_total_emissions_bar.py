# charts/chart_generators/fig5_3_sectoral_vs_wem_difference_emissions_bar_final_v7.py

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

from charts.common.style import apply_common_layout, color_for
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
def generate_fig5_3_sectoral_vs_wem_difference_emissions_bar_final_v7(df: pd.DataFrame, output_dir: str) -> None:
    """
    Final refined version (v7):
    - Fixed y-axis title (anchored annotation, shifted slightly left)
    - Minor gridlines every 2 MtCO₂-eq
    - Orange for Industrial Processes
    - Rotated x-axis (-90°), larger font
    - Stable layout, publication ready
    """
    print("generating figure 5.3: Sectoral vs WEM Difference in Emissions (final v7)")
    print(f"🛠️ dev_mode = {dev_mode}")
    print(f"📂 Output directory: {output_dir}")

    # ── Prepare data
    df = df.copy()
    df.rename(columns={
        "IPCC_Category_L1": "IPCC_Category",
        "Scenario: FamilyGroup": "Scenario",
        "Sector (group) 1": "Sector",
        "Difference in MtCO2-eq": "Diff_MtCO2"
    }, inplace=True)

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["Diff_MtCO2"] = pd.to_numeric(df["Diff_MtCO2"], errors="coerce")
    df = df[df["Year"] == 2035]

    # ── Orders
    sector_order = [
        "Power", "Transport", "Industry & Process Emissions",
        "Commerce & Residential", "Refineries & Supply", "Agriculture"
    ]
    sector_order = [s for s in sector_order if s in df["Sector"].unique()]
    scenario_order = ["CPP1", "CPP2", "CPP3", "CPP4", "High carbon", "Low carbon"]
    scenario_order = [s for s in scenario_order if s in df["Scenario"].unique()]

    # ── Custom colors
    ipcc_colors = {}
    for c in df["IPCC_Category"].unique():
        if "Industrial" in c:
            ipcc_colors[c] = "#FF7F0E"  # orange
        else:
            ipcc_colors[c] = color_for("sector", c)

    # ── Plot
    fig = px.bar(
        df,
        x="Sector",
        y="Diff_MtCO2",
        color="IPCC_Category",
        facet_col="Scenario",
        facet_col_wrap=df["Scenario"].nunique(),   # <-- forces a single row
        facet_col_spacing=0.02, 
        category_orders={"Sector": sector_order, "Scenario": scenario_order},
        color_discrete_map=ipcc_colors,
        barmode="group",
        labels={"Sector": "", "IPCC_Category": "IPCC Category"},
    )

    # ── Layout refinements
    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",
        bargap=0.25,
        margin=dict(l=60, r=60, t=40, b=220),
        width=2600,
        height=700,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.60,
            xanchor="center",
            x=0.5,
            font=dict(size=18),
        ),
    )

    # ── Y-axis (minor gridlines every 2)
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(0,0,0,0.15)",
        zeroline=True,
        zerolinecolor="black",
        zerolinewidth=1.3,
        tickfont=dict(size=18),
        minor=dict(
            ticks="outside",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.08)",
            dtick=2
        ),
    )

    # ── X-axis (rotated labels)
    fig.update_xaxes(
        tickangle=-90,
        tickfont=dict(size=18),
        title_standoff=10
    )

    # ── Remove per-facet y titles for stability
    for axis_name in fig.layout:
        if axis_name.startswith("yaxis"):
            getattr(fig.layout, axis_name).title.text = ""

    # ── Add fixed y-axis label (shifted slightly left)
    fig.add_annotation(
        text="Difference in Emissions compared to WEM (MtCO₂-eq)",
        xref="paper", yref="paper",
        x=-0.075,   # ← shift further left
        y=0.5,
        xanchor="left", yanchor="middle",
        textangle=-90,
        font=dict(size=18),
        showarrow=False
    )

    # ── Facet titles
    for anno in fig.layout.annotations:
        if "Scenario=" in anno.text:
            anno.text = anno.text.replace("Scenario=", "").replace("carbon", "Carbon")
            anno.font.size = 16
            anno.y += 0.02

    fig.update_traces(marker_line_width=0.3, marker_line_color="white")

    # ── Save
    if dev_mode:
        print("👩‍💻 dev_mode ON — preview only")
    else:
        print("💾 saving figure and data")
        save_figures(fig, output_dir, name="fig5_3_sectoral_vs_wem_difference_emissions_bar_final_v7")
        df.to_csv(Path(output_dir) / "fig5_3_sectoral_vs_wem_difference_emissions_bar_final_v7_data.csv", index=False)

        gallery_dir = project_root / "outputs" / "gallery"
        gallery_dir.mkdir(parents=True, exist_ok=True)
        src_img = Path(output_dir) / "fig5_3_sectoral_vs_wem_difference_emissions_bar_final_v7_report.png"
        if src_img.exists():
            shutil.copy(src_img, gallery_dir / src_img.name)


# ───────────────────────── Entry Point ─────────────────────────
if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "5.3_sectoral_vs_wem_difference_emissions_bar.csv"
    df = pd.read_csv(data_path)

    out = project_root / "outputs" / "charts_and_data" / "fig5_3_sectoral_vs_wem_difference_emissions_bar_final_v7"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig5_3_sectoral_vs_wem_difference_emissions_bar_final_v7(df, str(out))
