import simpy
import random
import pandas as pd

random.seed(42)

#Setting priority, so that urgent patietns always jump ahead of non urgent
PRIORITY = {'urgent': 1, 'non_urgent': 2}

#Starting service time in minutes (mean) - will change later
TRIAGE_MEAN = 10        #how long triage takes
TREATMENT_URGENT = 60   #doctor time to treat for urgent
TREATMENT_NON_UR = 35   #doctor time to treat for non urgent

#My actual hourly arrival rates from inpatient_arrivals
#Figures from explore_data.py
#They represent admitted patients per hour. Since about 12.6% of all A&E
#patients are admitted (from ed_visits.csv), we scale up to get
#the total A&E arrival rate for each hour.

#IMPORTANT:Need to mention this calc in the methods? chapter.
#This is how to connect my dataset to my sim

admit_hourly_rates = [
    0.792, 0.822, 0.666, 0.611, 0.742, 0.523,   #00:00–05:00
    0.627, 1.077, 1.471, 2.164, 2.668, 3.000,   #06:00–11:00
    3.129, 3.129, 2.962, 2.707, 2.605, 2.658,   #12:00–17:00
    2.422, 2.255, 2.211, 1.337, 1.112, 0.899    #18:00–23:00
]

admission_rate = 0.126  #figure from ed_visits 12.6% of patients admitted

# Scale admitted rates up to total A&E arrivals
total_hourly_rates = [r / admission_rate for r in admit_hourly_rates]

ADMISSION_PROB = {
    'urgent':       0.32, #~32% of urgent patients admitted
    'non_urgent':   0.06  #~6% of non-urgent patients admitted
}

#Mean time in A&E before ward transfer - taken form ed_visits
#Admitted patients to stay longer while waiting for a bed to become available
mean_los_admitted   =234.0 #minutes - taken from dataset
mean_los_discharged =158.0 #minutes - taken form dataset


def get_arrival_rate(sim_minute):
    """
    Returns the arrival rate (patients per minute) for a point in simulated time.
    
    sim_minute // 60 gives the hour now
    The % 24 wraps around so multi-day simulations work properly
    
    Convert from per hour to per minut as thats how simpy works
    """
    hour = int(sim_minute // 60) % 24
    rate_per_hour   = total_hourly_rates[hour]
    rate_per_minute = rate_per_hour / 60
    return rate_per_minute

#Process for patient
"""
Models a patient's complete journey through A&E

As of now there are 2 stages
    1.Traige: needs a triage nurse
    2.Treatment: doctor takes longer depending on urgency

Either patient will be seen immediately (resource free) or joins a queue
(resource busy) .request() handles this
"""
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
        
        # Urgent patients take longer to treat
        treatment_mean = (TREATMENT_URGENT if is_urgent
                          else TREATMENT_NON_UR)
        yield env.timeout(random.expovariate(1 / treatment_mean))

    #Stage 3: Admitted or Dishcarged?
    #Decide whether patient is admitted based on triage acuity
    #Probability comes from ed_visits analysis
    admission_prob = ADMISSION_PROB[urgency]
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

#Arrival Generator
"""
Keeps generating patients arriving at random times

"""
def patient_arrivals(env, triage_nurse, doctor, results, counters):
    patient_id = 0
    while True:
        patient_id += 1
        counters['arrivals'] += 1

        env.process(patient(env, patient_id, triage_nurse, doctor, results))
        
        #Gets arrival rate for THIS moment in simulated time
        rate_per_min = get_arrival_rate(env.now)
        
        #Inter-arrival time = exponential with mean = 1/rate
        #Rate is 0.1 patients/min, mean gap is 10 minutes
        inter_arrival = random.expovariate(rate_per_min)
        yield env.timeout(inter_arrival)


def run_simulation(n_nurses=2, n_doctors=2, sim_duration=1440):
    #1440 minutes means 24 hours - 1 full simulated day
    """
    Build and run sim
    Want to have it so user can change the params
    """
    env     = simpy.Environment()
    # PriorityResource instead of Resource
    #capacity is how many patients can be served simultaneously
    triage_nurse = simpy.PriorityResource(env, capacity=n_nurses)
    doctor       = simpy.PriorityResource(env, capacity=n_doctors)
    results = []
    counters = {'arrivals': 0}
    env.process(patient_arrivals(env, triage_nurse, doctor, results, counters))
    env.run(until=sim_duration)
    
    df = pd.DataFrame(results)
    print("Total arrivals:", counters['arrivals'])
    print("Total completed:", len(df))
    return df


#Summary 
df = run_simulation(n_nurses=6, n_doctors=11)

print("OVERALL")
print(f"Patients seen:       {len(df)}")
print(f"Admission rate:       {df['is_admitted'].mean()*100:.1f}%")
print(f"Mean triage wait:     {df['triage_wait'].mean():.1f} min")
print(f"Mean doctor wait:     {df['doctor_wait'].mean():.1f} min")
print(f"Mean total time:      {df['total_min'].mean():.1f} min")
print(f"4-hour breach rate:   {df['four_hr_breach'].mean()*100:.1f}%")

print("\nADMITTED vs DISCHARGED")
print(df.groupby('is_admitted')[['triage_wait','doctor_wait','total_min']]
        .mean().round(1))

print("\nBY URGENCY")
print(df.groupby('urgency')[['triage_wait','doctor_wait','total_min']]
        .mean().round(1))