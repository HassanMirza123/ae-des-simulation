import pandas as pd
import numpy as np
import plotly.graph_objects as go

#Loading datasets
arrivals = pd.read_csv('data/inpatient_arrivals.csv')
arrivals['arrival_datetime'] = pd.to_datetime(
    arrivals['arrival_datetime'], utc=True
)

ed = pd.read_csv('data/ed_visits.csv')
#New column for LOS in mins
ed['los_minutes'] = ed['elapsed_los'] / 60

#Getting Hourly arrival rates
arrivals['hour'] = arrivals['arrival_datetime'].dt.hour
arrivals['date'] = arrivals['arrival_datetime'].dt.date
n_days = arrivals['date'].nunique()

#Getting the rates
hourly_rates = arrivals.groupby('hour').size() / n_days
print("Hourly admitted arrival rates (patients per hour)")
print(hourly_rates.round(3).to_string())

#Routing through diff specialties (Medicine,)
specialty_props = arrivals['specialty'].value_counts(normalize=True)
print("\nSpecialty Routing Probabilities")
print(specialty_props.round(3).to_string())

#Grouping by visit id to get one row per visit los
per_visit = ed.groupby('visit_number').agg(
    max_los = ('los_minutes', 'max'),
    is_admitted = ('is_admitted', 'last'),
    triage = ('latest_obs_manchester_triage_acuity', 'last')
).reset_index()

admitted = per_visit[per_visit['is_admitted'] == True]['max_los']
discharged = per_visit[per_visit['is_admitted'] == False]['max_los']

print("\n===LOS Summary===")
print(f"Admission rate:          {per_visit['is_admitted'].mean()*100:.1f}%")
print(f"Mean LOS admitted:       {admitted.mean():.1f} min")
print(f"Mean LOS discharged:     {discharged.mean():.1f} min")
print(f"4-hour breach rate:      {(per_visit['max_los']>240).mean()*100:.1f}%")

#Triage breakdown
print("\n Triague Acuity")
for colour in ['Red','Orange','Yellow','Green','Blue']:
    subset = per_visit[per_visit['triage'] == colour]
    print(f"    {colour:8s}: {len(subset):6d} patients | "
          f"admitted {subset['is_admitted'].mean()*100:4.1f}% | "
          f"mean LOS {subset['max_los'].mean():.0f} min")

print("\nSimulation Parameters Summary")
print(f"\nADMISSION_RATE = {per_visit['is_admitted'].mean():.3f}")
print(f"MEAN_LOS_ADMITTED = {admitted.mean():.1f}")
print(f"MEAN_LOS_DISCHARGED = {discharged.mean():.1f}")
print(f"BASELINE_BREACH_RATE = {(per_visit['max_los']>240).mean():.3f}")
rates_list = [round(hourly_rates.get(h, 0), 3) for h in range(24)]
print(f"\nADMITTED_HOURLY_RATES = {rates_list}")