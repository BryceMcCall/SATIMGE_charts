# fig_2030v2035NDC_emissions

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


def generate_fig_2030v2035NDC(df: pd.DataFrame, output_dir: str) -> None:
    print("generating 2030 vs 2035 NDC targets and emissions ")

    # GET DATA
    ###################
    year_select = [2030, 2035]

    cols = ["Scenario","ScenarioKey","EconomicGrowth","Year","CO2eq"]


    scenario_colors = {
        'CPP-IRP': "#d46820",  
        'CPP-IRPLight': "#e58d5a",
        'CPP-SAREM': "#1cdaf3",
        'CPPS': "#ff6e1a",
        'CPP': "#ff6e1a",
        'High Carbon': "#ff0000",
        'Low Carbon': "#008000",
        'WEM': "#1E1BD3"
    }



    df_compare = df[(df["Year"].isin(year_select))][cols]
    df_compare['CO2eq'] = df_compare['CO2eq']*0.001 #convert to Mt

    #drop the variants we dont want
    df_compare = df_compare[~df_compare["Scenario"].str.contains("CPP4EKH|CPP4EK|CPP4GE", regex=True)] # DROP these Variants.

    #reduce to just emissions sum
    data = (
            df_compare.groupby(["Scenario","ScenarioKey","EconomicGrowth","Year"])["CO2eq"]
            .sum()
            .reset_index()
        )

        
    x_data = data[data["Year"] == 2030]
    y_data = data[data["Year"] == 2035]

    merged = pd.merge(x_data, y_data, on=["Scenario", "ScenarioKey", "EconomicGrowth"], suffixes=('_2030', '_2035'))

    #CHART CODE
    #######################

    ndc2030_low = 350
    ndc2030_high = 420

    import plotly.express as px

    fig = px.scatter(
        data_frame=merged,
        x="CO2eq_2030",
        y="CO2eq_2035",
        color="ScenarioKey",
        symbol="EconomicGrowth",
        color_discrete_map=scenario_colors,
        labels={
            "CO2eq_2030": "CO₂eq Emissions in 2030 (Mt)",
            "CO2eq_2035": "CO₂eq Emissions in 2035 (Mt)",
            "ScenarioKey": "Scenario Key",
            "EconomicGrowth": "Economic Growth Rate"
        }
        #,title="Comparison of CO₂eq Emissions: 2030 vs 2035"
    )

    fig.update_xaxes(range=[280, 440])
    fig = apply_common_layout(fig)
    # Add vertical lines for 2030 NDC range
    fig.add_vline(
        x=ndc2030_low,
        #line_dash="dash",
        #line_color="green",
        annotation_text="2030 NDC Lower",
        annotation_position="top left",
        annotation=dict(
            textangle=-90  # ✅ Rotate text vertically
            
        )
    )

    fig.add_vline(
        x=ndc2030_high,
        annotation_text="2030 NDC Upper",
        annotation_position="top left",
        annotation=dict(
            textangle=-90  # ✅ Rotate text vertically
            
        )
    )
    #change the legend title
    fig.update_layout(
        legend_title_text='Scenario, Growth rate'
        
    )
    

    ### END OF CHART CODE
    
    

    print("saving generate_fig_2030v2035NDC")
    save_figures(fig, output_dir, name="fig_2030v2035NDC_emissions")
    data = merged.copy()
    if not dev_mode:
        data.to_csv(Path(output_dir) / "data.csv", index=False)


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    parquet_path = project_root / "data/processed/processed_dataset.parquet"
    # Only load necessary columns
    columns_needed = ["Scenario", "Year", "CO2eq"]
    # Read in chunks and filter as we go (if pyarrow is available)
    try:
        import pyarrow.parquet as pq
        
        year_select = list(range(2024, 2036))
        table = pq.read_table(
            parquet_path        
        )
        df = table.to_pandas()
        
    except ImportError:
        # Fallback to pandas, but still only load columns
        df = pd.read_parquet(parquet_path, columns=columns_needed)
        selected_scenarios = ["NDC_BASE-LG", "NDC_BASE-RG", "NDC_BASE-HG"]
        year_select = list(range(2024, 2036))
        df = df[(df["Scenario"].isin(selected_scenarios)) & (df["Year"].isin(year_select))]

    out = project_root / "outputs/charts_and_data/generate_fig_2030v2035NDC_emissions"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig_2030v2035NDC(df, str(out))
