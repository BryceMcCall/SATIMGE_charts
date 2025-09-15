# charts/chart_generators/fig_transport_pkm.py

import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.express as px
from charts.common.style import apply_common_layout
from charts.common.save import save_figures
import yaml

# ────────────────────────── Config ────────────────────────────────
project_root = Path(__file__).resolve().parents[2]
config_path = project_root / "config.yaml"

if config_path.exists():
    with open(config_path) as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    print("⚠️ config.yaml not found — defaulting dev_mode = False")
    dev_mode = False


# Custom vehicle colors (matching Tableau)
VEHICLE_COLORS = {
    "MotoElectric": "#66c2a5",
    "MotoOil": "#ffd92f",
    "SUVElectric": "#a6d854",
    "SUVHybrid": "#b3e2cd",
    "SUVOil": "#8da0cb",
    "CarElectric": "#4daf4a",
    "CarOil": "#ffed6f",
    "BRTOil": "#e5c494",
    "BusElectric": "#b3de69",
    "BusOil": "#ffb74d",
    "MinibusElectric": "#80b1d3",
    "MinibusOil": "#999999",
    "PassengerRail": "#e78ac3",
}


# ────────────────────────── Generator ─────────────────────────────
def generate_fig_transport_pkm(df: pd.DataFrame, output_dir: str) -> None:
    """
    Generate stacked area chart for transport passenger demand (pkm),
    styled for reporting.

    Expected columns in df:
        Scenario | Subsector (PassPriv/PassPub) |
        Subsubsector (VehicleType) | Year | billion pkm
    """
    print("generating transport passenger demand pkm chart")
    print(f"🛠️ dev_mode = {dev_mode}")
    print(f"📂 Output directory: {output_dir}")

    # Standardize names
    df = df.rename(columns={
        "Subsector": "Category",
        "Subsubsector": "VehicleType",
        "billion pkm": "Value"
    })
    df["Year"] = df["Year"].astype(int)
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

    # Trim to 2024–2035
    df = df[df["Year"] <= 2035]

    # Plot
    fig = px.area(
        df,
        x="Year",
        y="Value",
        color="VehicleType",
        facet_col="Category",
        facet_col_spacing=0.05,
        category_orders={"Category": ["PassPriv", "PassPub"]},
        labels={"Value": "billion pkm"},
        color_discrete_map=VEHICLE_COLORS
    )

    # Apply consistent style
    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",  # remove title for report caption
        legend_title_text="Vehicle type",
        font=dict(size=14),
        margin=dict(l=40, r=40, t=40, b=40)
    )

    # Clean up facet titles
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    # Save
    if dev_mode:
        print("👩‍💻 dev_mode ON — showing chart only (no export)")
        # fig.show()
    else:
        print("💾 saving figure and data")
        save_figures(fig, output_dir, name="fig_transport_pkm")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        df.to_csv(Path(output_dir) / "transport_pkm_data.csv", index=False)


# ────────────────────────── Standalone run ─────────────────────────
if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "transport passenger demand pkm.xlsx"
    df = pd.read_excel(data_path)

    out = project_root / "outputs" / "charts_and_data" / "fig_transport_pkm"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig_transport_pkm(df, str(out))
