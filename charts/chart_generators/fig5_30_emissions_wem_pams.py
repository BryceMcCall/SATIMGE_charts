from __future__ import annotations
import sys
from pathlib import Path
import shutil
import yaml
import pandas as pd
import plotly.express as px

# If run directly, make shared packages importable
if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

# Shared helpers
from charts.common.style import apply_common_layout, FALLBACK_CYCLE
from charts.common.save import save_figures
from charts.common.style import apply_square_legend  # top

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
DEV_MODE = False
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        DEV_MODE = yaml.safe_load(f).get("dev_mode", False)

# ─────────────────── CONSISTENT SCENARIO COLORS ───────────────────
# Edit once—use in all emission-line charts so colors stay consistent
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
def color_for(label: str, i: int) -> str:
    return SCENARIO_COLOR_MAP.get(label, FALLBACK_CYCLE[i % len(FALLBACK_CYCLE)])

LEGEND_POSITION = "bottom"  # "bottom" | "right"

def _nice_label(raw: str) -> str:
    s = str(raw).replace("NDC_BASE-", "").replace("-RG", "")
    mapping = {
        "": "WEM",
        "RG": "WEM",
        "CtaxWEM": "WEM + Carbon tax",
        "TRA-EVOpt": "WEM + EV uptake (optimised)",
        "EE": "WEM + Energy efficiency",
        "FreiM": "WEM + Freight modal shift",
        "IRPFull": "WEM + IRP Full",
        "IRPLight": "WEM + IRP Light",
        "PassM": "WEM + Passenger modal shift",
        "SAREM": "WEM + SAREM",
    }
    return mapping.get(s, f"WEM + {s}" if s and s != "RG" else "WEM")

def _apply_legend(fig):
    if LEGEND_POSITION == "right":
        fig.update_layout(
            margin=dict(l=70, r=160, t=10, b=110),  # no title → small top margin
            legend=dict(
                orientation="h",
                yanchor="bottom", y=-0.22,
                xanchor="center", x=0.5,
                title="", traceorder="normal",
            ),
            title=None,
        )
    else:
        fig.update_layout(
            margin=dict(l=70, r=40, t=10, b=80),
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02, title=""),
            title=None,
        )

def generate_fig5_30_emissions_wem_pams(df: pd.DataFrame, output_dir: str) -> None:
    print("generating figure 5.30: WEM + individual PAMS emissions")
    print(f"🛠️ dev_mode = {DEV_MODE} | 📂 {output_dir}")

    df = df.copy()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["MtCO2-eq"] = pd.to_numeric(df["MtCO2-eq"], errors="coerce")
    df = df.dropna(subset=["Scenario", "Year", "MtCO2-eq"])
    df = df[(df["Year"] >= 2024) & (df["Year"] <= 2035)]
    df["ScenarioLabel"] = df["Scenario"].apply(_nice_label)

    labels = df["ScenarioLabel"].unique().tolist()
    labels_wo_base = sorted([x for x in labels if x != "WEM"])
    ordered_labels = labels_wo_base + ["WEM"]

    # Build color map with explicit overrides
    color_map = {lab: color_for(lab, i) for i, lab in enumerate(ordered_labels)}

    fig = px.line(
        df.sort_values(["ScenarioLabel", "Year"]),
        x="Year", y="MtCO2-eq",
        color="ScenarioLabel",
        color_discrete_map=color_map,
        category_orders={"ScenarioLabel": ordered_labels},
        markers=False,
        labels={"MtCO2-eq": "MtCO₂-eq", "Year": "Year", "ScenarioLabel": ""},
        title=None,
    )

    fig = apply_common_layout(fig)
    _apply_legend(fig)
    apply_square_legend(fig, order=ordered_labels, size=18)

    # Axis + minor ticks + guide
    X_PAD = 0.15
    fig.update_xaxes(range=[2024, 2035 + X_PAD],
                     title_text="", tickmode="linear", tick0=2024, dtick=1,
                     ticks="outside", minor=dict(ticks="outside", dtick=0.5),tickangle=-45)
    fig.update_yaxes(title_text="CO₂-eq Emissions (Mt)", ticks="outside",
                     minor=dict(ticks="outside", dtick=5))
    fig.add_vline(x=2035, line_dash="dot", line_width=1, line_color="rgba(0,0,0,0.25)")

    # End dots matching line colors
    last_pts = df.loc[df.groupby("ScenarioLabel")["Year"].idxmax()]
    label_to_color = color_map
    for _, r in last_pts.iterrows():
        c = label_to_color.get(r["ScenarioLabel"], "#000")
        fig.add_scatter(
            x=[int(r["Year"])], y=[float(r["MtCO2-eq"])],
            mode="markers",
            marker=dict(size=6, line=dict(width=0.5, color="white"), color=c),
            showlegend=False,
            hovertemplate=f"{r['ScenarioLabel']}<br>{int(r['Year'])}: {r['MtCO2-eq']:.1f} MtCO₂-eq<extra></extra>",
        )

        # Ensure Plotly knows the category order for the color field
    #category_col = SERIES_COL  # <-- whatever column you pass to color= in px.line
    fig.update_layout(legend=dict(traceorder="normal"))
    fig.update_traces(showlegend=False)  # real traces hidden; legend uses squares below

    # Use your existing order list
    apply_square_legend(fig, order=ordered_labels, size=18)


    out = Path(output_dir)
    if DEV_MODE:
        print("👩‍💻 dev_mode ON — preview only (no export)")
        return

    print("💾 saving figure and data")
    save_figures(fig, str(out), name="fig5_30_emissions_wem_pams")
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "fig5_30_emissions_wem_pams_data.csv", index=False)

    gal = PROJECT_ROOT / "outputs" / "gallery"
    gal.mkdir(parents=True, exist_ok=True)
    png = out / "fig5_30_emissions_wem_pams_report.png"
    if png.exists():
        shutil.copy2(png, gal / png.name)

if __name__ == "__main__":
    default_csv = PROJECT_ROOT / "data" / "processed" / "5.30_emissions_wem_pams.csv"
    if not default_csv.exists():
        raise SystemExit(f"CSV not found at {default_csv}")
    df0 = pd.read_csv(default_csv)
    out_dir = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig5_30_emissions_wem_pams"
    out_dir.mkdir(parents=True, exist_ok=True)
    generate_fig5_30_emissions_wem_pams(df0, str(out_dir))
