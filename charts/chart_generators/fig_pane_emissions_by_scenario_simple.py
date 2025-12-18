# charts/chart_generators/fig_pane_emissions_by_scenario.py
#simpler version
# charts/chart_generators/fig_pane_emissions_by_scenario_simple.py
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import yaml

# ── safe import path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures


# ── config
config_path = PROJECT_ROOT / "config.yaml"
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        _CFG = yaml.safe_load(f) or {}
    DEV_MODE = bool(_CFG.get("dev_mode", False))
else:
    DEV_MODE = False


def generate_fig_emissions_by_scenario_growth(df: pd.DataFrame, output_dir: str) -> None:
    """
    Emissions by scenario, 3 growth rates (unconstrained only):
      - No facets
      - ScenarioKey on x-axis
      - Exactly one dot per scenario per growth rate (LG/RG/HG) via aggregation
      - Deterministic x offsets for LG/RG/HG (no overlap)
      - Collapse CPPS Variant -> CPPS
      - Remove 'Additional mitigation' by filtering CarbonBudget == Unconstrained
      - Print scenarios + dot counts + missing/duplicate combos for verification
      - (Optional visual improvement) faint connector line per scenario between LG→RG→HG
    """
    print("▶ Generating: emissions by scenario (LG/RG/HG, unconstrained only)")
    print(f"dev_mode={DEV_MODE}  out={output_dir}")

    dfx = df.copy()

    # If Year exists, keep 2035 snapshot
    if "Year" in dfx.columns:
        dfx = dfx[dfx["Year"] == 2035].copy()

    required = ["ScenarioKey", "EconomicGrowth", "CarbonBudget", "CO2eq"]
    missing = [c for c in required if c not in dfx.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")

    dfx["CO2eq"] = pd.to_numeric(dfx["CO2eq"], errors="coerce")

    # Collapse CPPS Variant → CPPS
    dfx["ScenarioKey"] = dfx["ScenarioKey"].replace({"CPPS Variant": "CPPS"})

    # Harmonise budget labels and keep only Unconstrained
    dfx["CarbonBudget"] = dfx["CarbonBudget"].replace({
        "No Budget": "Unconstrained",
        "Constrained": "Additional mitigation",
    })
    dfx = dfx[dfx["CarbonBudget"] == "Unconstrained"].copy()
    dfx = dfx.dropna(subset=["ScenarioKey", "EconomicGrowth", "CO2eq"])

    # Ensure single dot per (ScenarioKey, EconomicGrowth) by aggregating
    dfx = (
        dfx.groupby(["ScenarioKey", "EconomicGrowth"], as_index=False)
           .agg(CO2eq=("CO2eq", "sum"))
    )

    # Scenario order
    scenario_order = ["WEM", "CPP-IRP", "CPP-IRPLight", "CPP-SAREM", "CPPS", "High Carbon", "Low Carbon"]
    present_scen = [s for s in scenario_order if s in set(dfx["ScenarioKey"].astype(str))]
    if not present_scen:
        present_scen = sorted(dfx["ScenarioKey"].astype(str).unique().tolist())

    # Growth order (your real labels)
    growth_order = ["LG", "RG", "HG"]
    present_growth = [g for g in growth_order if g in set(dfx["EconomicGrowth"].astype(str))]
    if len(present_growth) != 3:
        print("\n⚠️ Expected LG/RG/HG but found:", sorted(set(dfx["EconomicGrowth"].astype(str))))
        present_growth = sorted(set(dfx["EconomicGrowth"].astype(str)))

    # Deterministic offsets (no overlap)
    offsets = {"LG": -0.25, "RG": 0.0, "HG": 0.25}
    # fallback offsets if weird labels appear
    if any(g not in offsets for g in present_growth):
        step = 0.22
        center = (len(present_growth) - 1) / 2.0
        offsets = {g: (i - center) * step for i, g in enumerate(present_growth)}

    # Base x positions for scenarios
    scen_to_x = {s: i for i, s in enumerate(present_scen)}
    dfx["ScenarioKey"] = dfx["ScenarioKey"].astype(str)
    dfx["EconomicGrowth"] = dfx["EconomicGrowth"].astype(str)

    dfx["x"] = dfx["ScenarioKey"].map(scen_to_x)
    dfx["x_off"] = dfx["EconomicGrowth"].map(offsets)
    dfx["x_plot"] = dfx["x"] + dfx["x_off"]

    # --- Debug: what are we plotting? ---
    print("\n📌 Scenarios being plotted (x-axis order):")
    for s in present_scen:
        print("  -", s)

    print("\n📌 EconomicGrowth levels being plotted (legend order):")
    for g in present_growth:
        print("  -", g)

    counts = (
        dfx.groupby(["ScenarioKey", "EconomicGrowth"])
           .size()
           .reset_index(name="n")
    )
    print("\n📌 Dot counts per ScenarioKey × EconomicGrowth:")
    print(counts.to_string(index=False))

    expected = pd.MultiIndex.from_product(
        [present_scen, ["LG", "RG", "HG"]],
        names=["ScenarioKey", "EconomicGrowth"]
    ).to_frame(index=False)

    merged = expected.merge(counts, on=["ScenarioKey", "EconomicGrowth"], how="left")
    merged["n"] = merged["n"].fillna(0).astype(int)

    missing = merged[merged["n"] == 0]
    dupes = merged[merged["n"] > 1]

    if not missing.empty:
        print("\n⚠️ Missing combinations (expected 1 dot, got 0):")
        print(missing.to_string(index=False))

    if not dupes.empty:
        print("\n⚠️ Duplicate combinations (expected 1 dot, got >1):")
        print(dupes.to_string(index=False))
    print()

    # Colors for growth rates
    palette = px.colors.qualitative.Plotly
    growth_to_color = {g: palette[i % len(palette)] for i, g in enumerate(present_growth)}

    fig = go.Figure()

    # Optional: faint connector lines per scenario (LG→RG→HG)
    # This makes the growth spread per scenario instantly readable.
    if set(["LG", "RG", "HG"]).issubset(set(present_growth)):
        growth_rank = {"LG": 0, "RG": 1, "HG": 2}
        for s in present_scen:
            sub = dfx[dfx["ScenarioKey"] == s].copy()
            if sub.empty:
                continue
            sub = sub.sort_values(by="EconomicGrowth", key=lambda col: col.map(growth_rank))
            if len(sub) >= 2:
                fig.add_trace(
                    go.Scatter(
                        x=sub["x_plot"],
                        y=sub["CO2eq"],
                        mode="lines",
                        line=dict(width=1, color="rgba(120,120,120,0.35)"),
                        showlegend=False,
                        hoverinfo="skip",
                    )
                )

    # One marker trace per growth rate (clean legend)
    for g in present_growth:
        sub = dfx[dfx["EconomicGrowth"] == g].copy()
        fig.add_trace(
            go.Scatter(
                x=sub["x_plot"],
                y=sub["CO2eq"],
                mode="markers",
                name=str(g),
                marker=dict(size=12, opacity=0.95, color=growth_to_color[g]),
                hovertemplate="Scenario: %{customdata[0]}<br>Growth: %{customdata[1]}<br>CO₂eq: %{y:.1f} Mt<extra></extra>",
                customdata=sub[["ScenarioKey", "EconomicGrowth"]].to_numpy(),
            )
        )

    # Common layout styling
    apply_common_layout(fig, image_type="report")

    # X axis categorical labels at integer positions
    fig.update_xaxes(
        title_text="",
        tickmode="array",
        tickvals=list(range(len(present_scen))),
        ticktext=present_scen,
        tickangle=-35,
        range=[-0.6, len(present_scen) - 0.4],
        showgrid=False,
        zeroline=False,
    )

    # Y axis
    fig.update_yaxes(
        title="CO₂eq Emissions (Mt)",
        range=[200, 450],
        tick0=200,
        dtick=25,
        minor=dict(
            ticks="outside",
            showgrid=True,
            dtick=5,
        ),
    )

    fig.update_layout(
        title_text="",
        showlegend=True,
        legend=dict(
            orientation="v",
            x=1.02, xanchor="left",
            y=1.0, yanchor="top",
            font=dict(size=16),
            title_text="Economic Growth",
        ),
        margin=dict(l=110, r=200, t=20, b=80),
        height=520,
    )

    if DEV_MODE:
        print("dev_mode=True — preview only (not saving)")
        return

    outp = Path(output_dir)
    outp.mkdir(parents=True, exist_ok=True)
    save_figures(fig, str(outp), name="fig_emissions_by_scenario_growth")
    dfx.to_csv(outp / "fig_emissions_by_scenario_growth_data.csv", index=False)

    print("✓ Saved fig_emissions_by_scenario_growth")


if __name__ == "__main__":
    data_path = PROJECT_ROOT / "data" / "processed" / "data_Scenario_Pane_2035.csv"
    df = pd.read_csv(data_path)

    out = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig_emissions_by_scenario_growth"
    generate_fig_emissions_by_scenario_growth(df, str(out))
