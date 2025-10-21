# charts/chart_generators/fig4_19_heavy_industry_production_lines.py
#
# Heavy industry production (Mt) – line chart for Aluminium, Cement,
# FerroChrome Metal, Paper and Pulp, and Steel under NDC_BASE-RG, 2024–2035.
# charts/chart_generators/fig4_19_heavy_industry_production_lines.py
from __future__ import annotations
import sys, re, shutil, yaml
from pathlib import Path
import pandas as pd
import plotly.express as px

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

COM_COL  = "Commodity Short Description (group) 6"
IND_COL  = "Indicator"
SCEN_COL = "Scenario"
YEAR_COL = "Year"
VAL_COL  = "SATIMGE"

ORDER = ["Aluminium", "Cement", "FerroChrome Metal", "Paper and Pulp", "Steel"]
COLOR_MAP = {
    "Aluminium":        "#BFD5EA",
    "Cement":           "#3A6EA5",
    "FerroChrome Metal":"#F28C28",
    "Paper and Pulp":   "#2ECC71",
    "Steel":            "#9B59B6",
}

def _to_float_safe(x):
    if pd.isna(x): return None
    if isinstance(x, (int, float)): return float(x)
    s = str(x).replace("\xa0","")
    s = re.sub(r"[^\d.\-eE]", "", s)
    try: return float(s)
    except: return None

def generate_fig4_19_heavy_industry_production_lines(df: pd.DataFrame, output_dir: str) -> None:
    print("generating figure 4.19: Heavy industry production (lines)")
    d = df.copy()

    rename_map = {}
    for c in d.columns:
        cl = c.lower().strip()
        if "commodity" in cl: rename_map[c] = COM_COL
        elif cl == "indicator": rename_map[c] = IND_COL
        elif cl == "scenario":  rename_map[c] = SCEN_COL
        elif cl == "year":      rename_map[c] = YEAR_COL
        elif cl in ("satimge","value","mt"): rename_map[c] = VAL_COL
    if rename_map: d.rename(columns=rename_map, inplace=True)

    d = d[(d[IND_COL].astype(str).str.lower() == "flowout") &
          (d[SCEN_COL].astype(str).str.upper() == "NDC_BASE-RG")]
    d[YEAR_COL] = pd.to_numeric(d[YEAR_COL], errors="coerce").astype("Int64")
    d = d[d[YEAR_COL].between(2024, 2035)]
    d[VAL_COL] = d[VAL_COL].map(_to_float_safe).fillna(0.0)
    d = d[d[COM_COL].isin(ORDER)]

    years = sorted(d[YEAR_COL].dropna().unique().tolist())

    fig = px.line(
        d, x=YEAR_COL, y=VAL_COL, color=COM_COL,
        category_orders={COM_COL: ORDER, YEAR_COL: years},
        color_discrete_map=COLOR_MAP,
        labels={"Year": "", "SATIMGE": "Production (million tonnes)", COM_COL: ""},
    )

    fig = apply_common_layout(fig)
    fig.update_layout(
        legend_title_text="",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1.0,
            xanchor="left",
            x=1.02,
            font=dict(size=21)  
        ),
        margin=dict(l=70, r=180, t=20, b=60),
        yaxis=dict(title=dict(text="Production (million tonnes)", font=dict(size=22))),
    )

    # Slightly thicker lines
    for tr in fig.data:
        tr.update(line=dict(width=3))

    # Y-axis ticks: major every 1, minor every 0.25 (denser)
    fig.update_yaxes(dtick=1, minor=dict(showgrid=True, dtick=0.25))

    # X-axis: label every year and rotate -45°
    fig.update_xaxes(
        tickmode="array",
        tickvals=years,
        ticktext=[str(y) for y in years],
        tickangle=-45,
    )


    if dev_mode:
        print("👩‍💻 dev_mode ON — preview only (no files written)")
        return

    out_dir = Path(output_dir); out_dir.mkdir(parents=True, exist_ok=True)
    save_figures(fig, output_dir, name="fig4_19_heavy_industry_production_lines")
    d.to_csv(out_dir / "fig4_19_heavy_industry_production_lines_data.csv", index=False)

    gallery_dir = project_root / "outputs" / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    src = out_dir / "fig4_19_heavy_industry_production_lines_report.png"
    if src.exists():
        shutil.copy2(src, gallery_dir / src.name)

if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "4_19_heavy_industry_production_Mt.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found at {data_path}.")
    try:
        df = pd.read_csv(data_path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(data_path, encoding="cp1252", engine="python")

    out = project_root / "outputs" / "charts_and_data" / "fig4_19_heavy_industry_production_lines"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig4_19_heavy_industry_production_lines(df, str(out))
