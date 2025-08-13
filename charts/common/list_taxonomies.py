# charts/common/list_taxonomies.py
from __future__ import annotations
from pathlib import Path
import sys
import pandas as pd
import yaml

# --- Find repo root robustly (works no matter where you run this) -------------
HERE = Path(__file__).resolve()
CANDIDATES = [HERE] + list(HERE.parents)
PROJECT_ROOT = None
for p in CANDIDATES:
    if (p / "data" / "processed").exists():
        PROJECT_ROOT = p
        break
if PROJECT_ROOT is None:
    # fallback: cwd if launched elsewhere
    PROJECT_ROOT = Path.cwd()

DATA_DIR  = PROJECT_ROOT / "data" / "processed"
PARQ      = DATA_DIR / "processed_dataset.parquet"
CSV       = DATA_DIR / "processed_dataset.csv"
OUT_DIR   = PROJECT_ROOT / "outputs" / "lookups"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Ensure we can import charts.common.style
sys.path.insert(0, str(PROJECT_ROOT))

print(f"🔎 Using PROJECT_ROOT = {PROJECT_ROOT}")
print(f"📦 Looking for data at:\n  - {PARQ}\n  - {CSV}")

# --- Load dataset (Parquet preferred, else CSV) -------------------------------
if PARQ.exists():
    try:
        import pyarrow.parquet as pq
        df = pq.read_table(PARQ).to_pandas()
        print(f"✅ Loaded Parquet: {PARQ}")
    except Exception as e:
        print(f"⚠️ pyarrow read failed ({e}); trying pandas.read_parquet...")
        df = pd.read_parquet(PARQ)
elif CSV.exists():
    df = pd.read_csv(CSV)
    print(f"✅ Loaded CSV: {CSV}")
else:
    raise FileNotFoundError(
        f"Could not find dataset. Expected one of:\n  - {PARQ}\n  - {CSV}"
    )

# --- Style + palettes ---------------------------------------------------------
import charts.common.style as style
from charts.common.style import extend_palettes_from_df, color_for

# Populate palettes from the dataframe (keeps curated logic first)
extend_palettes_from_df(df)

def uniq(series):
    if series is None:
        return []
    return sorted({str(x).strip() for x in series.dropna().astype(str).tolist()})

# Detect column names present in your dataset
fam_col   = "ScenarioFamily" if "ScenarioFamily" in df.columns else None
group_col = "ScenarioGroup" if "ScenarioGroup" in df.columns else ("Scenario_Group" if "Scenario_Group" in df.columns else None)
fuel_col  = "Commodity_Name" if "Commodity_Name" in df.columns else ("Commodity" if "Commodity" in df.columns else None)

scenarios          = uniq(df["Scenario"]) if "Scenario" in df.columns else []
scenario_families  = uniq(df[fam_col]) if fam_col else []
scenario_groups    = uniq(df[group_col]) if group_col else []
sectors            = uniq(df["Sector"]) if "Sector" in df.columns else []
fuels              = uniq(df[fuel_col]) if fuel_col else []

# Color for groups: prefer dedicated group palette if present
def color_for_group(name: str) -> str:
    if hasattr(style, "SCENARIO_GROUP_COLORS"):
        return style.SCENARIO_GROUP_COLORS.get(name, style.DEFAULT_COLOR)
    # fallback: use family palette if group palette not defined
    return color_for("scenario_family", name)

def build_table(kind: str, names, override=None) -> pd.DataFrame:
    if override:
        rows = [{"label": n, "suggested_hex": override(n)} for n in names]
    else:
        rows = [{"label": n, "suggested_hex": color_for(kind, n)} for n in names]
    return pd.DataFrame(rows, columns=["label", "suggested_hex"])

tbl_scenarios   = build_table("scenario",         scenarios)
tbl_families    = build_table("scenario_family",  scenario_families)
tbl_groups      = build_table("scenario_group",   scenario_groups, override=color_for_group)
tbl_sectors     = build_table("sector",           sectors)
tbl_fuels       = build_table("fuel",             fuels)

# Save CSVs
tbl_scenarios.to_csv(OUT_DIR / "scenarios.csv", index=False)
tbl_families.to_csv(OUT_DIR / "scenario_families.csv", index=False)
tbl_groups.to_csv(OUT_DIR / "scenario_groups.csv", index=False)
tbl_sectors.to_csv(OUT_DIR / "sectors.csv", index=False)
tbl_fuels.to_csv(OUT_DIR / "fuels.csv", index=False)

# YAML palette skeleton
palette_yaml = {
    "scenarios":          {r.label: r.suggested_hex for _, r in tbl_scenarios.iterrows()},
    "scenario_families":  {r.label: r.suggested_hex for _, r in tbl_families.iterrows()},
    "scenario_groups":    {r.label: r.suggested_hex for _, r in tbl_groups.iterrows()},
    "sectors":            {r.label: r.suggested_hex for _, r in tbl_sectors.iterrows()},
    "fuels":              {r.label: r.suggested_hex for _, r in tbl_fuels.iterrows()},
}
with open(OUT_DIR / "palette_suggestions.yaml", "w", encoding="utf-8") as f:
    yaml.safe_dump(palette_yaml, f, sort_keys=True, allow_unicode=True)

# Console preview
def preview(name, items, max_show=25):
    print(f"\n{name} ({len(items)}):")
    for val in items[:max_show]:
        print(f"  - {val}")
    if len(items) > max_show:
        print(f"  … and {len(items) - max_show} more")

preview("Scenarios", scenarios)
preview("Scenario Families", scenario_families)
preview("Scenario Groups", scenario_groups)
preview("Sectors", sectors)
preview("Fuels", fuels)

print(f"\n📁 Outputs written to: {OUT_DIR}")
