import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# === Style Function ===
def apply_common_layout(fig, title, y_title="CO₂eq (kt)"):
    fig.update_layout(
        title=title,
        template="simple_white",
        font=dict(family="Arial", size=15),
        margin=dict(l=60, r=100, t=60, b=60),
        xaxis=dict(tickmode='linear', title="Year", range=[2017, 2050]),
        yaxis=dict(title=y_title),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.01,
            font=dict(size=10),
            bgcolor='rgba(255,255,255,0.9)'
        )
    )
    return fig

# === Mapping Functions ===
def apply_mapping_and_clean(df, mapPRC_df, mapCOM_df):
    df['SATIMGE'] = df['SATIMGE'].replace('Eps', 0).astype(float)
    df = df.merge(mapPRC_df, on='Process', how='left')
    df = df.merge(mapCOM_df, on='Commodity', how='left')
    return df

def map_scenario_family(scenario):
    scenario_mapping = [
        ('CPP4', 'CPP4 Variant'), ('CPP4', 'CPP4'), ('CPP1', 'CPP1'),
        ('CPP2', 'CPP2'), ('CPP3', 'CPP3'), ('HCARB', 'High Carbon'),
        ('LCARB', 'Low Carbon'), ('BASE', 'BASE')
    ]
    if scenario.strip() == 'CPP4':
        return 'CPP4'
    for key, value in scenario_mapping:
        if key in scenario:
            return value
    return 'Other'

def map_economic_growth(scenario):
    if '-RG' in scenario:
        return 'Reference'
    elif '-LG' in scenario:
        return 'Low'
    elif '-HG' in scenario:
        return 'High'
    else:
        return 'Unknown'

def extract_carbon_budget(df):
    carbonbudget_map = {
        '075':7.5, '0775':7.75, '08':8, '8':8, '0825':8.25, '085':8.5,
        '0875':8.75, '09':9, '0925':9.25, '095':9.5, '0975':9.75,
        '10':10, '1025':10.25, '105':10.5
    }
    df['number_str'] = df['Scenario'].str.extract(r'(\d{2,4})', expand=False)
    df['CarbonBudget'] = df['number_str'].map(carbonbudget_map).fillna("NoBudget")
    df.drop(columns=['number_str'], inplace=True)
    return df

# === Plot FT Product Output ===
def generate_secunda_FT_product_plot(df, output_dir):
    print("Generating UCTLFT Product Output Figure...")

    # Only keep UCTLFT and FT products
    ft_products = ['GIM', 'ODS', 'OGS', 'OKE', 'OLP', 'PCHEM']
    filtered_df = df[
        (df['Process'] == 'UCTLFT') &
        (df['Commodity'].isin(ft_products))
    ]

    if filtered_df.empty:
        print("No UCTLFT product data found.")
        return

    # Group by scenario, product, and year
    df_grouped = filtered_df.groupby(['Scenario', 'Commodity', 'Year'])['SATIMGE'].sum().reset_index()

    # Color palette
    colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"
    ]

    fig = go.Figure()
    commodities = df_grouped['Commodity'].unique()

    for i, product in enumerate(commodities):
        subset = df_grouped[df_grouped['Commodity'] == product]
        df_pivot = subset.pivot(index='Year', columns='Scenario', values='SATIMGE')
        df_pivot['Mean'] = df_pivot.mean(axis=1)

        fig.add_trace(go.Scatter(
            x=df_pivot.index,
            y=df_pivot['Mean'],
            mode='lines+markers',
            name=product,
            line=dict(width=2, color=colors[i % len(colors)]),
            marker=dict(size=4)
        ))

    fig = apply_common_layout(fig, "UCTLFT Product Output (Mean across Scenarios)", y_title="Product Output (PJ)")

    os.makedirs(output_dir, exist_ok=True)
    fig.write_image(f"{output_dir}/fig_UCTLFT_product_output.jpeg", width=1500, height=1200, scale=3)
    df_grouped.to_csv(f"{output_dir}/fig_UCTLFT_product_output.csv", index=False)
    print(f"Saved: {output_dir}/fig_UCTLFT_product_output.jpeg")
    print(f"Saved: {output_dir}/fig_UCTLFT_product_output.csv")

# === Main Run ===
if __name__ == "__main__":
    RAW_PATH = "C:/FinalNDC/REPORT_00.csv"
    SETSANDMAPS_PATH = "C:/Models/SATIMGE_Veda/SetsAndMaps/SetsAndMaps.xlsm"
    OUTPUT_DIR = "C:/FinalNDC/charts/resultsSecunda"
    PROCESSED_PATH = "C:/FinalNDC/processed_datasetSecunda.csv"

    usecols = ['Process', 'Commodity', 'Indicator', 'SATIMGE', 'Scenario', 'Year']
    chunks = []

    print("Reading large REPORT00.csv in chunks...")
    for chunk in pd.read_csv(RAW_PATH, usecols=usecols, chunksize=100000):
        chunks.append(chunk)
    df = pd.concat(chunks, ignore_index=True)

    print("Reading SETSANDMAPS Excel...")
    mapPRC_df = pd.read_excel(SETSANDMAPS_PATH, sheet_name="mapPRC")
    mapCOM_df = pd.read_excel(SETSANDMAPS_PATH, sheet_name="mapCOM")

    print("Applying mapping...")
    df = apply_mapping_and_clean(df, mapPRC_df, mapCOM_df)

    print("Converting to CO₂eq...")
    GWP = {'CO2': 1, 'CO2eq': 1, 'CH4': 28, 'N2O': 265, 'CF4': 6630, 'C2F6': 11100}
    df['CO2eq'] = df.apply(
        lambda row: row['SATIMGE'] * GWP.get(row['Indicator'], 0)
        if row['Indicator'] in GWP else np.nan,
        axis=1
    )

    print("Adding scenario metadata...")
    df['ScenarioFamily'] = df['Scenario'].apply(map_scenario_family)
    df['ScenarioGroup'] = df['ScenarioFamily'].apply(lambda s: 'CPP' if s.startswith('CPP') else s)
    df['EconomicGrowth'] = df['Scenario'].apply(map_economic_growth)
    df = extract_carbon_budget(df)

    os.makedirs("data/processed", exist_ok=True)
    df.to_csv(PROCESSED_PATH, index=False)
    print(f"Processed data saved to {PROCESSED_PATH}")

    # Generate UCTLFT product figure
    generate_secunda_FT_product_plot(df, OUTPUT_DIR)
    print("All charts generated.")
