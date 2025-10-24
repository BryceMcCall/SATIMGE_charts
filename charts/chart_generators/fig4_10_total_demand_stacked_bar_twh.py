# charts/chart_generators/fig4_10_total_demand_stacked_bar_twh.py
#
# Total electricity demand — Stacked by sector (TWh), 2024–2035
# Reads: data/processed/4_10_data_total_demand_TWh.csv
#
# Expected CSV columns:
#   "Year", "Sector", "TWh"
#
# CLI:
#   python charts/chart_generators/fig4_10_total_demand_stacked_bar_twh.py
#   (Optional) --labels / --no-labels to toggle in-bar value labels.

from __future__ import annotations
import sys
import argparse
from pathlib import Path
import pandas as pd
import plotly.express as px
import yaml
import shutil

# ── project root on path ────────────────────────────────────────────
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures

# ── config (dev mode) ───────────────────────────────────────────────
config_path = project_root / "config.yaml"
_CFG = {}
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        _CFG = yaml.safe_load(f) or {}
dev_mode = bool(_CFG.get("dev_mode", False))

# ── labels toggle (project default + local override; default OFF here) ──
SHOW_LABELS = bool(_CFG.get("charts", {}).get("value_labels", True))
SHOW_LABELS = False  # module default

# X-axis years (explicit ordering)
YEAR_ORDER = list(range(2024, 2035 + 1))

Y_LABEL = "Electricity Consumption (TWh)"

# Keep your sector ordering (bottom → top). We will filter to those present.
SECTOR_ORDER = [
    "Industry",
    "Residential",
    "Commerce",
    "Transport",
    "Refineries",
    "Agriculture",
    "Others",
    "Storage Losses",
    "Transmission Losses",
    "Distribution Losses",
    "Supply",
]

# Muted, professional palette (calm but with enough contrast)
# (If a sector is missing in the data, it’s simply unused.)
# Softer, professional versions of the source colors (diverse but not loud)
# Natural, grounded palette (diverse but professional)
# Vibrant–calm palette (clean hues, no “dust”)
SECTOR_COLORS = {
    # cores
    "Industry":            "#2F4858",  # deep blue-slate (anchor)
    "Residential":         "#33658A",  # steel blue
    "Commerce":            "#F6AE2D",  # amber
    "Transport":           "#F26419",  # orange
    "Refineries":          "#5A8FB8",  # mid-sky (derived from 86BBD8)
    "Agriculture":         "#2FA7B8",  # teal-cyan (derived/tempered)

    # minor/other
    "Others":              "#86BBD8",  # sky
    "Storage Losses":      "#D5DCE6",  
    "Transmission Losses": "#A7CBE3",  # light azure
    "Distribution Losses": "#8FA3B8",  # cool slate-blue
    "Supply":              "#E79157",  # very light cool blue
}




def generate_fig4_10_total_demand_stacked_bar_twh(df: pd.DataFrame, output_dir: str) -> None:
    """
    Build stacked yearly bars for total electricity demand by sector (TWh).
    """
    print("generating figure 4.10: Total demand by sector (stacked, 2024–2035)")
    print(f"📂 Output directory: {output_dir}")

    # Tidy
    df = df.rename(columns={"TWh": "Value"}).copy()
    need = {"Year", "Sector", "Value"}
    miss = need - set(df.columns)
    if miss:
        raise ValueError(f"Missing required columns: {sorted(miss)}")

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce").fillna(0.0)
    df = df[df["Year"].isin(YEAR_ORDER)].copy()

    # Aggregate (defensive if duplicates)
    agg = (
        df.groupby(["Year", "Sector"], as_index=False)["Value"].sum()
          .sort_values(["Year", "Sector"])
    )

    # Category orders & colors (respect your preferred sector ordering)
    agg["Year_cat"] = pd.Categorical(agg["Year"].astype(str), [str(y) for y in YEAR_ORDER], ordered=True)
    sectors_seen = [s for s in SECTOR_ORDER if s in set(agg["Sector"].unique())] + \
                   [s for s in agg["Sector"].unique() if s not in SECTOR_ORDER]
    color_map = {s: SECTOR_COLORS.get(s, "#888888") for s in sectors_seen}

    # Value labels: only show for segments ≥ 1.0 TWh to avoid clutter
    def _fmt(v: float) -> str:
        return f"{v:.1f}" if v >= 1.0 else ""

    agg["label"] = agg["Value"].apply(_fmt)

    # Figure
    fig = px.bar(
        agg,
        x="Year_cat",
        y="Value",
        color="Sector",
        text=("label" if SHOW_LABELS else None),
        barmode="stack",
        category_orders={"Year_cat": [str(y) for y in YEAR_ORDER],
                         "Sector": sectors_seen},
        color_discrete_map=color_map,
        labels={"Year_cat": "", "Value": Y_LABEL, "Sector": ""},
    )

    # Layout
    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",
        legend_title_text="",
        legend=dict(
            orientation="v",
            yanchor="top", y=1.0, xanchor="left", x=1.02,
            itemsizing="constant",
            itemwidth=48,
            font=dict(size=18),
            bgcolor="rgba(255,255,255,0.88)",
        ),
        margin=dict(l=80, r=380, t=40, b=90),
        bargap=0.10,
        width=1700,
        height=900,
    )
    fig.update_xaxes(type="category", tickangle=-45)
    # Major ticks ~10 TWh, minor ~2
    fig.update_yaxes(title=dict(text=Y_LABEL), dtick=20)
    fig.layout.yaxis["minor"] = dict(showgrid=True, dtick=5)

    # Labels (conditional)
    if SHOW_LABELS:
        fig.update_traces(
            textposition="inside",
            textfont=dict(color="white", size=15),
            insidetextanchor="middle",
        )
    else:
        fig.update_traces(text=None, textposition=None, texttemplate=None)

    # Crisp edges
    fig.update_traces(marker_line_width=0.6, marker_line_color="white", cliponaxis=True)

    if dev_mode:
        print("👩‍💻 dev_mode ON — preview only (no files written)")
        return

    # Save images + data
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base_name = "fig4_10_total_demand_stacked_bar_twh"

    save_figures(fig, output_dir, name=base_name)

    out_df = agg.rename(columns={"Year_cat": "Year", "Value": "TWh"})[["Year", "Sector", "TWh"]]
    out_df.to_csv(out_dir / f"{base_name}_data.csv", index=False)

    # Gallery copy (optional)
    gallery_dir = project_root / "outputs" / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    src_img = out_dir / f"{base_name}_report.png"
    if src_img.exists():
        shutil.copy2(src_img, gallery_dir / src_img.name)


# ── CLI ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", dest="labels", action="store_true", help="Show in-bar value labels")
    parser.add_argument("--no-labels", dest="labels", action="store_false", help="Hide in-bar value labels")
    parser.set_defaults(labels=SHOW_LABELS)
    args, _ = parser.parse_known_args()
    SHOW_LABELS = bool(args.labels)

    data_path = project_root / "data" / "processed" / "4_10_data_total_demand_TWh.csv"
    if not data_path.exists():
        raise FileNotFoundError(
            f"Data file not found at {data_path}.\n"
            "Expected columns: Year, Sector, TWh."
        )
    df = pd.read_csv(data_path)
    out = project_root / "outputs" / "charts_and_data" / "fig4_10_total_demand_stacked_bar_twh"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig4_10_total_demand_stacked_bar_twh(df, str(out))
