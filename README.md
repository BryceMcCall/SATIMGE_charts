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
│   │   └── REPORT\_00.csv
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
- Install required packages:  
```bash
  pip install -r requirements.txt
```

## 🛠 Installation & Setup

1. Clone this repository and `cd` into it.
2. Create or update your **`config.yaml`** to select which charts to run and output specs.
3. In `generate_dataset.py`, replace this directory with your local directory of `setsandmaps.xlsm`:

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
* Saves images & `data.csv` under `outputs/charts_and_data/<module_name>/`
* Copies images into `outputs/gallery/low_res` and `high_res`

### 3. Run an individual chart (for developers)

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

* **Per-chart** (`outputs/charts_and_data/<chart_name>/`):

  * `<chart_name>_dev.png` & `<chart_name>_report.png`
  * `data.csv` (the exact table used to plot)
* **Gallery** (`outputs/gallery/low_res`, `outputs/gallery/high_res`): image-only folders for quick browsing or inclusion in documents.

---

## 🙋 For Non-Coders

If you’re not familiar with Python:

1. **Clone this repository**
   Open your terminal or PowerShell and run:

   ```bash
   git clone https://github.com/BryceMcCall/SATIMGE_charts.git
   ```



2. **Navigate into the project folder**

   ```bash
   cd SATIMGE_charts
   ```

3. **Install Python 3.8+** (if you haven’t already) from [python.org](https://www.python.org/downloads/).

4. **Install dependencies**
   While still in the project folder, run:

   ```bash
   pip install -r requirements.txt
   ```

5. **Edit** `config.yaml` (optional)
   Use any text editor to open `config.yaml` and select which charts to run or adjust output sizes.

6. **Generate the processed dataset**

   ```bash
   python generate_dataset.py
   ```

7. **Generate all charts**

   ```bash
   python generate_charts.py
   ```

8. **Find your outputs**

   * **Per-chart folders:** `outputs/charts_and_data/<chart_name>/` (images + data.csv)
   * **Gallery:** `outputs/gallery/low_res/` and `outputs/gallery/high_res/` (image-only)


No Python coding required beyond these commands! Feel free to reach out (to ChatGPT, preferably o4-mini-high) if you hit any snags!
