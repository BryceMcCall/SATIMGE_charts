# --- utils/mappings.py ---

def apply_mapping_and_clean(df, mapPRC_df, mapCOM_df):
    """
    Cleans and merges the main report DataFrame with process and commodity mappings.

    Args:
        df (pd.DataFrame): Raw results with 'Process', 'Commodity', 'SATIMGE'.
        mapPRC_df (pd.DataFrame): Process mapping DataFrame (keyed by 'Process').
        mapCOM_df (pd.DataFrame): Commodity mapping DataFrame (keyed by 'Commodity').

    Returns:
        pd.DataFrame: Cleaned and merged DataFrame.
    """
    # Replace 'Eps' with 0 and convert to float
    df['SATIMGE'] = df['SATIMGE'].replace('Eps', 0).astype(float)

    # Merge mappings
    merged_df = df.merge(mapPRC_df, on='Process', how='left')
    merged_df = merged_df.merge(mapCOM_df, on='Commodity', how='left')

    # Reset index
    merged_df.reset_index(drop=True, inplace=True)

    return merged_df

def map_scenario_key(scenario):
    scenario = scenario.strip()

    # Handle CPP4 cases
    if scenario == "CPP4":
        return "CPP"
    elif "CPP4-" in scenario:   # dash after CPP4
        return "CPP"
    elif "CPP4" in scenario:    # any other CPP4 form
        return "CPP4 Variant"

    # Other mappings
    scenario_mapping = [
        ('CPP1', 'CPP-IRP'),
        ('CPP2', 'CPP-IRPLight'),
        ('CPP3', 'CPP-SAREM'),
        ('CPP4', 'CPPS'),
        ('HCARB', 'High Carbon'),
        ('LCARB', 'Low Carbon'),
        ('BASE', 'WEM')
    ]

    for key, value in scenario_mapping:
        if key in scenario:
            return value
    return 'Other'



def map_scenario_family(scenario):
    # Function to assign ScenarioFamily based on rules
    scenario_mapping = [
    ('CPP4', 'CPP4 Variant'),  # must come before exact 'CPP4' to catch variants like CPP4EK
    ('CPP4', 'CPP4'),          # exact match
    ('CPP1', 'CPP1'),
    ('CPP2', 'CPP2'),
    ('CPP3', 'CPP3'),
    ('HCARB', 'High Carbon'),
    ('LCARB', 'Low Carbon'),
    ('BASE', 'WEM')
    ]


    # First handle exact match for 'CPP4'
    if scenario.strip() == 'CPP4':
        return 'CPP4'
    for key, value in scenario_mapping:
        if key in scenario:
            return value
    return 'Other'

def map_sector_group(sector):
    
    if 'Industry' in sector or 'Process emissions' in sector:
        return 'Industry'
    elif 'Transport' in sector:
        return 'Transport'
    elif 'Refineries' in sector:
        return 'Refineries'
    elif 'Power' in sector:
        return 'Power'
    else:
        return 'All others'

def extract_carbon_budget(df):
    # carbon budget mapping using integers
    carbonbudget_map = {
    '075':7.5,
    '0775':7.75,    
    '08':8,
    '8':8,
    '0825':8.25,
    '085':8.5,
    '0875':8.75,
    '09':9,
    '0925':9.25,
    '095':9.5,
    '0975':9.75,
    '10':10,
    '1025':10.25,
    '105':10.5
    }
    df['number_str'] = df['Scenario'].str.extract(r'(\d{2,4})', expand=False)
    df['CarbonBudget'] = df['number_str'].map(carbonbudget_map).fillna("NoBudget")
    df.drop(columns=['number_str'], inplace=True) #remove this column
    
    return df





def map_economic_growth(scenario):
    
    if '-RG' in scenario:
        return 'Reference'
    elif '-LG' in scenario:
        return 'Low'
    elif '-HG' in scenario:
        return 'High'
    else:
        return 'Unknown'

