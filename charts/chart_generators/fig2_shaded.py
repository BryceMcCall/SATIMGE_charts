# charts/results/fig2_shaded.py

import pandas as pd
import plotly.graph_objects as go
from charts.common.style import apply_common_layout
from charts.common.save import save_figures


def generate_fig2_shaded(df: pd.DataFrame, output_dir: str) -> None:
    """
    Generates Figure 2: Total CO₂ Emissions by Scenario Group with shaded uncertainty bands.
    """
    # Prepare data: sum to scenario-year level
    scenario_year_emissions = (
        df.groupby(['Scenario', 'ScenarioFamily', 'Year'])['CO2eq']
        .sum()
        .reset_index(name='CO2eq_Total')
    )
    # Exclude Low Carbon scenario family if needed
    scenario_year_emissions = scenario_year_emissions[~scenario_year_emissions['ScenarioFamily'].isin(['Low Carbon'])]
    # Group into broader ScenarioGroup
    scenario_year_emissions['ScenarioGroup'] = scenario_year_emissions['ScenarioFamily'].apply(
        lambda x: 'CPP' if x.startswith('CPP') else x
    )
    # Compute stats across scenarios
    group_stats = (
        scenario_year_emissions
        .groupby(['ScenarioGroup', 'Year'])['CO2eq_Total']
        .agg(['min', 'max', 'mean'])
        .reset_index()
        .rename(columns={'min': 'Emissions_min', 'max': 'Emissions_max', 'mean': 'Emissions_mean'})
    )

    # Define colors
    group_colors = {
        'CPP': 'rgba(255, 255, 0, 0.2)',
        'BASE': 'rgba(0, 0, 255, 0.2)',
        'High Carbon': 'rgba(255, 0, 0, 0.2)',
        'Low Carbon': 'rgba(0, 128, 0, 0.2)',
        'Other': 'rgba(128, 128, 128, 0.2)'
    }
    line_colors = {
        'CPP': 'Yellow',
        'BASE': 'Blue',
        'High Carbon': 'red',
        'Low Carbon': 'green',
        'Other': 'gray'
    }

    # Build figure
    fig = go.Figure()
    for group in group_stats['ScenarioGroup'].unique():
        data = group_stats[group_stats['ScenarioGroup'] == group]
        # Shaded band trace
        fig.add_trace(go.Scatter(
            x=pd.concat([data['Year'], data['Year'][::-1]]),
            y=pd.concat([data['Emissions_min'], data['Emissions_max'][::-1]]),
            fill='toself',
            fillcolor=group_colors.get(group, 'rgba(128,128,128,0.2)'),
            line=dict(color='rgba(255,255,255,0)'),
            name=f'{group} Range',
            showlegend=True
        ))
        # Mean line trace
        fig.add_trace(go.Scatter(
            x=data['Year'],
            y=data['Emissions_mean'],
            line=dict(color=line_colors.get(group, 'gray'), width=2),
            name=f'{group} Mean'
        ))

    # Apply common layout
    fig = apply_common_layout(fig, "Total CO₂ Emissions by Scenario Group (Shaded Bands)")
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="CO₂ Emissions (kt)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=60, r=30, t=60, b=60)
    )

    # Save figure and data
    save_figures(fig, output_dir, "fig2_shadedbands")
    group_stats.to_csv(f"{output_dir}/fig2_data.csv", index=False)
