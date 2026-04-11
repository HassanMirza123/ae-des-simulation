import simpy
import random
import pandas as pd
import numpy as np
from scipy import stats


#Setting priority, so that urgent patietns always jump ahead of non urgent
PRIORITY = {'urgent': 1, 'non_urgent': 2}

#Starting service time in minutes (mean) - will change later
TRIAGE_MEAN = 10        #how long triage takes
TREATMENT_URGENT = 60   #doctor time to treat for urgent
TREATMENT_NON_UR = 35   #doctor time to treat for non urgent

#My actual hourly arrival rates from inpatient_arrivals
#Figures from explore_data.py
#I scale these up using overall admission rate to estimate total A&E arrivals by hour

#IMPORTANT:Need to mention this calc in the methods? chapter.
#This is how to connect my dataset to my sim

admit_hourly_rates = [
    0.792, 0.822, 0.666, 0.611, 0.742, 0.523,   #00:00–05:00
    0.627, 1.077, 1.471, 2.164, 2.668, 3.000,   #06:00–11:00
    3.129, 3.129, 2.962, 2.707, 2.605, 2.658,   #12:00–17:00
    2.422, 2.255, 2.211, 1.337, 1.112, 0.899    #18:00–23:00
]

admission_rate = 0.126  #figure from ed_visits 12.6% of patients admitted

#Estimated total A&E arrivals per hour
total_hourly_rates = [r / admission_rate for r in admit_hourly_rates]

ADMISSION_PROB = {
    'urgent':       0.32, #Given that a patient is urgent, ~32% will be admitted
    'non_urgent':   0.06  #Given that a patient is non urgent, ~6% will be admitted
}

#Mean time in A&E before ward transfer - taken form ed_visits
#Admitted patients to stay longer while waiting for a bed to become available
mean_los_admitted   =234.0 #minutes - taken from dataset
mean_los_discharged =158.0 #minutes - taken form dataset


