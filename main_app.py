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
    df_raw.columns = [str(c).strip().lower() for c in df_raw.columns]
    
    # --- BASIC CLEANING ---
    df_raw['instructor'] = df_raw['instructor'].astype(str).str.upper().str.strip()
    df_raw['quarter'] = df_raw['quarter'].astype(str).str.upper().str.strip()
    df_raw['dept'] = df_raw['dept'].astype(str).str.upper().str.strip()
    df_raw['course'] = df_raw['course'].astype(str).str.upper().str.strip()
    
    # Numeric Conversion
    gpa_col = 'avggpa' if 'avggpa' in df_raw.columns else 'avg_gpa'
    for col in [gpa_col, 'a', 'b', 'c', 'd', 'f']:
        if col in df_raw.columns:
            df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce').fillna(0)

    # --- THE YEAR FIX ---
    # This extracts '2023' from 'FALL 2023' and puts it in its own column
    df_raw['year'] = df_raw['quarter'].str.extract(r'(\d{4})').fillna(0).astype(int)
    # Required for your SQL queries in queries.py
    df_raw['q_year'] = df_raw['year']
    
    q_order = {'FALL': 4, 'SUMMER': 3, 'SPRING': 2, 'WINTER': 1}
    df_raw['q_rank'] = df_raw['quarter'].apply(lambda x: next((q_order[q] for q in q_order if q in x), 0))
    df_raw['course_num'] = df_raw['course'].str.extract(r'(\d+)').astype(float).fillna(0)

    # --- RMP ---
    if os.path.exists(rmp_path):
        try:
            rmp_df = pd.read_csv(rmp_path)
            rmp_df.columns = [str(c).strip().lower() for c in rmp_df.columns]
            rmp_df['match_key'] = rmp_df['instructor'].str.split().str[-1].str.upper()
            rmp_df = rmp_df.sort_values('rmp_rating', ascending=False).drop_duplicates('match_key')
            df_raw['match_key'] = df_raw['instructor'].str.split().str[0].str.upper()
            df_raw = pd.merge(df_raw, rmp_df[['match_key', 'rmp_rating']], on="match_key", how="left")
        except: pass

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
        
        # --- ORDERED COLUMN SELECTION ---
        # We explicitly add 'year' here so it shows up in the table
        display_cols = ['year', 'quarter', 'course', 'instructor', gpa_col, 'a', 'b', 'c', 'd', 'f']
        
        if 'rmp_rating' in data.columns:
            display_cols.append('rmp_rating')
            
        # Filter for only what actually exists to prevent errors
        existing_cols = [c for c in display_cols if c in data.columns]
        
        # Sorting: Newest years at the top
        final_df = data[existing_cols].sort_values(by=['year', gpa_col], ascending=[False, False])
        
        # Cleanup column names for the user (capitalize them)
        final_df.columns = [c.replace('_', ' ').title() if c != 'avgGPA' else 'Avg GPA' for c in final_df.columns]

        st.dataframe(final_df, use_container_width=True)
    else:
        st.info("No records found.")

if __name__ == "__main__":
    main()
