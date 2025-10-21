# make a chart for emissions of 2030 (and 2030 NDC target ranges) vs 2035 emissions results


import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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


def generate_2030NDC_v_2035NDC(df: pd.DataFrame, output_dir: str) -> None:
    print("generating 2030 vs 2035 NDC ranges")

    #all scenarios
    #coloured by scenario family
    #shape by economic growth rate

    #only data for 2030, and 2035

    year_select = [2030, 2035]

    cols = ["Scenario","ScenarioGroup","EconomicGrowth","Year","CO2eq"]

    scenario_colors = {
        'CPP-IRP': "#d46820",  
        'CPP-IRPLight': "#e58e5a",
        'CPP-SAREM': "#1cdaf3",
        'CPPS': "#ff6e1a",
        'CPP': "#ff6e1a",
        'High Carbon': "#ff0000",
        'Low Carbon': "#008000",
        'WEM': "#1E1BD3"
    }



    df_compare = df[(df["Year"].isin(year_select))][cols]
    df_compare['CO2eq'] = df_compare['CO2eq']*0.001 #convert to Mt


    #reduce to just emissions sum
    data = (
            df_compare.groupby(["Scenario","ScenarioGroup","EconomicGrowth","Year"])["CO2eq"]
            .sum()
            .reset_index()
            )

    
    x_data = data[data["Year"] == 2030]
    y_data = data[data["Year"] == 2035]


    ndc2030_low = 350
    ndc2030_high = 420

    import plotly.express as px

    fig = px.scatter(
        data_frame=pd.merge(x_data, y_data, on=["Scenario", "ScenarioGroup", "EconomicGrowth"], suffixes=('_2030', '_2035')),
        x="CO2eq_2030",
        y="CO2eq_2035",
        color="ScenarioGroup",
        symbol="EconomicGrowth",
        color_discrete_map=scenario_colors,
        labels={
            "CO2eq_2030": "CO₂eq Emissions in 2030 (Mt)",
            "CO2eq_2035": "CO₂eq Emissions in 2035 (Mt)",
            "ScenarioGroup": "Scenario Group",
            "EconomicGrowth": "Economic Growth Rate"
        }
        #,title="Comparison of CO₂eq Emissions: 2030 vs 2035"
    )

    # Add vertical lines for 2030 NDC range
    fig.add_vline(
        x=ndc2030_low,
        #line_dash="dash",
        #line_color="green",
        annotation_text="2030 NDC Lower",
        annotation_position="top left"
    )

    fig.add_vline(
        x=ndc2030_high,
        #line_dash="dash",
        #line_color="red",
        annotation_text="2030 NDC Upper",
        annotation_position="top right"
    )

    print("saving 2030 vs 2035 NDC ranges")
    save_figures(fig, output_dir, name="fig_2030NDC_v_2035NDC")

    if not dev_mode:
        data.to_csv(Path(output_dir) / "fig_data.csv", index=False)


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    df = pd.read_parquet(project_root / "data/processed/processed_dataset.parquet")
    out = project_root / "outputs/charts_and_data/2030NDC_v_2035NDC"
    out.mkdir(parents=True, exist_ok=True)
    generate_2030NDC_v_2035NDC(df, str(out))


