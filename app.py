import streamlit as st

#Old app.py changed into pages/1_Simulation.py
#Current app.py is acting as home page now
st.set_page_config(
    page_title="A&E Decision Support Tool", layout="wide"
)

st.title("A&E Discrete Event Simulation")
st.markdown("---")

st.markdown("""
### What is this tool?
            
This simulates patient flow through an Accident & Emergency (A&E) department using **Discrete Event Simulation (DES)**. You can explore how changes to staffing levels affect patient waiting times and NHS performance targets"
            
This simulation is built in Python using SimPy and is based on data modelled on a real UK hospital (UCLH) 

            """)

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### The Problem
    
    A&E departments across the UK have been under large amounts of pressure. This is backed by an investigation led by Lord Ara Darzi
    which found that the percentage of patients seen with the NHS 4 hour target dropped from XXX% to YYY% (Forgot how much check again)
    Meaning there is harm to the patients with staff being overworked
    
    Simulation models have been used in emergency departments before, but research shows that only around 
    14% of projects led to implemented operational changes (Syed Mohiuddin et al., 2017). A key reason is that models are not designed 
    with decision makers in mind and lack clear interpretation of outputs.
    """)

with col2:
    st.markdown("""
    ### This tool addresses that gap by providing:
    
    - A calibrated simulation of A&E patient flow
    - Interactive staffing scenario exploration
    - Automated interpretation of simulation results
    - Side by side comparison of staffing scenarios
    
    The model is calibrated against a real dataset so that baseline outputs 
    match observed NHS performance metrics, making scenario comparisons 
    useful in evidence
    """)

st.markdown("---")

st.markdown("""
### How to Use This Tool

Use the **sidebar** to navigate between pages:

- **Simulation** — adjust staffing levels and run the simulation to see results
- **Scenario Comparison** — compare predefined staffing scenarios side by side
- **About** — methodology, data sources, assumptions and limitations

👈 Select a page from the sidebar to begin.
""")

st.info(
    "This tool is a proof-of-concept prototype developed as a final-year "
    "Computer Science project at City St George's, University of London. "
    "It is not intended for real clinical decision-making.",
    icon="ℹ️"
)
