import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px
import streamlit.components.v1 as components

# --- 1. CONFIG & CSS ---
st.set_page_config(page_title="Gaucho Insights", layout="wide", page_icon="🎓")

def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

# --- 2. SESSION STATE (ROUTING LOGIC) ---
if 'dept_query' not in st.session_state: st.session_state.dept_query = " "
if 'course_query' not in st.session_state: st.session_state.course_query = ""
if 'prof_query' not in st.session_state: st.session_state.prof_query = ""
if 'view_professor' not in st.session_state: st.session_state.view_professor = None

def reset_filters():
    st.session_state.dept_query = " "
    st.session_state.course_query = ""
    st.session_state.prof_query = ""
    st.session_state.view_professor = None

# --- 3. DATA ENGINE ---
@st.cache_data
def load_data():
    csv_path = 'courseGrades.csv' # Adjust if in /data folder
    if not os.path.exists(csv_path):
        st.error("CSV not found.")
        st.stop()
    df = pd.read_csv(csv_path)
    df.columns = [str(c).lower().strip() for c in df.columns]
    
    # Cleaning
    df['course'] = df['course'].astype(str).str.upper()
    df['instructor'] = df['instructor'].astype(str).str.upper()
    df['dept'] = df['dept'].astype(str).str.upper()
    
    gpa_col = 'avggpa' if 'avggpa' in df.columns else 'avg_gpa'
    return df, gpa_col

full_df, gpa_col = load_data()

# --- 4. PROFESSOR DETAIL PAGE (THE CLICKED VIEW) ---
if st.session_state.view_professor:
    prof_name = st.session_state.view_professor
    
    if st.button("⬅ BACK TO SEARCH"):
        st.session_state.view_professor = None
        st.rerun()
    
    st.title(f"👤 {prof_name}")
    
    prof_data = full_df[full_df['instructor'] == prof_name]
    avg_prof_gpa = prof_data[gpa_col].mean()

    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Aggregate GPA", f"{avg_prof_gpa:.2f}")
        st.subheader("RMP Insights")
        # Example tags - in a real app, you'd pull these from your RMP CSV
        st.markdown("""
        <span style='background:#FFD700; color:black; padding:5px; border-radius:5px; margin:2px;'>Clear Grading</span>
        <span style='background:#0074D9; color:white; padding:5px; border-radius:5px; margin:2px;'>Tough Exams</span>
        """, unsafe_allow_html=True)
        
    with c2:
        st.subheader("Teaching History")
        st.dataframe(prof_data[['course', 'quarter', 'year', gpa_col]].sort_values('year', ascending=False), use_container_width=True)
    
    st.stop() # Prevents showing the home tabs when viewing a prof

# --- 5. SIDEBAR ---
st.sidebar.header("( 🔍 ) FILTERS")
all_depts = sorted(full_df['dept'].unique().tolist())
selected_dept = st.sidebar.selectbox("Select Department", options=[" "] + all_depts, key="dept_query")
course_q = st.sidebar.text_input("COURSE #", key="course_query").strip().upper()
prof_q = st.sidebar.text_input("PROFESSOR NAME", key="prof_query").strip().upper()

if st.sidebar.button("( ✖ ) Clear All"):
    reset_filters()
    st.rerun()

# --- 6. 3D HTML (Simplified for brevity) ---
stats_3d_html = """
<style>
    .card { width: 98%; height: 600px; background: rgba(0,31,63,0.8); border: 2px solid #FFD700; border-radius: 20px; color: white; padding: 40px; font-family: sans-serif; }
</style>
<div class="card">
    <h1>WELCOME GAUCHOS!</h1>
    <p>Numbers don't lie. Search professors and courses below.</p>
</div>
"""

# --- 7. TABS ---
tab1, tab2 = st.tabs(["🏠 HOME", "🔍 SEARCH TOOL"])

with tab1:
    col_l, col_r = st.columns([2, 1])
    with col_l:
        components.html(stats_3d_html, height=650)
    with col_r:
        st.metric("Data Recency", "Summer 2025")

with tab2:
    results = full_df.copy()
    if selected_dept != " ": results = results[results['dept'] == selected_dept]
    if course_q: results = results[results['course'].str.contains(course_q)]
    if prof_q: results = results[results['instructor'].str.contains(prof_q)]

    if not results.empty:
        for idx, row in results.head(15).iterrows():
            with st.container(border=True):
                ca, cb = st.columns([2, 1])
                with ca:
                    st.subheader(f"{row['course']} | {row['quarter']} {row['year']}")
                    
                    # PROFESSOR CLICK LOGIC
                    p_name = row['instructor']
                    if st.button(f"👤 {p_name}", key=f"prof_{idx}"):
                        st.session_state.view_professor = p_name
                        st.rerun()
                    
                    st.write(f"**GPA:** {row[gpa_col]:.2f}")
                with cb:
                    # Small plotly chart
                    fig = px.bar(x=['A','B','C','D','F'], y=[row['a'],row['b'],row['c'],row['d'],row['f']], height=150)
                    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True, key=f"p_{idx}")
    else:
        st.warning("No data found for those filters.")
