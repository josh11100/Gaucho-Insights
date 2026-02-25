import streamlit as st
import pandas as pd
import os
import sqlite3

# 1. Database Queries Import (Restored)
from queries import (
    GET_RECENT_LECTURES, 
    GET_EASIEST_LOWER_DIV, 
    GET_EASIEST_UPPER_DIV, 
    GET_EASIEST_DEPTS, 
    GET_BEST_GE_PROFS
)

# 2. Logic File Imports (Restored)
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
    rmp_path = os.path.join('data', 'rmp_ratings.csv')
    
    if not os.path.exists(csv_path):
        st.error(f"Main CSV file not found at {csv_path}")
        st.stop()
        
    df_raw = pd.read_csv(csv_path)
    
    # --- CRITICAL FIX: Clean Column Names ---
    # This removes hidden spaces like " instructor" or "instructor "
    df_raw.columns = df_raw.columns.str.strip()
    
    # Check if instructor exists after cleaning
    if 'instructor' not in df_raw.columns:
        st.error(f"Column 'instructor' not found. Available columns: {list(df_raw.columns)}")
        st.stop()
    
    # --- PRE-PROCESSING ---
    df_raw['dept'] = df_raw['dept'].str.strip()
    df_raw['course'] = df_raw['course'].str.replace(r'\s+', ' ', regex=True).str.strip()
    
    # Handle potential NaN values in instructor before calling .str
    df_raw['instructor'] = df_raw['instructor'].fillna("UNKNOWN").str.strip().upper() 
    
    df_raw['course_num'] = df_raw['course'].str.extract(r'(\d+)').astype(float)
    
    # Setup Quarter Sorting
    q_order = {'FALL': 4, 'SUMMER': 3, 'SPRING': 2, 'WINTER': 1}
    # Ensure quarter is string and drop NaNs
    df_raw['quarter'] = df_raw['quarter'].fillna("UNKNOWN 0").astype(str)
    temp_split = df_raw['quarter'].str.upper().str.split(' ')
    
    df_raw['q_year'] = pd.to_numeric(temp_split.str.get(1), errors='coerce').fillna(0).astype(int)
    df_raw['q_rank'] = temp_split.str.get(0).map(q_order).fillna(0).astype(int)

    # --- RMP INTEGRATION ---
    if os.path.exists(rmp_path):
        rmp_df = pd.read_csv(rmp_path)
        rmp_df.columns = rmp_df.columns.str.strip() # Clean RMP columns too
        
        # Create a 'match_key' using the LAST NAME from RMP (e.g., "JORGE SOLIS" -> "SOLIS")
        rmp_df['match_key'] = rmp_df['instructor'].fillna("").str.split().str[-1].str.upper()
        rmp_df = rmp_df.sort_values('rmp_rating', ascending=False).drop_duplicates('match_key')
        
        # Create a 'match_key' using the LAST NAME from Grades (e.g., "SOLIS J" -> "SOLIS")
        df_raw['match_key'] = df_raw['instructor'].str.split().str[0].str.upper()
        
        # Merge on the key
        df_raw = pd.merge(df_raw, rmp_df[['match_key', 'rmp_rating']], on="match_key", how="left")
        df_raw = df_raw.drop(columns=['match_key'])

    # --- SQLITE WORKFLOW ---
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    # Ensure all columns are SQL-friendly
    df_raw.to_sql('courses', conn, index=False, if_exists='replace')
    
    # Run Leaderboard & Display Queries
    df_sorted = pd.read_sql_query(GET_RECENT_LECTURES, conn)
    lower_div_df = pd.read_sql_query(GET_EASIEST_LOWER_DIV, conn)
    upper_div_df = pd.read_sql_query(GET_EASIEST_UPPER_DIV, conn)
    dept_df = pd.read_sql_query(GET_EASIEST_DEPTS, conn)
    ge_profs_df = pd.read_sql_query(GET_BEST_GE_PROFS, conn)
    
    conn.close()
    return df_sorted, lower_div_df, upper_div_df, dept_df, ge_profs_df
