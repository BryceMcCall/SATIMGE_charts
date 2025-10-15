from __future__ import annotations
import sys
from pathlib import Path
import shutil, yaml
import pandas as pd
import plotly.express as px

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout, FALLBACK_CYCLE
from charts.common.save import save_figures

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEV_MODE = False
cfg = PROJECT_ROOT / "config.yaml"
if cfg.exists():
    DEV_MODE = yaml.safe_load(open(cfg, "r", encoding="utf-8")).get("dev_mode", False)

# ---- Consistent palette (same across all modules) ----------------
SCENARIO_COLOR_MAP = {
    "WEM":                         "#FF7F0E",  # orange
    "WEM + Carbon tax":            "#1F77B4",  # blue
    "WEM + Energy efficiency":     "#2CA02C",  # green
    "WEM + Freight modal shift":   "#D62728",  # red
    "WEM + Passenger modal shift": "#E377C2",  # pink
    "WEM + IRP Full":              "#9467BD",  # purple
    "WEM + IRP Light":             "#8C564B",  # brown
    "WEM + SAREM":                 "#7F7F7F",  # grey
    "WEM + EV uptake (optimised)": "#17BECF",  # teal
}
def color_for(label, i): return SCENARIO_COLOR_MAP.get(label, FALLBACK_CYCLE[i % len(FALLBACK_CYCLE)])

# ---- Layout knobs ------------------------------------------------
LEGEND_POSITION = "right"  # "right" | "bottom"
AXIS_TITLE_SIZE = 20
AXIS_TICK_SIZE  = 17
LEGEND_FONT_SIZE = AXIS_TITLE_SIZE  # keep legend text = y-title

def _nice_label(code: str) -> str:
    s = str(code).replace("NDC_BASE-", "").replace("-RG", "")
    if s in ("", "RG"): return "WEM"
    if s == "EE": return "WEM + Energy efficiency"
    return f"WEM + {s}"

def _apply_legend(fig):
    if LEGEND_POSITION == "bottom":
        fig.update_layout(margin=dict(l=70, r=40, t=10, b=110),
                          legend=dict(orientation="h", y=-0.22, x=0.5, xanchor="center",
                                      yanchor="bottom", title="", font=dict(size=LEGEND_FONT_SIZE)))
    else:
        fig.update_layout(margin=dict(l=70, r=100, t=10, b=80),
                          legend=dict(orientation="v", y=1, x=1.02, xanchor="left",
                                      yanchor="top", title="", font=dict(size=LEGEND_FONT_SIZE)))

def generate_fig5_2_1_ee_emissions_line(df: pd.DataFrame, output_dir: str) -> None:
    df = df.copy()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["MtCO2-eq"] = pd.to_numeric(df["MtCO2-eq"], errors="coerce")
    df = df.dropna().query("2024 <= Year <= 2035")
    df["ScenarioLabel"] = df["Scenario"].apply(_nice_label)

    labels = df["ScenarioLabel"].unique().tolist()
    ordered = sorted([x for x in labels if x != "WEM"]) + (["WEM"] if "WEM" in labels else [])
    color_map = {lab: color_for(lab, i) for i, lab in enumerate(ordered)}

    fig = px.line(df.sort_values(["ScenarioLabel","Year"]),
                  x="Year", y="MtCO2-eq", color="ScenarioLabel",
                  color_discrete_map=color_map, category_orders={"ScenarioLabel": ordered},
                  labels={"Year":"Year","MtCO2-eq":"Emissions (MtCO₂-eq)","ScenarioLabel":""},
                  title=None)
    fig = apply_common_layout(fig); _apply_legend(fig)

    fig.update_xaxes(range=[2024, 2035+0.15], tickmode="linear", tick0=2024, dtick=1,
                     ticks="outside", minor=dict(ticks="outside", dtick=0.5),
                     title_font=dict(size=AXIS_TITLE_SIZE), tickfont=dict(size=AXIS_TICK_SIZE))
    fig.update_yaxes(ticks="outside", minor=dict(ticks="outside", dtick=5),
                     title="Emissions (MtCO₂-eq)", title_font=dict(size=AXIS_TITLE_SIZE),
                     tickfont=dict(size=AXIS_TICK_SIZE))
    fig.add_vline(x=2035, line_dash="dot", line_width=1, line_color="rgba(0,0,0,0.25)")

    last = df.loc[df.groupby("ScenarioLabel")["Year"].idxmax()]
    for _, r in last.iterrows():
        c = color_map.get(r["ScenarioLabel"], "#000")
        fig.add_scatter(x=[int(r["Year"])], y=[float(r["MtCO2-eq"])], mode="markers",
                        marker=dict(size=6, line=dict(width=0.5, color="white"), color=c),
                        showlegend=False, hovertemplate=f"{r['ScenarioLabel']}<br>{int(r['Year'])}: {r['MtCO2-eq']:.1f} MtCO₂-eq<extra></extra>")

    out = Path(output_dir); 
    if not DEV_MODE:
        save_figures(fig, str(out), name="fig5_2_1_ee_emissions_line")
        out.mkdir(parents=True, exist_ok=True)
        df.to_csv(out / "fig5_2_1_ee_emissions_line_data.csv", index=False)
        gal = PROJECT_ROOT / "outputs" / "gallery"; gal.mkdir(parents=True, exist_ok=True)
        png = out / "fig5_2_1_ee_emissions_line_report.png"
        if png.exists(): shutil.copy2(png, gal / png.name)

if __name__ == "__main__":
    csv = PROJECT_ROOT / "data" / "processed" / "5.2.1_EE_emissions_line.csv"
    if not csv.exists(): raise SystemExit(f"CSV not found at {csv}")
    df0 = pd.read_csv(csv)
    out = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig5_2_1_ee_emissions_line"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig5_2_1_ee_emissions_line(df0, str(out))
