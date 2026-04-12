import streamlit as st

st.set_page_config(
    page_title="About - A&E DES", page_icon="🏥", layout="wide"
)

st.title("About this tool")
st.markdown("---")

st.subheader("Understanding The Results")

st.markdown("### 4-Hour Breach Rate")
st.markdown("""The 4 hour breach rate is the percentage of patients who waiting longer than 4 hours from arrival to either discharge/admission to a ward.
            An independent review led by Lord Ara Darzi found that the rate had fallen from 94% compliance in 2010, to around 60% in 2024. Meaning 34% of patients now wait longer than 4 hours. 
            The metric displayed in the simulation is the percentage of people seen after 4 hours, whereas the metric Darzi uses is the number of people seen before 4 hours. Hence, a lower 
            number on our metric shows a better breach rate, if the simulation shows above 20%, the department is under significant pressure
            """)

st.markdown("### Doctor and Nurse Utilisation")
st.markdown("""
Utilisation measures what percentage of time each resource is actively busy with a patient.
            
1. **Below 70%** - staff have comfortable capacity, there is room to uphold unexpected surges without significant impact on waiting times

2. **70-85%** - staff are productively busy. The system is running efficiently but starting to feel some pressure at peak hours

3. **Above 85%** - the system is under significant pressure, very little capcity exists to absorb unexpected surges. A busier than average hour can cause waits to spike rapidly

4. **Above 90%** - staff are critically overloaded. Long waits are certain and the breach rate will be high

Having high doctor utilisaiton with low nurse utilisation (or vise verse) shows a bottleneck
""")

st.markdown("### Mean Time in A&E")
st.markdown("""
The average total time a patient spends in the department from arrival to departure. This includes waiting for triage, the triage assessment itself, 
waiting for a doctor, treatment, and for admitted patients, waiting for a 
ward bed.
 
Admitted patients consistently have longer times than discharged patients because of the additional wait for a ward bed after the treatment decision 
is made. This is seen in the patient time distribution chart on the Simulation page
""")

st.markdown("### Admission Rate")
st.markdown("""
The percentage of patients who are admitted to a ward rather than discharged home. In this simulation, urgent patients have a 32% chance of admission and 
non-urgent patients have a 6% chance, derived from the dataset.
 
A higher admission rate puts more pressure on the department because admitted patients occupy resources for longer while waiting for ward beds
""")

st.subheader("What This Tool Cannot Tell You")

st.warning("""
This tool is a proof-of-concept prototype. Please ensure you understand this before acting on any results
""")

st.markdown("""
- Results show relative comparison, not precise predictions** If the simulation shows that adding 2 doctors reduces the breach rate by 10%, the direction of that change is meaningful.
The numbers will differ for your hospital
- This model doesn't account for ward bed shortages** In reality, a shortage of inpatient beds is one of the reasons for A&E crowding, this tool models a fixed bed wait delay but does not simulate ward capacity constraints
- Staffing levels are constant across 24 hours** Real departments may run reduced staffing overnight and incraese during peak hours. This simulation represents an average-day rather than specific shift configurations
- This is not a substitute for clinical judgement** It is designed to support exploratory thinking about the relationship between staffing and performance
""")

st.info(
    "This tool is a proof-of-concept prototype developed as a final-year "
    "Computer Science project at City St George's, University of London. "
    "It is not intended for real clinical decision-making.",
    icon="ℹ️"
)
