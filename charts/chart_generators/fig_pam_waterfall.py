# charts/chart_generators/fig_pam_waterfall.py
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go

# Allow running this file directly
if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures

# ───────────────────────── Config ─────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]

_CSV_CANDIDATES = [
    PROJECT_ROOT / "data" / "processed" / "waterfall_pam_sector_reductions.csv",
    PROJECT_ROOT / "data" / "raw" / "waterfall_pam_sector_reductions.csv",
    PROJECT_ROOT / "waterfall_pam_sector_reductions.csv",
]

# Set WEM baseline (Mt CO2eq) — change here or wire to a CSV if preferred
WEM_2035 = 356.0

# Colors (compatible with older Plotly Waterfall)
ANCHOR_COLOR   = "#9E9E9E"   # used for subtle WEM shading (via vrect)
DECREASING_COL = "#6A1B9A"   # PaM step-down bars (IRP color)
CONNECTOR_COL  = "#BDBDBD"   # connectors + zero line
LABEL_COL      = "#222222"   # text color

# Sort order for PaMs: "desc" (largest ∆ first), "asc", or "csv" to keep file order
ORDER = "desc"


def _load_pam_table() -> pd.DataFrame:
    for p in _CSV_CANDIDATES:
        if p.exists():
            print(f"✅ Loaded PaM table from: {p}")
            return pd.read_csv(p)
    raise FileNotFoundError(
        "Could not find 'waterfall_pam_sector_reductions.csv' in any of:\n"
        + "\n".join(str(p) for p in _CSV_CANDIDATES)
    )


def _compute_reductions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input (wide):
        Policy, <sector1>, <sector2>, ... [optional TOTAL]
    Output:
        Policy, Reduction (Mt)
    """
    if "TOTAL" in df.columns:
        out = df[["Policy", "TOTAL"]].rename(columns={"TOTAL": "Reduction"})
    else:
        num_cols = [c for c in df.columns if c != "Policy" and pd.api.types.is_numeric_dtype(df[c])]
        out = df[["Policy"]].copy()
        out["Reduction"] = df[num_cols].sum(axis=1)

    if ORDER == "desc":
        out = out.sort_values("Reduction", ascending=False, ignore_index=True)
    elif ORDER == "asc":
        out = out.sort_values("Reduction", ascending=True, ignore_index=True)
    # else: keep CSV order
    return out


def generate_fig_pam_waterfall(_: pd.DataFrame, output_dir: str) -> None:
    """
    Absolute-emissions view:
      Sequence = [WEM (absolute), -∆(PaM), WEM (absolute), -∆(next PaM), ...]
      y-axis shows absolute Mt CO₂eq; the top of each PaM step lands at (WEM - ∆).
      Effects are NOT added together.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw = _load_pam_table()
    red = _compute_reductions(raw)

    # Tight y-range around levels we show
    max_drop = float(red["Reduction"].max()) if not red.empty else 0.0
    y_min = max(0.0, (WEM_2035 - max_drop) - 5)  # small padding
    y_max = WEM_2035 + 10

    # Build alternating anchors and steps
    x_labels, measures, y_vals, abs_text = [], [], [], []

    def add_wem():
        x_labels.append("WEM 2035")
        measures.append("absolute")
        y_vals.append(WEM_2035)
        abs_text.append(f"{WEM_2035:.0f}")  # absolute level label

    def add_policy(name: str, reduction: float):
        x_labels.append(name)
        measures.append("relative")
        y_vals.append(-float(reduction))  # relative step down
        final_level = WEM_2035 - float(reduction)
        abs_text.append(f"{final_level:.0f}")  # show absolute level at step end

    for _, row in red.iterrows():
        add_wem()
        add_policy(str(row["Policy"]), float(row["Reduction"]))

    # Waterfall trace (single-color for decreasing bars for compatibility)
    fig = go.Figure(
        go.Waterfall(
            orientation="v",
            measure=measures,
            x=x_labels,
            y=y_vals,
            text=abs_text,                  # absolute level labels
            textposition="outside",
            decreasing=dict(marker=dict(color=DECREASING_COL)),
            connector=dict(line=dict(color=CONNECTOR_COL, width=1)),
            hovertemplate="<b>%{x}</b><br>Level: %{text} Mt CO₂eq<extra></extra>",
        )
    )

    # Apply shared style
    fig = apply_common_layout(fig, image_type="report")
    fig.update_layout(
        title="2035 emissions: WEM vs single-policy effects (non-additive)",
        yaxis_title="Emissions in 2035 (Mt CO₂eq)",
        showlegend=False,
        margin=dict(l=90, r=40, t=60, b=100),
        annotations=[
            dict(
                x=0.5, y=1.12, xref="paper", yref="paper",
                text="Each policy shown as a step down from WEM; effects are not added together.",
                showarrow=False, font=dict(size=12, color=LABEL_COL),
            )
        ],
    )

    # Clean axes: tight range, 5-Mt ticks, dotted WEM reference line
    fig.update_yaxes(range=[y_min, y_max], dtick=5, showgrid=True, gridcolor="#E7E7E7",
                     zeroline=True, zerolinecolor="#CCCCCC", zerolinewidth=1)
    try:
        # Optional minor ticks (ignore if Plotly build doesn't support)
        fig.update_yaxes(minor=dict(showgrid=False, ticks="outside", ticklen=3, dtick=1))
    except Exception:
        pass
    fig.update_xaxes(tickangle=-15)

    # Dotted horizontal line at WEM
    fig.add_hline(y=WEM_2035, line_color="#AFAFAF", line_dash="dot", opacity=0.9)

    # Subtle shading behind each WEM anchor bar (no alternating bands)
    # Find x-indexes for anchors and add faint vrects
    for i, (lab, m) in enumerate(zip(x_labels, measures)):
        if m == "absolute" and lab == "WEM 2035":
            fig.add_vrect(x0=i - 0.45, x1=i + 0.45, fillcolor=ANCHOR_COLOR, opacity=0.12, line_width=0)

    # Add small ∆ labels near each PaM step (e.g., "–56")
    delta_annos = []
    xi = 0
    for _, row in red.iterrows():
        # The PaM step is at xi+1 (because xi is WEM, xi+1 is PaM)
        pam_x_index = xi + 1
        delta_val = float(row["Reduction"])
        # place a small delta just above the final level
        y_here = WEM_2035 - delta_val + 2.5
        delta_annos.append(
            dict(
                x=pam_x_index, y=y_here, xref="x", yref="y",
                text=f"–{delta_val:.0f}", showarrow=False,
                font=dict(size=11, color="#444"),
            )
        )
        xi += 2  # move to next [WEM, PaM] pair
    fig.update_layout(annotations=(fig.layout.annotations or []) + tuple(delta_annos))

    # Save figure + tidy data table (WEM, ∆, and absolute with-PaM level)
    name = "fig_pam_waterfall"
    out_dir = Path(output_dir)
    save_figures(fig, str(out_dir), name=name)

    out_tbl = red.copy()
    out_tbl["WEM_2035"] = WEM_2035
    out_tbl["Emissions_with_PaM"] = WEM_2035 - out_tbl["Reduction"]
    out_tbl.to_csv(out_dir / f"{name}_data.csv", index=False)

    print(f"✔ Saved: {out_dir / (name + '_report.png')}")

# Standalone run
if __name__ == "__main__":
    out = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig_pam_waterfall"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig_pam_waterfall(pd.DataFrame(), str(out))

