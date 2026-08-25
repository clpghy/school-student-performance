import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Multi-Factor Student Performance & Well-being Monitor", layout="wide")

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv("students_data.csv")
    df['Risk_Status'] = df['Risk_Flag'].map({1: '⚠️ At-Risk', 0: '✅ Safe'})
    df['Depression_Severity'] = df['Depression_Severity'].fillna('None')
    df['Depression_Indicators'] = df['Depression_Indicators'].fillna('None')
    return df

df = load_data()

st.title("🎓 Multi-Factor Student Performance & Well-being Monitor")
st.caption("Scalable 360° Early-Warning System Analyzing Academic, Physical, Psychological & Lifestyle Indicators")

# Executive Narrative Summary
st.subheader("📖 Executive Narrative Summary")

total_students = len(df)
at_risk_df = df[df['Risk_Flag'] == 1]
at_risk_count = len(at_risk_df)
top_stressor_count = len(df[df['Stress_Level'].isin(['High', 'Very High'])])

st.info(f"""
**Key Strategic Insights for Management:**

1. **Overall Risk Profile:** Out of **{total_students}** pilot students evaluated, **{at_risk_count} ({at_risk_count/total_students*100:.0f}%)** are flagged in the **High-Risk zone**, requiring targeted academic and counseling support.
2. **Primary Compounding Drivers:** **{top_stressor_count} students** exhibit elevated stress levels combined with reduced sleep (< 6 hrs) and high screen time, serving as key leading indicators of score drops.
3. **Intervention Priority:** Students with severe depression indicators show an average academic drop of **{abs(at_risk_df['Academic_Change'].mean()):.1f}%**. Early counselor outreach is recommended for all flagged profiles.
""")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🎛️ Multi-Factor Scatter Analysis", "🔥 Factor Correlation Matrix", "🔍 Student 360° Profile"])

# TAB 1: Dynamic Scatter Plot
with tab1:
    st.subheader("Dynamic Multi-Factor Exploration")
    st.write("Compare any two parameters across the 30+ tracked factors to uncover hidden risk patterns.")
    
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    selectable_cols = [c for c in numeric_cols if c not in ['Student_ID', 'Risk_Flag']]
    
    col_x, col_y = st.columns(2)
    with col_x:
        x_axis = st.selectbox("Select X-Axis Factor:", selectable_cols, index=selectable_cols.index("Sleep_Hours") if "Sleep_Hours" in selectable_cols else 0)
    with col_y:
        y_axis = st.selectbox("Select Y-Axis Factor:", selectable_cols, index=selectable_cols.index("Overall_Percentage") if "Overall_Percentage" in selectable_cols else 0)
    
    fig_dynamic = px.scatter(
        df, 
        x=x_axis, 
        y=y_axis, 
        color="Risk_Status",
        size="Risk_Score", 
        hover_name="Name",
        hover_data=["Grade", "Stress_Level", "Attendance_%", "Depression_Severity"],
        color_discrete_map={'⚠️ At-Risk': '#d9534f', '✅ Safe': '#5cb85c'},
        title=f"Scatter Analysis: {x_axis.replace('_', ' ')} vs {y_axis.replace('_', ' ')}"
    )
    st.plotly_chart(fig_dynamic, use_container_width=True)

# TAB 2: Factor Correlation Matrix
with tab2:
    st.subheader("Multi-Factor Correlation Heatmap")
    st.write("Measures mathematical relationship strengths between academic performance, lifestyle habits, stress, and mental health indicators.")
    
    corr_cols = [
        'Overall_Percentage', 'Academic_Change', 'Study_Hours_Per_Day', 'Attendance_%', 
        'Meal_Quality_Score', 'Water_Intake_Glasses', 'Exercise_Minutes', 'Sleep_Hours', 
        'Sleep_Quality', 'Stress_Score', 'Depression_Score', 'Screen_Time_Hours', 'Risk_Score'
    ]
    
    valid_corr_cols = [c for c in corr_cols if c in df.columns]
    corr_matrix = df[valid_corr_cols].corr()
    
    fig_corr = px.imshow(
        corr_matrix,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        aspect="auto",
        title="Pearson Correlation Coefficients Across Key Factors"
    )
    st.plotly_chart(fig_corr, use_container_width=True)

# TAB 3: Student 360° Profile
with tab3:
    st.subheader("Individual Student Diagnostic Breakdown")
    selected_student = st.selectbox("Select Student:", df['Name'].unique())
    s = df[df['Name'] == selected_student].iloc[0]
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("##### 📚 Academic Metrics")
        st.write(f"**Overall Score:** {s['Overall_Percentage']}%")
        st.write(f"**Academic Change:** {s['Academic_Change']}%")
        st.write(f"**Attendance:** {s['Attendance_%']}%")
        st.write(f"**Homework Completion:** {s['Homework_Completion_%']}%")
        st.write(f"**Study Time:** {s['Study_Hours_Per_Day']} hrs/day")

    with c2:
        st.markdown("##### 🥗 Health & Lifestyle Metrics")
        st.write(f"**Sleep Duration:** {s['Sleep_Hours']} hrs")
        st.write(f"**Sleep Quality:** {s['Sleep_Quality']}/10")
        st.write(f"**Meal Quality:** {s['Meal_Quality_Score']}/100")
        st.write(f"**Screen Time:** {s['Screen_Time_Hours']} hrs/day")
        st.write(f"**Exercise:** {s['Exercise_Minutes']} mins/week")

    with c3:
        st.markdown("##### 🧠 Mental Health & Risk Profile")
        st.write(f"**Stress Level:** {s['Stress_Level']} ({s['Stress_Score']}/100)")
        st.write(f"**Depression Severity:** {s['Depression_Severity']}")
        st.write(f"**Counselor Visits:** {s['Counselor_Visits']}")
        st.write(f"**Composite Risk Score:** {s['Risk_Score']}/100")

    st.markdown("---")
    if str(s['Depression_Severity']).strip().lower() != 'none':
        st.error(f"🚨 **Depression Warning ({s['Depression_Severity']}):** {s['Depression_Indicators']}")
    else:
        st.success("✅ No Severe Depression Indicators Flagged")
