# SATIMGE_charts

Inital proposed structure (from chatgpt)

FOLDER STRUCTURE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

energy_model_reporting/
│
├── data/
│   ├── raw/                      # Original CSV exports from the model
│   └── processed/               # Cleaned and transformed data (with CO2eq, labels, mappings)
│
├── charts/
│   ├── common/                  # Shared styling functions, themes
│   ├── methodology/            # Charts used in the methodology report
│   └── results/                # Charts used in the results report
│
├── tables/
│   ├── methodology/            # Tables for the methodology report
│   └── results/                # Tables for the results report
│
├── utils/
│   └── mappings.py             # Sector groupings, carbon budget logic, etc.
│
├── generate_dataset.py         # Master script to generate the processed dataset
├── generate_charts.py          # Runs both sets of figures
├── requirements.txt
└── README.md


~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Detailed info on files:


1. generate_dataset.py
Transforms raw model results to a common format used for all figures:

    Compute CO2eq from gases

    Add ScenarioFamily, ScenarioGroup, EconomicGrowth, CarbonBudget, etc.

    Save as processed_dataset.csv


2. charts/common/style.py
Shared styling and layout code:
    apply_common_layout(fig, title)

    Color palettes

    Fonts and margins

 Use this across both reports for consistency.


3. charts/methodology/
Charts specific to explaining the model, e.g.:

Figure	Chart Description
M1	Total CO2eq vs Time for Base Scenarios (Reference Growth)
M2	Comparison of emission scope: combustion vs process
M3	Carbon budget levels by scenario family
M4	Chart showing sector groupings and their mapping

Save:

JPEGs to /charts/methodology/

CSVs to /tables/methodology/


4. charts/results/
Charts specific to model outcomes, e.g.:

Figure	Chart Description
R1	Total emissions by scenario
R2	ScenarioGroup shaded bands
R3	Sectoral emissions comparison (2024 vs 2035)
R4	2035 emissions by scenario and sector (stacked bar)
R5	BASE scenarios (Reference growth) over time
R6	Carbon budget sensitivity chart
R7	MAC curves if applicable
R8	Electricity sector detail for key scenarios


5. generate_charts.py
Script that:

Loads processed_dataset.csv

Calls functions like generate_methodology_charts(df) and generate_results_charts(df)

Optionally regenerates all figures with flags: