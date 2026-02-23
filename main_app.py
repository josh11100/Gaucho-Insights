import streamlit as st
import pandas as pd
import os
import sqlite3
from queries import GET_RECENT_LECTURES, GET_EASIEST_CLASSES

# 1. Logic Imports
try:
    from pstat_logic import process_pstat
    from cs_logic import process_cs
    from mcdb_logic import process_mcdb
    from chem_logic import process_chem
except ImportError as e:
    st.error(f"🚨 Logic File Missing: {e}")
    st.stop()

st.set_page_config(page_title="Gaucho Insights", layout="wide")

@st.cache_data
def load_and_query_data():
    csv_path = os.path.join('data', 'courseGrades.csv')
    df_raw = pd.read_csv(csv_path)
    
    # --- PRE-PROCESSING (Setup for SQL) ---
    df_raw['course_num'] = df_raw['course'].str.extract(r'(\d+)').astype(float)
    q_order = {'FALL': 4, 'SUMMER': 3, 'SPRING': 2, 'WINTER': 1}
    temp_split = df_raw['quarter'].str.upper().str.split(' ')
    df_raw['q_year'] = pd.to_numeric(temp_split.str[1], errors='coerce').fillna(0).astype(int)
    df_raw['q_rank'] = temp_split.str[0].map(q_order).fillna(0).astype(int)

    # --- SQL EXECUTION ---
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    # Important: We name the table 'courses' so it matches your SQL 'FROM courses'
    df_raw.drop(columns=['temp_split'], errors='ignore').to_sql('courses', conn, index=False, if_exists='replace')
    
    # !!! THIS IS THE PART THAT USES YOUR SQL FILE !!!
    df_sorted = pd.read_sql_query(GET_RECENT_LECTURES, conn)
    easiest_df = pd.read_sql_query(GET_EASIEST_CLASSES, conn)
    
    conn.close()
    
    # Return ONLY the results from the SQL queries
    return df_sorted, easiest_df
    
def main():
    st.title("📊 Gaucho Insights: UCSB Grade Distribution")
    st.markdown("Historical data powered by SQLite. Standard undergraduate courses only.")
    
    # Receive the two DataFrames from the cached function
    df, easiest_df = load_and_query_data()

    # --- SIDEBAR SELECTION ---
    st.sidebar.header("Navigation")
    options = ["PSTAT", "CS", "MCDB", "CHEM", "All Departments"]
    mode = st.sidebar.selectbox("Choose Department", options)
    
    prefix_map = {"PSTAT": "PSTAT", "CS": "CMPSC", "MCDB": "MCDB", "CHEM": "CHEM"}
    
    if mode == "All Departments":
        course_query = st.sidebar.text_input("Global Search (e.g., MATH 3A)", "").strip().upper()
        data = df.copy()
    else:
        course_query = st.sidebar.text_input(f"Enter {mode} Number (e.g., 120)", "").strip().upper()
        if mode == "PSTAT": data = process_pstat(df)
        elif mode == "CS": data = process_cs(df)
        elif mode == "MCDB": data = process_mcdb(df)
        elif mode == "CHEM": data = process_chem(df)

    # --- FILTERING ---
    if course_query:
        if mode == "All Departments":
            data = data[data['course'].str.contains(course_query, case=False, na=False)]
        else:
            pattern = rf"{prefix_map[mode]}\s+{course_query}"
            data = data[data['course'].str.contains(pattern, case=False, na=False, regex=True)]

    # --- RESULTS DISPLAY ---
    st.header(f"Results for {mode}")
    
    if not data.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Avg GPA", f"{data['avgGPA'].mean():.2f}")
        m2.metric("Classes Found", len(data))
        m3.metric("Professors", len(data['instructor'].unique()))

        st.subheader("Historical Records (Newest First)")
        # Hide the helper columns from the final user table
        display_df = data.drop(columns=['q_year', 'q_rank', 'course_num'], errors='ignore')
        st.dataframe(display_df, use_container_width=True)
        
        st.subheader("Instructor Performance")
        prof_chart = data.groupby('instructor')['avgGPA'].mean().sort_values()
        st.bar_chart(prof_chart)
    else:
        st.info("Enter a course number in the sidebar to begin.")

    # --- SQL HALL OF FAME ---
    st.divider()
    st.subheader("🏆 The 'GPA Booster' Hall of Fame")
    st.write("The top 10 easiest courses based on historical averages (SQL Calculated):")

    if not easiest_df.empty:
        # Create a display copy and rename for the user
        easiest_display = easiest_df.copy()
        easiest_display.columns = ['Course Name', 'Average GPA']
        st.table(easiest_display)
    else:
        st.warning("No data found for the Hall of Fame.")

if __name__ == "__main__":
    main()
