# change in emissions 2024 to 2035, by sector, with grey points for all others

import sys
from pathlib import Path

# ────────────────────────────────────────────────────────
if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))
# ────────────────────────────────────────────────────────

import pandas as pd
import plotly.graph_objects as go
from charts.common.style import apply_common_layout, color_for, color_sequence
from charts.common.save import save_figures

import yaml
project_root = Path(__file__).resolve().parents[2]
config_path = project_root / "config.yaml"

if config_path.exists():
    with open(config_path) as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    print("⚠️ config.yaml not found — defaulting dev_mode = False")
    dev_mode = False


def generate_fig2(df: pd.DataFrame, output_dir: str) -> None:
    print("generating figure 2")
    print(f"🛠️  dev_mode = {dev_mode}")
    print(f"📂 Output directory: {output_dir}")
    
    df["CO2eq"] = df["CO2eq"]*0.001 #convert to Mt

    subset = df[
        (df["CO2eq"] != 0.0) &
        (df["Scenario"] == "NDC_BASE-RG") &
        (df["Year"].isin([2024, 2035]))
    ].copy()


    def map_sector_group(sector):
        if sector in ["Industry", "Process emissions"]:
            return "Industry"
        elif sector == "Power":
            return "Power"
        elif sector == "Transport":
            return "Transport"
        elif sector == "Refineries":
            return "Refineries"
        else:
            return "All others"

    subset["SectorGroup"] = subset["Sector"].apply(map_sector_group)
    data = subset.groupby(["Year", "SectorGroup"])["CO2eq"].sum().reset_index()

    pivot = data.pivot(index="SectorGroup", columns="Year", values="CO2eq").fillna(0)
    pivot["diff"] = pivot[2035] - pivot[2024]
    pivot["label"] = (
        pivot.index + " (" + pivot["diff"].round(0).astype(int).astype(str) + ")"
    )
    label_map = pivot["label"].to_dict()
    data["SectorLabel"] = data["SectorGroup"].map(label_map)

    order_df = data[data["Year"] == 2035][["SectorGroup", "SectorLabel"]].drop_duplicates()
    order_df["abs_diff"] = order_df["SectorLabel"].map(pivot["diff"].abs().to_dict())
    ordered_label_list = order_df.sort_values("abs_diff")["SectorLabel"].tolist()
    y_pos = {label: i for i, label in enumerate(ordered_label_list)}

    fig = go.Figure()

    # create 2024 value on chart
    part_2024 = data[data["Year"] == 2024]
    fig.add_trace(go.Scatter(
        x=part_2024["CO2eq"],
        y=part_2024["SectorLabel"],
        mode="markers",
        name="2024",
        marker=dict(size=10, color="red", symbol="circle")
    ))

    #create 2035 value on chart
    part_2035 = data[data["Year"] == 2035]
    fig.add_trace(go.Scatter(
        x=part_2035["CO2eq"],
        y=part_2035["SectorLabel"],
        mode="markers",
        name="2035",
        marker=dict(size=10, color="blue", symbol="x")
    ))

    #add a scatter of all other scenarios in the datafile
    other_scenarios = df[
        (df["CO2eq"] != 0.0) &
        (df["Scenario"] != "NDC_BASE-RG") &
        (df["Year"].isin([2024, 2035]))
    ].copy()

    other_scenarios["SectorGroup"] = other_scenarios["Sector"].apply(map_sector_group)
    other_scenarios["SectorLabel"] = other_scenarios["SectorGroup"].map(label_map)

    for yr, symbol in zip([2024, 2035], ["circle", "x"]):
        part = other_scenarios[other_scenarios["Year"] == yr]
        fig.add_trace(go.Scatter(
            x=part["CO2eq"],
            y=part["SectorLabel"],
            mode="markers",
            name=f"{yr} (others)",
            marker=dict(size=10, color="grey", symbol=symbol),
            showlegend=False,
            opacity=0.4
        ))

    for _, row in part_2024.iterrows():
        label = row["SectorLabel"]
        x0 = row["CO2eq"]
        match = part_2035[part_2035["SectorLabel"] == label]
        if not match.empty:
            x1 = match["CO2eq"].values[0]
            y_index = y_pos[label]
            fig.add_shape(
                type="line",
                x0=x0, y0=y_index,
                x1=x1, y1=y_index,
                line=dict(color="gray", width=1.5, dash="dot"),
                xref="x", yref="y"
            )

    fig = apply_common_layout(fig)
    #fig.update_xaxes(showgrid=True, automargin=True, nticks=6)
    fig.update_yaxes(showgrid=True)

    fig.update_layout(
        title="",
        xaxis=dict(
            title="Mt CO₂eq",
            #rangemode="tozero",
            range=[-50, 200],
            tickmode="auto"  # ← fixes tick misalignment
        ),
        yaxis=dict(
            title="Sector",
            type="category",
            categoryorder="array",
            categoryarray=ordered_label_list
        )
    )


    if dev_mode:
        print("👩‍💻 dev_mode ON — showing chart only (no export)")
        #fig.show() this crashes the script.

    else:
        print("💾 saving figure and data")
        save_figures(fig, output_dir, name="fig3_ndc_emissions_by_sector")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        data.to_csv(Path(output_dir) / "data.csv", index=False)


if __name__ == "__main__":
    df = pd.read_parquet(project_root / "data/processed/processed_dataset.parquet")
    out = project_root / "outputs/charts_and_data/fig2"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig2(df, str(out))
