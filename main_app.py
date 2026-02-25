import streamlit as st
import pandas as pd
import os
import sqlite3

# 1. Database Queries Import
try:
    from queries import (
        GET_RECENT_LECTURES, 
        GET_EASIEST_LOWER_DIV, 
        GET_EASIEST_UPPER_DIV, 
        GET_EASIEST_DEPTS, 
        GET_BEST_GE_PROFS
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
    # Standardize column names to lowercase to prevent mapping errors
    df_raw.columns = [str(c).strip().lower() for c in df_raw.columns]
    
    # --- BASIC CLEANING ---
    df_raw['instructor'] = df_raw['instructor'].astype(str).str.upper().str.strip()
    df_raw['quarter'] = df_raw['quarter'].astype(str).str.upper().str.strip()
    df_raw['dept'] = df_raw['dept'].astype(str).str.upper().str.strip()
    df_raw['course'] = df_raw['course'].astype(str).str.upper().str.strip()
    
    # Force GPA and Grades to Numeric
    # We check for both 'avggpa' and 'avg_gpa' just in case
    gpa_col = 'avggpa' if 'avggpa' in df_raw.columns else 'avg_gpa'
    for col in [gpa_col, 'a', 'b', 'c', 'd', 'f', 'nletterstudents']:
        if col in df_raw.columns:
            df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce').fillna(0)

    # --- YEAR & RANKING (For SQL Queries) ---
    # Using a simple split; assumes format like "FALL 2024"
    df_raw['q_year'] = df_raw['quarter'].str.extract(r'(\d{4})').fillna(0).astype(int)
    q_order = {'FALL': 4, 'SUMMER': 3, 'SPRING': 2, 'WINTER': 1}
    df_raw['q_rank'] = df_raw['quarter'].apply(lambda x: next((q_order[q] for q in q_order if q in x), 0))
    df_raw['course_num'] = df_raw['course'].str.extract(r'(\d+)').astype(float).fillna(0)

    # --- RMP INTEGRATION ---
    if os.path.exists(rmp_path):
        try:
            rmp_df = pd.read_csv(rmp_path)
            rmp_df.columns = [str(c).strip().lower() for c in rmp_df.columns]
            rmp_df['match_key'] = rmp_df['instructor'].str.split().str[-1].str.upper()
            rmp_df = rmp_df.sort_values('rmp_rating', ascending=False).drop_duplicates('match_key')
            df_raw['match_key'] = df_raw['instructor'].str.split().str[0].str.upper()
            df_raw = pd.merge(df_raw, rmp_df[['match_key', 'rmp_rating']], on="match_key", how="left")
        except: pass

    # --- SQLITE WORKFLOW ---
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
    
    # Load data from the cached function
    df, lower_div_df, upper_div_df, dept_df, ge_profs_df = load_and_query_data()

    # --- SEARCH ---
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

    # --- MAIN DISPLAY ---
    if not data.empty:
        # 1. Metrics
        col_gpa = 'avggpa' if 'avggpa' in data.columns else 'avg_gpa'
        m1, m2 = st.columns(2)
        m1.metric("Avg GPA", f"{data[col_gpa].mean():.2f}")
        m2.metric("Records", len(data))

        # 2. Reordered Table
        # We put Course, Instructor, and GPA first. Everything else follows.
        important_cols = ['course', 'instructor', col_gpa, 'quarter']
        grade_cols = ['a', 'b', 'c', 'd', 'f']
        rmp_cols = ['rmp_rating'] if 'rmp_rating' in data.columns else []
        
        # Combine them in order
        all_cols = important_cols + grade_cols + rmp_cols
        # Only include columns that actually exist in the CSV
        existing_cols = [c for c in all_cols if c in data.columns]
        
        display_df = data[existing_cols].copy()
        
        # Sort by Quarter Year (q_year) and GPA
        if 'q_year' in data.columns:
            display_df['sort_year'] = data['q_year']
            display_df = display_df.sort_values(by=['sort_year', col_gpa], ascending=[False, False]).drop(columns=['sort_year'])

        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No records found. Try searching for a different course!")

if __name__ == "__main__":
    main()
