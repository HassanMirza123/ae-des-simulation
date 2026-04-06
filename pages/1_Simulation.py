import streamlit as st
import sys
import os
import numpy as np
import plotly.graph_objects as go
from scipy import stats

#Path for simulation file
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'simulation'))
from model import run_multiple_replications
from charts import breach_rate_chart, utilisation_chart, patient_time_histogram



st.set_page_config(
    page_title="A&E Decision Support",layout="wide"
)

st.title("A&E Discrete Event Simulation")
st.markdown("Explores how changes to staffing levels affect patient wait times and performance targets.")

#Param sliders on the sidebar
st.sidebar.header("Change params")

st.sidebar.markdown("**Baseline:** 6 nurses, 13 doctors")

n_nurses = st.sidebar.slider(
    label="Number of Triage Nurses", min_value=1, max_value=15, value=6, step=1
)

n_doctors = st.sidebar.slider(
    label="Number of Doctors", min_value=1, max_value=25, value=13, step=1
)

n_reps = st.sidebar.slider(
    label="Replications (higher = more accurate, but slower)",min_value=5,max_value=30,value=10
)

run_button = st.sidebar.button("▶ Run Simulation", type="primary")

#Once buttons clicked, run reps and output metrics
if run_button:
    with st.spinner("Running the Sim"):
        rep_df,patients_df = run_multiple_replications(n_reps=n_reps, n_nurses=n_nurses, n_doctors=n_doctors)
    
    #Metrics
    st.subheader("Results")
    
    c1,c2,c3,c4 = st.columns(4)

    breach_mean =rep_df['breach_rate'].mean()*100
    total_mean =rep_df['mean_total_time'].mean()
    doc_util =rep_df['doctor_util_mean'].mean()*100
    adm_rate =rep_df['admission_rate'].mean()*100

    #Baseline results from 6 nurses, 13 docs, 30 reps
    BASELINE_BREACH_RATE = 17.4 #%
    BASELINE_TOTAL_TIME = 130.3 #min
    BASELINE_DOC_UTIL = 68.8 #%
    BASELINE_ADMISSION = 14.5 #%

    c1.metric(
        label="4 hour breach rate", value=f"{breach_mean:.1f}%", delta=f"{breach_mean - BASELINE_BREACH_RATE:.1f}% vs baseline",
        delta_color="inverse"
    )
    c2.metric(
        label="Mean time in A&E", value=f"{total_mean:.0f}min", delta=f"{total_mean - BASELINE_TOTAL_TIME:.0f} min vs baseline",
        delta_color="inverse"
    )
    c3.metric(
        label="Dcotor utilisation", value=f"{doc_util:.1f}%", delta=f"{doc_util - BASELINE_DOC_UTIL:.1f}% vs baseline",
        delta_color="inverse"
    )
    c4.metric(
        label="Admission rate", value=f"{adm_rate:.1f}%", delta=f"{adm_rate - BASELINE_ADMISSION:.1f}% vs baseline",
        delta_color="off"
    )

    st.subheader("4-Hour Breach Rate")
    st.plotly_chart(breach_rate_chart(rep_df, BASELINE_BREACH_RATE),use_container_width=True)

    st.subheader("Resource Utilisation")
    st.plotly_chart(utilisation_chart(rep_df), use_container_width=True)

    st.subheader("Patient Time Distribution")
    st.caption("Distribution of total time in A&E per patient across all reps. Everything to the right of red line is a 4 hour breach")
    st.plotly_chart(patient_time_histogram(patients_df), use_container_width=True)