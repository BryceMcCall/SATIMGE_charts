# charts/chart_generators/fig4_4_emissions_under_300mt_lines.py
from __future__ import annotations
import sys
from pathlib import Path
import shutil, yaml
import pandas as pd
import plotly.express as px

# Allow shared imports when run directly
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

# ───────────── Consistent colours (keyed by CANONICAL IDs) ─────────────
PALETTE = {
    "WEM":                  "#FF7F0E",  # from NDC_BASE-RG
    "CPP4":                 "#D62728",  # from NDC_CPP4-RG
    "BELOW_300_BUNDLE":     "#2CA02C",  # all cases below 300 in 2035
}
def color_for(label: str, i: int) -> str:
    return PALETTE.get(label, FALLBACK_CYCLE[i % len(FALLBACK_CYCLE)])

# ───────────── Layout knobs ─────────────
LEGEND_POSITION   = "right"   # "right" | "bottom"
AXIS_TITLE_SIZE   = 20
AXIS_TICK_SIZE    = 17
LEGEND_FONT_SIZE  = AXIS_TITLE_SIZE

# End-marker policy (you asked for no dots here)
END_MARKERS = "none"          # "highlighted" | "all" | "none"

# ───────────── Helpers ─────────────
def _find_group_col(df: pd.DataFrame) -> str:
    """Return the name of the 'group' column (often 'NDC Scenarios below 300 (copy)')."""
    known = {"Scenario", "Year", "MtCO2-eq", "MtCO2eq", "MtCO2_eq", "MtCO2e"}
    for c in df.columns:
        if c not in known:
            return c
    raise ValueError("Could not find the group column in the CSV.")

def _apply_legend(fig):
    if LEGEND_POSITION == "bottom":
        fig.update_layout(
            margin=dict(l=70, r=40, t=10, b=110),
            legend=dict(orientation="h", yanchor="bottom", y=-0.22,
                        xanchor="center", x=0.5, title="", font=dict(size=LEGEND_FONT_SIZE)),
            title=None,
        )
    else:
        fig.update_layout(
            margin=dict(l=70, r=110, t=10, b=80),
            legend=dict(orientation="v", yanchor="top", y=1,
                        xanchor="left", x=1.02, title="", font=dict(size=LEGEND_FONT_SIZE)),
            title=None,
        )

# Canonicalize messy CSV labels → canonical IDs
def _canonical_group(value: str) -> str:
    s = str(value).strip().lower()
    if "ndc_base-rg" in s:
        return "WEM"
    if "ndc_cpp4-rg" in s:
        return "CPP4"
    if "below 300" in s:
        return "BELOW_300_BUNDLE"
    # Fallbacks that still appear sometimes
    if s in {"wem", "base", "ndc_base"}:
        return "WEM"
    return value  # pass through (will get fallback colour/label if unknown)

# Canonical ID → display label (legend text)
DISPLAY_LABEL = {
    "WEM":                "WEM",
    "CPP4":               "CPP4",
    "BELOW_300_BUNDLE":   "Scenarios below 300MtCO₂-eq",
}

