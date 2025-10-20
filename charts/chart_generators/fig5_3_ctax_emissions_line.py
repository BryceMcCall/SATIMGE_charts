from __future__ import annotations
import sys
from pathlib import Path
import shutil
import yaml
import pandas as pd
import plotly.express as px

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout, FALLBACK_CYCLE
from charts.common.save import save_figures

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
DEV_MODE = False
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        DEV_MODE = yaml.safe_load(f).get("dev_mode", False)

# ─────────────────── CONSISTENT SCENARIO COLORS ───────────────────
SCENARIO_COLOR_MAP = {
    "WEM":                         "#FF7F0E",  # same as above
    "WEM + Carbon tax":            "#1F77B4",
}
def color_for(label: str, i: int) -> str:
    return SCENARIO_COLOR_MAP.get(label, FALLBACK_CYCLE[i % len(FALLBACK_CYCLE)])

LEGEND_POSITION = "right"

def _nice_label(raw: str) -> str:
    s = str(raw).replace("NDC_BASE-", "").replace("-RG", "")
    if s in ("", "RG"):
        return "WEM"
    if s == "CtaxWEM":
        return "WEM + Carbon tax"
    if "Ctax" in s or "CTax" in s:
        suffix = s.replace("CtaxWEM", "").strip("-_ ")
        return "Carbon tax" if not suffix else f"Carbon tax – {suffix}"
    return f"WEM + {s}"

def _apply_legend(fig):
    if LEGEND_POSITION == "bottom":
        fig.update_layout(
            margin=dict(l=70, r=40, t=10, b=110),
            legend=dict(orientation="h", yanchor="bottom", y=-0.22,
                        xanchor="center", x=0.5, title="", traceorder="normal"),
            title=None,
        )
    else:
        fig.update_layout(
            margin=dict(l=70, r=40, t=25, b=80),
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02, title=""),
            title=None,
        )

def generate_fig5_2_1_ctax_emissions_line(df: pd.DataFrame, output_dir: str) -> None:
    print("generating figure 5.2.1: Carbon tax emissions line")
    print(f"🛠️ dev_mode = {DEV_MODE} | 📂 {output_dir}")

    df = df.copy()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["MtCO2-eq"] = pd.to_numeric(df["MtCO2-eq"], errors="coerce")
    df = df.dropna(subset=["Scenario", "Year", "MtCO2-eq"])
    df = df[(df["Year"] >= 2024) & (df["Year"] <= 2035)]
    df["ScenarioLabel"] = df["Scenario"].apply(_nice_label)

    labels = df["ScenarioLabel"].unique().tolist()
    labels_wo_base = sorted([x for x in labels if x != "WEM"])
    ordered_labels = labels_wo_base + (["WEM"] if "WEM" in labels else [])
    color_map = {lab: color_for(lab, i) for i, lab in enumerate(ordered_labels)}

    fig = px.line(
        df.sort_values(["ScenarioLabel", "Year"]),
        x="Year", y="MtCO2-eq",
        color="ScenarioLabel" if df["ScenarioLabel"].nunique() > 1 else None,
        color_discrete_map=color_map,
        category_orders={"ScenarioLabel": ordered_labels},
        markers=False,
        labels={"MtCO2-eq": "MtCO₂-eq", "Year": "Year", "ScenarioLabel": ""},
        title=None,
    )

    fig = apply_common_layout(fig)
    _apply_legend(fig)

    X_PAD = 0.03
    fig.update_xaxes(range=[2025, 2035 + X_PAD],
                     title_text="", tickmode="linear", tick0=2025, dtick=1,
                     ticks="outside", minor=dict(ticks="outside", dtick=0.5))
    fig.update_yaxes(title_text="Emissions (MtCO₂-eq)", ticks="outside",
                     minor=dict(ticks="outside", dtick=5))
    fig.add_vline(x=2035, line_dash="dot", line_width=1, line_color="rgba(0,0,0,0.25)")

    AXIS_TITLE_SIZE = 22
    AXIS_TICK_SIZE  = 19

    fig.update_xaxes(title_font=dict(size=AXIS_TITLE_SIZE),
                    tickfont=dict(size=AXIS_TICK_SIZE))
    fig.update_yaxes(title_font=dict(size=AXIS_TITLE_SIZE),
                    tickfont=dict(size=AXIS_TICK_SIZE))

    # Match legend font to Y-axis title size
    fig.update_layout(legend=dict(font=dict(size=AXIS_TITLE_SIZE)))


    # End dots with matching colors
    if "ScenarioLabel" in df:
        last_pts = df.loc[df.groupby("ScenarioLabel")["Year"].idxmax()]
        for _, r in last_pts.iterrows():
            c = color_map.get(r["ScenarioLabel"], "#000")
            fig.add_scatter(
                x=[int(r["Year"])], y=[float(r["MtCO2-eq"])],
                mode="markers",
                marker=dict(size=6, line=dict(width=0.5, color="white"), color=c),
                showlegend=False,
                hovertemplate=f"{r['ScenarioLabel']}<br>{int(r['Year'])}: {r['MtCO2-eq']:.1f} MtCO₂-eq<extra></extra>",
            )

    out = Path(output_dir)
    if DEV_MODE:
        print("👩‍💻 dev_mode ON — preview only (no export)")
        return

    print("💾 saving figure and data")
    save_figures(fig, str(out), name="fig5_2_1_ctax_emissions_line")
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "fig5_2_1_ctax_emissions_line_data.csv", index=False)

    gal = PROJECT_ROOT / "outputs" / "gallery"
    gal.mkdir(parents=True, exist_ok=True)
    png = out / "fig5_2_1_ctax_emissions_line_report.png"
    if png.exists():
        shutil.copy2(png, gal / png.name)

if __name__ == "__main__":
    default_csv = PROJECT_ROOT / "data" / "processed" / "5.2.1_ctax_emissions_line.csv"
    if not default_csv.exists():
        raise SystemExit(f"CSV not found at {default_csv}")
    df0 = pd.read_csv(default_csv)
    out_dir = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig5_2_1_ctax_emissions_line"
    out_dir.mkdir(parents=True, exist_ok=True)
    generate_fig5_2_1_ctax_emissions_line(df0, str(out_dir))
