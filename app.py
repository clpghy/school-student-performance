import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="Multi-Factor Student Performance & Well-being Monitor", layout="wide")

# Live Google Sheet CSV Link
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ldtaVjWIPQILcwLEpSvxVmRCJiJN3vzNbMn4gBtCQh4/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=0)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df['Risk_Status'] = df['Risk_Flag'].map({1: '⚠️ At-Risk', 0: '✅ Safe'})
    df['Depression_Severity'] = df['Depression_Severity'].fillna('None')
    df['Depression_Indicators'] = df['Depression_Indicators'].fillna('None')
    
    # Feature 1: Automated MTSS/RTI Tier Allocation
    def assign_tier(score):
        if score <= 35:
            return "Tier 1: Universal Support (Low Risk)"
        elif score <= 70:
            return "Tier 2: Targeted Intervention (Moderate)"
        else:
            return "Tier 3: Intensive Intervention (High Risk)"
            
    df['MTSS_Tier'] = df['Risk_Score'].apply(assign_tier)
    return df

raw_df = load_data()

# Feature 2: Sidebar Global Cohort & Demographics Filtering
st.sidebar.header("🎯 Cohort Filters")
selected_grade = st.sidebar.multiselect("Filter by Grade:", options=sorted(raw_df['Grade'].unique()), default=sorted(raw_df['Grade'].unique()))
selected_section = st.sidebar.multiselect("Filter by Section:", options=sorted(raw_df['Section'].unique()), default=sorted(raw_df['Section'].unique()))
selected_gender = st.sidebar.multiselect("Filter by Gender:", options=sorted(raw_df['Gender'].unique()), default=sorted(raw_df['Gender'].unique()))

# Apply Sidebar Filters
df = raw_df[
    (raw_df['Grade'].isin(selected_grade)) & 
    (raw_df['Section'].isin(selected_section)) & 
    (raw_df['Gender'].isin(selected_gender))
]

st.title("🎓 Multi-Factor Student Performance & Well-being Monitor")
st.caption("Scalable 360° Early-Warning System Analyzing Academic, Physical, Psychological & Lifestyle Indicators")

# MTSS TIER BREAKDOWN METRICS
tier1_count = len(df[df['MTSS_Tier'].str.startswith('Tier 1')])
tier2_count = len(df[df['MTSS_Tier'].str.startswith('Tier 2')])
tier3_count = len(df[df['MTSS_Tier'].str.startswith('Tier 3')])

m1, m2, m3, m4 = st.columns(4)
m1.metric("Evaluated Cohort Size", len(df))
m2.metric("🟢 Tier 1 (Universal)", tier1_count)
m3.metric("🟡 Tier 2 (Targeted)", tier2_count)
m4.metric("🔴 Tier 3 (Intensive)", tier3_count)

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["🎛️ Multi-Factor Scatter Analysis", "🔥 Factor Correlation Matrix", "🔍 Student 360° Profile & Interventions", "📋 Complete Live Dataset"])

# TAB 1: Dynamic Scatter Plot
with tab1:
    st.subheader("Dynamic Multi-Factor Exploration")
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    selectable_cols = [c for c in numeric_cols if c not in ['Student_ID', 'Risk_Flag']]
    
    col_x, col_y = st.columns(2)
    with col_x:
        x_axis = st.selectbox("Select X-Axis Factor:", selectable_cols, index=selectable_cols.index("Sleep_Hours") if "Sleep_Hours" in selectable_cols else 0)
    with col_y:
        y_axis = st.selectbox("Select Y-Axis Factor:", selectable_cols, index=selectable_cols.index("Overall_Percentage") if "Overall_Percentage" in selectable_cols else 0)
    
    fig_dynamic = px.scatter(
        df, x=x_axis, y=y_axis, color="MTSS_Tier", size="Risk_Score", hover_name="Name",
        hover_data=["Grade", "Section", "Stress_Level", "Attendance_%", "Depression_Severity"]
    )
    st.plotly_chart(fig_dynamic, use_container_width=True)

# TAB 2: Correlation Heatmap
with tab2:
    st.subheader("Multi-Factor Correlation Heatmap")
    corr_cols = ['Overall_Percentage', 'Academic_Change', 'Study_Hours_Per_Day', 'Attendance_%', 'Meal_Quality_Score', 'Sleep_Hours', 'Stress_Score', 'Risk_Score']
    valid_corr_cols = [c for c in corr_cols if c in df.columns]
    st.plotly_chart(px.imshow(df[valid_corr_cols].corr(), text_auto=".2f", color_continuous_scale="RdBu_r", aspect="auto"), use_container_width=True)