# ───────────── Generator ─────────────
def generate_fig4_4_emissions_under_300mt_lines(df: pd.DataFrame, output_dir: str) -> None:
    """
    Additional mitigation: emissions trajectories for model carbon-budget cases below 300 MtCO₂-eq in 2035.
    Legend shows: WEM, CPP4, and 'Scenarios below 300'.

    Expected columns (flexible header for the group column):
        <Group> | Scenario | Year | MtCO2-eq
    """
    df = df.copy()

    # Normalise y-column name
    if "MtCO2-eq" not in df.columns:
        for k in ("MtCO2eq", "MtCO2_eq", "MtCO2e"):
            if k in df.columns:
                df = df.rename(columns={k: "MtCO2-eq"})
                break

    # Detect/rename group header, normalise group VALUES to canonical IDs
    group_col = _find_group_col(df)
    df = df.rename(columns={group_col: "Group"})
    group_col = "Group"
    df[group_col] = df[group_col].apply(_canonical_group)

    # Types & range
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["MtCO2-eq"] = pd.to_numeric(df["MtCO2-eq"], errors="coerce")
    df = df.dropna(subset=[group_col, "Scenario", "Year", "MtCO2-eq"])
    df = df[(df["Year"] >= 2024) & (df["Year"] <= 2035)]

    # Use display labels for legend while keeping canonical IDs for colour mapping
    df["Legend"] = df[group_col].map(DISPLAY_LABEL).fillna(df[group_col])

    # Legend order
    legend_order = ["WEM", "CPP4", "BELOW_300_BUNDLE"]
    present = [g for g in legend_order if g in df[group_col].unique().tolist()]
    colors = {DISPLAY_LABEL[g]: color_for(g, i) for i, g in enumerate(present)}
    legend_labels_order = [DISPLAY_LABEL[g] for g in present]

    # Plot: many lines but only 3 legend items
    fig = px.line(
        df.sort_values([group_col, "Scenario", "Year"]),
        x="Year", y="MtCO2-eq",
        color="Legend", line_group="Scenario",
        color_discrete_map=colors,
        category_orders={"Legend": legend_labels_order},
        labels={"Year": "", "MtCO2-eq": "MtCO₂-eq", "Legend": ""},
        title=None,
    )

    # Styling (minor ticks + minor grids)
    fig = apply_common_layout(fig)
    _apply_legend(fig)
    fig.update_xaxes(
        range=[2024, 2035 + 0.03],
        tickmode="linear", tick0=2024, dtick=1,
        ticks="outside", showgrid=True,
        minor=dict(ticks="outside", dtick=0.5, showgrid=True),
        title_font=dict(size=AXIS_TITLE_SIZE), tickfont=dict(size=AXIS_TICK_SIZE),
    )
    fig.update_yaxes(
        ticks="outside", showgrid=True,
        minor=dict(ticks="outside", dtick=10, showgrid=True),
        title="MtCO₂-eq",
        title_font=dict(size=AXIS_TITLE_SIZE), tickfont=dict(size=AXIS_TICK_SIZE),
    )
    fig.add_vline(x=2035, line_dash="dot", line_width=1, line_color="rgba(0,0,0,0.25)")

    # End markers policy (none for this figure)
    if END_MARKERS != "none":
        last = df.loc[df.groupby([group_col, "Scenario"])["Year"].idxmax()]
        for _, r in last.iterrows():
            canon = r[group_col]
            disp  = DISPLAY_LABEL.get(canon, str(canon))
            if END_MARKERS == "highlighted" and canon not in {"WEM", "CPP4"}:
                continue
            c = colors.get(disp, "#000")
            fig.add_scatter(
                x=[int(r["Year"])], y=[float(r["MtCO2-eq"])],
                mode="markers",
                marker=dict(size=6, line=dict(width=0.5, color="white"), color=c),
                showlegend=False,
                hovertemplate=f"{disp}<br>{int(r['Year'])}: {r['MtCO2-eq']:.1f} MtCO₂-eq<extra></extra>",
            )

    # Save
    out = Path(output_dir)
    if not DEV_MODE:
        save_figures(fig, str(out), name="fig4_4_emissions_under_300mt_lines")
        out.mkdir(parents=True, exist_ok=True)
        df.to_csv(out / "fig4_4_emissions_under_300mt_lines_data.csv", index=False)
        gal = PROJECT_ROOT / "outputs" / "gallery"
        gal.mkdir(parents=True, exist_ok=True)
        png = out / "fig4_4_emissions_under_300mt_lines_report.png"
        if png.exists():
            shutil.copy2(png, gal / png.name)

# ───────────── CLI ─────────────
if __name__ == "__main__":
    default_csv = PROJECT_ROOT / "data" / "processed" / "4.4_line_emissions_under_300Mt_wem_cpp4.csv"
    if not default_csv.exists():
        raise SystemExit(f"CSV not found at {default_csv}")
    df0 = pd.read_csv(default_csv)
    out_dir = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig4_4_emissions_under_300mt_lines"
    out_dir.mkdir(parents=True, exist_ok=True)
    generate_fig4_4_emissions_under_300mt_lines(df0, str(out_dir))
