# charts/chart_generators/fig4_31_waste_emissions_stacked_bar.py
#
# Waste — Emissions by IPCC L2 (CO2-eq, Mt), stacked by year (2024–2035)
# Reads: data/processed/4_31_waste_emissions_area.csv
#
# Columns expected:
#   "IPCC_Category_L1", "IPCC_Category_L2", "Year", "MtCO2-eq"
#
# CLI:
#   python charts/chart_generators/fig4_31_waste_emissions_stacked_bar.py
#   (Optional) --labels / --no-labels to toggle in-bar value labels.

from __future__ import annotations
import sys, re, argparse, shutil
from pathlib import Path
import pandas as pd
import plotly.express as px
import yaml

# ── project root on path ────────────────────────────────────────────
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures

# ── config ─────────────────────────────────────────────────────────
_CFG = {}
cfg_path = project_root / "config.yaml"
if cfg_path.exists():
    _CFG = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
dev_mode = bool(_CFG.get("dev_mode", False))

# labels toggle (default OFF here; CLI can override)
SHOW_LABELS = bool(_CFG.get("charts", {}).get("value_labels", True))
SHOW_LABELS = False

# Years & y-label
YEAR_ORDER = list(range(2024, 2035 + 1))
Y_LABEL = "CO₂-eq Emissions (Mt)"

# Canonicalize frequent typos/aliases for cleaner legend & stable colors
_CANON = {
    "5D1 Domsetic Wastewater Treatment and Discharge":
        "5D1 Domestic Wastewater Treatment and Discharge",
}

# Stack order (bottom → top)
STACK_ORDER = [
    "5A Solid Waste Disposal",
    "5D1 Domestic Wastewater Treatment and Discharge",
    "5D2 Industrial Wastewater Treatment and Discharge",
    "5B Biological treatment of solid waste",
    "5C2 Open Burning of Waste",
]

# ── Muted professional palette (color-blind friendly-ish, desaturated) ──
# Greens for solids/biological, cool blues for wastewater pair, soft red for burning.
_LOCAL_COLORS = {
    "5A Solid Waste Disposal":                          "#4F9D7A",  # deeper teal-green
    "5D1 Domestic Wastewater Treatment and Discharge":  "#7DA6D1",  # muted medium blue
    "5D2 Industrial Wastewater Treatment and Discharge":"#2F6FA6",  # darker steel blue
    "5B Biological treatment of solid waste":           "#9BBC6B",  # olive-green (darker than before)
    "5C2 Open Burning of Waste":                        "#C96E6E",  # softened brick red
}

# Wrap legend labels after the word "Wastewater " (case-insensitive)
def _wrap_wastewater(label: str) -> str:
    return re.sub(r"(?i)Wastewater\s+", "Wastewater<br>", label)

# Add extra spacing in legend by padding with a final <br>
def _pad_legend(label: str) -> str:
    return f"{label}<br>"

# Build display (wrapped + padded) labels for nicer legend
def _legend_label(raw: str) -> str:
    return _pad_legend(_wrap_wastewater(raw))

# Pre-compute the display order for legend/stacking
STACK_ORDER_DISP = [_legend_label(s) for s in STACK_ORDER]


