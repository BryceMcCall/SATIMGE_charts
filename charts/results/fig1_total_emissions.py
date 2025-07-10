# --- charts/results/fig1_total_emissions.py ---
import pandas as pd
import plotly.graph_objects as go
from charts.common.style import apply_common_layout
import os

def generate_fig1(df, output_dir):
    print('generating figure 1')
    data = df.groupby(['ScenarioFamily', 'Scenario', 'Year'])['CO2eq'].sum().reset_index()
    fig = go.Figure()

    for scenario in data['Scenario'].unique():
        subset = data[data['Scenario'] == scenario]
        fig.add_trace(go.Scatter(
            x=subset['Year'],
            y=subset['CO2eq'],
            mode='lines',
            line=dict(width=1, color='lightgray'),
            showlegend=False
        ))

    fig = apply_common_layout(fig, "Fig 1: Total Emissions by Scenario")
    print('saving figure 1')
    fig.write_image(f"{output_dir}/fig1_total_emissions_by_scenario.jpeg")
    data.to_csv(f"{output_dir}/fig1_data.csv", index=False)