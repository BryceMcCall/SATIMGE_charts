# charts/chart_generators/fig4_25_residential_energy_by_income_pj.py
#
# Residential energy consumption by income group (PJ) — stacked bars, 2024/2030/2035
# Facets by income group, fuel colors taken from common palette.
#
# Expected CSV columns:
#   "Commodity Short Description", "Subsector", "Year", "SATIMGE"
#   where Subsector ∈ {"HighIncome","MiddleIncome","LowIncome"} and SATIMGE is PJ.
# charts/chart_generators/fig4_25_residential_energy_by_income_pj.py

from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import yaml
import shutil

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout, color_for
from charts.common.save import save_figures

config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    dev_mode = False

# ── EDITABLE FACET TITLES ───────────────────────────────────────────
HIGH_INCOME_TITLE = "High Income"
MIDDLE_INCOME_TITLE = "Middle Income"
LOW_INCOME_TITLE = "Low Income"
# --------------------------------------------------------------------

_FUEL_CANON = {
    "Coal": "Coal",
    "Kerosene": "Kerosene",
    "LPG": "LPG",
    "Gas": "Gas",
    "Electricity": "Electricity",
    "Biowood": "Biowood",
}
STACK_ORDER = ["Electricity", "Biowood", "LPG", "Coal", "Kerosene",  "Gas"]

INCOME_ORDER = ["HighIncome", "MiddleIncome", "LowIncome"]
INCOME_LABEL = {
    "HighIncome": HIGH_INCOME_TITLE,
    "MiddleIncome": MIDDLE_INCOME_TITLE,
    "LowIncome": LOW_INCOME_TITLE,
}
YEAR_ORDER = [2024, 2030, 2035]

Y_LABEL = "Energy consumption (PJ)"
Y_LABEL_SIZE = 22
FACET_TITLE_SIZE = Y_LABEL_SIZE  # match y-axis title size

def generate_fig4_25_residential_energy_by_income_pj(df: pd.DataFrame, output_dir: str) -> None:
    print("generating figure 4.25a: Residential — PJ consumed by income group (stacked)")
    print(f"📂 Output directory: {output_dir}")

    # ── tidy & filter ───────────────────────────────────────────────
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

    df["Fuel_canon"] = df["Fuel"].map(_FUEL_CANON).fillna(df["Fuel"])
    df["PJ"] = pd.to_numeric(df["PJ"], errors="coerce").fillna(0.0)

    df = (df.groupby(["Income", "Year", "Fuel_canon"], as_index=False)["PJ"].sum())
    df["Income"] = pd.Categorical(df["Income"], INCOME_ORDER, ordered=True)
    df["Income_pretty"] = df["Income"].map(INCOME_LABEL)

    # years as **categorical** so we do not get continuous ticks
    df["Year_cat"] = pd.Categorical(df["Year"].astype(str), [str(y) for y in YEAR_ORDER], ordered=True)

    # seen fuels & colors (use canonical palette from style.py)
    fuels_seen = [f for f in STACK_ORDER if f in set(df["Fuel_canon"].unique())]
    color_map = {f: color_for("fuel", f) for f in fuels_seen}


    # ── build figure ────────────────────────────────────────────────
    fig = px.bar(
        df,
        x="Year_cat",  # categorical x
        y="PJ",
        color="Fuel_canon",
        facet_col="Income_pretty",
        facet_col_spacing=0.07,
        barmode="stack",
        category_orders={
            "Year_cat": [str(y) for y in YEAR_ORDER],
            "Fuel_canon": fuels_seen,
            "Income_pretty": [INCOME_LABEL[i] for i in INCOME_ORDER],
        },
        color_discrete_map=color_map,
        labels={"Year_cat": "", "PJ": Y_LABEL, "Fuel_canon": "", "Income_pretty": ""},
    )

    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",
        legend_title_text="",
        legend=dict(orientation="v", yanchor="top", y=1.0, xanchor="left", x=1.02),
        margin=dict(l=90, r=260, t=48, b=90),
        bargap=0.15,
    )

    # categorical axes + -45° years (only 3 labels)
    fig.update_xaxes(type="category", tickangle=-45, matches=None)

    # consistent y range + single y title on left facet
    global_max = df.groupby(["Income_pretty", "Year_cat"])["PJ"].sum().max()
    ymax = float(global_max) * 1.08
    for i in range(1, 4):
        axis = "yaxis" if i == 1 else f"yaxis{i}"
        fig.layout[axis].update(
            range=[0, ymax],
            rangemode="tozero",
            title=dict(text=(Y_LABEL if i == 1 else ""), font=dict(size=Y_LABEL_SIZE)),
            automargin=True,
        )
        # MORE minor ticks
        fig.layout[axis]["minor"] = dict(showgrid=True, dtick=2)

    # facet titles: clean any leading "=..." and apply your editable labels
    title_map = {
        "HighIncome": HIGH_INCOME_TITLE,
        "MiddleIncome": MIDDLE_INCOME_TITLE,
        "LowIncome":  LOW_INCOME_TITLE,
    }
    for ann in fig.layout.annotations:
        if not isinstance(ann.text, str):
            continue
        t = ann.text
        # Plotly may give "Income_pretty=High Income" or "=High Income" or "High Income"
        t = t.split("=", 1)[-1].strip().lstrip("=").strip()

        if t in ("High Income", "HighIncome"):
            ann.text = title_map["HighIncome"]
        elif t in ("Middle Income", "MiddleIncome"):
            ann.text = title_map["MiddleIncome"]
        elif t in ("Low Income", "LowIncome"):
            ann.text = title_map["LowIncome"]

        ann.font.size = FACET_TITLE_SIZE  # match y-axis title size
        # NOTE: don't move ann.y — leaving default keeps titles visible



    fig.update_traces(cliponaxis=True)

    if dev_mode:
        print("👩‍💻 dev_mode ON — preview only (no files written)")
        return

    # ── save + copy to gallery ──────────────────────────────────────
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    base_name = "fig4_25_residential_energy_by_income_pj"
    save_figures(fig, output_dir, name=base_name)

    df_out = df.rename(columns={"Fuel_canon": "Fuel", "Income_pretty": "Income", "Year_cat": "Year"})
    df_out["Year"] = df_out["Year"].astype(str)
    df_out.to_csv(out_dir / f"{base_name}_data.csv", index=False)

    gallery_dir = project_root / "outputs" / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    src_img = out_dir / f"{base_name}_report.png"
    if src_img.exists():
        shutil.copy2(src_img, gallery_dir / src_img.name)

if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "4_25_residential_energy_consump_by_income_cat_bar.csv"
    if not data_path.exists():
        raise FileNotFoundError(
            f"Data file not found at {data_path}.\n"
            "Expected columns: 'Commodity Short Description', 'Subsector', 'Year', 'SATIMGE'."
        )
    df = pd.read_csv(data_path)
    out = project_root / "outputs" / "charts_and_data" / "fig4_25_residential_energy_by_income_pj"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig4_25_residential_energy_by_income_pj(df, str(out))
