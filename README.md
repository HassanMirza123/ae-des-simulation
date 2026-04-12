# A&E Discrete Event Simulation

This is a decision support tool that simulates patient flow through an Accident and Emergency department using Discrete Event Simulation (DES). It is built with Python, SimPy and Streamlit

This is a final year Computer Science project at City St George's University of London

---

## What It Does

- Simulates patient arrivals, triage, doctor treatment, and 
  admission/discharge decisions using a two-stage DES model
- Uses empirical hourly arrival rates derived from a real NHS dataset
- Runs 30 independent replications with 95% confidence intervals
- Provides an interactive Streamlit interface for staffing what-if scenarios
- Automatically interprets simulation results and identifies bottlenecks
- Compares predefined and custom staffing scenarios side by side

---

## Project Structure

ae-des-simulation/
├── Home.py                        # Entry point - run this to start the app
├── pages/
│   ├── 1_Simulation.py           # Interactive simulation page
│   ├── 2_Scenarios.py            # Scenario comparison page
│   └── 3_About.py                # Methodology and limitations
├── simulation/
│   ├── model.py                  # SimPy DES model and replications
│   └── charts.py                 # Plotly chart functions
├── data_analysis/
│   ├── explore_data.py           # Dataset analysis and parameter extraction
│   └── outputs/                  # Pre-generated analysis outputs
│       ├── chart_a_hourly_arrival_rates.png
│       ├── chart_b_specialty.png
│       ├── chart_c_los_dist.png
│       ├── chart_d_adm_rate_triage.png
│       ├── table1_hourly_rates.csv
│       ├── table2_triage_summary.csv
│       └── explore_data_output.txt
├── data/
│   ├── inpatient_arrivals.csv    # UCL-CORU dataset
│   └── ed_visits.csv             # UCL-CORU dataset
├── diagrams/
│   └── sim_model.png      # Patient flow diagram
├── requirements.txt

## Installation

These instructions assume you have Python 3.10 or later installed on your machine.
All commands should be typed into your terminal or Command Prompt

**Step 1 - Navigate to the project folder**

Unzip the submission and open a terminal inside the unzipped folder.
You should be in the same directory as `Home.py`

**Step 2 - Create a virtual environment**

```bash
python -m venv venv
```
**Step 3 - Activate the virtual environment**

Windows:
```bash
venv\Scripts\activate
```

Mac/Linux:
```bash
source venv/bin/activate
```

You will know it worked when you see `(venv)` at the start of your 
terminal line

**Step 4 - Install dependencies**

```bash
pip install -r requirements.txt
```

This installs all required packages including SimPy, Streamlit, 
Plotly, Pandas, NumPy, and SciPy

---

## Running the App

In the virtual environment, run:

```bash
streamlit run Home.py
```

You may be prompted to enter your email. Leave this blank and press the Enter button on your keyboard to get past this
Your browser will automatically open at `https://localhost:8501`
If it doesn't, open your browser and navigate to that address manually

If you close out of the browser page. Enter Ctrl + C in the terminal to interrupt


---

## Visibility Options

You are able to change between Light and Dark mode. (Dark mode is recommended)
To do this, navigate to the ellipsis/more options menu button in the top right (3 vertically stacked dots) and select Dark mode

---

#Running the Data Analysis (Optional)

With the virtual environment active, run:

```bash
python data_analysis/explore_data.py
```

This reads both CSV files from the `data/` folder and saves some outputs into `data_analysis/outputs/`

The zip file contains pre-generated outputs if you prefer not to run the script yourself