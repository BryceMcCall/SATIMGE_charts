# charts/chart_generators/fig4_21_industry_energy_consumption_stacked.py
# charts/chart_generators/fig4_21_industry_energy_consumption_stacked.py
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

from charts.common.style import apply_common_layout, color_for
from charts.common.save import save_figures

config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    dev_mode = False

DATA_FILE = project_root / "data" / "processed" / "4_21_industry+m1m2+energy_consumption.csv"

STACK_ORDER = [
    "Coal", "Coke", "Gas", "Electricity", "LPG",
    "HFO", "Diesel", "Waste", "Biomass & Biowood"
]

PALETTE_KEYS = {
    "Coal": "Coal",
    "Coke": "Coke",
    "Gas": "Natural Gas",
    "Electricity": "Electricity",   # must stay identical
    "LPG": "LPG",
    "HFO": "HFO",
    "Diesel": "Oil",
    "Waste": "Waste",
    "Biomass & Biowood": "Biomass",
}

# Stronger separation: keep LPG warm amber, move HFO to mauve/rose, Electricity unchanged.
COLOR_OVERRIDE = {
    "LPG": "#FF9F1C",
    "HFO": "#B56576",    # (distinct from Diesel + Electricity)
}

RENAME_INDUSTRY = {"M1 Industry": "Rest of industry", "M2 Industry": "Heavy Industry"}

def generate_fig4_21_industry_energy_consumption(df: pd.DataFrame, output_dir: str) -> None:
    print("generating figure 4.21: Industry energy consumption (stacked bars)")
    print(f"📂 Output directory: {output_dir}")

    d = df.copy()
    col_comm = next(c for c in d.columns if "Commodity" in c)
    col_ind = next(c for c in d.columns if "Industry" in c and ("M1" in c or "M2" in c))
    d = d.rename(columns={col_comm: "Commodity", col_ind: "Industry", "SATIMGE": "Energy (PJ)"})
    if "Scenario" in d.columns:
        d = d[d["Scenario"] == "NDC_BASE-RG"]

    d["Year"] = pd.to_numeric(d["Year"], errors="coerce").astype("Int64")
    d = d[d["Year"].between(2024, 2035)]
    d["Energy (PJ)"] = pd.to_numeric(d["Energy (PJ)"], errors="coerce").fillna(0.0)
    d["Industry"] = d["Industry"].replace(RENAME_INDUSTRY)
    d = d[d["Commodity"].isin(STACK_ORDER)]
    d["Commodity"] = pd.Categorical(d["Commodity"], categories=STACK_ORDER, ordered=True)

    color_map = {
        fuel: COLOR_OVERRIDE.get(fuel, color_for("fuel", PALETTE_KEYS.get(fuel, fuel)))
        for fuel in STACK_ORDER
    }

    fig = px.bar(
        d, x="Year", y="Energy (PJ)", color="Commodity", facet_row="Industry",
        category_orders={"Commodity": STACK_ORDER, "Year": sorted(d["Year"].unique())},
        barmode="stack", color_discrete_map=color_map,
        labels={"Year": "", "Energy (PJ)": "", "Commodity": "", "Industry": ""},
        text=None,
    )

    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",
        legend_title_text="",
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02, font=dict(size=20)),
        margin=dict(l=110, r=220, t=20, b=80),
        bargap=0.25,
    )

    # Replace facet annotations; give EACH y-axis its own multiline title.
    fig.layout.annotations = tuple()
    years = sorted(d["Year"].unique())
    fig.update_xaxes(tickmode="array", tickvals=years, ticktext=[str(y) for y in years], tickangle=-45)

    # Smaller y tick labels + more minor ticks
    fig.update_yaxes(tickfont=dict(size=18), minor=dict(showgrid=True, dtick=25))

    # Row-specific y-axis titles (multiline after (PJ))
    fig.update_yaxes(title_text="Energy consumption (PJ)<br>Rest of industry", row=1, col=1, title_font=dict(size=21))
    fig.update_yaxes(title_text="Energy consumption (PJ)<br>Heavy Industry",  row=2, col=1, title_font=dict(size=21))

    if dev_mode:
        print("👩‍💻 dev_mode ON — preview only")
        return

    outdir = Path(output_dir); outdir.mkdir(parents=True, exist_ok=True)
    save_figures(fig, output_dir, name="fig4_21_industry_energy_consumption")
    d.to_csv(outdir / "fig4_21_industry_energy_consumption_data.csv", index=False)

    gallery = project_root / "outputs" / "gallery"; gallery.mkdir(parents=True, exist_ok=True)
    img = outdir / "fig4_21_industry_energy_consumption_report.png"
    if img.exists():
        shutil.copy2(img, gallery / img.name)

if __name__ == "__main__":
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Could not find {DATA_FILE}")
    df = pd.read_csv(DATA_FILE, encoding="utf-8", engine="python")
    out = project_root / "outputs" / "charts_and_data" / "fig4_21_industry_energy_consumption"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig4_21_industry_energy_consumption(df, str(out))
