# %%
# generate_dataset.py

import pandas as pd
import numpy as np
from utils.mappings import (
    map_scenario_family,
    map_scenario_key,
    map_sector_group,
    extract_carbon_budget,
    map_economic_growth,
    apply_mapping_and_clean
)

# 1) Point to the actual CSV (with underscore)
RAW_PATH = "data/raw/REPORT_00.csv"

# 2) Where to write your processed dataset
OUT_PATH = "data/processed/processed_dataset.csv"

# 3) Your local Sets & Maps file in OneDrive
# path_setsandmaps = r"C:\Models\SATIMGE_Veda\SetsAndMaps\SetsAndMaps.xlsm"
path_setsandmaps = r"C:\Models\SATIMGE_charts\SetsAndMaps.xlsm"

print('reading in raw data file')
df = pd.read_csv(RAW_PATH)

# load setsandmaps mappings
print('read in setsandmaps')
mapPRC_df = pd.read_excel(path_setsandmaps, sheet_name="mapPRC")
mapCOM_df = pd.read_excel(path_setsandmaps, sheet_name="mapCOM")

print('applying setsandmaps')
proc_df = apply_mapping_and_clean(df, mapPRC_df, mapCOM_df)

# --- Create CO2eq from gases ---
print('applying GWPs')
GWP = {
    'CO2': 1,
    'CO2eq': 1,
    'CH4': 28,
    'N2O': 265,
    'CF4': 6630,
    'C2F6': 11100
}
proc_df['CO2eq'] = proc_df.apply(
    lambda row: row['SATIMGE'] * GWP.get(row['Indicator'], 0)
    if row['Indicator'] in GWP else np.nan,
    axis=1
)

# --- Add scenario metadata ---
print('applying custom maps and groupings')
proc_df['ScenarioFamily'] = proc_df['Scenario'].apply(map_scenario_family)
proc_df['ScenarioKey'] = proc_df['Scenario'].apply(map_scenario_key)
proc_df['ScenarioGroup'] = proc_df['ScenarioFamily'].apply(
    lambda s: 'CPP' if s.startswith('CPP') else s
)

proc_df = extract_carbon_budget(proc_df)
proc_df['EconomicGrowth'] = proc_df['Scenario'].apply(map_economic_growth)
# proc_df['SectorGroup'] = proc_df['Sector'].apply(map_sector_group)

# Convert object columns to categories (efficient for repeated labels)
for col in proc_df.select_dtypes(include="object"):
    proc_df[col] = proc_df[col].astype("category")

# Save outputs
proc_df.to_csv(OUT_PATH, index=False)
print(f"Processed dataset saved to {OUT_PATH}")

parquet_path = "data/processed/processed_dataset.parquet"
proc_df.to_parquet(parquet_path, index=False)
print(f"Also saved Parquet dataset to {parquet_path}")
