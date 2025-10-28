# charts/chart_generators/fig_4_18_freight_road_vs_rail.py
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import yaml

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures

config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    dev_mode = False

Y_LABEL = "Freight tonne-kilometers (billion tkm)"
TEXT_SIZE = 18  # ↑ bigger in-bar labels

# Display names for legend/labels
DISPLAY_NAMES = {
    "FreightRoad": "Freight road",
    "FreightRail": "Freight rail",
}

# Colors use the display keys
COLORS = {
    "Freight road": "#d8b6d9",
    "Freight rail": "#a678b4",
}

def generate_fig_4_18_freight(df: pd.DataFrame, output_dir: str) -> None:
    df = df.rename(columns={
        "Subsector": "Subsector",
        "Year": "Year",
        "% of Total SATIMGE": "Pct",
        "SATIMGE": "Value",
    }).copy()

    # Map to display names for legend + labels
    df["SubDisplay"] = df["Subsector"].map(DISPLAY_NAMES).fillna(df["Subsector"])

    # Percent to numeric and compose TWO-LINE label text
    df["Pct_num"] = (
        df["Pct"].astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", "", regex=False)
        .astype(float)
    )
    df["label_text"] = df.apply(
        lambda r: f"{r['SubDisplay']}<br>{r['Pct_num']:.1f}%", axis=1
    )

    # Treat Year as *category* for the x-axis
    df["Year"] = df["Year"].astype(str)
    year_order = sorted(df["Year"].unique(), key=int)

    fig = px.bar(
        df.sort_values(["Year", "SubDisplay"]),
        x="Year",
        y="Value",
        color="SubDisplay",                 # ← drives renamed legend entries
        text="label_text",                  # ← two-line in-bar labels
        color_discrete_map=COLORS,
        category_orders={
            "Year": year_order,
            "SubDisplay": ["Freight rail", "Freight road"],  # legend/stack order
        },
        labels={"Value": Y_LABEL, "Year": "", "SubDisplay": ""},
    )

    fig.update_traces(
        texttemplate="%{text}",
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="#333", size=TEXT_SIZE),
        marker_line_width=0,
    )

    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",                                 # ← remove title
        legend_title_text="",
        barmode="stack",
        bargap=0.25,
        margin=dict(l=70, r=220, t=20, b=80),
        width=600, height=900,                   # ← 900x900
        legend=dict(                             # ← legend on the right
            orientation="v",
            yanchor="top", y=1.0,
            xanchor="left", x=1.02,
            font=dict(size=20),
            itemwidth=60
        ),
    )

    # Axis styling
    ymax = 1.08 * df.groupby("Year")["Value"].sum().max()
    fig.update_yaxes(title=Y_LABEL, 
                     range=[0, ymax],
                     title_font=dict(size=22)  # ← y-axis LABEL size
                     )

    out_dir = Path(output_dir); out_dir.mkdir(parents=True, exist_ok=True)
    base = "fig_4_18_freight_road_vs_rail"
    if dev_mode:
        print("dev_mode ON — preview only")
        # fig.show()
    else:
        save_figures(fig, str(out_dir), name=base)
        df.to_csv(out_dir / f"{base}_data.csv", index=False)

if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "4_18_transport_freight_road_vs_rail_bar.csv"
    df = pd.read_csv(data_path)
    out = project_root / "outputs" / "charts_and_data" / "fig_4_18_freight_road_vs_rail"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig_4_18_freight(df, str(out))
