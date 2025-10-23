# charts/chart_generators/fig4_25b_residential_energy_by_income_share.py
#
# Residential energy consumption by income group — SHARE (100%) stacked bars
# Facets by income group; colors from common palette; Electricity at the bottom
# to match the PJ version.
#
# Expected CSV columns:
#   "Commodity Short Description", "Subsector", "Year", "SATIMGE"

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

from charts.common.style import apply_common_layout, color_for
from charts.common.save import save_figures

# ── config (dev mode) ───────────────────────────────────────────────
config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    dev_mode = False

# ── EDITABLE FACET TITLES (you can change these) ────────────────────
HIGH_INCOME_TITLE = "High Income"
MIDDLE_INCOME_TITLE = "Middle Income"
LOW_INCOME_TITLE  = "Low Income"

# ── canonical fuel labels & stack order (Electricity at the bottom) ─
_FUEL_CANON = {
    "Coal": "Coal",
    "Kerosene": "Kerosene",
    "LPG": "LPG",
    "Gas": "Gas",
    "Electricity": "Electricity",
    "Biowood": "Biowood",
}
STACK_ORDER = ["Gas", "Kerosene", "Coal", "LPG", "Biowood", "Electricity"]

INCOME_ORDER = ["HighIncome", "MiddleIncome", "LowIncome"]
INCOME_LABEL = {
    "HighIncome": HIGH_INCOME_TITLE,
    "MiddleIncome": MIDDLE_INCOME_TITLE,
    "LowIncome":  LOW_INCOME_TITLE,
}
YEAR_ORDER = [2024, 2030, 2035]

Y_LABEL = "Share of household category (%)"
Y_LABEL_SIZE = 22
FACET_TITLE_SIZE = Y_LABEL_SIZE

