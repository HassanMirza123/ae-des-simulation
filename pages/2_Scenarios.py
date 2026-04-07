import streamlit as st
import os
import sys

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

#func for the diff scenarios
def run_scenario(n_nurses,n_doctors,n_reps=N_REPS):
    rep_df, patients_df = run_multiple_replications(n_reps=n_reps,
                                       n_nurses=n_nurses,
                                       n_doctors=n_doctors)
    return {
        "breach_rate": rep_df["breach_rate"].mean() * 100,
        "mean_total_time": rep_df["mean_total_time"].mean(),
        "doctor_util": rep_df["doctor_util_mean"].mean() * 100,
        "nurse_util": rep_df["triage_util_mean"].mean() * 100
    }

if st.button("Run scenarios"):
    results = {}
    with st.spinner("Running scenarios... (Please allow some time)"):
        for name, params in SCENARIOS.items():
            results[name] = run_scenario(n_nurses=params["n_nurses"],
                                         n_doctors=params["n_doctors"])
    st.subheader("Results")

    for name, metrics in results.items():
        st.markdown(f"{name}")
        st.write(f"Breach rate: {metrics['breach_rate']:.1f}%")
        st.write(f"Mean time in A&E: {metrics['mean_total_time']:.1f} min")
        st.write(f"Doctor utilisation: {metrics['doctor_util']:.1f}%")
        st.write(f"Nurse utilisation: {metrics['nurse_util']:.1f}%")