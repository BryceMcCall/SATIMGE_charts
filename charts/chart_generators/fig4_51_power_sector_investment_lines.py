# charts/chart_generators/fig4_51_power_sector_investment_lines.py
#
# Multi-line chart: cumulative investment in the power sector (Billion ZAR)
# across many scenarios, coloured by whether the scenario is "All others" or
# "Scenarios below 300". Uses dense minor y-ticks and -45° x-ticks.

# charts/chart_generators/fig4_51_power_sector_investment_lines.py
#
# Multi-line chart: cumulative investment in the power sector (Billion ZAR)
# Colours: Blue = "All others", Orange = "Scenarios below 300Mt CO₂eq in 2035"
# Legend on the right (no title), orange label wraps after "300Mt" and uses CO₂.

from __future__ import annotations
import sys, re, yaml, shutil
from pathlib import Path
import pandas as pd
import plotly.express as px

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

# ── constants ───────────────────────────────────────────────────────
GROUP_COL = "NDC Scenarios below 300"
VALUE_COL = "Running Sum of Investment in POWER"

# Legend labels (with line break + CO₂)
LABEL_BELOW300 = "Scenarios below 300Mt<br>CO\u2082eq in 2035"  # CO₂
LABEL_OTHERS   = "All others"

# Display mapping, colour map, and order
LABELS = {"Scenarios below 300": LABEL_BELOW300, "All others": LABEL_OTHERS}
COLOR_MAP = {LABEL_BELOW300: "#F4A261", LABEL_OTHERS: "#6EA3C6"}  # orange / blue
LEGEND_ORDER = [LABEL_BELOW300, LABEL_OTHERS]

# ── helpers ─────────────────────────────────────────────────────────
def _to_float_safe(x):
    """Coerce strings like '1 086.39' (NBSP) or with commas to float."""
    if pd.isna(x):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x)
    s = s.replace("\xa0", "")  # NBSP from Excel exports
    s = re.sub(r"[^\d.\-eE]", "", s)  # remove thousands separators/odd chars
    try:
        return float(s)
    except Exception:
        return None

def _co2_sub(s: str | None) -> str | None:
    """Replace 'CO2' with 'CO₂' in any layout titles."""
    return None if s is None else str(s).replace("CO2", "CO\u2082")

# ── generator ───────────────────────────────────────────────────────
def generate_fig4_51_power_sector_investment_lines(df: pd.DataFrame, output_dir: str) -> None:
    print("generating figure 4.51: Power sector cumulative investment (lines)")
    print(f"📂 Output directory: {output_dir}")

    d = df.copy()

    # Normalize column names to expected ones
    rename_map = {}
    for c in d.columns:
        cl = c.lower().strip()
        if "ndc" in cl and "scenarios" in cl:
            rename_map[c] = GROUP_COL
        elif cl == "scenario":
            rename_map[c] = "Scenario"
        elif cl == "year":
            rename_map[c] = "Year"
        elif "running" in cl and "power" in cl:
            rename_map[c] = VALUE_COL
    if rename_map:
        d.rename(columns=rename_map, inplace=True)

    # Keep required cols
    d = d[[GROUP_COL, "Scenario", "Year", VALUE_COL]].copy()

    # Types & ranges
    d["Year"] = pd.to_numeric(d["Year"], errors="coerce").astype("Int64")
    d = d[d["Year"].between(2025, 2035)]
    d[VALUE_COL] = d[VALUE_COL].map(_to_float_safe).fillna(0.0)

    # Map display labels (incl. CO₂ + line break)
    d[GROUP_COL] = d[GROUP_COL].map(lambda x: LABELS.get(str(x), str(x)))

    years = sorted(d["Year"].dropna().unique().tolist())

    # Plot — one line per Scenario, coloured by group
    fig = px.line(
        d,
        x="Year",
        y=VALUE_COL,
        color=GROUP_COL,
        line_group="Scenario",
        category_orders={"Year": years, GROUP_COL: LEGEND_ORDER},
        color_discrete_map=COLOR_MAP,
        labels={
            "Year": "",
            VALUE_COL: "Cumulative investment in the power sector (Billion ZAR)",
            GROUP_COL: "",
        },
    )

    fig = apply_common_layout(fig)

    # Ensure any stray CO2 in titles becomes CO₂
    fig.update_layout(
        title=_co2_sub(fig.layout.title.text),
        xaxis_title=_co2_sub(fig.layout.xaxis.title.text),
        yaxis_title=_co2_sub(fig.layout.yaxis.title.text),
    )

    # Layout & legend (right, no title, slightly smaller font)
    fig.update_layout(
        legend_title_text="",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1.0,
            xanchor="left",
            x=1.02,
            font=dict(size=20) 
        ),
        margin=dict(l=70, r=180, t=20, b=90),
        yaxis=dict(title=dict(text="Cumulative investment in power sector (Billion ZAR)", font=dict(size=22))),
    )

    # Styling: thin lines, mild opacity
    for tr in fig.data:
        tr.update(line=dict(width=2), opacity=0.9)

    # Axes: -45° x-ticks, major y dtick and dense minors
    fig.update_xaxes(
        tickmode="array",
        tickvals=years,
        ticktext=[str(y) for y in years],
        tickangle=-45,
    )
    fig.update_yaxes(dtick=200, minor=dict(showgrid=True, dtick=50))

    # ── Save ──
    if dev_mode:
        print("👩‍💻 dev_mode ON — preview only")
        return

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    save_figures(fig, output_dir, name="fig4_51_power_sector_investment_lines")
    d.to_csv(out_dir / "fig4_51_power_sector_investment_lines_data.csv", index=False)

    gallery_dir = project_root / "outputs" / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    src_img = out_dir / "fig4_51_power_sector_investment_lines_report.png"
    if src_img.exists():
        shutil.copy2(src_img, gallery_dir / src_img.name)

# ── CLI entry ───────────────────────────────────────────────────────
if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "4_51_power_sector_investment.csv"
    if not data_path.exists():
        raise FileNotFoundError(
            f"Data file not found at {data_path}. "
            "Expected columns: 'NDC Scenarios below 300', 'Scenario', 'Year', 'Running Sum of Investment in POWER'."
        )

    # Robust CSV load for Windows/Excel exports
    try:
        df = pd.read_csv(data_path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(data_path, encoding="cp1252", engine="python")

    out = project_root / "outputs" / "charts_and_data" / "fig4_51_power_sector_investment_lines"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig4_51_power_sector_investment_lines(df, str(out))