def get_arrival_rate(sim_minute):
    #Find current hour in sim and return the matching arrival rate in patients per minute
    hour = int(sim_minute // 60) % 24
    rate_per_hour   = total_hourly_rates[hour]
    rate_per_minute = rate_per_hour / 60
    return rate_per_minute

#Models a patient's complete journey through A&E
def patient(env, patient_id, triage_nurse, doctor, results):
    
    arrival_time = env.now
    
    #30% patients seen as urgent - for now assigning at arrival
    is_urgent  = random.random() < 0.30
    urgency    = 'urgent' if is_urgent else 'non_urgent'
    priority   = PRIORITY[urgency]

    #Stage 1: Triage
    #Patient joins triage queue. If a nurse is free
    #they go straight in, otherwise wait.
    #'with' will free a nurse once triage is done
    with triage_nurse.request(priority=priority) as triage_req:
        yield triage_req #wait until nurse free

        triage_wait = env.now - arrival_time #how long waited

        yield env.timeout(random.expovariate(1 / TRIAGE_MEAN))
    
    #Nurse released here at end of 'with' block
    #patient will join doctor queue
    post_triage_time = env.now #timestap of triage finished

    #Stage 2: Doctor Treatment
    #REQUEST doctor resource. If doctor is free patient seen
    with doctor.request(priority=priority) as doctor_req:
        yield doctor_req   #Patient waits in queue here
        
        doctor_wait = env.now - post_triage_time
        
        treatment_mean = (TREATMENT_URGENT if is_urgent
                          else TREATMENT_NON_UR)
        yield env.timeout(random.expovariate(1 / treatment_mean))

    #Stage 3: Admitted or Dishcarged?
    #Decide whether patient is admitted based on triage acuity
    #Probability comes from ed_visits analysis
    admission_prob = ADMISSION_PROB[urgency] #picks 0.32 or 0.06
    is_admitted    = random.random() < admission_prob
    
    if is_admitted:
        #Admitted patients wait for ward bed after treatment
        #Extra wait is why admitted patients have higher los
        #Delaye represents bed request -> porter -> transfer
        bed_wait_mean = 45 #minutes - ward transfer wait
        yield env.timeout(random.expovariate(1/bed_wait_mean))

    #doctor moves onto next patient
    total_time = env.now - arrival_time

    results.append({
        'patient_id':     patient_id,
        'urgency':        urgency,
        'is_admitted':    is_admitted,
        'arrival_min':    round(arrival_time, 2),
        'triage_wait':    round(triage_wait, 2),
        'doctor_wait':    round(doctor_wait, 2),
        'total_min':      round(total_time, 2),
        'four_hr_breach': total_time > 240
    })


def monitor_resources(env, triage_nurse, doctor, triage_util, doctor_util, interval=30):
#including average staff utilisation from each replication, essentially checking how busy each nurse/doctor is during run
    while True:
        #.count = number of resource units currently in use
        #.capacity = total available units
        triage_util.append({
            'time':         env.now,
            'utilisation':  triage_nurse.count / triage_nurse.capacity
        })
        doctor_util.append({
            'time':         env.now,
            'utilisation':  doctor.count / doctor.capacity
        })
        yield env.timeout(interval)

#Arrival Generator
def patient_arrivals(env, triage_nurse, doctor, results):
    patient_id = 0
    while True:
        patient_id += 1
        env.process(patient(env, patient_id, triage_nurse, doctor, results))
        
        #Sample next gap between arrivals using the rate for current simulated hour
        rate_per_min = get_arrival_rate(env.now)
        
        inter_arrival = random.expovariate(rate_per_min)
        yield env.timeout(inter_arrival)

# def run_simulation(n_nurses=2, n_doctors=2, sim_duration=1440):
#     #1440 minutes means 24 hours - 1 full simulated day
#     env     = simpy.Environment()
#     #PriorityResource instead of Resource
#     #capacity is how many patients can be served simultaneously
#     triage_nurse = simpy.PriorityResource(env, capacity=n_nurses)
#     doctor       = simpy.PriorityResource(env, capacity=n_doctors)
#     results = []
#     env.process(patient_arrivals(env, triage_nurse, doctor, results))
#     env.run(until=sim_duration)
    
#     return pd.DataFrame(results)

#Baseline staffing for the simulation
#These values were chosen by calibrating the model against the main summary results from ed_visits.csv.

#The main targets used here were:
# - breach rate = 19.9%
# - admission rate = 12.6%

#In the current version, n_nurses=6 and n_doctors=13 produced results that were reasonably close to those targets across
#30 replications, so this is being used as the baseline scenario.

#Data source: UCL-CORU patientflow dataset on Zenodo

def run_multiple_replications(n_reps=30, n_nurses=6, n_doctors=11,
                               sim_duration=1440):
    #Run model several times with diff seeds so the results not based on single random run
    replication_summaries = []
    all_patients = [] #collecting every patient

    for seed in range(n_reps):
        random.seed(seed)

        env          = simpy.Environment()
        triage_nurse = simpy.PriorityResource(env, capacity=n_nurses)
        doctor       = simpy.PriorityResource(env, capacity=n_doctors)
        results      = []
        #Storing utilisation snapshots
        triage_util = []
        doctor_util = []

        env.process(patient_arrivals(env, triage_nurse, doctor, results))

        #Launch monitor as parallel process alongside arrivals
        env.process(monitor_resources(env, triage_nurse, doctor, triage_util, doctor_util, interval=30
        ))

        env.run(until=sim_duration)

        df = pd.DataFrame(results)

        #Ignore runs if almost nobody completed (means the queue overloaded)
        if len(df) < 10:
            continue

        df['replication'] = seed
        all_patients.append(df)

        #Convert utilisation snapshots into Df
        triage_util_df = pd.DataFrame(triage_util)
        doctor_util_df = pd.DataFrame(doctor_util)

        replication_summaries.append({
            'seed':              seed,
            'n_completed':       len(df),
            'admission_rate':    df['is_admitted'].mean(),
            'mean_triage_wait':  df['triage_wait'].mean(),
            'mean_doctor_wait':  df['doctor_wait'].mean(),
            'mean_total_time':   df['total_min'].mean(),
            'breach_rate':       df['four_hr_breach'].mean(),
            'triage_util_mean':  triage_util_df['utilisation'].mean(),
            'doctor_util_mean':  doctor_util_df['utilisation'].mean(),
        })

    rep_df = pd.DataFrame(replication_summaries)
    patients_df = pd.concat(all_patients, ignore_index=True)

    return rep_df,patients_df


def summarise_replications(rep_df):
    #Print mean results and 95% confidence intervals
    metrics = ['breach_rate', 'mean_total_time',
               'mean_doctor_wait', 'mean_triage_wait',
               'admission_rate', 'triage_util_mean',
               'doctor_util_mean']

    print("RESULTS ACROSS 30 REPLICATIONS")
    print(f"{'Metric':<22} {'Mean':>8} {'95% CI Lower':>14} {'95% CI Upper':>14}")

    for metric in metrics:
        values = rep_df[metric].values
        mean   = np.mean(values)
        #scipy.stats.t.interval gives a 95% confidence interval
        #using the t distribution (best for small samples)
        ci     = stats.t.interval(
                     confidence=0.95,
                     df=len(values) - 1,   # degrees of freedom
                     loc=mean,
                     scale=stats.sem(values)  # standard error of mean
                 )
        print(f"{metric:<22} {mean:>8.3f} {ci[0]:>14.3f} {ci[1]:>14.3f}")

    print(f"\nReplications completed: {len(rep_df)}/30")
    print(f"Mean patients per run:  {rep_df['n_completed'].mean():.0f}")

if __name__ == "__main__":
    BASELINE_NURSES = 6
    BASELINE_DOCTORS = 13
    #Run everything
    rep_df, patients_df = run_multiple_replications(n_reps=30, n_nurses=BASELINE_NURSES, n_doctors=BASELINE_DOCTORS)
    summarise_replications(rep_df)