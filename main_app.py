import streamlit as st
import pandas as pd
import os
import sqlite3
import re

# 1. Database Queries Import
try:
    from queries import (
        GET_RECENT_LECTURES, GET_EASIEST_LOWER_DIV, 
        GET_EASIEST_UPPER_DIV, GET_EASIEST_DEPTS, GET_BEST_GE_PROFS
    )
except ImportError:
    st.error("❌ 'queries.py' missing!")
    st.stop()

# 2. Logic File Imports
try:
    import pstat_logic, cs_logic, mcdb_logic, chem_logic
except ImportError as e:
    st.error(f"❌ Logic File Missing: {e}")
    st.stop()

st.set_page_config(page_title="Gaucho Insights", layout="wide")

@st.cache_data
def load_and_query_data():
    csv_path = os.path.join('data', 'courseGrades.csv')
    rmp_path = os.path.join('data', 'rmp_ratings.csv')
    
    if not os.path.exists(csv_path):
        st.error(f"❌ CSV not found at {csv_path}")
        st.stop()
        
    df_raw = pd.read_csv(csv_path)
    df_raw.columns = [str(c).strip().lower() for c in df_raw.columns]
    
    # --- CLEANING ---
    df_raw['instructor'] = df_raw['instructor'].astype(str).str.upper().str.strip()
    df_raw['quarter'] = df_raw['quarter'].astype(str).str.upper().str.strip()
    df_raw['dept'] = df_raw['dept'].astype(str).str.upper().str.strip()
    df_raw['course'] = df_raw['course'].astype(str).str.upper().str.strip()
    
    # --- ULTRA-AGGRESSIVE YEAR EXTRACTOR ---
    def deep_extract_year(q_str):
        # 1. Try to find a 4-digit year (2024)
        match4 = re.search(r'(20\d{2})', q_str)
        if match4: return int(match4.group(1))
        
        # 2. Try to find a 2-digit year (24)
        match2 = re.search(r'(\d{2})', q_str)
        if match2: 
            val = int(match2.group(1))
            # Only convert if it's a reasonable year (between 10 and 30)
            return 2000 + val if 10 <= val <= 30 else val
            
        return "Unknown" # Return a string so we see it in the table instead of 0

    df_raw['year'] = df_raw['quarter'].apply(deep_extract_year)
    df_raw['q_year'] = pd.to_numeric(df_raw['year'], errors='coerce').fillna(0)
    
    q_order = {'FALL': 4, 'SUMMER': 3, 'SPRING': 2, 'WINTER': 1}
    df_raw['q_rank'] = df_raw['quarter'].apply(lambda x: next((q_order[q] for q in q_order if q in x), 0))
    df_raw['course_num'] = df_raw['course'].str.extract(r'(\d+)').astype(float).fillna(0)

    # --- NUMERIC FIXES ---
    gpa_col = 'avggpa' if 'avggpa' in df_raw.columns else 'avg_gpa'
    for col in [gpa_col, 'a', 'b', 'c', 'd', 'f']:
        if col in df_raw.columns:
            df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce').fillna(0)

    # --- SQLITE ---
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    df_raw.to_sql('courses', conn, index=False, if_exists='replace')
    results = (
        pd.read_sql_query(GET_RECENT_LECTURES, conn),
        pd.read_sql_query(GET_EASIEST_LOWER_DIV, conn),
        pd.read_sql_query(GET_EASIEST_UPPER_DIV, conn),
        pd.read_sql_query(GET_EASIEST_DEPTS, conn),
        pd.read_sql_query(GET_BEST_GE_PROFS, conn)
    )
    conn.close()
    return results

def main():
    st.title("(｡•̀ᴗ-)✧ Gaucho Insights")
    df, lower_div_df, upper_div_df, dept_df, ge_profs_df = load_and_query_data()

    st.sidebar.header("🔍 Filters")
    mode = st.sidebar.selectbox("Department", ["All Departments", "PSTAT", "CS", "MCDB", "CHEM"])
    course_q = st.sidebar.text_input("Course #", "").strip().upper()
    prof_q = st.sidebar.text_input("Professor", "").strip().upper()
    
    data = df.copy()
    if mode == "PSTAT": data = pstat_logic.process_pstat(data)
    elif mode == "CS": data = cs_logic.process_cs(data)
    elif mode == "MCDB": data = mcdb_logic.process_mcdb(data)
    elif mode == "CHEM": data = chem_logic.process_chem(data)

    if course_q: data = data[data['course'].str.contains(course_q, na=False)]
    if prof_q: data = data[data['instructor'].str.contains(prof_q, na=False)]

    if not data.empty:
        gpa_col = 'avggpa' if 'avggpa' in data.columns else 'avg_gpa'
        
        # --- NEW ORDER: Course, Instructor, GPA, Quarter, Year, then Grades ---
        display_cols = ['course', 'instructor', gpa_col, 'quarter', 'year', 'a', 'b', 'c', 'd', 'f']
        existing_cols = [c for c in display_cols if c in data.columns]
        
        final_df = data[existing_cols].copy()
        
        # Sort by Year (treating it as numeric where possible) and GPA
        data['sort_year'] = pd.to_numeric(data['year'], errors='coerce').fillna(0)
        final_df = final_df.loc[data.sort_values(by=['sort_year', gpa_col], ascending=[False, False]).index]
        
        # Final formatting for the UI
        final_df.columns = [c.replace('_', ' ').title() if c != 'avggpa' else 'Avg GPA' for c in final_df.columns]

        st.dataframe(final_df, use_container_width=True)
    else:
        st.info("No records found.")

if __name__ == "__main__":
    main()
