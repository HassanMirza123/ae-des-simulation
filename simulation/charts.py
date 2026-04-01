import plotly.graph_objects as go
import numpy as np
from scipy import stats

def breach_rate_chart(rep_df, baseline_breach):
    #Bar chart showing mean breach rate with 95% confidence interval

    breach_values = rep_df['breach_rate'].values * 100
    breach_mean_val = np.mean(breach_values)
    ci = stats.t.interval(
        confidence=0.95, df=len(breach_values) - 1, loc=breach_mean_val, scale=stats.sem(breach_values)
    )

    #error bar size = distance from mean to upper CI bound
    error = ci[1] - breach_mean_val

    fig = go.Figure()

    #bar for current scenario
    fig.add_trace(go.Bar(
        x=["Current Scenario"],
        y=[breach_mean_val],
        error_y=dict(type='data', array=[error], visible=True),marker_color="red", name="Breach Rate", width=0.3
    ))

    #horizontal line to show baseline breach rate from sim
    fig.add_hline(
        y=baseline_breach, line_dash="dash", line_color="orange",
        annotation_text=f"Baseline: {baseline_breach}%",annotation_position="bottom right"
    )

    #horizontal line to show baseline breach ratefrom dataset
    fig.add_hline(
        y=19.9, line_dash="dot", line_color="green",
        annotation_text="Dataset target: 19.9%", annotation_position="top right"
    )

    fig.update_layout(
        yaxis_title="Breach Rate (%)",
        yaxis=dict(range=[0, max(breach_mean_val + error + 5, 40)]), showlegend=False, height=425
    )

    return fig


def utilisation_chart(rep_df):
    #Bar chart showing mean utilisation for nurses and doctors
    #Red dashed line at 85% pressure threshold

    triage_util = rep_df['triage_util_mean'].mean() * 100
    doctor_util = rep_df['doctor_util_mean'].mean() * 100

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=["Triage Nurses", "Doctors"],
        y=[triage_util, doctor_util],
        marker_color=['cyan', 'orange'],
        text=[f"{triage_util:.1f}%", f"{doctor_util:.1f}%"],
        textposition='outside',
        width=0.4
    ))

    fig.add_hline(
        #threshold line
        y=85, line_dash="dash",line_color="red",
        annotation_text="Pressure threshold (85%)",
        annotation_position="top right"
    )

    fig.update_layout(
        yaxis_title="Mean Utilisation (%)",
        yaxis=dict(range=[0, 110]), height=350,showlegend=False
    )

    return fig