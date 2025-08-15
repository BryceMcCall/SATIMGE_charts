#SHADED families chart


import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.graph_objects as go
from charts.common.style import apply_common_layout, color_for, color_sequence
from charts.common.save import save_figures

import yaml
project_root = Path(__file__).resolve().parents[2]
config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path) as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    dev_mode = False


def generate_fig2_shaded(df: pd.DataFrame, output_dir: str) -> None:
    print("generating figure 2")

    scenario_year_emissions = (
        df.groupby(['Scenario', 'ScenarioFamily', 'Year'])['CO2eq']
        .sum()
        .reset_index(name='CO2eq_Total')
    )

    scenario_year_emissions = scenario_year_emissions[
        ~scenario_year_emissions['ScenarioFamily'].isin(['Low Carbon'])
    ]

    scenario_year_emissions['ScenarioGroup'] = (
        scenario_year_emissions['ScenarioFamily']
        .apply(lambda x: 'CPP' if x.startswith('CPP') else x)
    )

    data = (
        scenario_year_emissions
        .groupby(['ScenarioGroup', 'Year'])['CO2eq_Total']
        .agg(['min', 'max', 'mean'])
        .reset_index()
        .rename(columns={'min': 'Emissions_min', 'max': 'Emissions_max', 'mean': 'Emissions_mean'})
    )

    group_colors = {
        'CPP': 'rgba(255, 255, 0, 0.2)',
        'BASE': 'rgba(0, 0, 255, 0.2)',
        'High Carbon': 'rgba(255, 0, 0, 0.2)',
        'Low Carbon': 'rgba(0, 128, 0, 0.2)',
        'Other': 'rgba(128, 128, 128, 0.2)'
    }
    line_colors = {
        'CPP': 'Orange',
        'BASE': 'Blue',
        'High Carbon': 'red',
        'Low Carbon': 'green',
        'Other': 'gray'
    }

    fig = go.Figure()
    for group in data['ScenarioGroup'].unique():
        d = data[data['ScenarioGroup'] == group]
        fig.add_trace(go.Scatter(
            x=pd.concat([d['Year'], d['Year'][::-1]]),
            y=pd.concat([d['Emissions_min'], d['Emissions_max'][::-1]]),
            fill='toself',
            fillcolor=group_colors.get(group, 'rgba(128,128,128,0.2)'),
            line=dict(color='rgba(255,255,255,0)'),
            name=f'{group} Range',
            showlegend=True
        ))
        fig.add_trace(go.Scatter(
            x=d['Year'],
            y=d['Emissions_mean'],
            line=dict(color=line_colors.get(group, 'gray'), width=2),
            name=f'{group} Mean'
        ))

    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",
        xaxis_title="Year",
        yaxis_title="CO₂ Emissions (kt)"
    )

    print("saving figure 2")
    save_figures(fig, output_dir, name="fig2_shaded")

    if not dev_mode:
        data.to_csv(Path(output_dir) / "fig2_data.csv", index=False)


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    df = pd.read_parquet(project_root / "data/processed/processed_dataset.parquet")
    out = project_root / "outputs/charts_and_data/fig2_shaded"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig2_shaded(df, str(out))


