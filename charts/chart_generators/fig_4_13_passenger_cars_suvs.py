# charts/chart_generators/fig_4_13_passenger_cars_suvs.py
from __future__ import annotations
import sys
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

# ── config ──────────────────────────────────────────────────────────
config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    dev_mode = False

# ── parameters you might tweak ──────────────────────────────────────
YEAR_ORDER = ["2024", "2030", "2035"]
Y_LABEL = "Number of vehicles (×10³)"
BAR_TEXT_SIZE = 16
LEGEND_FONT_SIZE = 22
Y_TITLE_SIZE = 22

COLORS = {
    "CarOil":       "#ffed6f",  # pale yellow
    "CarElectric":  "#4daf4a",  # green
    "SUVOil":       "#8da0cb",  # slate blue
    "SUVHybrid":    "#b3e2cd",  # mint
    "SUVElectric":  "#a6d854",  # lime
}

# ── utils ───────────────────────────────────────────────────────────
def _read_csv_clean(path: Path) -> pd.DataFrame:
    """
    Read CSV robustly and clean numeric fields that may contain NBSP
    or thousands separators.
    """
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="latin-1")

    # Standardize headers we expect
    df = df.rename(columns={
        "Scenario": "Scenario",
        "Subsubsector": "Subsubsector",
        "Year": "Year",
        "Capacity": "Capacity",
    }).copy()

    # Clean weird spaces and thousands separators in Capacity
    if df["Capacity"].dtype == object:
        df["Capacity"] = (
            df["Capacity"]
            .astype(str)
            .str.replace("\u00A0", "", regex=False)  # NBSP
            .str.replace("\u202F", "", regex=False)  # narrow NBSP
            .str.replace(",", "", regex=False)       # commas
            .str.strip()
        )
    df["Capacity"] = pd.to_numeric(df["Capacity"], errors="coerce")

    # Keep only our three years; cast to ordered categorical strings
    df["Year"] = df["Year"].astype(int).astype(str)
    df = df[df["Year"].isin(YEAR_ORDER)].copy()

    # Add a top-level group (Cars vs SUVs) for faceting
    df["Group"] = df["Subsubsector"].apply(
        lambda s: "Cars" if s.startswith("Car") else "SUVs"
    )

    # Sort for consistent stacking order
    df = df.sort_values(["Group", "Year", "Subsubsector"])
    return df


# ── main generator ──────────────────────────────────────────────────
def generate_fig_4_13_passenger_cars_suvs(df: pd.DataFrame, output_dir: str) -> None:
    # categorical years in a fixed order
    df["Year"] = df["Year"].astype(str)
    df = df[df["Year"].isin(YEAR_ORDER)].copy()

    fig = px.bar(
        df,
        x="Year",
        y="Capacity",
        color="Subsubsector",
        facet_col="Group",
        facet_col_spacing=0.08,
        category_orders={"Year": YEAR_ORDER, "Group": ["Cars", "SUVs"]},
        color_discrete_map=COLORS,
        labels={"Year": "", "Capacity": Y_LABEL, "Subsubsector": ""},
        text="Capacity",
    )

    # Style bars + inside labels
    fig.update_traces(
        texttemplate="%{text:.0f}",  # integer rounded labels
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(size=BAR_TEXT_SIZE, color="#262626"),
        marker_line_width=0,
    )

    # Apply shared layout
    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",
        barmode="stack",
        bargap=0.25,
        legend_title_text="",
        width=1300, height=800,
        margin=dict(l=80, r=260, t=60, b=90),
        legend=dict(
            orientation="v",
            yanchor="top", y=1.0,
            xanchor="left", x=1.02,
            font=dict(size=LEGEND_FONT_SIZE),
            itemwidth=80,
        ),
    )

    # Axes
    fig.update_xaxes(
        tickangle=-45,
        tickmode="array",
        tickvals=YEAR_ORDER,
    )

    # y-axis title only on the left subplot; right keeps ticks but no title
    fig.update_yaxes(
        title_text=Y_LABEL,
        title_font=dict(size=Y_TITLE_SIZE),
        row=1, col=1
    )
    fig.update_yaxes(
        title_text="",
        row=1, col=2
    )

    # Move/center subplot titles individually
    # (Facet titles are annotations; adjust x values until centered)
    for ann in fig.layout.annotations:
        if ann.text.endswith("=Cars") or ann.text == "Cars":
            ann.update(text="Cars", x=0.23, y=1.0)
        elif ann.text.endswith("=SUVs") or ann.text == "SUVs":
            ann.update(text="SUVs", x=0.77, y=1.0)

    # Save
    out_dir = Path(output_dir); out_dir.mkdir(parents=True, exist_ok=True)
    base = "fig_4_13_passenger_cars_suvs"
    if dev_mode:
        print("dev_mode ON — preview only (no files written)")
        # fig.show()
    else:
        save_figures(fig, str(out_dir), name=base)
        df.to_csv(out_dir / f"{base}_data.csv", index=False)


# ── CLI ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "4_13_transport_passenger_cars_suvs.csv"
    df = _read_csv_clean(data_path)

    out = project_root / "outputs" / "charts_and_data" / "fig_4_13_passenger_cars_suvs"
    out.mkdir(parents=True, exist_ok=True)

    generate_fig_4_13_passenger_cars_suvs(df, str(out))

