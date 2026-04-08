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
    #making it so it reads as two charts, then two charts underneath rather than 4 in one line
    #maybe I keep this for any other visuals 
    st.subheader("Visual Comparison")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**4-Hour Breach Rate %**")
        st.plotly_chart(
            comparison_bar(results, "breach_mean", "Breach Rate %",
                           reference_line=19.9, reference_label="Dataset target: 19.9%"),use_container_width=True
        )
    with col2:
        st.markdown("**Mean Time in A&E mins**")
        st.plotly_chart(
            comparison_bar(results, "total_mean", "Mean Time min",
                           reference_line=240, reference_label="4-hour target: 240 min"), use_container_width=True
        )
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**Doctor Utilisation %**")
        st.plotly_chart(
            comparison_bar(results, "doctor_mean", "Doctor Utilisation %",
                           reference_line=85, reference_label="Pressure threshold: 85%"), use_container_width=True
        )
    with col4:
        st.markdown("**Nurse Utilisation %**")
        st.plotly_chart(
            comparison_bar(results, "nurse_mean", "Nurse Utilisation %",
                           reference_line=85,reference_label="Pressure threshold: 85%"), use_container_width=True
        )
#Users scenario
#for now it works as finding saved settings, using saved settings and rerunning chart to add users scenraio
#logic seems like its working? Check fully tomorrow
st.markdown("---")
st.subheader("Add your own scneario")

if st.session_state.get('sim_run'):
    saved_nurses = st.session_state['sim_nurses']
    saved_doctors = st.session_state['sim_doctors']

    st.success(
        f"Simulation page settings found: {saved_nurses} nurses, {saved_doctors} doctors."
    )
    saved = st.button(
        f"Add Simulation Page Scenario ({saved_nurses}N / {saved_doctors}D)", type="primary"
    )
    if saved:
        if not st.session_state.get('predefined_results'):
            st.warning("Please run the predefined scenarios first before adding a custom scenario")
        else:
            with st.spinner("Running your scenario..."):
                user_result = run_scenario(n_nurses=saved_nurses, n_doctors=saved_doctors)
                user_label = f"Your scenario ({saved_nurses}N&{saved_doctors}D)"
                #user result getst merged into existing predefined one
                all_results  = dict(st.session_state['predefined_results'])
                all_results[user_label] = user_result
                st.session_state['predefined_results'] = all_results
                #wlil rerun the charts to add the users scenario to it
                st.rerun()

else:
    #No changes run on the sim page
    st.info(
        "No custom configuration found. Visit the Simulation page first, adjust the sliders to your desired staffing level, and click Run then come back here to add it to the comparison"
    )
    #takes back to sim page
    if st.button("Go to Simulation page"):
        st.switch_page("pages/1_Simulation.py")
