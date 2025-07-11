# --- generate_charts.py ---
import pandas as pd
import os
from charts.results.fig1_total_emissions import generate_fig1
from charts.results.fig2 import generate_fi2_shaded


OUTPUT_DIR = "charts/results"
DATA_PATH = "data/processed/processed_dataset.csv"

df = pd.read_csv(DATA_PATH)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Generate all result charts
generate_fig1(df, OUTPUT_DIR)
print("Figures generated in:", OUTPUT_DIR)

generate_fi2_shaded(df,OUTPUT_DIR)
print("Figures generated in:", OUTPUT_DIR)