def generate_fig4_25_residential_energy_by_income_share(df: pd.DataFrame, output_dir: str) -> None:
    print("generating figure 4.25b: Residential — Share by income group (100% stacked)")
    print(f"📂 Output directory: {output_dir}")

    # ── tidy ────────────────────────────────────────────────────────
    df = df.rename(columns={
        "Commodity Short Description": "Fuel",
        "Subsector": "Income",
        "SATIMGE": "PJ",
    }).copy()
    if "PJ" not in df.columns:
        raise ValueError("Input must contain a 'SATIMGE' column (PJ values).")

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df = df[df["Year"].between(2024, 2035)]
    df = df[df["Year"].isin(YEAR_ORDER)]

    # normalize fuel labels to palette keys
    df["Fuel_canon"] = df["Fuel"].map(_FUEL_CANON).fillna(df["Fuel"])
    df["PJ"] = pd.to_numeric(df["PJ"], errors="coerce").fillna(0.0)

    # aggregate and compute shares within each Income-Year
    agg = (
        df.groupby(["Income", "Year", "Fuel_canon"], as_index=False)["PJ"].sum()
    )
    totals = agg.groupby(["Income", "Year"], as_index=False)["PJ"].sum().rename(columns={"PJ": "Total"})
    agg = agg.merge(totals, on=["Income", "Year"], how="left")
    agg["Share"] = (agg["PJ"] / agg["Total"].where(agg["Total"].ne(0), 1)) * 100.0

    # ordering / pretty labels
    agg["Income"] = pd.Categorical(agg["Income"], INCOME_ORDER, ordered=True)
    agg["Income_pretty"] = agg["Income"].map(INCOME_LABEL)
    agg["Year_cat"] = pd.Categorical(agg["Year"].astype(str), [str(y) for y in YEAR_ORDER], ordered=True)

    fuels_seen = [f for f in STACK_ORDER if f in set(agg["Fuel_canon"].unique())]
    color_map = {f: color_for("fuel", f) for f in fuels_seen}

    # ── figure ──────────────────────────────────────────────────────
    fig = px.bar(
            agg,
            x="Year_cat",
            y="Share",
            color="Fuel_canon",
            text="Share",                       # ← percentage labels source
            facet_col="Income_pretty",
            facet_col_spacing=0.07,
            barmode="stack",
            category_orders={
                "Year_cat": [str(y) for y in YEAR_ORDER],
                "Fuel_canon": fuels_seen,
                "Income_pretty": [INCOME_LABEL[i] for i in INCOME_ORDER],
            },
            color_discrete_map=color_map,
            labels={"Year_cat": "", "Share": Y_LABEL, "Fuel_canon": "", "Income_pretty": ""},
        )


    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",
        legend_title_text="",
        legend=dict(orientation="v", yanchor="top", y=1.0, xanchor="left", x=1.02),
        margin=dict(l=90, r=260, t=48, b=90),
        bargap=0.15,
    )

    # categorical x + rotation
    fig.update_xaxes(type="category", tickangle=-45, matches=None)

    # consistent y across facets (0–100) + single y title + more minor ticks
    for i in range(1, 4):
        axis = "yaxis" if i == 1 else f"yaxis{i}"
        fig.layout[axis].update(
            range=[0, 100],
            dtick=10,
            title=dict(text=(Y_LABEL if i == 1 else ""), font=dict(size=Y_LABEL_SIZE)),
            automargin=True,
        )
        fig.layout[axis]["minor"] = dict(showgrid=True, dtick=2)

    # clean facet titles and apply your editable labels
    wanted = {
        HIGH_INCOME_TITLE, MIDDLE_INCOME_TITLE, LOW_INCOME_TITLE,
        "High Income", "Middle Income", "Low Income",
        "HighIncome", "MiddleIncome", "LowIncome"
    }
    for ann in fig.layout.annotations:
        if isinstance(ann.text, str) and ann.text.strip() in wanted or "=" in str(ann.text):
            t = str(ann.text).split("=", 1)[-1].strip()
            if "High" in t:
                ann.text = HIGH_INCOME_TITLE
            elif "Middle" in t:
                ann.text = MIDDLE_INCOME_TITLE
            elif "Low" in t:
                ann.text = LOW_INCOME_TITLE
            ann.font.size = FACET_TITLE_SIZE

        # White percentage labels inside bars
    fig.update_traces(
        texttemplate="%{text:.0f}%",      # round to 0 decimals and show '%'
        textposition="inside",
        textfont=dict(color="white", size=18),
        insidetextanchor="middle",
        cliponaxis=True,
    )
    fig.update_layout(width=1200, height=800)  # keep your exact canvas



    if dev_mode:
        print("👩‍💻 dev_mode ON — preview only (no files written)")
        return

    # ── save + gallery copy ─────────────────────────────────────────
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base_name = "fig4_25_residential_energy_by_income_share"

    save_figures(fig, output_dir, name=base_name)

    # write out the shares we plotted
    out_df = agg.rename(columns={"Fuel_canon": "Fuel", "Income_pretty": "Income", "Year_cat": "Year"})[
        ["Income", "Year", "Fuel", "Share"]
    ].copy()
    out_df.to_csv(out_dir / f"{base_name}_data.csv", index=False)

    gallery_dir = project_root / "outputs" / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    src_img = out_dir / f"{base_name}_report.png"
    if src_img.exists():
        shutil.copy2(src_img, gallery_dir / src_img.name)

# ── CLI ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "4_25_residential_energy_consump_by_income_cat_bar.csv"
    if not data_path.exists():
        raise FileNotFoundError(
            f"Data file not found at {data_path}.\n"
            "Expected columns: 'Commodity Short Description', 'Subsector', 'Year', 'SATIMGE'."
        )
    df = pd.read_csv(data_path)
    out = project_root / "outputs" / "charts_and_data" / "fig4_25_residential_energy_by_income_share"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig4_25_residential_energy_by_income_share(df, str(out))
