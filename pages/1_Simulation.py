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

#This is to generate information based on the output of the simulation
def generate_info(breach_mean, doc_util, triage_util, total_mean, adm_rate, n_nurses, n_doctors):
    #So we get output values from the sim and this func will return English interpretation
    info = []

    #Breaches
    if breach_mean <=5:
        info.append(('success',
            f"The 4 hour breach rate is very low at {breach_mean:.1f}% "
            f"The department is easily meeting the NHS target. "
            f"Current staffing levels are sufficient for this demand level. Patients are unlikely to experience harmful delays. "
            f"If cost pressures exist, perhaps reducing staff slightly will be helpful while remaining with performance ranges. "
            f"Use the scenario comparison page to explore this"))
    elif breach_mean <=23:
        info.append(('success',
            f"The 4 hour breach rate is {breach_mean:.1f}%, this remains "
            f"consistent with the dataset baseline of 19.9% "
            f"Current performance is in an acceptable range with current staffing. "
            f"Around 1 in {round(100/breach_mean):.0f} patients will wait longer than 4 hours. This is likely to affect admitted atients awaiting ward transfer rather than discharged patients"))
    elif breach_mean <=35:
        info.append(('warning',
            f"The 4 hour breach rate is {breach_mean:.1f}% - approximately {round(breach_mean)} in every 100 patients are waiting beyond the NHS target. This "
            f"**exceeds** the dataset baseline of 19.9%. A large number of patients "
            f"are waiting longer which increases risk of harm, especially for older and vulnerable patients. Review the utilisation figures to see which resource is the primary driver."))
    else:
        info.append(('error',
            f"The 4 hour breach rate is {breach_mean:.1f}% More than {round(breach_mean)} in every 100 patients are waiting beyond the target "
            f"The department is under serious pressure. "
            f"Staffing must be reviewed. Use the scenario comparison page to model the impact of specific staffing increases before making changes."))

    #Doctor Utilisation
    if doc_util >= 90:
        info.append(('error',
            f"Doctor utilisation is critically high at {doc_util:.1f}%. "
            f"Staff are struggling with surges in demand, increasing waiting times for patients. The non-linear relationship between utilisation and waiting times means "
            f"even a small reduction in demand or small increase in capacity produces a large improvement in wait times at this point. "
            f"Try adding 1-2 doctors on the scenario comparison page to see the expected improvement. "))
    elif doc_util >= 85:
        info.append(('warning',
            f"Doctor utilisation is {doc_util:.1f}%, the threshold is 85%. "
            f"Peak hours (11am to 2pm) will push utilisation higher than the daily average shown here. Perhaps concentrate doctor capacity at these times - "
            f"a small increase in the number of doctors is recommended to help ease risk of breaches."))
    elif doc_util >= 70:
        info.append(('success',
            f"Doctor utilisation is {doc_util:.1f}%. Staff are busy while retaining capacity for any unexpected variation in demand. "
            f"This is a healthy operating range"))
    else:
        info.append(('success',
            f"Doctor utilisation is {doc_util:.1f}%. Staff have significant spare capacity.  If the breach rate is also low, current doctor staffing may be more than what is needed. "
            f"Use the scenario comparison page to check the effect of reducing doctors by 1-2 to see how to keep performance within the right range."))
    
    #Triage nurse utilisation
    if triage_util >= 85:
        info.append(('error',
            f"Triage nurse utilisation is {triage_util:.1f}%. There is a current bottleneck, "
            f"patients are waiting to be assessed before they can join the doctor queue. High risk patients may not be identified quickly enough. " 
            f"Increase the number triage nurses to reduce the overall breach rate more effectively than adding doctors at this point."))
    elif triage_util >= 60:
        info.append(('warning',
            f"Triage nurse utilisation is {triage_util:.1f}%. Nurses are under a little pressure. " 
            f"If arrival rates are peaking between 11am and 2pm, hourly triage utilisation during this time will be higher than this daily average. "
            f"it is recommended to closely monitor triage wait times during peak hours."))
    else:
        info.append(('success',
            f"Triage nurse utilisation is {triage_util:.1f}%. Triage capacity is comfortable at current staffing levels. "
            f"If breach rate is still high, the bottleneck is later in the pathway, perhaps in doctor capacity."))
        
    #Mean time in department (240 mins is our 4 hour breach)
    if total_mean > 240:
        info.append(('error',
            f"The mean time in A&E is {total_mean:.0f} minutes. This is exceeding the 4 hour target on average. This is showing overcrowding across the department rather than outlier long length of stay cases. "
            f"When the mean exceeds 240 mins, most patients experience the long waits at different stages of their pathway, not just one bottleneck"))
    elif total_mean > 180:
        info.append(('warning',
            f"The mean time in A&E is {total_mean:.0f} minutes. Eventhough the mean is below the 4 hour target, the spread of patient times show a large amount will breach the target. "
            f"Admitted patients are likely driving the breach rate. Perhaps something like increasing ward capacity would address this rather than adding staff"))
    else:
        info.append(('success',
            f"The mean time in A&E is {total_mean:.0f} minutes. Most patients are moving through the department efficiently and "
            f"most breaches will be isolated cases."))    
    
    #Bottleneck help
    if doc_util> triage_util + 20:
        info.append(('warning',
        f"Bottleneck: doctors ({doc_util:.1f}% utilisation) are under more pressure than triage nurses ({triage_util:.1f}%) "
        f"As of now, adding doctors will have a larger improvement in breach rate than adding nurses"))
    elif triage_util >doc_util + 20:
        info.append(('warning',
        f"Bottleneck: triage nurses ({triage_util:.1f}% utilisation) are under more pressure than doctors *{doc_util:.1f}%) "
        f"As of now, patients are waiting before they even reach the doctor queue, add triage nurses to see more impact than adding doctors."))

    return info



