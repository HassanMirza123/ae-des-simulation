import streamlit as st

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
