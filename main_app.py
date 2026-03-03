import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px
import streamlit.components.v1 as components

# --- 1. SET PAGE CONFIG ---
st.set_page_config(page_title="Gaucho Insights", layout="wide", page_icon="🎓")

# --- 2. LOAD CSS ---
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

# --- 3. SESSION STATE (ROUTING & FILTERS) ---
if 'dept_query' not in st.session_state: st.session_state.dept_query = " "
if 'course_query' not in st.session_state: st.session_state.course_query = ""
if 'prof_query' not in st.session_state: st.session_state.prof_query = ""
if 'view_professor' not in st.session_state: st.session_state.view_professor = None

def reset_filters():
    st.session_state.dept_query = " "
    st.session_state.course_query = ""
    st.session_state.prof_query = ""
    st.session_state.view_professor = None

# --- 4. DATA ENGINE (FIXED CSV LOADING) ---
@st.cache_data
def load_and_clean_data():
    # Attempt to find the file in multiple common locations
    possible_paths = [
        'courseGrades.csv',
        'data/courseGrades.csv',
        '../courseGrades.csv'
    ]
    
    target_path = None
    for p in possible_paths:
        if os.path.exists(p):
            target_path = p
            break
            
    if not target_path:
        st.error("⚠️ CSV NOT FOUND: Please ensure 'courseGrades.csv' is in your folder.")
        st.info("Currently searching in: " + str(os.getcwd()))
        st.stop()
        
    df = pd.read_csv(target_path)
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Standardize names
    for col in ['instructor', 'quarter', 'course', 'dept']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()

    gpa_col = next((c for c in ['avggpa', 'avg_gpa'] if c in df.columns), 'avggpa')
    return df, gpa_col

full_df, gpa_col = load_and_clean_data()

# --- 5. PROFESSOR DETAIL ROUTER ---
if st.session_state.view_professor:
    prof_name = st.session_state.view_professor
    
    if st.button("⬅ BACK TO SEARCH"):
        st.session_state.view_professor = None
        st.rerun()
    
    st.title(f"👤 {prof_name}")
    
    prof_data = full_df[full_df['instructor'] == prof_name]
    avg_gpa = prof_data[gpa_col].mean()

    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Avg Career GPA", f"{avg_gpa:.2f}")
        st.subheader("Professor Info")
        st.write("Data pulled from Registrar records.")
        # Placeholder for RMP tags if you join that data later
        st.markdown("""
            <div style='display:flex; gap:10px; flex-wrap:wrap;'>
                <span style='background:#FFD700; color:black; padding:5px 12px; border-radius:20px; font-weight:bold;'>REGISTRAR DATA</span>
                <span style='background:#0074D9; color:white; padding:5px 12px; border-radius:20px; font-weight:bold;'>GAUCHO VERIFIED</span>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("Past Courses & Distributions")
        st.dataframe(prof_data[['course', 'quarter', 'year', gpa_col]].sort_values('year', ascending=False), use_container_width=True)
    
    st.stop() # Hide the home/search tabs when viewing profile

# --- 6. SIDEBAR ---
st.sidebar.header("( 🔍 ) FILTERS")
all_depts = sorted(full_df['dept'].unique().tolist())
selected_dept = st.sidebar.selectbox("Select Department", options=[" "] + all_depts, key="dept_query")
course_q = st.sidebar.text_input("COURSE #", key="course_query").strip().upper()
prof_q = st.sidebar.text_input("PROFESSOR NAME", key="prof_query").strip().upper()

if st.sidebar.button("( ✖ ) Clear All"):
    reset_filters()
    st.rerun()

# --- 7. HOME & SEARCH TABS ---
tab1, tab2 = st.tabs(["🏠 HOME", "🔍 SEARCH TOOL"])

with tab1:
    col_l, col_r = st.columns([2, 1])
    with col_l:
        # 3D BOX (Placeholder for your full JS version)
        st.markdown("""
        <div style="background: rgba(0,31,63,0.8); border: 2px solid #FFD700; border-radius: 25px; padding: 50px; height: 600px;">
            <h1 style="color:#FFD700; font-family:sans-serif;">WELCOME GAUCHOS!</h1>
            <p style="font-size:1.2em;">Search professors in the <b>Search Tool</b> tab to see their RMP tags and grading history.</p>
        </div>
        """, unsafe_allow_html=True)
    with col_r:
        st.metric("Data Recency", "Summer 2025")

with tab2:
    data = full_df.copy()
    if selected_dept != " ": data = data[data['dept'] == selected_dept]
    if course_q: data = data[data['course'].str.contains(course_q)]
    if prof_q: data = data[data['instructor'].str.contains(prof_q)]

    if not data.empty:
        for idx, row in data.head(20).iterrows():
            with st.container(border=True):
                cA, cB = st.columns([2, 1])
                with cA:
                    st.subheader(f"{row['course']} | {row['quarter']} {row['year']}")
                    
                    # PROFESSOR BUTTON (Updates state to trigger Profile view)
                    if st.button(f"👤 {row['instructor']}", key=f"p_btn_{idx}"):
                        st.session_state.view_professor = row['instructor']
                        st.rerun()
                        
                    st.markdown(f"**GPA:** {row[gpa_col]:.2f}")
                with cB:
                    # Quick plotly bar chart
                    fig = px.bar(x=['A','B','C','D','F'], 
                                 y=[row.get('a',0), row.get('b',0), row.get('c',0), row.get('d',0), row.get('f',0)], 
                                 height=140, template="plotly_dark")
                    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0))
                    st.plotly_chart(fig, use_container_width=True, key=f"plot_{idx}")
    else:
        st.info("Use the sidebar to search for courses or professors!")
