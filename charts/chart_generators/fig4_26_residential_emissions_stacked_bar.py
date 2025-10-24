# charts/chart_generators/fig4_26_residential_emissions_stacked_bar.py
#
# Residential (Households) — Emissions by fuel (MtCO2-eq), stacked by year (2024–2035)
# Colors & layout via charts.common.style + charts.common.save
#
# Expected CSV columns:
#   "Commodity Short Description", "Year", "MtCO2-eq"
#
# CLI:
#   python charts/chart_generators/fig4_26_residential_emissions_stacked_bar.py

from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import yaml
import shutil

# ── project root on path ────────────────────────────────────────────
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout, color_for      # shared style
from charts.common.save import save_figures                         # PNG+SVG saver

# ── config (dev mode) ───────────────────────────────────────────────
config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    dev_mode = False

# Canonical fuel names for palette
_FUEL_CANON = {
    "Coal": "Coal",
    "Kerosene": "Kerosene",   
    "LPG": "LPG",
    "Gas": "Gas",       
}

# Stack order (bottom → top) to match your example image
STACK_ORDER = ["Coal", "Kerosene", "LPG", "Gas"]

# X-axis years (kept explicit for ordering)
YEAR_ORDER = list(range(2024, 2035 + 1))

Y_LABEL = "CO₂-eq Emissions (Mt)"


def generate_fig4_26_residential_emissions_stacked_bar(df: pd.DataFrame, output_dir: str) -> None:
    """
    Build the stacked yearly bars (single panel) for residential emissions by fuel.
    """
    print("generating figure 4.26: Residential emissions by fuel (stacked, 2024–2035)")
    print(f"📂 Output directory: {output_dir}")

    # ── tidy ────────────────────────────────────────────────────────
    df = df.rename(columns={
        "Commodity Short Description": "Fuel",
        "MtCO2-eq": "MtCO2eq",
    }).copy()

    # keep just the columns we need
    cols_needed = {"Fuel", "Year", "MtCO2eq"}
    missing = cols_needed - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    # coerce types and filter years
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["MtCO2eq"] = pd.to_numeric(df["MtCO2eq"], errors="coerce").fillna(0.0)
    df = df[df["Year"].isin(YEAR_ORDER)].copy()

    # canonicalize fuel labels for palette & ordering
    df["Fuel_canon"] = df["Fuel"].map(_FUEL_CANON).fillna(df["Fuel"])

    # aggregate (in case of duplicates)
    agg = (
        df.groupby(["Year", "Fuel_canon"], as_index=False)["MtCO2eq"].sum()
        .sort_values(["Year", "Fuel_canon"])
    )

    # category orders and color map
    agg["Year_cat"] = pd.Categorical(agg["Year"].astype(str), [str(y) for y in YEAR_ORDER], ordered=True)
    fuels_seen = [f for f in STACK_ORDER if f in set(agg["Fuel_canon"].unique())] + \
                 [f for f in agg["Fuel_canon"].unique() if f not in STACK_ORDER]
    color_map = {f: color_for("fuel", f) for f in fuels_seen}


    # value labels: only show if ≥ 0.05 Mt (avoids clutter for tiny gas slices)
    def _fmt(v: float) -> str:
        return f"{v:.1f}" if v >= 0.05 else ""

    agg["label"] = agg["MtCO2eq"].apply(_fmt)

    # ── figure ──────────────────────────────────────────────────────
    fig = px.bar(
        agg,
        x="Year_cat",
        y="MtCO2eq",
        color="Fuel_canon",
        text="label",
        barmode="stack",
        category_orders={"Year_cat": [str(y) for y in YEAR_ORDER],
                         "Fuel_canon": fuels_seen},
        color_discrete_map=color_map,
        labels={"Year_cat": "", "CO₂-eq Emissions (Mt)": Y_LABEL, "Fuel_canon": ""},
    )

    # shared layout
    fig = apply_common_layout(fig)

    # axis + legend tuning to match your look
    fig.update_layout(
        title="",
        legend_title_text="",
        legend=dict(orientation="v", yanchor="top", y=1.0, xanchor="left", x=1.02),
        margin=dict(l=80, r=260, t=40, b=90),
        bargap=0.10,
    )
    fig.update_xaxes(type="category", tickangle=-45)
    fig.update_yaxes(title=dict(text=Y_LABEL), dtick=0.2)
    # minor gridlines at 0.05
    fig.layout.yaxis["minor"] = dict(showgrid=True, dtick=0.05)

    # inside labels (white) as in your examples
    fig.update_traces(
        textposition="inside",
        textfont=dict(color="white", size=18),
        insidetextanchor="middle",
        marker_line_width=0.5,
        marker_line_color="white",
        cliponaxis=True,
    )

    # fixed canvas; saving helper writes both PNG + SVG
    fig.update_layout(width=1200, height=800)

    if dev_mode:
        print("👩‍💻 dev_mode ON — preview only (no files written)")
        return
    # Quick explicit override for Kerosene (speed/simplicity)
    if "Kerosene" in fuels_seen:
        color_map["Kerosene"] = "#1E90FF"  # kerosene hex from your style

    # ── save images + data ─────────────────────────────────────────
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base_name = "fig4_26_residential_emissions_stacked_bar"

    save_figures(fig, output_dir, name=base_name)

    # write out the plot table (clean cols)
    out_df = agg.rename(columns={"Fuel_canon": "Fuel", "Year_cat": "Year"})[["Year", "Fuel", "MtCO2eq"]]
    out_df.to_csv(out_dir / f"{base_name}_data.csv", index=False)

    # copy PNG to gallery for quick reuse
    gallery_dir = project_root / "outputs" / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    src_img = out_dir / f"{base_name}_report.png"
    if src_img.exists():
        shutil.copy2(src_img, gallery_dir / src_img.name)


# ── CLI ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # default data path (drop your CSV here)
    data_path = project_root / "data" / "processed" / "4_26_residential_emissions_bar.csv"
    if not data_path.exists():
        raise FileNotFoundError(
            f"Data file not found at {data_path}.\n"
            "Expected columns: 'Commodity Short Description', 'Year', 'MtCO2-eq'."
        )
    df = pd.read_csv(data_path)
    out = project_root / "outputs" / "charts_and_data" / "fig4_26_residential_emissions_stacked_bar"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig4_26_residential_emissions_stacked_bar(df, str(out))
