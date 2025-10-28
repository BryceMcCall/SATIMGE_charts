# charts/chart_generators/fig_transport_pkm.py

import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

import pandas as pd
import yaml
import plotly.express as px
import plotly.graph_objects as go

from charts.common.style import apply_common_layout
from charts.common.save import save_figures

# ────────────────────────── Config ────────────────────────────────
project_root = Path(__file__).resolve().parents[2]
config_path = project_root / "config.yaml"

if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    print("⚠️ config.yaml not found — defaulting dev_mode = False")
    dev_mode = False

YEAR_MIN, YEAR_MAX = 2024, 2035

# Vehicle colors (same as before)
VEHICLE_COLORS = {
    "MotoElectric": "#66c2a5",
    "MotoOil": "#ffff2f",
    "SUVElectric": "#7db621",
    "SUVHybrid": "#b3e2cd",
    "SUVOil": "#8da0cb",
    "CarElectric": "#4daf4a",
    "CarOil": "#ffed6f",
    "BRTOil": "#e5c494",
    "BusElectric": "#b3de69",
    "BusOil": "#fca31f",
    "MinibusElectric": "#80b1d3",
    "MinibusOil": "#999999",
    "PassengerRail": "#e78ac3",
}

# Pretty legend names (one-by-one)
LEGEND_RENAMES = {
    "MotoElectric": "Motorcycle (electric)",
    "MotoOil": "Motorcycle (oil)",
    "SUVElectric": "SUV (electric)",
    "SUVHybrid": "SUV (hybrid)",
    "SUVOil": "SUV (oil)",
    "CarElectric": "Car (electric)",
    "CarOil": "Car (oil)",
    "BRTOil": "BRT (oil)",
    "BusElectric": "Bus (electric)",
    "BusOil": "Bus (oil)",
    "MinibusElectric": "Minibus (electric)",
    "MinibusOil": "Minibus (oil)",
    "PassengerRail": "Passenger rail",
}

CATEGORY_ORDER = ["PassPriv", "PassPub"]  # facet order (Private left, Public right)
FACET_RENAME = {"PassPriv": "Private", "PassPub": "Public"}

# ────────────────────────── Generator ─────────────────────────────
def generate_fig_transport_pkm(df: pd.DataFrame, output_dir: str) -> None:
    """
    Generate stacked area chart for transport passenger demand (pkm),
    using mini dataset with columns:
      Scenario | Category | VehicleType | Year | Value
    """
    print("generating transport passenger demand pkm chart")
    print(f"🛠️ dev_mode = {dev_mode}")
    print(f"📂 Output directory: {output_dir}")

    # Clean + aggregate
    df = df.copy()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce").fillna(0.0)

    df = df[
        df["Year"].between(YEAR_MIN, YEAR_MAX, inclusive="both")
        & df["Category"].notna()
        & df["VehicleType"].notna()
    ]

    df = (
        df.groupby(["Category", "VehicleType", "Year"], as_index=False)["Value"]
        .sum()
        .sort_values(["Category", "VehicleType", "Year"])
    )

    # Plot
    fig = px.area(
        df,
        x="Year",
        y="Value",
        color="VehicleType",
        facet_col="Category",
        facet_col_spacing=0.05,
        category_orders={"Category": CATEGORY_ORDER},
        labels={"Value": "Passenger Kilometers (billion pkm)", "Year": ""},
        color_discrete_map=VEHICLE_COLORS,
    )

    # Base style
    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",
        legend_title_text="",
        font=dict(size=18),
    )

    # ── Facet titles: rename, center, resize ─────────────────────────
    TITLE_SIZE = 22
    def _facet_title(a):
        key = a.text.split("=")[-1]
        a.update(text=FACET_RENAME.get(key, key),
                 font=dict(size=TITLE_SIZE, color="#222"))
    fig.for_each_annotation(_facet_title)

    # ── Legend: square swatches, renamed, fully below ───────────────
    LEGEND_ORDER = [
        "MotoElectric","SUVElectric","PassengerRail","SUVHybrid","MotoOil", "BRTOil","SUVOil",
         "BusOil", "BusElectric","CarElectric",
        "MinibusElectric","MinibusOil","CarOil"
    ]

    # Hide area traces from legend
    for tr in fig.data:
        tr.showlegend = False

    # Add square proxies with pretty names
    for key in LEGEND_ORDER:
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(symbol="square", size=20,
                            color=VEHICLE_COLORS[key], line=dict(width=0)),
                name=LEGEND_RENAMES.get(key, key),
                hoverinfo="skip",
                showlegend=True,
            )
        )

    fig.update_layout(
        legend=dict(
            orientation="h",
            x=0.0, xanchor="left",
            y=-0.22, yanchor="top",
            itemwidth=110,
            font=dict(size=20),
            traceorder="normal",
        ),
        margin=dict(l=90, r=70, t=70, b=180),
        width=1400,
        height=900,
    )

    # ── Axes: ticks/labels ──────────────────────────────────────────
    # X ticks on both facets: −45° and bigger labels
    # Show every year (2024–2035) on both subplots
    all_years = list(range(2024, 2036))
    fig.update_xaxes(
        tickmode="array",
        tickvals=all_years,
        ticktext=[str(y) for y in all_years],
        tickangle=-45,
        tickfont=dict(size=14),
        row=1, col=1
    )
    fig.update_xaxes(
        tickmode="array",
        tickvals=all_years,
        ticktext=[str(y) for y in all_years],
        tickangle=-45,
        tickfont=dict(size=14),
        row=1, col=2
    )


    # Y-axis title only on left facet; both show tick labels
    fig.update_yaxes(
        title="Passenger Kilometers (billion pkm)",
        title_font=dict(size=20),
        showticklabels=True,
        row=1, col=1
    )
    fig.update_yaxes(
        title_text="",
        showticklabels=True,
        row=1, col=2
    )

    # Major every 25, minor every 5 (both facets)
    for c in (1, 2):
        fig.update_yaxes(
            tickmode="linear", dtick=25,
            ticks="outside", ticklen=6, tickfont=dict(size=16),
            minor=dict(dtick=5, ticks="outside", ticklen=3, showgrid=True),
            row=1, col=c
        )

    # Save
    if dev_mode:
        print("👩‍💻 dev_mode ON — showing chart only (no export)")
        # fig.show()
    else:
        print("💾 saving figure and data")
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        save_figures(fig, str(out_dir), name="fig_transport_pkm")
        df.to_csv(out_dir / "transport_pkm_data.csv", index=False)

# ────────────────────────── Standalone run ─────────────────────────
if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "4_14_transport_pkm_data.csv"
    df = pd.read_csv(data_path)

    out = project_root / "outputs" / "charts_and_data" / "fig_transport_pkm"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig_transport_pkm(df, str(out))

