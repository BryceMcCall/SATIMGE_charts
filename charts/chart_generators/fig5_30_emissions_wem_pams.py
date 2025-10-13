# charts/chart_generators/fig5_30_emissions_wem_pams.py
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

# ---- SATIMGE shared helpers --------------------------------------
# Adjust these imports to your project layout if needed
from charts.common.style import apply_common_layout, FALLBACK_CYCLE
from charts.common.save import save_figures

# ---- Config -------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        _CFG = yaml.safe_load(f)
    DEV_MODE = _CFG.get("dev_mode", False)
else:
    DEV_MODE = False

# Choose "right" or "bottom" (bottom for narrow report columns)
LEGEND_POSITION = "right"   # "right" | "bottom"

# ---- Helpers ------------------------------------------------------
def _nice_label(raw: str) -> str:
    """
    Convert scenario code → publication label.
    Uses 'WEM' (not 'WEM base') and 'WEM + ...' wording.
    """
    s = str(raw).replace("NDC_BASE-", "").replace("-RG", "")
    mapping = {
        "": "WEM",                     # NDC_BASE-RG → WEM
        "RG": "WEM",                   # safety net
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

def _build_color_map(labels: list[str]) -> dict[str, str]:
    """Stable color per label from our fallback cycle."""
    return {lab: FALLBACK_CYCLE[i % len(FALLBACK_CYCLE)] for i, lab in enumerate(labels)}

def _apply_legend(fig):
    if LEGEND_POSITION == "bottom":
        fig.update_layout(
            margin=dict(l=70, r=40, t=60, b=110),
            legend=dict(
                orientation="h",
                yanchor="bottom", y=-0.22,
                xanchor="center", x=0.5,
                title="", traceorder="normal",
            ),
        )
    else:  # right
        fig.update_layout(
            margin=dict(l=70, r=40, t=60, b=80),
            legend=dict(
                orientation="v",
                yanchor="top", y=1,
                xanchor="left", x=1.02,
                title="",
            ),
        )

# ---- Generator ----------------------------------------------------
def generate_fig5_30_emissions_wem_pams(df: pd.DataFrame, output_dir: str) -> None:
    """
    Plot WEM + individual PAMS total GHG emissions (MtCO2-eq), 2024–2035.

    Expected columns:
        Scenario | Year | MtCO2-eq
    """
    print("generating figure 5.30: WEM + individual PAMS emissions")
    print(f"🛠️ dev_mode = {DEV_MODE}")
    print(f"📂 Output directory: {output_dir}")

    # Clean & filter
    df = df.copy()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["MtCO2-eq"] = pd.to_numeric(df["MtCO2-eq"], errors="coerce")
    df = df.dropna(subset=["Scenario", "Year", "MtCO2-eq"])
    df = df[(df["Year"] >= 2024) & (df["Year"] <= 2035)]

    # Labels & order (put "WEM" last in legend)
    df["ScenarioLabel"] = df["Scenario"].apply(_nice_label)
    labels = df["ScenarioLabel"].unique().tolist()
    labels_wo_base = sorted([x for x in labels if x != "WEM"])
    ordered_labels = labels_wo_base + ["WEM"]
    color_map = _build_color_map(ordered_labels)

    # Plot
    fig = px.line(
        df.sort_values(["ScenarioLabel", "Year"]),
        x="Year",
        y="MtCO2-eq",
        color="ScenarioLabel",
        color_discrete_map=color_map,
        category_orders={"ScenarioLabel": ordered_labels},
        markers=False,
        labels={"MtCO2-eq": "MtCO₂-eq", "Year": "Year", "ScenarioLabel": ""},
        title="",
    )

    # Style
    fig = apply_common_layout(fig)
    _apply_legend(fig)

    # Minor ticks & 2035 guide
    X_PAD = 0.05
    fig.update_xaxes(range=[2024, 2035 + X_PAD])
    fig.update_xaxes(
        title_text="Year",
        tickmode="linear", tick0=2024, dtick=1,
        ticks="outside",
        minor=dict(ticks="outside", dtick=0.5),
    )
    fig.update_yaxes(
        title_text="MtCO₂-eq",
        ticks="outside",
        minor=dict(ticks="outside", dtick=5),
    )
    fig.add_vline(x=2035, line_dash="dot", line_width=1, line_color="rgba(0,0,0,0.25)")

    # End markers (and optional value labels)
    last_pts = df.loc[df.groupby("ScenarioLabel")["Year"].idxmax()].copy()
    for _, r in last_pts.iterrows():
        fig.add_scatter(
            x=[int(r["Year"])],
            y=[float(r["MtCO2-eq"])],
            mode="markers",
            marker=dict(size=6, line=dict(width=0.5, color="white")),
            showlegend=False,
            hovertemplate=f"{r['ScenarioLabel']}<br>{int(r['Year'])}: {r['MtCO2-eq']:.1f} MtCO₂-eq<extra></extra>",
        )
        # Uncomment to show small numeric labels next to 2035 points
        # fig.add_annotation(
        #     x=2035.15, y=float(r["MtCO2-eq"]),
        #     text=f"{r['MtCO2-eq']:.0f}",
        #     showarrow=False, xanchor="left", yanchor="middle",
        #     font=dict(size=10),
        # )

    # Save
    out = Path(output_dir)
    if DEV_MODE:
        print("👩‍💻 dev_mode ON — preview only (no export)")
        return

    print("💾 saving figure and data")
    save_figures(fig, str(out), name="fig5_30_emissions_wem_pams")
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "fig5_30_emissions_wem_pams_data.csv", index=False)

    # Mirror into gallery for quick reuse
    gal = PROJECT_ROOT / "outputs" / "gallery"
    gal.mkdir(parents=True, exist_ok=True)
    png = out / "fig5_30_emissions_wem_pams_report.png"
    if png.exists():
        shutil.copy2(png, gal / png.name)

# ---- CLI ----------------------------------------------------------
if __name__ == "__main__":
    default_csv = PROJECT_ROOT / "data" / "processed" / "5.30_emissions_wem_pams.csv"
    if not default_csv.exists():
        raise SystemExit(f"CSV not found at {default_csv}")
    df0 = pd.read_csv(default_csv)
    out_dir = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig5_30_emissions_wem_pams"
    out_dir.mkdir(parents=True, exist_ok=True)
    generate_fig5_30_emissions_wem_pams(df0, str(out_dir))