st.set_page_config(
    page_title="A&E Decision Support",layout="wide"
)

st.title("A&E Discrete Event Simulation")
st.markdown("Explores how changes to staffing levels affect patient wait times and performance targets.")

#Param sliders on the sidebar
st.sidebar.header("Change parameters")

st.sidebar.markdown("**Baseline:** 6 nurses, 12 doctors")

n_nurses = st.sidebar.slider(
    label="Number of Triage Nurses", min_value=1, max_value=15, value=6, step=1
)

n_doctors = st.sidebar.slider(
    label="Number of Doctors", min_value=1, max_value=25, value=12, step=1
)

n_reps = st.sidebar.slider(
    label="Replications (higher = more accurate, but slower)",min_value=5,max_value=30,value=30,
    help="30 replications is the recommended minimum for statistically valid confidence intervals (Central Limit Theorem). Lower values run fast but produce wider uncertainty ranges"
)

run_button = st.sidebar.button("▶ Run Simulation", type="primary")

#Once buttons clicked, run reps and output metrics
if run_button:
    with st.spinner("Running the Sim"):
        rep_df,patients_df = run_multiple_replications(n_reps=n_reps, n_nurses=n_nurses, n_doctors=n_doctors)
    
    #Saving to sesssion state so can be added as scenario in Scenario page
    #also create flag to see a run ahs occurs
    st.session_state['sim_nurses'] = n_nurses
    st.session_state['sim_doctors'] = n_doctors
    st.session_state['sim_run'] = True
    st.session_state['sim_rep_df']= rep_df
    st.session_state['sim_patients'] = patients_df
    
if st.session_state.get('sim_rep_df') is not None:
 
    rep_df      = st.session_state['sim_rep_df']
    patients_df = st.session_state['sim_patients']
 
    #Old Baseline - no warm up period
    # #Baseline results from 6 nurses, 13 docs, 30 reps
    # BASELINE_BREACH_RATE = 17.4 #%
    # BASELINE_TOTAL_TIME = 130.3 #min
    # BASELINE_DOC_UTIL = 68.8 #%
    # BASELINE_ADMISSION = 14.5 #%

    #Recalibrated baseline results from 6 nurses, 12 doctors, 30 reps, with warm up period
    BASELINE_BREACH_RATE = 21.6
    BASELINE_TOTAL_TIME  = 142.4
    BASELINE_DOC_UTIL    = 81.0
    BASELINE_ADMISSION   = 14.3
 
    breach_mean = rep_df['breach_rate'].mean() * 100
    total_mean  = rep_df['mean_total_time'].mean()
    doc_util    = rep_df['doctor_util_mean'].mean() * 100
    adm_rate    = rep_df['admission_rate'].mean() * 100
 
    #Metrics
    st.subheader("Results")
    c1, c2, c3, c4 = st.columns(4)
 
    c1.metric(
        label="4 hour breach rate",
        value=f"{breach_mean:.1f}%",
        delta=f"{breach_mean - BASELINE_BREACH_RATE:.1f}% vs baseline",
        delta_color="inverse"
    )
    c2.metric(
        label="Mean time in A&E",
        value=f"{total_mean:.0f}min",
        delta=f"{total_mean - BASELINE_TOTAL_TIME:.0f} min vs baseline",
        delta_color="inverse"
    )
    c3.metric(
        label="Doctor utilisation",
        value=f"{doc_util:.1f}%",
        delta=f"{doc_util - BASELINE_DOC_UTIL:.1f}% vs baseline",
        delta_color="inverse"
    )
    c4.metric(
        label="Admission rate",
        value=f"{adm_rate:.1f}%",
        delta=f"{adm_rate - BASELINE_ADMISSION:.1f}% vs baseline",
        delta_color="off"
    )

    #Charts
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("4-Hour Breach Rate")
        st.plotly_chart(breach_rate_chart(rep_df, BASELINE_BREACH_RATE),use_container_width=True)

    with col_right:
        st.subheader("Resource Utilisation")
        st.plotly_chart(utilisation_chart(rep_df),use_container_width=True)

    st.subheader("Patient Time Distribution")
    st.caption(
        "Distribution of total time in A&E per patient across all "
        "replications. Everything to the right of the red line is a "
        "4-hour breach."
    )
    st.plotly_chart(patient_time_histogram(patients_df),use_container_width=True
    )

    #Text info generation
    st.markdown("---")
    st.subheader("What do these results mean?")

    information = generate_info(
        breach_mean=breach_mean,
        doc_util=doc_util,
        triage_util=rep_df['triage_util_mean'].mean() * 100,
        total_mean=total_mean,
        adm_rate=adm_rate,
        n_nurses=n_nurses,
        n_doctors=n_doctors
    )
    for level, info in information:
        if level== 'success':
            st.success(info)
        elif level== 'warning':
            st.warning(info)
        elif level== 'error':
            st.error(info)