# charts/chart_generators/fig3_ndc_emissions_by_sector.py
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from charts.common.style import apply_common_layout
from charts.common.save import save_figures
import yaml

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

cfg_path = project_root / "config.yaml"
if cfg_path.exists():
    with open(cfg_path) as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    print("⚠️ config.yaml not found — defaulting dev_mode = False")
    dev_mode = False


def _map_sector_group(sector: str) -> str:
    if sector in ["Industry", "Process emissions"]:
        return "Industry"
    if sector == "Power":
        return "Power"
    if sector == "Transport":
        return "Transport"
    if sector == "Refineries":
        return "Refineries"
    return "All others"


def generate_fig3_ndc_emissions_by_sector(df: pd.DataFrame, output_dir: str) -> None:
    print("generating figure 3 — Mt units, minor horiz grid, smaller markers, labels visible")

    subset = df[
        (df["CO2eq"] != 0.0) &
        (df["Scenario"] == "NDC_BASE-RG") &
        (df["Year"].isin([2024, 2035]))
    ].copy()

    subset["SectorGroup"] = subset["Sector"].apply(_map_sector_group)
    data = subset.groupby(["Year", "SectorGroup"])["CO2eq"].sum().reset_index()

    # kt → Mt for plotting
    data["CO2eq_plot"] = data["CO2eq"] / 1000.0

    pivot = data.pivot(index="SectorGroup", columns="Year", values="CO2eq_plot").fillna(0)
    pivot["diff"] = pivot.get(2035, 0) - pivot.get(2024, 0)
    pivot["label"] = pivot.index + " (" + pivot["diff"].round(1).astype(str) + ")"
    label_map = pivot["label"].to_dict()
    data["SectorLabel"] = data["SectorGroup"].map(label_map)

    # Order categories by absolute change (smallest → largest)
    order_df = data[data["Year"] == 2035][["SectorGroup", "SectorLabel"]].drop_duplicates()
    order_df["abs_diff"] = order_df["SectorLabel"].map(pivot["diff"].abs().to_dict())
    ordered_labels = order_df.sort_values("abs_diff")["SectorLabel"].tolist()

    # Build figure
    fig = go.Figure()
    p24 = data[data["Year"] == 2024]
    p35 = data[data["Year"] == 2035]

    # 2024 (red circles) — slightly smaller markers
    fig.add_trace(go.Scatter(
        x=p24["SectorLabel"], y=p24["CO2eq_plot"],
        mode="markers", name="2024",
        marker=dict(size=12, color="red", symbol="circle"),
        hovertemplate="%{x}<br>2024: %{y:.2f} Mt<extra></extra>"
    ))

    # 2035 (blue crosses)
    fig.add_trace(go.Scatter(
        x=p35["SectorLabel"], y=p35["CO2eq_plot"],
        mode="markers", name="2035",
        marker=dict(size=13, color="blue", symbol="x"),
        hovertemplate="%{x}<br>2035: %{y:.2f} Mt<extra></extra>"
    ))

    # Layout/styling
    fig = apply_common_layout(fig)
    fig.update_layout(
        title_text="",
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="center", x=0.5
        ),
        margin=dict(b=90)  # room for x labels
    )

    # X axis: horizontal labels, fixed category order
    fig.update_xaxes(
        title=dict(text="Sector Group (Δ 2035–2024)", font=dict(size=16)),  
        type="category",
        categoryorder="array",
        categoryarray=ordered_labels,
        tickangle=0,             # horizontal
        showticklabels=True,
        ticklabelposition="outside bottom",
        automargin=True
    )

    # Y axis: main + minor horizontal gridlines
    fig.update_yaxes(
        title=dict(text="CO₂eq (Mt)", font=dict(size=16)),                 
        rangemode="tozero",
        showgrid=True,
        gridcolor="lightgrey",
        zeroline=True,
        zerolinecolor="black",
        minor=dict(showgrid=True, gridcolor="lightgrey")
    )

    if dev_mode:
        print("👩‍💻 dev_mode ON — preview only")
        # fig.show()
    else:
        print("💾 saving figure and data")
        save_figures(fig, output_dir, name="fig3_ndc_emissions_by_sector")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        data.to_csv(Path(output_dir) / "data.csv", index=False)


if __name__ == "__main__":
    df = pd.read_parquet(project_root / "data/processed/processed_dataset.parquet")
    out = project_root / "outputs/charts_and_data/fig3_ndc_emissions_by_sector"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig3_ndc_emissions_by_sector(df, str(out))
