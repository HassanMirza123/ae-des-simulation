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
    
    #doctor moves onto next patient
    total_time = env.now - arrival_time
    
    #Storing current patients record
    results.append({
        'patient_id':     patient_id,
        'urgency':        urgency,
        'arrival_min':    round(arrival_time, 2),
        'triage_wait':    round(triage_wait, 2),
        'doctor_wait':    round(doctor_wait, 2),
        'total_min':      round(total_time, 2),
        'four_hr_breach': total_time > 240
    })

#Arrival Generator
"""
Keeps generating patients arriving at random times
For now I am using random.expovariate(1/20) to get
distribution between arrivals of 20 mins
So should be about 3 patients per hour arriving
*NEED TO CHANGE* to real hourly rates
"""
def patient_arrivals(env, triage_nurse, doctor, results):
    patient_id = 0
    while True:
        patient_id += 1
        env.process(patient(env, patient_id, triage_nurse, doctor, results))
        yield env.timeout(random.expovariate(1 / 20))


def run_simulation(n_nurses=2, n_doctors=2, sim_duration=480):
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
    
    env.process(patient_arrivals(env, triage_nurse, doctor, results))
    env.run(until=sim_duration)
    
    return pd.DataFrame(results)

#Summary 
df = run_simulation(n_nurses=2, n_doctors=2)

print("OVERALL")
print(f"Patients seen:       {len(df)}")
print(f"Mean triage wait:    {df['triage_wait'].mean():.1f} min")
print(f"Mean doctor wait:    {df['doctor_wait'].mean():.1f} min")
print(f"Mean total time:     {df['total_min'].mean():.1f} min")
print(f"4-hour breach rate:  {df['four_hr_breach'].mean()*100:.1f}%")

print("\nBY URGENCY")
print(df.groupby('urgency')[['triage_wait','doctor_wait','total_min']]
        .mean().round(1))