def generate_fig4_31_waste_emissions_stacked_bar(df: pd.DataFrame, output_dir: str) -> None:
    print("generating figure 4.31: Waste emissions by IPCC L2 (stacked, 2024–2035)")
    print(f"📂 Output directory: {output_dir}")

    # rename & tidy
    df = df.rename(columns={
        "IPCC_Category_L1": "IPCC_L1",
        "IPCC_Category_L2": "IPCC_L2",
        "MtCO2-eq": "MtCO2eq",
    }).copy()

    need = {"IPCC_L1", "IPCC_L2", "Year", "MtCO2eq"}
    miss = need - set(df.columns)
    if miss:
        raise ValueError(f"Missing required columns: {sorted(miss)}")

    # keep Waste rows only (defensive)
    df = df[df["IPCC_L1"].astype(str).str.contains("Waste", case=False, na=False)].copy()

    # canonicalize names and create legend-friendly display labels
    df["IPCC_L2"] = df["IPCC_L2"].replace(_CANON)
    df["IPCC_L2_disp"] = df["IPCC_L2"].apply(_legend_label)

    # types & filter
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["MtCO2eq"] = pd.to_numeric(df["MtCO2eq"], errors="coerce").fillna(0.0)
    df = df[df["Year"].isin(YEAR_ORDER)].copy()

    # aggregate for plotting (use wrapped display labels)
    agg = (
        df.groupby(["Year", "IPCC_L2_disp"], as_index=False)["MtCO2eq"].sum()
          .sort_values(["Year", "IPCC_L2_disp"])
    )

    # orders & colors
    agg["Year_cat"] = pd.Categorical(
        agg["Year"].astype(str), [str(y) for y in YEAR_ORDER], ordered=True
    )
    cats_seen = [c for c in STACK_ORDER_DISP if c in set(agg["IPCC_L2_disp"].unique())] + \
                [c for c in agg["IPCC_L2_disp"].unique() if c not in STACK_ORDER_DISP]

    # Map colours onto the *unwrapped* keys, then key by the wrapped+spaced labels
    color_map = {_legend_label(k): _LOCAL_COLORS.get(k, "#888888") for k in _LOCAL_COLORS}

    # labels (threshold to avoid clutter)
    def _fmt(v: float) -> str:
        return f"{v:.1f}" if v >= 0.5 else ""
    agg["label"] = agg["MtCO2eq"].apply(_fmt)

    # figure
    fig = px.bar(
        agg,
        x="Year_cat",
        y="MtCO2eq",
        color="IPCC_L2_disp",
        text=("label" if SHOW_LABELS else None),
        barmode="stack",
        category_orders={"Year_cat": [str(y) for y in YEAR_ORDER],
                         "IPCC_L2_disp": cats_seen},
        color_discrete_map=color_map,
        labels={"Year_cat": "", "MtCO2eq": Y_LABEL, "IPCC_L2_disp": ""},
    )

    # layout & axes
    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",
        legend_title_text="",
        legend=dict(
            orientation="v",
            yanchor="top", y=1.0, xanchor="left", x=1.02,
            itemsizing="constant",
            itemwidth=48,                 # a bit more room between marker and text
            font=dict(size=23),
            bgcolor="rgba(255,255,255,0.88)",
        ),
        margin=dict(l=80, r=380, t=40, b=90),
        bargap=0.10,
        width=1600, height=800,
    )
    fig.update_xaxes(type="category", tickangle=-45)
    fig.update_yaxes(title=dict(text=Y_LABEL), dtick=1.0)
    fig.layout.yaxis["minor"] = dict(showgrid=True, dtick=0.2)

    # in-bar labels
    if SHOW_LABELS:
        fig.update_traces(textposition="inside",
                          textfont=dict(color="white", size=15),
                          insidetextanchor="middle")
    else:
        fig.update_traces(text=None, textposition=None, texttemplate=None)

    # crisp edges
    fig.update_traces(marker_line_width=0.5, marker_line_color="white", cliponaxis=True)

    if dev_mode:
        print("👩‍💻 dev_mode ON — preview only (no files written)")
        return

    # save
    out_dir = Path(output_dir); out_dir.mkdir(parents=True, exist_ok=True)
    base = "fig4_31_waste_emissions_stacked_bar"
    save_figures(fig, output_dir, name=base)

    # Write clean (unwrapped) data table
    out_df = (
        df.groupby(["Year", "IPCC_L2"], as_index=False)["MtCO2eq"].sum()
          .sort_values(["Year", "IPCC_L2"])
    )
    out_df.to_csv(out_dir / f"{base}_data.csv", index=False)

    # gallery copy (optional)
    gal = project_root / "outputs" / "gallery"; gal.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"{base}_report.png"
    if p.exists(): shutil.copy2(p, gal / p.name)


# ── CLI ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", dest="labels", action="store_true", help="Show in-bar value labels")
    parser.add_argument("--no-labels", dest="labels", action="store_false", help="Hide in-bar value labels")
    parser.set_defaults(labels=SHOW_LABELS)
    args, _ = parser.parse_known_args()
    SHOW_LABELS = bool(args.labels)

    data_path = project_root / "data" / "processed" / "4_31_waste_emissions_area.csv"
    if not data_path.exists():
        raise FileNotFoundError(
            f"Data file not found at {data_path}.\n"
            "Expected columns: IPCC_Category_L1, IPCC_Category_L2, Year, MtCO2-eq."
        )
    df = pd.read_csv(data_path)
    out = project_root / "outputs" / "charts_and_data" / "fig4_31_waste_emissions_stacked_bar"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig4_31_waste_emissions_stacked_bar(df, str(out))
