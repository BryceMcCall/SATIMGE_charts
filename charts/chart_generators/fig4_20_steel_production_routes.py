# charts/chart_generators/fig4_20_steel_production_routes.py
#
# Stacked bars of production by route (Mt) for Steel (top) and DRI (bottom), 2024–2035.
# Matches the reference layout and legend order/colours:
#   Coal DRI (light blue), New Coal DRI (orange), EAF (light green),
#   BF-BOF (blue), EAF - Secondary Producers (pink)
# charts/chart_generators/fig4_20_steel_production_routes.py
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

config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    dev_mode = False

COM_COL = "Commodity Short Description"
TECH_COL = "TechDescription"
YEAR_COL = "Year"
VAL_COL = "SATIMGE"

STACK_ORDER = [
    "Coal DRI",
    "New Coal DRI",
    "EAF",
    "BF-BOF",
    "EAF - Secondary Producers",
]
COLOR_MAP = {
    "Coal DRI": "#BFD5EA",                 # light blue
    "New Coal DRI": "#F28C28",             # orange
    "EAF": "#A9D98E",                      # light green
    "BF-BOF": "#18639C",                   # deep blue
    "EAF - Secondary Producers": "#E08AD8" # pink
}
FACET_ORDER = ["Steel", "DRI"]

def generate_fig4_20_steel_production_routes(df: pd.DataFrame, output_dir: str) -> None:
    print("generating figure 4.20: Steel & DRI production routes (stacked)")
    d = df.copy()

    # Normalize column names (be tolerant of slight variations)
    rename_map = {}
    for c in d.columns:
        cl = c.lower().strip()
        if "commodity" in cl:
            rename_map[c] = COM_COL
        elif "tech" in cl:
            rename_map[c] = TECH_COL
        elif cl == "year":
            rename_map[c] = YEAR_COL
        elif cl in ("satimge", "value", "mt"):
            rename_map[c] = VAL_COL
    if rename_map:
        d.rename(columns=rename_map, inplace=True)

    d[YEAR_COL] = pd.to_numeric(d[YEAR_COL], errors="coerce").astype("Int64")
    d = d[d[YEAR_COL].between(2024, 2035)]
    d[VAL_COL] = pd.to_numeric(d[VAL_COL], errors="coerce").fillna(0.0)
    d = d[d[TECH_COL].isin(STACK_ORDER)]
    d = d[d[COM_COL].isin(FACET_ORDER)]

    years = sorted(d[YEAR_COL].dropna().unique().tolist())

    fig = px.bar(
        d,
        x=YEAR_COL,
        y=VAL_COL,
        color=TECH_COL,
        facet_row=COM_COL,
        barmode="stack",
        category_orders={YEAR_COL: years, TECH_COL: STACK_ORDER, COM_COL: FACET_ORDER},
        color_discrete_map=COLOR_MAP,
        labels={YEAR_COL: "", VAL_COL: "Mt", TECH_COL: "Steel production process", COM_COL: ""},
    )

    fig = apply_common_layout(fig)

    # Legend on the right; reduce title & entry font sizes
    fig.update_layout(
        legend_title=dict(text="Steel production process", font=dict(size=22)),  # smaller title
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1.0,
            xanchor="left",
            x=1.02,
            font=dict(size=20)  # smaller legend entries
        ),
        margin=dict(l=70, r=230, t=20, b=60),
        bargap=0.15,
    )

    # Remove the facet labels on the right (the “=Steel”, “=DRI” tags)
    fig.for_each_annotation(lambda a: a.update(text=""))


    # Set explicit y-axis titles per facet (size = 20)
    fig.update_yaxes(title_text="Steel - Production (Mt)", row=1, col=1, title_font=dict(size=20))
    fig.update_yaxes(title_text="DRI - Production (Mt)",   row=2, col=1, title_font=dict(size=20))


    # Show all years on x-axis
    fig.update_xaxes(tickmode="array", tickvals=years, ticktext=[str(y) for y in years])

    # Subtle minor grid on y
    fig.update_yaxes(minor=dict(showgrid=True, dtick=0.25))

    if dev_mode:
        print("👩‍💻 dev_mode ON — preview only (no files written)")
        return

    out_dir = Path(output_dir); out_dir.mkdir(parents=True, exist_ok=True)
    save_figures(fig, output_dir, name="fig4_20_steel_production_routes")
    d.to_csv(out_dir / "fig4_20_steel_production_routes_data.csv", index=False)

    gallery_dir = project_root / "outputs" / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    src_img = out_dir / "fig4_20_steel_production_routes_report.png"
    if src_img.exists():
        shutil.copy2(src_img, gallery_dir / src_img.name)

if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "4_20_steel_production_routes.csv"
    if not data_path.exists():
        raise FileNotFoundError(
            f"Data file not found at {data_path}. "
            "Expected columns: 'Commodity Short Description', 'TechDescription', 'Year', 'SATIMGE'."
        )
    try:
        df = pd.read_csv(data_path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(data_path, encoding="cp1252", engine="python")

    out = project_root / "outputs" / "charts_and_data" / "fig4_20_steel_production_routes"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig4_20_steel_production_routes(df, str(out))
