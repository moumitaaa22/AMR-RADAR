# AMR RADAR — Antimicrobial Resistance Monitoring and Analytics Platform

**Tagline:** Turning Laboratory Data into Meaningful Surveillance Insights.

AMR RADAR is an open-source healthcare analytics and surveillance platform built with Python, Streamlit, Pandas, Plotly, ReportLab, OpenPyXL, and Pytest. It supports individual laboratory susceptibility records (Format A) as well as aggregated surveillance statistics (Format B, such as ICMR summary tables).

> **Surveillance & Research Disclaimer:** AMR RADAR is designed strictly for retrospective laboratory surveillance and research analytics. It does **not** diagnose patients or recommend treatments.

---

## Folder Structure

```
AMR_RADAR/
├── app.py                     # Home landing page & Streamlit entry point
├── config.py                  # Palette, thresholds, and scientific constants
├── requirements.txt           # Python dependencies
├── README.md                  # Setup, testing, and hackathon demo guide
├── modules/
│   ├── data_loader.py         # CSV, XLSX, XLS, and optional Stata .dta ingestion
│   ├── data_processing.py     # Validation, column mapping, duplicate detection, Format A/B
│   ├── analytics.py           # Exact R/(S+I+R)*100 calculation, heatmap, trends
│   ├── visualizations.py      # Interactive Plotly charts & heatmap
│   ├── alerts.py              # Explainable surveillance alert system
│   ├── reports.py             # ReportLab PDF & OpenPyXL Excel exporters
│   └── session_state.py       # Shared Streamlit state and sidebar filters
├── pages/
│   ├── 01_Overview.py
│   ├── 02_Data_Upload.py
│   ├── 03_Organism_Analysis.py
│   ├── 04_Resistance_Analytics.py
│   ├── 05_Trends_Geography.py
│   ├── 06_Surveillance_Alerts.py
│   └── 07_Reports.py
├── data/
│   ├── sample_amr.csv         # Synthetic demonstration dataset (fictional)
│   ├── amr_template.csv       # Standard upload template
│   └── icmr_sample_aggregated.csv
├── tests/
│   ├── test_analytics.py
│   └── test_data_processing.py
└── assets/
    └── logo.png
```

---

## Step-by-Step Windows Installation & Launch (VS Code)

1. **Open the `AMR_RADAR` folder in VS Code** (`File -> Open Folder... -> select AMR_RADAR`).
2. **Open the VS Code Integrated Terminal** (`Ctrl + ~`).
3. **Create a Python virtual environment:**
   ```powershell
   python -m venv .venv
   ```
4. **Activate the virtual environment:**
   ```powershell
   .venv\Scripts\Activate.ps1
   ```
   *(If PowerShell blocks scripts, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use Command Prompt: `.venv\Scripts\activate.bat`.)*
5. **Install dependencies:**
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
6. **Run the automated Pytest suite:**
   ```powershell
   pytest -v
   ```
   Expected result: All tests in `tests/test_analytics.py` and `tests/test_data_processing.py` pass (`passed`).
7. **Launch the Streamlit web application:**
   ```powershell
   streamlit run app.py
   ```
   Expected result: VS Code terminal outputs `Local URL: http://localhost:8501` and opens AMR RADAR in your browser.

---

## Uploading an ICMR Sample Dataset

1. Navigate to **02 Data Upload** in the left sidebar.
2. Upload your `.csv`, `.xlsx`, `.xls`, or `.dta` file.
3. Choose **Format A** if your file has one row per isolate/test result (`Organism`, `Antibiotic`, `Result` = S/I/R), or **Format B** if your file contains published summary counts and percentages (`Organism`, `Antibiotic`, `Tested_Count`, `Resistant_Pct`).
4. Map your source columns using the dropdown selectors and click **Validate & Load Dataset**.

---

## Common Error Fixes (Windows)

- **`python` is not recognized:** Install Python 3.10+ from python.org and check **"Add Python to PATH"**.
- **`streamlit` is not recognized:** Ensure `.venv` is activated (`(.venv)` prefix visible in terminal) or run `python -m streamlit run app.py`.
- **`pyreadstat` / `.dta` import error:** Install via `pip install pyreadstat`.
- **`openpyxl` error on `.xlsx`:** Run `pip install openpyxl xlrd`.
