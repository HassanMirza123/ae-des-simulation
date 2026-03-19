import simpy
import random
import pandas as pd

random.seed(42)

#Setting priority
PRIORITY = {'urgent': 1, 'non_urgent': 2}

def patient(env, patient_id, doctor, results):
    
    arrival_time = env.now
    
    #30% patients seen as urgent
    is_urgent  = random.random() < 0.30
    urgency    = 'urgent' if is_urgent else 'non_urgent'
    priority   = PRIORITY[urgency]
    
    #REQUEST doctor resource. If doctor is free patient seen
    with doctor.request(priority=priority) as request:
        yield request   #Patient waits in queue here
        
        wait_time = env.now - arrival_time
        
        # Urgent patients take longer to treat
        treatment = 60 if is_urgent else 35
        yield env.timeout(treatment)
    
    #doctor moves onto next patient
    total_time = env.now - arrival_time
    
    #Storing current patients record
    results.append({
        'patient_id':     patient_id,
        'urgency':        urgency,
        'arrival_min':    round(arrival_time, 2),
        'wait_min':       round(wait_time, 2),
        'total_min':      round(total_time, 2),
        'four_hr_breach': total_time > 240
    })


def patient_arrivals(env, doctor, results):
    patient_id = 0
    while True:
        patient_id += 1
        env.process(patient(env, patient_id, doctor, results))
        yield env.timeout(random.expovariate(1 / 20))


def run_simulation(n_doctors=2, sim_duration=480):
    env     = simpy.Environment()
    # PriorityResource instead of Resource
    doctor  = simpy.PriorityResource(env, capacity=n_doctors)
    results = []
    
    env.process(patient_arrivals(env, doctor, results))
    env.run(until=sim_duration)
    
    return pd.DataFrame(results)


df = run_simulation(n_doctors=2)

print("OVERALL")
print(f"Patients:           {len(df)}")
print(f"Mean wait:          {df['wait_min'].mean():.1f} min")
print(f"4-hour breach rate: {df['four_hr_breach'].mean()*100:.1f}%")

print("\nBY URGENCY")
print(df.groupby('urgency')[['wait_min','total_min','four_hr_breach']]
        .mean().round(2))