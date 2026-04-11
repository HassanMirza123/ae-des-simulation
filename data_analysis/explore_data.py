import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import os

#creating outputs folder
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

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

#charts
#using admission rate from per_visit analysis above
admission_rate = per_visit['is_admitted'].mean()
total_rates = hourly_rates/admission_rate

#chart a to show raw and mine follow same pattern
fig_a = go.Figure()

#line for what we will use in sim
fig_a.add_trace(go.Scatter(
    x=list(range(24)), y=list(total_rates),
    name='Estimated total A&E arrivals per hour',
    fill='tozeroy', mode='lines+markers', fillcolor='rgba(179,226,205,0.5)'))

#line for dataset values
fig_a.add_trace(go.Scatter(
    x=list(range(24)), y=list(hourly_rates),
    mode='lines+markers', line=dict(color='red', width=1.5, dash='dot'), marker=dict(size=5),
    name='Admitted patients per hour (raw data)'))

fig_a.update_layout(
    title='Empirical Hourly Arrival Rate - inpatient_arrivals.csv',
    xaxis_title='Hour of Day', yaxis_title='Mean Patients per Hour', xaxis=dict(tickmode='linear', tick0=0, dtick=2),
    legend=dict(orientation='h', yanchor='bottom', y=1.02,xanchor='right', x=1),
    height=420)

#chart b to show which specialties patients go - didn't end up using this in the simulation (improvement for future)
fig_b = go.Figure()

fig_b.add_trace(go.Bar(
    x=list(specialty_props.index), y=list(specialty_props.values*100),
    marker_color=['red','green','blue','yellow'],
    text=[f"{p*100:.1f}%" for p in specialty_props.values], textposition='outside'))

fig_b.update_layout(
    xaxis_title='Specialty', yaxis_title='Admitted Patients %',
    showlegend=False, height=400)

#chart c los distrubtion same in charts.py but for sim patients
fig_c = go.Figure()

fig_c.add_trace(go.Histogram(
    x=discharged[discharged<=600], #drops anyone over 600 mins to remove outliers. excluding them doesnt change distribution shape
    name='Discharged',
    marker_color='lightblue',
    opacity=0.7,
    xbins=dict(size=15)))

fig_c.add_trace(go.Histogram(
    x=admitted[admitted<=600], #drops anyone over 600 mins to remove outliers. excluding them doesnt change distribution shape
    name='Admitted',
    marker_color='red',
    opacity=0.7,
    xbins=dict(size=15)))

#4hour breach line(everything on right is breach)
fig_c.add_vline(
    x=240,
    line_dash='dash',
    line_color='black',
    annotation_text='4 hour target (240 min)',
    annotation_position='top right')

fig_c.update_layout(
    title='Length of Stay Distribution',
    barmode='overlay',
    xaxis_title='Time in A&E (minutes, capped at 600)',
    yaxis_title='Number of Visits',
    height=400,
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

path_a = os.path.join(OUTPUT_DIR, 'chart_a_hourly_arrival_rates.png')
pio.write_image(fig_a, path_a, width=900, height=450)
print(f"Saved: {path_a}")

path_b = os.path.join(OUTPUT_DIR,'chart_b_specialty.png')
pio.write_image(fig_b, path_b, width = 900, height=450)
print(f"Saved: {path_b}")

path_c = os.path.join(OUTPUT_DIR,'chart_c_los_dist.png')
pio.write_image(fig_c, path_c, width = 900, height=450)
print(f"Saved: {path_c}")
