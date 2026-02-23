import streamlit as st
import pandas as pd
import os
import sqlite3
from queries import GET_RECENT_LECTURES, GET_EASIEST_CLASSES, GET_EASIEST_LOWER_DIV

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
    if not os.path.exists(csv_path):
        st.error("CSV file not found.")
        st.stop()
        
    df_raw = pd.read_csv(csv_path)
    
    # --- PRE-PROCESSING ---
    df_raw['dept'] = df_raw['dept'].str.strip()
    df_raw['course'] = df_raw['course'].str.replace(r'\s+', ' ', regex=True).str.strip()
    df_raw['course_num'] = df_raw['course'].str.extract(r'(\d+)').astype(float)
    
    q_order = {'FALL': 4, 'SUMMER': 3, 'SPRING': 2, 'WINTER': 1}
    temp_split = df_raw['quarter'].str.upper().str.split(' ')
    df_raw['q_year'] = pd.to_numeric(temp_split.str[1], errors='coerce').fillna(0).astype(int)
    df_raw['q_rank'] = temp_split.str[0].map(q_order).fillna(0).astype(int)

    # --- SQLITE ENGINE ---
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    # Exclude list columns that crash SQLite
    df_raw.drop(columns=['temp_split'], errors='ignore').to_sql('courses', conn, index=False, if_exists='replace')
    
    # Run the three queries
    df_sorted = pd.read_sql_query(GET_RECENT_LECTURES, conn)
    easiest_df = pd.read_sql_query(GET_EASIEST_CLASSES, conn)
    lower_div_df = pd.read_sql_query(GET_EASIEST_LOWER_DIV, conn)
    
    conn.close()
    return df_sorted, easiest_df, lower_div_df

def main():
    st.title("📊 Gaucho Insights: UCSB Grade Distribution")
    st.markdown("Historical data powered by SQLite. *Outliers (4.0 avg) and Independent Studies (198+) excluded.*")
    
    # Get all three DataFrames
    df, easiest_df, lower_div_df = load_and_query_data()

    # --- SIDEBAR ---
    st.sidebar.header("Navigation")
    options = ["PSTAT", "CS", "MCDB", "CHEM", "All Departments"]
    mode = st.sidebar.selectbox("Choose Department", options)
    
    prefix_map = {"PSTAT": "PSTAT", "CS": "CMPSC", "MCDB": "MCDB", "CHEM": "CHEM"}
    
    if mode == "All Departments":
        course_query = st.sidebar.text_input("Global Search (e.g., MATH 3A)", "").strip().upper()
        data = df.copy()
    else:
        course_query = st.sidebar.text_input(f"Enter {mode} Number (e.g., 10)", "").strip().upper()
        if mode == "PSTAT": data = process_pstat(df)
        elif mode == "CS": data = process_cs(df)
        elif mode == "MCDB": data = process_mcdb(df)
        elif mode == "CHEM": data = process_chem(df)

    # --- SEARCH FILTERING ---
    if course_query:
        if mode == "All Departments":
            data = data[data['course'].str.contains(course_query, case=False, na=False)]
        else:
            pattern = rf"{prefix_map[mode]}\s+{course_query}"
            data = data[data['course'].str.contains(pattern, case=False, na=False, regex=True)]

    # --- MAIN DISPLAY ---
    st.header(f"Results for {mode}")
    
    if not data.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Avg GPA", f"{data['avgGPA'].mean():.2f}")
        m2.metric("Classes Found", len(data))
        m3.metric("Professors", len(data['instructor'].unique()))

        st.subheader("Historical Records (Newest First)")
        display_df = data.drop(columns=['q_year', 'q_rank', 'course_num'], errors='ignore')
        st.dataframe(display_df, use_container_width=True)
        
        st.subheader("Instructor Performance")
        prof_chart = data.groupby('instructor')['avgGPA'].mean().sort_values()
        st.bar_chart(prof_chart)
    else:
        st.info("Enter a course number in the sidebar to begin searching.")

    # --- LEADERBOARDS ---
    st.divider()
    st.subheader("🏆 Course Leaderboards")
    
    tab1, tab2 = st.tabs(["Top 10 (All Levels)", "Top 10 (Lower Div < 98)"])
    
    with tab1:
        st.write("Easiest overall courses based on historical averages:")
        t1_display = easiest_df.copy()
        t1_display.columns = ['Course Name', 'Average GPA']
        st.table(t1_display)

    with tab2:
        st.write("Easiest introductory and GE courses:")
        t2_display = lower_div_df.copy()
        t2_display.columns = ['Course Name', 'Average GPA']
        st.table(t2_display)

if __name__ == "__main__":
    main()
