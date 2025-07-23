import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# === Layout Styling ===
def apply_common_layout(fig, title, y_title="Product Output (PJ)"):
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

# === Mapping functions ===
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
        '075': 7.5, '0775': 7.75, '08': 8, '8': 8, '0825': 8.25, '085': 8.5,
        '0875': 8.75, '09': 9, '0925': 9.25, '095': 9.5, '0975': 9.75,
        '10': 10, '1025': 10.25, '105': 10.5
    }
    df['number_str'] = df['Scenario'].str.extract(r'(\d{2,4})', expand=False)
    df['CarbonBudget'] = df['number_str'].map(carbonbudget_map).fillna("NoBudget")
    df.drop(columns=['number_str'], inplace=True)
    return df

# === Hex to RGBA utility ===
def hex_to_rgba(hex_color, alpha=0.2):
    hex_color = hex_color.lstrip('#')
    r, g, b = [int(hex_color[i:i + 2], 16) for i in (0, 2, 4)]
    return f'rgba({r},{g},{b},{alpha})'

# === Plot FT Output ===
def generate_total_FT_product_plot(df, output_dir):
    print("Generating Total FT Product Output from UCTLFT...")

    ft_products = ['GIM', 'ODS', 'OGS', 'OKE', 'OLP', 'PCHEM']

    filtered_df = df[
        (df['Process'] == 'UCTLFT') &
        (df['Commodity'].isin(ft_products))
    ]

    if filtered_df.empty:
        print("No FT product data found for UCTLFT.")
        return

    # Grouping
    df_grouped = (
        filtered_df
        .groupby(['ScenarioFamily', 'Scenario', 'Year'])['SATIMGE']
        .sum()
        .reset_index()
    )

    # Aggregate stats per ScenarioFamily
    df_stats = (
        df_grouped
        .groupby(['ScenarioFamily', 'Year'])['SATIMGE']
        .agg(['min', 'max', 'mean'])
        .reset_index()
    )

    # Plotting
    colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
    ]

    fig = go.Figure()

    for i, (family, subset) in enumerate(df_stats.groupby('ScenarioFamily')):
        color = colors[i % len(colors)]
        rgba_fill = hex_to_rgba(color, alpha=0.2)
        rgba_mean = hex_to_rgba(color, alpha=0.6)

        # Mean Line
        fig.add_trace(go.Scatter(
            x=subset['Year'],
            y=subset['mean'],
            mode='lines+markers',
            name=f"{family} Mean",
            line=dict(color=rgba_mean, width=2),
            marker=dict(size=4)
        ))

        # Min-Max Range
        fig.add_trace(go.Scatter(
            x=subset['Year'].tolist() + subset['Year'][::-1].tolist(),
            y=subset['max'].tolist() + subset['min'][::-1].tolist(),
            fill='toself',
            fillcolor=rgba_fill,
            line=dict(color='rgba(255,255,255,0)'),
            name=f"{family} Range",
            showlegend=False,
            hoverinfo='skip'
        ))

    fig = apply_common_layout(fig, "Total FT Product Output from UCTLFT by Scenario Family")
    os.makedirs(output_dir, exist_ok=True)
    fig.write_image(f"{output_dir}/fig_total_FT_output_transparent.jpeg", width=1500, height=1200, scale=3)
    df_stats.to_csv(f"{output_dir}/fig_total_FT_output_transparent.csv", index=False)
    print(f"Saved figure and CSV to {output_dir}")

# === MAIN RUN ===
if __name__ == "__main__":
    RAW_PATH = "C:/FinalNDC/REPORT_00.csv"
    SETSANDMAPS_PATH = "C:/Models/SATIMGE_Veda/SetsAndMaps/SetsAndMaps.xlsm"
    OUTPUT_DIR = "C:/FinalNDC/charts/resultsSecunda"
    PROCESSED_PATH = "C:/FinalNDC/processed_datasetSecunda.csv"

    usecols = ['Process', 'Commodity', 'Indicator', 'SATIMGE', 'Scenario', 'Year']
    chunks = []

    print("Reading CSV in chunks...")
    for chunk in pd.read_csv(RAW_PATH, usecols=usecols, chunksize=100000):
        chunks.append(chunk)
    df = pd.concat(chunks, ignore_index=True)

    print("Reading mapping files...")
    mapPRC_df = pd.read_excel(SETSANDMAPS_PATH, sheet_name="mapPRC")
    mapCOM_df = pd.read_excel(SETSANDMAPS_PATH, sheet_name="mapCOM")

    print("Applying mapping...")
    df = apply_mapping_and_clean(df, mapPRC_df, mapCOM_df)

    print("Adding metadata...")
    df['ScenarioFamily'] = df['Scenario'].apply(map_scenario_family)
    df['ScenarioGroup'] = df['ScenarioFamily'].apply(lambda s: 'CPP' if s.startswith('CPP') else s)
    df['EconomicGrowth'] = df['Scenario'].apply(map_economic_growth)
    df = extract_carbon_budget(df)

    os.makedirs("data/processed", exist_ok=True)
    df.to_csv(PROCESSED_PATH, index=False)

    generate_total_FT_product_plot(df, OUTPUT_DIR)
    print("✅ Done.")

