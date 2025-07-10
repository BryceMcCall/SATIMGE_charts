# generate_dataset.py
import pandas as pd
import numpy as np
from utils.mappings import map_scenario_family, map_sector_group, extract_carbon_budget, map_economic_growth

RAW_PATH = "data/raw/REPORT_00.csv"
OUT_PATH = "data/processed/processed_dataset.csv"

df = pd.read_csv(RAW_PATH)

# --- Create CO2eq from gases ---
print('applying GWPs')
GWP =  {'CO2': 1,
    'CO2eq': 1,
    'CH4': 28,
    'N2O': 265,
    'CF4': 6630,
    'C2F6': 11100
}

df['CO2eq'] = df.apply(lambda row: row['SATIMGE'] * GWP.get(row['Indicator'], 0) if row['Indicator'] in GWP else np.nan, axis=1)

# --- Add scenario metadata ---
df['ScenarioFamily'] = df['Scenario'].apply(map_scenario_family)
df['ScenarioGroup'] = df['ScenarioFamily'].apply(lambda s: 'CPP' if s.startswith('CPP') else s)
df['CarbonBudget'] = df['Scenario'].apply(extract_carbon_budget)
df['EconomicGrowth'] = df['Scenario'].apply(map_economic_growth)
df['SectorGroup'] = df['Sector'].apply(map_sector_group)

df.to_csv(OUT_PATH, index=False)
print(f"Processed dataset saved to {OUT_PATH}")
