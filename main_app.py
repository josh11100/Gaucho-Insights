import streamlit as st
import pandas as pd
import os
import sqlite3
from queries import GET_RECENT_LECTURES

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
def load_data():
    csv_path = os.path.join('data', 'courseGrades.csv')
    
    if not os.path.exists(csv_path):
        st.error(f"File not found at {csv_path}. Ensure it is in the 'data' folder on GitHub.")
        st.stop()
        
    # Read raw data
    df_raw = pd.read_csv(csv_path)
    
    # --- PRE-PROCESSING FOR SQL ---
    df_raw['dept'] = df_raw['dept'].str.strip()
    df_raw['course'] = df_raw['course'].str.replace(r'\s+', ' ', regex=True).str.strip()
    
    # Extract numeric part for course filtering
    df_raw['course_num'] = df_raw['course'].str.extract(r'(\d+)').astype(float)
    
    # Create sort keys for the SQL engine
    q_order = {'FALL': 4, 'SUMMER': 3, 'SPRING': 2, 'WINTER': 1}
    df_raw['temp_split'] = df_raw['quarter'].str.upper().str.split(' ')
    df_raw['q_year'] = pd.to_numeric(df_raw['temp_split'].str[1])
    df_raw['q_rank'] = df_raw['temp_split'].str[0].map(q_order)

    # --- SQLITE WORKFLOW ---
    # Create connection to in-memory database
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    
    # Load the dataframe into a SQL table named 'courses'
    df_raw.to_sql('courses', conn, index=False, if_exists='replace')
    
    # Run the SQL query from queries.py
    df_final = pd.read_sql_query(GET_RECENT_LECTURES, conn)
    
    conn.close()
    
    # Cleanup helper columns used for sorting before returning
    return df_final.drop(columns=['course_num', 'temp_split', 'q_year', 'q_rank'], errors='ignore')

def main():
    st.title("📊 Gaucho Insights: UCSB Grade Distribution")
    st.markdown("Historical data powered by SQLite. Standard undergraduate courses only.")
    
    df = load_data()

    # --- SIDEBAR SELECTION ---
    st.sidebar.header("Navigation")
    options = ["PSTAT", "CS", "MCDB", "CHEM", "All Departments"]
    mode = st.sidebar.selectbox("Choose Department", options)
    
    prefix_map = {
        "PSTAT": "PSTAT", 
        "CS": "CMPSC", 
        "MCDB": "MCDB", 
        "CHEM": "CHEM"
    }
    
    # --- SEARCH LOGIC ---
    if mode == "All Departments":
        st.sidebar.info("Search full course name (e.g., MATH 3A)")
        course_query = st.sidebar.text_input("Global Search", "").strip().upper()
        data = df.copy()
    else:
        course_query = st.sidebar.text_input(f"Enter {mode} Number (e.g., 10, 120)", "").strip().upper()
        
        if mode == "PSTAT": data = process_pstat(df)
        elif mode == "CS": data = process_cs(df)
        elif mode == "MCDB": data = process_mcdb(df)
        elif mode == "CHEM": data = process_chem(df)

    # --- FUZZY FILTERING ---
    if course_query:
        if mode == "All Departments":
            data = data[data['course'].str.contains(course_query, case=False, na=False)]
        else:
            pattern = rf"{prefix_map[mode]}\s+{course_query}"
            data = data[data['course'].str.contains(pattern, case=False, na=False, regex=True)]

    # --- RESULTS DISPLAY ---
    st.header(f"Results for {mode}")
    
    if not data.empty:
        # Layout metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Avg GPA", f"{data['avgGPA'].mean():.2f}")
        with col2:
            st.metric("Classes Found", len(data))
        with col3:
            st.metric("Unique Professors", len(data['instructor'].unique()))

        # Data Table
        st.subheader("Historical Grades (Newest First)")
        st.dataframe(data, use_container_width=True)
        
        # Comparison Chart
        st.subheader("Instructor Performance")
        prof_chart = data.groupby('instructor')['avgGPA'].mean().sort_values()
        st.bar_chart(prof_chart)
        
        # Export Button
        st.download_button(
            label="📥 Download Results as CSV",
            data=data.to_csv(index=False),
            file_name=f"{mode}_grades.csv",
            mime="text/csv",
        )
    else:
        st.info("Enter a course to see historical grade distributions.")
        st.warning("Note: Graduate and research units (198+) are excluded.")

if __name__ == "__main__":
    main()
