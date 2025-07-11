

# %%
# generate_dataset.py
import pandas as pd
import numpy as np
from utils.mappings import map_scenario_family, map_sector_group, extract_carbon_budget, map_economic_growth, apply_mapping_and_clean


RAW_PATH = "data/raw/REPORT00.csv"
OUT_PATH = "data/processed/processed_dataset.csv"
path_setsandmaps = 'C:/Models/SATIMGE_veda/setsandmaps/setsandmaps.xlsm' # your local copy of setsandmaps


print('reading in raw data file')
df = pd.read_csv(RAW_PATH) #read in the raw report00 file.

#load setsandmaps mappings
print('read in setsandmaps')
mapPRC_df = pd.read_excel(path_setsandmaps, sheet_name="mapPRC")
mapCOM_df = pd.read_excel(path_setsandmaps, sheet_name="mapCOM")

print('applying setsandmaps')
proc_df = apply_mapping_and_clean(df, mapPRC_df, mapCOM_df) # create 'processed df' which will have all the mappings etc. applied. 


# --- Create CO2eq from gases ---
print('applying GWPs')
GWP =  {'CO2': 1,
    'CO2eq': 1,
    'CH4': 28,
    'N2O': 265,
    'CF4': 6630,
    'C2F6': 11100
}

proc_df['CO2eq'] = proc_df.apply(lambda row: row['SATIMGE'] * GWP.get(row['Indicator'], 0) if row['Indicator'] in GWP else np.nan, axis=1)

# --- Add scenario metadata ---
print('applying custom maps and groupings')

proc_df['ScenarioFamily'] = proc_df['Scenario'].apply(map_scenario_family)
proc_df['ScenarioGroup'] = proc_df['ScenarioFamily'].apply(lambda s: 'CPP' if s.startswith('CPP') else s)

proc_df = extract_carbon_budget(proc_df) # add the carbon budgets

proc_df['EconomicGrowth'] = proc_df['Scenario'].apply(map_economic_growth)
#proc_df['SectorGroup'] = proc_df['Sector'].apply(map_sector_group)


proc_df.to_csv(OUT_PATH, index=False)
print(f"Processed dataset saved to {OUT_PATH}")
