# charts/chart_generators/fig4_11_wem_liquid_fuels_supply_area.py
#
# Stacked AREA chart of WEM liquid fuels supply (PJ) across 2024–2035.
# Colours align with the fuel palette by mapping:
#   CTL → Coal colour
#   Crude refineries → Oil colour
#   Imported → Imports colour
# charts/chart_generators/fig4_11_wem_liquid_fuels_supply_area.py
# charts/chart_generators/fig4_11_wem_liquid_fuels_supply_area.py
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import yaml
import shutil

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures
from charts.common.style import apply_square_legend 

config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    dev_mode = False

# Order & custom colors (match reference image)
TECHS = ["Imported", "Crude refineries", "CTL"]  # top-to-bottom stack & legend order
CUSTOM_COLORS = {
    "CTL": "#F4A261",               # orange
    "Crude refineries": "#6EA3C6",  # blue
    "Imported": "#E76F51",          # red
}

def generate_fig4_11_wem_liquid_fuels_supply_area(df: pd.DataFrame, output_dir: str) -> None:
    print("generating figure 4.11: WEM liquid fuels supply (stacked area, PJ)")
    print(f"📂 Output directory: {output_dir}")

    d = df.copy()

    ind_col = next((c for c in d.columns if c.lower() == "indicator"), None)
    if ind_col:
        d = d[d[ind_col].astype(str).str.lower() == "flowout"]

    d["Year"] = pd.to_numeric(d["Year"], errors="coerce").astype("Int64")
    d = d[d["Year"].between(2024, 2035)]
    d["FlowOut (PJ)"] = pd.to_numeric(d["FlowOut (PJ)"], errors="coerce").fillna(0.0)

    cat_col = next(
        (c for c in d.columns if "liquid" in c.lower() and "supply" in c.lower()),
        "NDC liquid fuel supply",
    )
    d.rename(columns={cat_col: "Category"}, inplace=True)
    d = d[d["Category"].isin(TECHS)]

    years = sorted(d["Year"].dropna().unique().tolist())

    fig = px.area(
        d,
        x="Year",
        y="FlowOut (PJ)",
        color="Category",
        category_orders={"Year": years, "Category": TECHS},
        color_discrete_map={
            "Imported": CUSTOM_COLORS["Imported"],
            "Crude refineries": CUSTOM_COLORS["Crude refineries"],
            "CTL": CUSTOM_COLORS["CTL"],
        },
        labels={"Year": "", "FlowOut (PJ)": "Liquid Fuels Supply (PJ)", "Category": ""},
    )

    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",
        legend_title_text="",  # no legend title
        legend=dict(orientation="v", yanchor="top", y=1.0, xanchor="left", x=1.02),
        margin=dict(l=70, r=180, t=40, b=90),
        yaxis=dict(
            title=dict(text="Liquid Fuels Supply (PJ)", font=dict(size=24)),
            dtick=100,  # major ticks every 100
        ),
    )
        # Use square legend entries, ordered as in TECHS
    fig.update_layout(legend=dict(traceorder="normal"))
    # (apply_square_legend hides the real trace legends and adds square swatches)
    apply_square_legend(fig, order=TECHS, size=18)


    # x-axis labels at -45°
    fig.update_xaxes(
        tickmode="array",
        tickvals=years,
        ticktext=[str(y) for y in years],
        tickangle=-45,
    )

    # optional minor grid every 50 (kept subtle)
    fig.update_yaxes(minor=dict(showgrid=True, dtick=50))

    # Force SOLID fills (no transparency, no borders)
    for tr in fig.data:
        tr.update(opacity=1.0, line=dict(width=0), fillcolor=tr.line.color)

    if dev_mode:
        print("👩‍💻 dev_mode ON — preview only (no files written)")
        return

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    save_figures(fig, output_dir, name="fig4_11_wem_liquid_fuels_supply_area")
    d.to_csv(out_dir / "fig4_11_wem_liquid_fuels_supply_area_data.csv", index=False)

    gallery_dir = project_root / "outputs" / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    src_img = out_dir / "fig4_11_wem_liquid_fuels_supply_area_report.png"
    if src_img.exists():
        shutil.copy2(src_img, gallery_dir / src_img.name)

if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "4_11_WEM_Liquid_fuels_supply.csv"
    if not data_path.exists():
        raise FileNotFoundError(
            f"Data file not found at {data_path}. "
            "Expected columns: Indicator, NDC liquid fuel supply, Year, FlowOut (PJ)."
        )
    df = pd.read_csv(data_path)
    out = project_root / "outputs" / "charts_and_data" / "fig4_11_wem_liquid_fuels_supply_area"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig4_11_wem_liquid_fuels_supply_area(df, str(out))