def main():
    st.title("(｡•̀ᴗ-)✧ Gaucho Insights: UCSB Grade Distribution")
    
    # Load all 5 data sources
    df, lower_div_df, upper_div_df, dept_df, ge_profs_df = load_and_query_data()

    # --- LEADERBOARD EXPANDER ---
    with st.expander("°˖✧◝(⁰▿⁰)◜✧˖° View University Leaderboards", expanded=False):
        tab1, tab2, tab3, tab4 = st.tabs([
            "🐣 Lower Div", "🎓 Upper Div", "🏢 Depts", "👨‍🏫 Best GE Profs"
        ])
        with tab1: st.table(lower_div_df.rename(columns={'course': 'Course', 'mean_gpa': 'Avg GPA'}))
        with tab2: st.table(upper_div_df.rename(columns={'course': 'Course', 'mean_gpa': 'Avg GPA'}))
        with tab3: st.table(dept_df.rename(columns={'dept': 'Department', 'dept_avg_gpa': 'Avg GPA', 'total_records': 'Count'}))
        with tab4: st.table(ge_profs_df.rename(columns={'instructor': 'Professor', 'avg_instructor_gpa': 'Avg GPA', 'classes_taught': 'Records'}))

    st.divider()

    # --- SIDEBAR SEARCH ---
    st.sidebar.header("🔍 Search Filters")
    mode = st.sidebar.selectbox("Choose Department", ["All Departments", "PSTAT", "CS", "MCDB", "CHEM"])
    
    course_query = st.sidebar.text_input("Course Number (e.g., 1 or 120A)", "").strip().upper()
    prof_query = st.sidebar.text_input("Instructor Name (e.g., SOLIS)", "").strip().upper()
    
    prefix_map = {"PSTAT": "PSTAT", "CS": "CMPSC", "MCDB": "MCDB", "CHEM": "CHEM"}
    data = df.copy()

    # 1. Apply Major-Specific Logic
    if mode == "PSTAT": data = pstat_logic.process_pstat(data)
    elif mode == "CS": data = cs_logic.process_cs(data)
    elif mode == "MCDB": data = mcdb_logic.process_mcdb(data)
    elif mode == "CHEM": data = chem_logic.process_chem(data)

    # 2. Apply Course Regex (Strict Matching)
    if course_query:
        if mode == "All Departments":
            pattern = rf"\b{course_query}\b"
        else:
            pattern = rf"{prefix_map[mode]}\s+{course_query}\b"
        data = data[data['course'].str.contains(pattern, case=False, na=False, regex=True)]

    # 3. Apply Professor Filter
    if prof_query:
        data = data[data['instructor'].str.contains(prof_query, case=False, na=False)]

    # --- RESULTS DISPLAY ---
    st.header(f"Results for {mode}")
    
    if not data.empty:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Avg GPA", f"{data['avgGPA'].mean():.2f}")
        m2.metric("Classes Found", len(data))
        m3.metric("Professors", len(data['instructor'].unique()))
        
        # Calculate RMP Metric
        if 'rmp_rating' in data.columns:
            avg_rmp = pd.to_numeric(data['rmp_rating'], errors='coerce').dropna().mean()
            m4.metric("RMP Rating", f"{avg_rmp:.1f} / 5.0" if not pd.isna(avg_rmp) else "N/A")
        else:
            m4.metric("RMP Data", "Missing")

        st.subheader("Historical Records (Sorted by Most Recent)")
        # Clean up table for display
        cols_to_drop = ['q_year', 'q_rank', 'course_num']
        display_df = data.drop(columns=[c for c in cols_to_drop if c in data.columns], errors='ignore')
        st.dataframe(display_df, use_container_width=True)
        
        if len(data['instructor'].unique()) > 1:
            st.subheader("Instructor GPA Comparison")
            prof_chart = data.groupby('instructor')['avgGPA'].mean().sort_values()
            st.bar_chart(prof_chart)
    else:
        st.info("No matching records found. Try adjusting your sidebar filters!")

if __name__ == "__main__":
    main()
