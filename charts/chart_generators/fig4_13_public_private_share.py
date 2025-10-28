# charts/chart_generators/fig4_13_public_private_pkm.py
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import yaml

# ── project root on path ────────────────────────────────────────────
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures

DATA_FILE = project_root / "data" / "processed" / "4_13_transport_mode_share_wem.csv"
OUT_DIR   = project_root / "outputs" / "charts_and_data" / "fig4_13_public_private_pkm"

# Toggle dev preview via config.yaml (optional)
dev_mode = False
cfg = project_root / "config.yaml"
if cfg.exists():
    with open(cfg, "r", encoding="utf-8") as f:
        dev_mode = yaml.safe_load(f).get("dev_mode", False)

# Legend renaming (customize as you like)
LEGEND_LABELS = {
    "PassPriv": "Private",
    "PassPub":  "Public",
}

COLOR_MAP = {
    "PassPriv": "#f4a742",  # orange
    "PassPub":  "#7ec8f5",  # light blue
}

def _read_tidy(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Expect: Scenario, Subsector, Year, "% of Total SATIMGE", "SATIMGE"
    df = df.rename(columns={
        "Subsector": "Group",
        "% of Total SATIMGE": "Pct",
        "SATIMGE": "pkm"
    }).copy()

    # % column -> float (0–1) for labeling
    df["Pct"] = (
        df["Pct"].astype(str).str.strip().str.replace("%", "", regex=False)
        .replace({"": "0"}).astype(float) / 100.0
    )
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["pkm"]  = pd.to_numeric(df["pkm"],  errors="coerce").fillna(0.0)

    # Keep only PassPriv / PassPub
    df = df[df["Group"].isin(["PassPriv", "PassPub"])].copy()

    # If multiple rows per year/group, aggregate (sum)
    df = (df.groupby(["Year", "Group"], as_index=False)
            .agg(pkm=("pkm","sum"), Pct=("Pct","mean"))
            .sort_values(["Year","Group"]))
    return df

def generate_fig(df: pd.DataFrame) -> go.Figure:
    years = sorted(df["Year"].dropna().unique().tolist())
    piv = df.pivot(index="Year", columns="Group", values="pkm").fillna(0.0).reindex(years)
    piv_pct = df.pivot(index="Year", columns="Group", values="Pct").fillna(0.0).reindex(years)

    priv = piv.get("PassPriv", pd.Series(0.0, index=years))
    pub  = piv.get("PassPub",  pd.Series(0.0, index=years))

    fig = go.Figure()

    # Bottom: Private (pkm)
    fig.add_trace(go.Bar(
        x=years, y=priv.values,
        name=LEGEND_LABELS.get("PassPriv","PassPriv"),
        marker_color=COLOR_MAP["PassPriv"],
        hovertemplate=f"{LEGEND_LABELS.get('PassPriv','PassPriv')}<br>%{{x}}: %{{y:.1f}} billion pkm<extra></extra>",
    ))

    # Top: Public (pkm)
    fig.add_trace(go.Bar(
        x=years, y=pub.values,
        name=LEGEND_LABELS.get("PassPub","PassPub"),
        marker_color=COLOR_MAP["PassPub"],
        hovertemplate=f"{LEGEND_LABELS.get('PassPub','PassPub')}<br>%{{x}}: %{{y:.1f}} billion pkm<extra></extra>",
    ))

    # On-bar % labels (from the % column)
    # Y positions: center of each stacked segment
    cum_priv = priv.values
    cum_pub  = priv.values + pub.values
    label_y_priv = cum_priv / 2.0
    label_y_pub  = cum_priv + (pub.values / 2.0)

    for i, yr in enumerate(years):
        p_priv = piv_pct.loc[yr, "PassPriv"]*100 if "PassPriv" in piv_pct.columns else 0
        p_pub  = piv_pct.loc[yr, "PassPub"]*100  if "PassPub"  in piv_pct.columns else 0

        fig.add_annotation(x=yr, y=label_y_priv[i],
            text=f"{p_priv:.0f}%", showarrow=False,
            font=dict(color="#333", size=18))
        fig.add_annotation(x=yr, y=label_y_pub[i],
            text=f"{p_pub:.0f}%",  showarrow=False,
            font=dict(color="#333", size=18))

    # Layout
    fig = apply_common_layout(fig)
    fig.update_layout(
        barmode="stack",
        legend_title_text="",
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(l=80, r=180, t=40, b=90),
        width=1200, height=650,
    )
    fig.update_xaxes(
        title_text="",
        tickangle=-45,
        tickmode="array",
        tickvals=years,
    )
    fig.update_yaxes(
        title_text="Passenger kilometers (billion pkm)",
    )

    return fig

if __name__ == "__main__":
    print("generating: Public vs Private passenger-km (absolute, stacked)")
    df = _read_tidy(DATA_FILE)
    fig = generate_fig(df)

    if dev_mode:
        print("👀 dev_mode ON — preview only")
        # fig.show()
    else:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        save_figures(fig, str(OUT_DIR), name="fig4_13_public_private_pkm")
        df.to_csv(OUT_DIR / "fig4_13_public_private_pkm_data.csv", index=False)
        print(f"✔️ saved to {OUT_DIR}")
