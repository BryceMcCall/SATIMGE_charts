# charts/chart_generators/fig_line_emissions_all.py
from __future__ import annotations

import sys
from pathlib import Path
import re
import pandas as pd
import plotly.graph_objects as go
import yaml

# ── safe import path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures


# ── Legend colour map (matches your palette; IRPLight updated)
SCENARIO_COLORS = {
    "CPP-IRP":       "#d46820",
    "CPP-IRPLight":  "#a3fc5a",
    "CPP-SAREM":     "#1cdaf3",
    "CPPS":          "#ff6e1a",
    "CPPS Variant":  "#b3ada9",
    "High Carbon":   "#ff0000",
    "Low Carbon":    "#008000",
    "WEM":           "#1E1BD3",
}


def infer_family(name: str) -> str:
    """Map concrete Scenario names to high-level legend families."""
    n = str(name).upper()

    # Direct matches first
    if "WEM" in n:
        return "WEM"
    if "SAREM" in n:
        return "CPP-SAREM"
    if "IRPLIGHT" in n:
        return "CPP-IRPLight"
    if "IRPFULL" in n or re.search(r"\bIRP\b", n):
        return "CPP-IRP"
    if "LCARB" in n or "LOWCARB" in n or re.search(r"\bLOW[-_ ]?CARB\b", n):
        return "Low Carbon"
    if "HCARB" in n or "HIGHCARB" in n or re.search(r"\bHIGH[-_ ]?CARB\b", n):
        return "High Carbon"

    # CPPS Variant (special CPP flavours)
    if any(k in n for k in ["CPP5", "CPPV", "CPP4GE", "CPP4EK", "CPP4EKH"]):
        return "CPPS Variant"

    # Everything else that is CPP*, BASE*, NZ, APS, etc. → CPPS
    if "CPP" in n or "BASE" in n:
        return "CPPS"

    # Fallback
    return "CPPS"


def _load_df(csv_hint: str | Path | None = None) -> pd.DataFrame:
    """Load Scenario/Year/MtCO2-eq from CSV and prepare for plotting."""
    candidates: list[Path] = []
    if csv_hint:
        candidates.append(Path(csv_hint))
    candidates += [
        PROJECT_ROOT / "data" / "raw" / "emissions_line_all_scenarios.csv",
        PROJECT_ROOT / "data" / "processed" / "emissions_line_all_scenarios.csv",
    ]

    for p in candidates:
        if p.exists():
            df = pd.read_csv(p)
            break
    else:
        raise FileNotFoundError("Could not find emissions_line_all_scenarios.csv")

    # Normalize column names and types
    df = df.rename(columns={"MtCO2-eq": "MtCO2eq"})
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["MtCO2eq"] = pd.to_numeric(df["MtCO2eq"], errors="coerce")

    # Keep 2024–2035 and valid rows
    df = df[df["Year"].between(2024, 2035)].dropna(subset=["Scenario", "Year", "MtCO2eq"]).copy()

    # Add family mapping
    df["ScenarioFamily"] = df["Scenario"].astype(str).map(infer_family)

    # If your source were kt instead of Mt, you would scale here:
    # df["MtCO2eq"] = df["MtCO2eq"] * 0.001

    return df


def generate_fig_line_emissions_all(
    df_in: pd.DataFrame | None,
    output_dir: str,
    csv_hint: str | Path | None = None,
) -> None:
    """Grey lines for each Scenario; coloured diamond means at 2035 by ScenarioFamily."""
    print("▶ Generating: line emissions (all scenarios) — CSV source")

    df = df_in.copy() if df_in is not None else _load_df(csv_hint)
    df = df.sort_values(["Scenario", "Year"])

    fig = go.Figure()

    # 1) thin grey trajectories for every scenario
    for scen, sub in df.groupby("Scenario", sort=False):
        fig.add_trace(
            go.Scatter(
                x=sub["Year"],
                y=sub["MtCO2eq"],
                mode="lines",
                line=dict(color="#919090", width=1.4),
                hovertemplate=f"{scen}<br>%{{x}}: %{{y:.1f}} Mt<extra></extra>",
                showlegend=False,
            )
        )

    # 2) legend diamonds in a SPECIFIC order
    families_present = (
        df.loc[df["Year"] <= 2035, "ScenarioFamily"]
          .dropna().unique().tolist()
    )

    def _last_or_2035_mean(g: pd.DataFrame) -> float:
        """Mean at 2035 if present; else mean at the last available year ≤2035."""
        if (g["Year"] == 2035).any():
            return g.loc[g["Year"] == 2035, "MtCO2eq"].mean()
        last_year = g.loc[g["Year"] <= 2035, "Year"].max()
        return g.loc[g["Year"] == last_year, "MtCO2eq"].mean()

    means = (
        df[df["Year"] <= 2035]
          .groupby("ScenarioFamily")
          .apply(_last_or_2035_mean)
          .reset_index(name="MtCO2eq")
    )

    # --- preferred legend order (edit this list any time) ---
    FAMILY_ORDER = [
        "High Carbon",
        "WEM",
        "CPP-IRP",
        "CPP-IRPLight",
        "CPPS Variant",
        "CPP-SAREM",
        "CPPS",
        "Low Carbon",
    ]

    ordered_families = [f for f in FAMILY_ORDER if f in families_present] + \
                       sorted(set(families_present) - set(FAMILY_ORDER))

    for fam in ordered_families:
        yval = means.loc[means["ScenarioFamily"] == fam, "MtCO2eq"]
        if yval.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=[2035],
                y=[float(yval.iloc[0])],
                mode="markers",
                name=fam,
                marker=dict(size=10, color=SCENARIO_COLORS.get(fam, "#666"), symbol="diamond"),
                hovertemplate=f"{fam}<br>value used: %{{y:.1f}} Mt<extra></extra>",
                showlegend=True,
            )
        )

    # ── Layout & styling
    apply_common_layout(fig, image_type="report")
    fig.update_layout(
        width=2000,
        title_text="",
        legend_title_text="",
        legend=dict(
            traceorder="normal",            # keep our manual order
            orientation="v",
            x=1.02, xanchor="left",
            y=0.80, yanchor="middle",
            itemsizing="constant",
        ),
        margin=dict(l=92, r=160, t=8, b=48),
    )

    YEARS = list(range(2024, 2036))
    fig.update_xaxes(
        title="",
        range=[2024, 2035.09],   # tiny right pad for markers
        tickangle=-45,
        tickfont=dict(size=18),
        ticklabeloverflow="allow",
        tickmode="array",
        tickvals=YEARS,
        ticktext=[str(y) for y in YEARS],
    )
    fig.update_yaxes(
        title="CO₂eq Emissions (Mt)",
        tickformat=".0f",
        title_font=dict(size=22),
    )

    # ── Save
    save_figures(fig, output_dir, name="fig_line_emissions_all")

    # Also write a data snapshot (unless dev_mode true)
    cfg_path = PROJECT_ROOT / "config.yaml"
    dev_mode = False
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as f:
            dev_mode = bool(yaml.safe_load(f).get("dev_mode", False))
    if not dev_mode:
        df.to_csv(Path(output_dir) / "data.csv", index=False)

    print("✓ Saved fig_line_emissions_all")


if __name__ == "__main__":
    outdir = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig_line_emissions_all"
    outdir.mkdir(parents=True, exist_ok=True)
    # Pass a specific CSV if needed: generate_fig_line_emissions_all(None, str(outdir), "path/to/file.csv")
    generate_fig_line_emissions_all(None, str(outdir))
