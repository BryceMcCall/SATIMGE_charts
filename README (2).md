# SATIMGE Charts Pipeline

A code-driven workflow to process SATIMGE model outputs and generate publication-quality charts in Python, replacing ad-hoc Tableau processes.  

## 📁 Project Structure

```

project\_root/
├── .gitignore
├── README.md
├── requirements.txt
├── config.yaml
├── generate\_dataset.py        # preprocess raw REPORT\_00.csv → CSV + Parquet
├── generate\_charts.py         # auto-discovers & runs all chart modules
├── data/
│   ├── raw/
│   │   └── REPORT\_00\_sample.zip
│   └── processed/
│       ├── processed\_dataset.csv
│       └── processed\_dataset.parquet
├── utils/
│   └── mappings.py            # Sets & Maps Excel → mappings functions
├── charts/
│   ├── common/
│   │   ├── **init**.py
│   │   ├── style.py           # shared Plotly styling
│   │   └── save.py            # image‐saving helper reading config.yaml
│   └── chart\_generators/      # one module per figure
│       ├── **init**.py
│       ├── fig1\_total\_emissions.py
│       └── fig2\_shaded.py
└── outputs/
├── charts\_and\_data/       # per-figure folders containing images & data.csv
└── gallery/
├── low\_res/           # all `_dev` images
└── high\_res/          # all report-quality images

```

## ⚙️ Prerequisites

- Python 3.8+ 
- Git (to clone repos)  
- OneDrive access for the SATIMGE_Veda sets & maps file  
- Install required packages:  
```bash
  pip install -r requirements.txt
```

## 🛠 Installation & Setup

1. **Clone the SATIMGE_charts repo**  
   ```bash
   git clone https://github.com/BryceMcCall/SATIMGE_charts.git
2. **Clone the main SATIMGE\_Veda repo** (contains `setsandmaps.xlsm`)

   ```bash
   git clone https://github.com/brunomerven/SATIMGE_Veda.git
   ```
3. **Change into the charts project folder**

   ```bash
   cd SATIMGE_charts
   ```
4. **After cloning, fetch the dataset zip**

   ```bash
   # inside the charts repo root
   ls data/raw/dataset.zip  # should already be there after git clone
   unzip data/raw/dataset.zip -d data/raw/
   ```
5. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```
6. Create or update your **`config.yaml`** to select which charts to run and output specs.
7. In `generate_dataset.py`, replace this directory with your local directory of `setsandmaps.xlsm`:

   ```
   C:\Users\<you>\OneDrive\Documents\GitHub\SATIMGE_Veda\setsandmaps\setsandmaps.xlsm
   ```
    ps. it's likely:
      ```
   C:\Models\SATIMGE_Veda\SetsAndMaps
   ```




## 🚀 Usage

### 1. Generate the processed dataset

```bash
python generate_dataset.py
```

This reads `data/raw/REPORT_00.csv`, applies mappings, writes:

* `data/processed/processed_dataset.csv`
* `data/processed/processed_dataset.parquet`

### 2. Generate all charts

```bash
python generate_charts.py
```

This:

* Auto-discovers every `charts/chart_generators/fig*_*.py` module
* Runs its `generate_<module_name>` function
* Saves high-res `*_report.png` and optionally `data.csv` to `outputs/charts_and_data/<module_name>/`
* Copies images to `outputs/gallery/` for quick access

### 3. Run an individual chart

```bash
python charts/chart_generators/fig1_total_emissions.py
```

Each module boots itself onto the correct import path and outputs to:

```
outputs/charts_and_data/fig1_total_emissions/
```

## 🔧 Configuration (`config.yaml`)

Non-coders can open `config.yaml` to:

* **Include** or **exclude** charts by name
* Set output **formats** (`png`, `svg`, etc.)
* Define **resolutions** (`dev`, `report`)

Example:

```yaml
charts:
  include:
    - total_emissions_by_scenario
    - emissions_uncertainty_bands

output:
  formats:
    - png
    - svg
  resolutions:
    dev:
      width: 800
      height: 600
    report:
      width: 1600
      height: 1200
```

## 📂 Outputs

* **Per-chart folders**: `outputs/charts_and_data/<chart_name>/`
  * Always: `<chart_name>_report.png` (high-res image)
  * If `dev_mode: false`: `data.csv` (the exact table used to plot)
* **Gallery folder**: `outputs/gallery/`
  * High-res `.png` images for quick reuse in reports and slides

---

## 🙋 For Non-Coders

If you’re not familiar with Python:

1. **Clone both repos**

   ```bash
   git clone https://github.com/BryceMcCall/SATIMGE_charts.git
   git clone https://github.com/brunomerven/SATIMGE_Veda.git
   ```
2. **Navigate into the project folder**

   ```bash
   cd SATIMGE_charts
   ```
3. **After cloning, fetch the dataset zip**

   ```bash
   # inside the repo root
   ls data/raw/dataset.zip  # should already be there after git clone
   unzip data/raw/dataset.zip -d data/raw/
   ```
4. **Install Python 3.8+** (if you haven’t already) from [python.org](https://www.python.org/downloads/).

5. **Install dependencies**
   While still in the project folder, run:

   ```bash
   pip install -r requirements.txt
   ```

6. **Edit** `config.yaml` (optional)
   Use any text editor to open `config.yaml` and select which charts to run or adjust output sizes.

7. **Generate the processed dataset**

   ```bash
   python generate_dataset.py
   ```

8. **Generate all charts**

   ```bash
   python generate_charts.py
   ```

9. **Find your outputs**

   * **Per-chart folders:** `outputs/charts_and_data/<chart_name>/` (images + data.csv)
   * **Gallery:** `outputs/gallery/low_res/` and `outputs/gallery/high_res/` (image-only)


No Python coding required beyond these commands! Feel free to reach out (to ChatGPT, preferably o4-mini-high) if you hit any snags!
