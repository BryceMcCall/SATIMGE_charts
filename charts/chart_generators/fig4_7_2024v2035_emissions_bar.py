# charts/chart_generators/fig4_7_2024v2035_emissions_bar.py
from __future__ import annotations
import sys
from pathlib import Path
import shutil
import yaml
import pandas as pd
import plotly.express as px

# Allow shared imports when run directly
if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

# If you use the shared helpers in your repo, keep these:
try:
    from charts.common.style import apply_common_layout   # optional, but nice if present
except Exception:
    def apply_common_layout(fig):  # no-op fallback
        return fig

try:
    from charts.common.save import save_figures           # expects (fig, out_dir, name)
except Exception:
    def save_figures(fig, out_dir: str, name: str):
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        # default high-res export
        fig.write_image(out / f"{name}_report.png", scale=4, width=1800, height=900)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
DEV_MODE = False
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        DEV_MODE = yaml.safe_load(f).get("dev_mode", False)


def _wrap_label(text: str, width: int = 22) -> str:
    """Clean 'CategoryGroup=...' and soft-wrap long labels while respecting <br>."""
    lbl = text.split("=")[-1].strip()
    parts = []
    for chunk in lbl.split("<br>"):
        words, line, out = chunk.split(), "", []
        for w in words:
            if len(line) + len(w) + (1 if line else 0) <= width:
                line = f"{line} {w}".strip()
            else:
                out.append(line)
                line = w
        if line:
            out.append(line)
        parts.append("<br>".join(out))
    return "<br>".join(parts)


# ───────────────────────── Generator ─────────────────────────
def generate_fig4_7_2024v2035_emissions_bar(df: pd.DataFrame, output_dir: str) -> None:
    """
    Faceted grouped bar chart:
      x = Year (2024 vs 2035), y = CO2eq, facet = CategoryGroup.
    Expects columns: ['CategoryGroup','Year','CO2eq'].
    Drops 'Other'.
    """
    data = df.copy()

    # Robust rename to expected column names
    rename = {}
    for c in data.columns:
        lc = c.lower().strip()
        if lc in {"categorygroup", "category_group", "category"}:
            rename[c] = "CategoryGroup"
        elif lc == "year":
            rename[c] = "Year"
        elif lc in {"co2eq", "mtco2-eq", "mtco2eq", "value"}:
            rename[c] = "CO2eq"
    if rename:
        data = data.rename(columns=rename)

    # Validate + tidy
    req = {"CategoryGroup", "Year", "CO2eq"}
    missing = req - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    data["Year"] = pd.to_numeric(data["Year"], errors="coerce").astype("Int64")
    data["CO2eq"] = pd.to_numeric(data["CO2eq"], errors="coerce")
    data = data.dropna(subset=["CategoryGroup", "Year", "CO2eq"])

    # Drop 'Other' and keep only 2024 & 2035
    data = data[data["CategoryGroup"].astype(str).str.strip().ne("Other")]
    data = data[data["Year"].isin([2024, 2035])].copy()

    # Plotly colour mapping wants strings
    data["Year"] = data["Year"].astype(str)
    year_colors = {"2024": "#1f77b4", "2035": "#ff7f0e"}  # blue / orange

    # Base figure
    fig = px.bar(
        data_frame=data,
        x="Year",
        y="CO2eq",
        facet_col="CategoryGroup",
        color="Year",
        barmode="group",
        color_discrete_map=year_colors,
        category_orders={"Year": ["2024", "2035"]},
        labels={"CO2eq": "Emissions (Mt CO2-eq)", "Year": ""},
        title="",
        facet_col_spacing=0.02,
    )

    # Clean & wrap facet titles
    fig.for_each_annotation(
        lambda a: a.update(
            text=_wrap_label(a.text, width=22),
            font=dict(size=13),
            align="center",
            yshift=8,
        )
    )

    # Shared layout + requested axis tweaks
    fig = apply_common_layout(fig)

    # Axis/title sizing + bar gaps
    fig.update_layout(
        showlegend=False,
        barmode="group",
        bargap=0.12,                 # ↓ smaller gap between category groups (facets)
        bargroupgap=0.0,             # ↓ no gap between 2024 & 2035 bars (closer)
        margin=dict(t=90, l=70, r=40, b=100),
        yaxis_title="Emissions (MtCO₂-eq)",
        yaxis_title_font=dict(size=20),  # just a bit bigger than x-tick labels
    )

    # X labels: rotate and set tick font a touch smaller than y-axis title
    fig.update_xaxes(tickangle=-90, ticks="outside", tickfont=dict(size=19))

    # (optional) keep your denser y ticks
    fig.update_yaxes(dtick=25, minor=dict(showgrid=True, dtick=5))


    # Save outputs
    out = Path(output_dir)
    if not DEV_MODE:
        save_figures(fig, str(out), name="fig4_7_2024v2035_emissions_bar")
        out.mkdir(parents=True, exist_ok=True)
        data.to_csv(out / "fig4_7_2024v2035_emissions_bar_data.csv", index=False)

        # Optional: copy PNG to gallery
        png = out / "fig4_7_2024v2035_emissions_bar_report.png"
        gallery = PROJECT_ROOT / "outputs" / "gallery"
        if png.exists():
            gallery.mkdir(parents=True, exist_ok=True)
            shutil.copy2(png, gallery / png.name)


# ──────────────────────────── CLI ────────────────────────────
if __name__ == "__main__":
    default_csv = PROJECT_ROOT / "data" / "processed" / "4_7_2024v2035_emissions_bar.csv"
    if not default_csv.exists():
        raise SystemExit(f"CSV not found at {default_csv}")
    df0 = pd.read_csv(default_csv)
    out_dir = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig4_7_2024v2035_emissions_bar"
    out_dir.mkdir(parents=True, exist_ok=True)
    generate_fig4_7_2024v2035_emissions_bar(df0, str(out_dir))
