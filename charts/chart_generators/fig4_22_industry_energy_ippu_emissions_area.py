# charts/chart_generators/fig4_22_industry_energy_ippu_emissions_area.py
#
# Stacked AREA chart: IPPU vs Energy emissions (MtCO2-eq), 2024–2035 (NDC_BASE-RG).
# - Legend on the right, no legend title
# - "2 Industrial Processes and Product Use" wraps after "Processes"
# - Solid fills (no transparency/borders)
# - No text labels inside the plot
# - Y-axis title: "CO2-eq Emissions (Mt)"
# - X-axis tick labels rotated -45

from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import yaml
import shutil

# ── Easy-to-edit style knobs ───────────────────────────────────────────────────
LEGEND_FONT_SIZE = 18   # ← edit this to change legend entry font size
LEGEND_GAP = 10         # vertical spacing between legend items (px)
YAXIS_TITLE_SIZE = 20   # y-axis title font size

# ── Project plumbing ────────────────────────────────────────────────────────────
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures

config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    dev_mode = False

# ── Main generator ─────────────────────────────────────────────────────────────
def generate_fig4_22_industry_energy_ippu_emissions_area(df: pd.DataFrame, output_dir: str) -> None:
    print("generating figure 4.22: IPPU & Energy emissions (stacked area, MtCO2-eq)")
    print(f"📂 Output directory: {output_dir}")

    d = df.copy()

    # Normalize expected columns
    col_map = {
        "IPCC_Category_L1": "Category",
        "MtCO2-eq": "Emissions (MtCO2-eq)",
        "MtCO2eq": "Emissions (MtCO2-eq)",
        "MtCO2e": "Emissions (MtCO2-eq)",
    }
    for k, v in col_map.items():
        if k in d.columns and v not in d.columns:
            d = d.rename(columns={k: v})
    if "Category" not in d.columns:
        raise KeyError("Expected column 'IPCC_Category_L1' not found.")
    if "Year" not in d.columns or "Scenario" not in d.columns:
        raise KeyError("Expected columns 'Year' and 'Scenario' not found.")
    if "Emissions (MtCO2-eq)" not in d.columns:
        raise KeyError("Expected an emissions column such as 'MtCO2-eq'.")

    # Filter to scenario & years
    d = d[d["Scenario"].astype(str).str.upper() == "NDC_BASE-RG"]
    d["Year"] = pd.to_numeric(d["Year"], errors="coerce").astype("Int64")
    d = d[d["Year"].between(2024, 2035)]
    d["Emissions (MtCO2-eq)"] = pd.to_numeric(d["Emissions (MtCO2-eq)"], errors="coerce").fillna(0.0)

    # Wrap the long legend label after "Processes"
    wrap_map = {
        "2 Industrial Processes and Product Use": "2 Industrial Processes<br>and Product Use"
    }
    d["Category"] = d["Category"].replace(wrap_map)

    # Order (bottom→top)
    cats = ["2 Industrial Processes<br>and Product Use", "1 Energy"]

    # Colors
    color_map = {
        "2 Industrial Processes<br>and Product Use": "#F28E2B",  # orange
        "1 Energy": "#4E79A7",                                    # blue
    }

    years = sorted(d["Year"].dropna().unique().tolist())

    fig = px.area(
        d,
        x="Year",
        y="Emissions (MtCO2-eq)",
        color="Category",
        category_orders={"Category": cats, "Year": years},
        color_discrete_map=color_map,
        labels={"Year": "", "Emissions (MtCO2-eq)": "CO2-eq Emissions (Mt)", "Category": ""},
    )

    # Layout
    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",
        legend_title_text="",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1.0,
            xanchor="left",
            x=1.02,
            font=dict(size=LEGEND_FONT_SIZE),
            itemclick=False,
            itemdoubleclick=False,
            tracegroupgap=LEGEND_GAP,
        ),
        margin=dict(l=80, r=260, t=30, b=90),
        yaxis=dict(title=dict(text="CO2-eq Emissions (Mt)", font=dict(size=YAXIS_TITLE_SIZE))),
    )

    fig.update_xaxes(
        tickmode="array",
        tickvals=years,
        ticktext=[str(y) for y in years],
        tickangle=-45,
    )

    
    fig.update_yaxes(
        tickmode="linear",
        dtick=10,                              # major tick step
        minor=dict(showgrid=True, dtick=5),   # minor tick step
        ticks="outside",
    )

    # Solid fills; ensure no text labels inside traces
    for tr in fig.data:
        col = tr.line.color
        tr.update(opacity=1.0, line=dict(width=0), fillcolor=col, text=None, hovertemplate=None)

    if dev_mode:
        print("👩‍💻 dev_mode ON — preview only (no files written)")
        return

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    save_figures(fig, output_dir, name="fig4_22_industry_energy_ippu_emissions_area")
    d.to_csv(out_dir / "fig4_22_industry_energy_ippu_emissions_area_data.csv", index=False)

    # Copy preview to gallery
    gallery_dir = project_root / "outputs" / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    src_img = out_dir / "fig4_22_industry_energy_ippu_emissions_area_report.png"
    if src_img.exists():
        shutil.copy2(src_img, gallery_dir / src_img.name)

# ── Script entry ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "4_22_industry_energy_ippu_emissions_area.csv"
    if not data_path.exists():
        raise FileNotFoundError(
            f"Data file not found at {data_path}. "
            "Expected columns: IPCC_Category_L1, Scenario, Year, MtCO2-eq."
        )
    try:
        df = pd.read_csv(data_path)
    except UnicodeDecodeError:
        df = pd.read_csv(data_path, encoding="latin-1")

    out = project_root / "outputs" / "charts_and_data" / "fig4_22_industry_energy_ippu_emissions_area"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig4_22_industry_energy_ippu_emissions_area(df, str(out))
