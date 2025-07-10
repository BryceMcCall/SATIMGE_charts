# --- utils/mappings.py ---
def map_scenario_family(scenario):
    print('applying scenario family mapping')
    if 'CPP4' in scenario and len(scenario) > 5:
        return 'CPP4 Variant'
    for key in ['BASE', 'CPP1', 'CPP2', 'CPP3', 'CPP4', 'HCARB', 'LCARB']:
        if key in scenario:
            return key
    return 'Other'

def map_sector_group(sector):
    print('applying sector mapping')
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

def extract_carbon_budget(scenario):
    print('applying carbon budget mapping')
    if '0875' in scenario:
        return 8.75
    elif '09' in scenario or '9' in scenario:
        return 9.0
    else:
        return None

def map_economic_growth(scenario):
    print('applying economic growth mapping')
    if '-RG' in scenario:
        return 'Reference'
    elif '-LG' in scenario:
        return 'Low'
    elif '-HG' in scenario:
        return 'High'
    else:
        return 'Unknown'

