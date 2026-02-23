import streamlit as st
import pandas as pd
import os

# 1. Imports
try:
    from pstat_logic import process_pstat
    from cs_logic import process_cs
    from mcdb_logic import process_mcdb
    from chem_logic import process_chem
except ImportError as e:
    st.error(f"Logic File Missing: {e}")
    st.stop()

st.set_page_config(page_title="Gaucho Insights", layout="wide")

@st.cache_data
def load_data():
    # 1. Define the variable FIRST
    csv_path = os.path.join('data', 'courseGrades.csv')
    
    # 2. Check if it exists (Safety check)
    if not os.path.exists(csv_path):
        st.error(f"File not found at {csv_path}")
        st.stop()
        
    # 3. NOW you can use it
    df = pd.read_csv(csv_path)
    
    # ... the rest of your cleaning and sorting code
    return df
def main():
    st.title("📊 Gaucho Insights: UCSB Grade Distribution")
    
    df = load_data()

    # --- SIDEBAR ---
    st.sidebar.header("Department Selection")
    options = ["PSTAT", "CS", "MCDB", "CHEM", "All Departments"]
    mode = st.sidebar.selectbox("Choose Department", options)
    
    prefix_map = {"PSTAT": "PSTAT", "CS": "CMPSC", "MCDB": "MCDB", "CHEM": "CHEM"}
    
    if mode == "All Departments":
        course_query = st.sidebar.text_input("Global Search (e.g. MATH 3A)", "").strip().upper()
        data = df.copy()
    else:
        course_query = st.sidebar.text_input(f"Enter {mode} Number (e.g. 1A, 120)", "").strip().upper()
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

    # --- DISPLAY ---
    st.header(f"Viewing: {mode}")
    
    if not data.empty:
        # Layout metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Avg GPA", f"{data['avgGPA'].mean():.2f}")
        with col2:
            st.metric("Classes Found", len(data['course'].unique()))
        with col3:
            st.metric("Total Records", len(data))

        st.dataframe(data, use_container_width=True)
        
        # Comparison Chart
        st.subheader("Instructor Comparison")
        prof_chart = data.groupby('instructor')['avgGPA'].mean().sort_values()
        st.bar_chart(prof_chart)
    else:
        st.info("Search for a course to begin.")

if __name__ == "__main__":
    main()
