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
    adm_mean,_,_=mean_conf_int(rep_df['admission_rate']*100)

    return{
        "breach_mean":breach_mean, "breach_lo": br_lo, "breach_hi": br_hi,
        "total_mean":total_mean,"total_lo":to_mean_lo,"total_hi":to_mean_hi,
        "doctor_mean":doc_mean, "doctor_lo":doc_lo,"doctor_hi":doc_hi,
        "nurse_mean":nur_mean,"nurse_lo":nur_lo,"nurse_hi":nur_hi,
        'adm_mean':adm_mean
    }
    
#The bar chart for comparison, eventaully move func into charts.py once working
def comparison_bar(results, metric, y, reference_line=None, reference_label=None):
    scenario_names= list(results.keys())
    values= [results[name][metric] for name in scenario_names]

    bar = go.Figure()
    bar.add_trace(go.Bar(x=scenario_names, y=values,textposition="outside", width=0.5))
    if reference_line is not None:
        bar.add_hline(y=reference_line,line_dash="dash", line_color="red", annotation_text= reference_label, annotation_position="top right")
    bar.update_layout(yaxis_title=y,showlegend=False,height=400)
    return bar

if st.button("Run scenarios"):
    results = {}
    with st.spinner("Running scenarios... (Please allow some time)"):
        for name, params in SCENARIOS.items():
            results[name] = run_scenario(n_nurses=params["n_nurses"],
                                         n_doctors=params["n_doctors"])
            
    #saving results to current session state so can be used across pages
    st.session_state['predefined_results'] = results
#Display results
if st.session_state.get('predefined_results'):
    results= st.session_state['predefined_results']
    st.subheader("Results")

    #Summary metric table to clean up
    table = []
    for name, metrics in results.items():
        table.append({"Scenario": name,
                      "Breach Rate (%)": round(metrics["breach_mean"],1),
                      "Breach CI Low": round(metrics["breach_lo"],1),
                      "Breach CI High": round(metrics["breach_hi"],1),
                      "Mean Time in A&E (min)": round(metrics["total_mean"],1),
                      "Time CI Low": round(metrics["total_lo"],1),
                      "Time CI High": round(metrics["total_hi"],1),
                      "Doctor Utilisation (%)": round(metrics["doctor_mean"], 1),
                      "Nurse Utilisation (%)": round(metrics["nurse_mean"], 1),
                      "Admission Rate (%)": round(metrics['adm_mean'],1)})
                    
    results_df = pd.DataFrame(table).set_index("Scenario")
    st.dataframe(results_df, use_container_width=True)

    #The comparison bar charts
    st.subheader("Visual Comparison")

    st.markdown("**4-Hour Breach Rate (%)**")
    st.plotly_chart(
        comparison_bar(results, "breach_mean", "Breach Rate (%)",
                        reference_line=19.9, reference_label="Dataset target: 19.9%"),use_container_width=True
    )

#Users scenario - TODO make it so a user can add their own scenario to the existing chart. their own version is saved in session_state
#so like if sim was already run with diff params to baseline, get the results of whatever metric you are looking at and add that to the visuals
#if there was no run with diff params, tell user to run before you add custom scenario
#so theres the flag in 1_simulation.py to check if a sim is run, we use that, if run then go ahead and add the saved nurses and doctors
st.markdown("---")
st.subheader("Add your own scneario")