# TAB 3: Student 360° Profile, PDF Generator & Intervention Tracker
with tab3:
    st.subheader("Individual Student Diagnostic & Intervention Center")
    if len(df) == 0:
        st.warning("No students match the current sidebar filter selections.")
    else:
        selected_student = st.selectbox("Select Student:", df['Name'].unique())
        s = df[df['Name'] == selected_student].iloc[0]
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("##### 📚 Academic Metrics")
            st.write(f"**Overall Score:** {s['Overall_Percentage']}%")
            st.write(f"**Attendance:** {s['Attendance_%']}%")
            st.write(f"**Study Hours:** {s['Study_Hours_Per_Day']} hrs/day")
        with c2:
            st.markdown("##### 🥗 Health & Lifestyle Metrics")
            st.write(f"**Sleep Duration:** {s['Sleep_Hours']} hrs")
            st.write(f"**Screen Time:** {s['Screen_Time_Hours']} hrs/day")
            st.write(f"**Meal Quality Score:** {s['Meal_Quality_Score']}/100")
        with c3:
            st.markdown("##### 🧠 Mental Health Profile")
            st.write(f"**MTSS Classification:** {s['MTSS_Tier']}")
            st.write(f"**Stress Level:** {s['Stress_Level']} ({s['Stress_Score']}/100)")
            st.write(f"**Composite Risk Score:** {s['Risk_Score']}/100")

        st.markdown("---")
        
        # Feature 4: Printable PDF Diagnostic Card Generator
        def generate_pdf(student_data):
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
            styles = getSampleStyleSheet()
            story = []
            
            title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#1E3A8A'))
            story.append(Paragraph(f"Student Diagnostic Card: {student_data['Name']} ({student_data['Student_ID']})", title_style))
            story.append(Spacer(1, 12))
            
            data = [
                ["Parameter", "Metric Value", "Parameter", "Metric Value"],
                ["Grade & Section", f"Grade {student_data['Grade']} - {student_data['Section']}", "MTSS Classification", str(student_data['MTSS_Tier'])],
                ["Overall Academic %", f"{student_data['Overall_Percentage']}%", "Attendance %", f"{student_data['Attendance_%']}%"],
                ["Sleep Hours", f"{student_data['Sleep_Hours']} hrs/day", "Screen Time", f"{student_data['Screen_Time_Hours']} hrs/day"],
                ["Stress Score", f"{student_data['Stress_Score']}/100", "Depression Severity", str(student_data['Depression_Severity'])],
                ["Composite Risk Score", f"{student_data['Risk_Score']}/100", "Risk Status", str(student_data['Risk_Status'])],
            ]
            
            t = Table(data, colWidths=[130, 140, 130, 140])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('PADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(t)
            doc.build(story)
            buffer.seek(0)
            return buffer

        pdf_data = generate_pdf(s)
        st.download_button(
            label=f"📄 Download Printable PDF Card for {s['Name']}",
            data=pdf_data,
            file_name=f"{s['Student_ID']}_Diagnostic_Card.pdf",
            mime="application/pdf"
        )
        
        st.markdown("---")
        
        # Feature 3: Action & Intervention Note Tracker
        st.subheader("📝 Action & Intervention Log")
        if 'notes' not in st.session_state:
            st.session_state.notes = {}
            
        student_id = s['Student_ID']
        if student_id not in st.session_state.notes:
            st.session_state.notes[student_id] = []
            
        with st.form(key=f"intervention_form_{student_id}"):
            int_type = st.selectbox("Intervention Type:", ["Academic Tutoring", "Counselor Consultation", "Parent Meeting", "Behavioral Check-in"])
            note_text = st.text_area("Session Notes / Next Actions:")
            submit_note = st.form_submit_button("Save Log Entry")
            
            if submit_note and note_text:
                st.session_state.notes[student_id].append({"Type": int_type, "Note": note_text})
                st.success("Intervention logged successfully!")

        if st.session_state.notes[student_id]:
            st.markdown("**Previous Logged Interventions:**")
            for log in st.session_state.notes[student_id]:
                st.info(f"**[{log['Type']}]** {log['Note']}")

# TAB 4: Raw Dataset View
with tab4:
    st.subheader("📋 Complete Live Student Dataset")
    st.dataframe(df, use_container_width=True)
