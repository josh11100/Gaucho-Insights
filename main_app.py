import streamlit as st
import pandas as pd
import os
import sqlite3

# 1. Database Queries Import
from queries import (
    GET_RECENT_LECTURES, 
    GET_EASIEST_LOWER_DIV, 
    GET_EASIEST_UPPER_DIV, 
    GET_EASIEST_DEPTS, 
    GET_BEST_GE_PROFS
)

# 2. Logic File Imports
try:
    import pstat_logic
    import cs_logic
    import mcdb_logic
    import chem_logic
except ImportError as e:
    st.error(f"(＿ ＿*) Z z z Logic File Missing: {e}")
    st.stop()

st.set_page_config(page_title="Gaucho Insights", layout="wide")

@st.cache_data
def load_and_query_data():
    csv_path = os.path.join('data', 'courseGrades.csv')
    if not os.path.exists(csv_path):
        st.error("CSV file not found.")
        st.stop()
        
    df_raw = pd.read_csv(csv_path)
    
    # --- PRE-PROCESSING ---
    df_raw['dept'] = df_raw['dept'].str.strip()
    df_raw['course'] = df_raw['course'].str.replace(r'\s+', ' ', regex=True).str.strip()
    df_raw['instructor'] = df_raw['instructor'].str.strip()
    df_raw['course_num'] = df_raw['course'].str.extract(r'(\d+)').astype(float)
    
    q_order = {'FALL': 4, 'SUMMER': 3, 'SPRING': 2, 'WINTER': 1}
    temp_split = df_raw['quarter'].str.upper().str.split(' ')
    df_raw['q_year'] = pd.to_numeric(temp_split.str[1], errors='coerce').fillna(0).astype(int)
    df_raw['q_rank'] = temp_split.str[0].map(q_order).fillna(0).astype(int)

    # --- SQLITE WORKFLOW ---
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    df_raw.drop(columns=['temp_split'], errors='ignore').to_sql('courses', conn, index=False, if_exists='replace')
    
    df_sorted = pd.read_sql_query(GET_RECENT_LECTURES, conn)
    lower_div_df = pd.read_sql_query(GET_EASIEST_LOWER_DIV, conn)
    upper_div_df = pd.read_sql_query(GET_EASIEST_UPPER_DIV, conn)
    dept_df = pd.read_sql_query(GET_EASIEST_DEPTS, conn)
    ge_profs_df = pd.read_sql_query(GET_BEST_GE_PROFS, conn)
    
    conn.close()
    return df_sorted, lower_div_df, upper_div_df, dept_df, ge_profs_df

def main():
    st.title("(｡•̀ᴗ-)✧ Gaucho Insights: UCSB Grade Distribution")
    
    df, lower_div_df, upper_div_df, dept_df, ge_profs_df = load_and_query_data()

    # --- LEADERBOARD EXPANDER ---
    with st.expander("°˖✧◝(⁰▿⁰)◜✧˖° View University Leaderboards", expanded=False):
        tab1, tab2, tab3, tab4 = st.tabs(["🐣 Lower Div", "🎓 Upper Div", "🏢 Depts", "👨‍🏫 Best GE Profs"])
        with tab1: st.table(lower_div_df.rename(columns={'course': 'Course', 'mean_gpa': 'Avg GPA'}))
        with tab2: st.table(upper_div_df.rename(columns={'course': 'Course', 'mean_gpa': 'Avg GPA'}))
        with tab3: st.table(dept_df.rename(columns={'dept': 'Department', 'dept_avg_gpa': 'Avg GPA', 'total_records': 'Count'}))
        with tab4: st.table(ge_profs_df.rename(columns={'instructor': 'Professor', 'avg_instructor_gpa': 'Avg GPA', 'classes_taught': 'Records'}))

    st.divider()

    # --- SIDEBAR ---
    st.sidebar.header("🔍 Search Filters")
    mode = st.sidebar.selectbox("Choose Department", ["All Departments", "PSTAT", "CS", "MCDB", "CHEM"])
    
    # New Search Inputs
    course_query = st.sidebar.text_input("Course Number (e.g., 1 or 120A)", "").strip().upper()
    prof_query = st.sidebar.text_input("Instructor Name (e.g., SOLIS)", "").strip().upper()
    
    prefix_map = {"PSTAT": "PSTAT", "CS": "CMPSC", "MCDB": "MCDB", "CHEM": "CHEM"}
    data = df.copy()

    # 1. Apply Logic based on Department Selection
    if mode == "PSTAT": data = pstat_logic.process_pstat(data)
    elif mode == "CS": data = cs_logic.process_cs(data)
    elif mode == "MCDB": data = mcdb_logic.process_mcdb(data)
    elif mode == "CHEM": data = chem_logic.process_chem(data)

    # 2. Apply Course Filter (Regex)
    if course_query:
        if mode == "All Departments":
            pattern = rf"\b{course_query}\b"
        else:
            pattern = rf"{prefix_map[mode]}\s+{course_query}\b"
        data = data[data['course'].str.contains(pattern, case=False, na=False, regex=True)]

    # 3. Apply Professor Filter (New Feature)
    if prof_query:
        data = data[data['instructor'].str.contains(prof_query, case=False, na=False)]

    # --- RESULTS DISPLAY ---
    st.header(f"Results for {mode}")
    if prof_query and not data.empty:
        st.subheader(f"Filtered for Instructor: {prof_query}")
    
    if not data.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Avg GPA", f"{data['avgGPA'].mean():.2f}")
        m2.metric("Classes Found", len(data))
        m3.metric("Professors", len(data['instructor'].unique()))

        st.subheader("Historical Records")
        display_df = data.drop(columns=['q_year', 'q_rank', 'course_num'], errors='ignore')
        st.dataframe(display_df, use_container_width=True)
        
        # Instructor comparison chart (unless only 1 professor is left)
        if len(data['instructor'].unique()) > 1:
            st.subheader("Instructor Performance")
            prof_chart = data.groupby('instructor')['avgGPA'].mean().sort_values()
            st.bar_chart(prof_chart)
    else:
        st.warning("No records found matching those filters. Try broadening your search!")

if __name__ == "__main__":
    main()
