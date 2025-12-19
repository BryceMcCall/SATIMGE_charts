# %%
# generate_dataset.py

import pandas as pd
import numpy as np
from utils.mappings import (
    map_scenario_family,
    map_sector_group,
    extract_carbon_budget,
    map_economic_growth,
    apply_mapping_and_clean,
)

# ─────────────────────────────────────────────────────────────────────────────
# Paths
RAW_PATH = "data/raw/REPORT_00.csv"
OUT_CSV = "data/processed/processed_dataset.csv"
OUT_PARQUET = "data/processed/processed_dataset.parquet"

# Pick the Sets & Maps workbook you actually have locally
# (edit this if your file lives elsewhere)
path_setsandmaps = r"C:\Models\SATIMGE_Veda\SetsAndMaps\SetsAndMaps.xlsm"
# path_setsandmaps = r"C:\Users\savan\OneDrive\Documents\GitHub\SATIMGE_Veda\setsandmaps\setsandmaps.xlsm"
# ─────────────────────────────────────────────────────────────────────────────

print("📥 reading raw data file")
# low_memory=False to avoid dtype fragmentation/mixed-type surprises
df = pd.read_csv(RAW_PATH, low_memory=False)

print("📚 reading SetsAndMaps")
mapPRC_df = pd.read_excel(path_setsandmaps, sheet_name="mapPRC")
mapCOM_df = pd.read_excel(path_setsandmaps, sheet_name="mapCOM")

print("🔄 applying sets and maps")
proc_df = apply_mapping_and_clean(df, mapPRC_df, mapCOM_df)

# ── Ensure Sector exists and is safe to use
if "Sector" not in proc_df.columns:
    raise KeyError(
        "Sector column missing after mapping — check SetsAndMaps and apply_mapping_and_clean()."
    )

# Normalize Sector to string and fill missing
proc_df["Sector"] = proc_df["Sector"].astype("string").fillna("Unknown")

# Safe wrapper: tolerate non-strings / unexpected values
def _safe_sector_group(x):
    try:
        s = "" if (x is None or (isinstance(x, float) and np.isnan(x))) else str(x)
        return map_sector_group(s)
    except Exception:
        return "Unknown"

proc_df["SectorGroup"] = proc_df["Sector"].apply(_safe_sector_group)

# ── Create CO2eq from gases (uses SATIMGE × GWP for known gases)
print("⚖ calculating CO2eq")
GWP = {"CO2": 1, "CO2eq": 1, "CH4": 28, "N2O": 265, "CF4": 6630, "C2F6": 11100}
if "Indicator" not in proc_df.columns or "SATIMGE" not in proc_df.columns:
    raise KeyError("Expected columns 'Indicator' and 'SATIMGE' not found after mapping.")
proc_df["CO2eq"] = proc_df.apply(
    lambda r: r["SATIMGE"] * GWP.get(r["Indicator"], 0)
    if pd.notna(r["Indicator"])
    else np.nan,
    axis=1,
)

# ── Scenario metadata
print("🗂 adding scenario metadata")
if "Scenario" not in proc_df.columns:
    raise KeyError("Expected column 'Scenario' not found after mapping.")

proc_df["ScenarioFamily"] = proc_df["Scenario"].apply(map_scenario_family)
proc_df["ScenarioGroup"] = proc_df["ScenarioFamily"].apply(
    lambda s: "CPP" if isinstance(s, str) and s.startswith("CPP") else s
)

proc_df = extract_carbon_budget(proc_df)
proc_df["EconomicGrowth"] = proc_df["Scenario"].apply(map_economic_growth)

# ── Memory‑friendly dtype cleanup (avoid giant object consolidation)
# Use Arrow-backed dtypes where possible before saving
proc_df = proc_df.convert_dtypes(dtype_backend="pyarrow")

# ── Save
print(f"💾 writing CSV → {OUT_CSV}")
proc_df.to_csv(OUT_CSV, index=False)

print(f"💾 writing Parquet → {OUT_PARQUET}")
proc_df.to_parquet(OUT_PARQUET, index=False)

print("✅ dataset build complete")
