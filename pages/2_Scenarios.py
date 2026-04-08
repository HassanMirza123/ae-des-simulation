import streamlit as st
import os
import sys
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from scipy import stats

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'simulation'))
from model import run_multiple_replications

st.set_page_config(
    page_title="Scenarios - A&E DES", page_icon="🏥", layout="wide")

st.title("Scenario Comparison")
st.write("Run a few predefined staffing scenarios and compare the main results")

SCENARIOS = {
    "Baseline": {"n_nurses": 6, "n_doctors": 13},
    "Less Staff":{"n_nurses": 4, "n_doctors": 9},
    "More Capacity":{"n_nurses": 8, "n_doctors": 16}
}
N_REPS = 30

def mean_conf_int(values):
    #Calc the mean
    mean=np.mean(values)
    #calc 95% confidence interval on t-distribution
    conf_int=stats.t.interval(confidence=0.95, df=len(values)-1,
                              loc=mean, scale=stats.sem(values))
    return mean, conf_int[0], conf_int[1]

#func for the diff scenarios
def run_scenario(n_nurses,n_doctors,n_reps=N_REPS):
    rep_df, patients_df = run_multiple_replications(n_reps=n_reps,
                                       n_nurses=n_nurses,
                                       n_doctors=n_doctors)
    
    breach_mean, br_lo, br_hi = mean_conf_int(rep_df["breach_rate"] * 100)
    total_mean, to_mean_lo, to_mean_hi =mean_conf_int(rep_df["mean_total_time"])
    doc_mean, doc_lo, doc_hi= mean_conf_int(rep_df["doctor_util_mean"]* 100)
    nur_mean, nur_lo, nur_hi=mean_conf_int(rep_df["triage_util_mean"] * 100)

    return{
        "breach_mean":breach_mean, "breach_lo": br_lo, "breach_hi": br_hi,
        "total_mean":total_mean,"total_lo":to_mean_lo,"total_hi":to_mean_hi,
        "doctor_mean":doc_mean, "doctor_lo":doc_lo,"doctor_hi":doc_hi,
        "nurse_mean":nur_mean,"nurse_lo":nur_lo,"nurse_hi":nur_hi
    }
    
#The bar chart for comparison, eventaully move func into charts.py once working
def comparison_bar(results, metric, y):
    scenario_names= list(results.keys())
    values= [results[name][metric] for name in scenario_names]

    bar = go.Figure()
    bar.add_trace(go.Bar(x=scenario_names, y=values, textposition="outside"))
    bar.update_layout(yaxis_title=y,showlegend=False,height=400)
    return bar

if st.button("Run scenarios"):
    results = {}
    with st.spinner("Running scenarios... (Please allow some time)"):
        for name, params in SCENARIOS.items():
            results[name] = run_scenario(n_nurses=params["n_nurses"],
                                         n_doctors=params["n_doctors"])
    st.subheader("Results")

    #Summary metric table to clean up
    table = []
    for name, metrics in results.items():
        table.append({"Scenario": name,
                      "Breach Rate (%)": round(metrics["breach_mean"],1),
                      "Breach Confidence Interval Low": round(metrics["breach_lo"],1),
                      "Breach Confidence Interval High": round(metrics["breach_hi"],1),
                      "Mean Time in A&E (min)": round(metrics["total_mean"],1),
                      "Mean Time Confidence Interval Low": round(metrics["total_lo"],1),
                      "Mean Time Confidence Interval High": round(metrics["total_hi"],1),
                      "Doctor Utilisation (%)": round(metrics["doctor_mean"], 1),
                      "Nurse Utilisation (%)": round(metrics["nurse_mean"], 1)})
    results_df = pd.DataFrame(table)
    st.dataframe(results, use_container_width=True)

    st.subheader("Breach Rate Comparison")
    st.plotly_chart(comparison_bar(results,"breach_mean", "Breach Rate %"), use_container_width=True)