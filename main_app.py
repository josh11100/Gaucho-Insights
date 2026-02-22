import streamlit as st
import pandas as pd
import os

# 1. Direct Imports
try:
    from pstat_logic import process_pstat
    from cs_logic import process_cs
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.stop()

st.set_page_config(page_title="Gaucho Insights", layout="wide")

@st.cache_data
def load_data():
    # Points to the 'data' folder
    csv_path = os.path.join('data', 'courseGrades.csv')
    
    if not os.path.exists(csv_path):
        st.error(f"File not found at {csv_path}")
        st.stop()
        
    df = pd.read_csv(csv_path)
    
    # --- CLEANING ---
    df['dept'] = df['dept'].str.strip()
    df['course'] = df['course'].str.replace(r'\s+', ' ', regex=True).str.strip()
    
    # --- CHRONOLOGICAL SORTING LOGIC ---
    # Define the order of quarters within a year
    q_map = {'WINTER': 1, 'SPRING': 2, 'SUMMER': 3, 'FALL': 4}
    
    # Split "WINTER 2024" into parts and make them uppercase for consistency
    # This creates temporary columns for sorting
    df['temp_q'] = df['quarter'].str.upper().str.split(' ')
    df['q_name'] = df['temp_q'].str[0]
    df['q_year'] = pd.to_numeric(df['temp_q'].str[1])
    df['q_val'] = df['q_name'].map(q_map)
    
    # Sort by Year (Descending) and then Quarter (Descending)
    # This puts FALL 2024 above WINTER 2024, and 2024 above 2023
    df = df.sort_values(by=['q_year', 'q_val'], ascending=False)
    
    # Drop the temporary helper columns before returning the data
    df = df.drop(columns=['temp_q', 'q_name', 'q_year', 'q_val'])
    
    return df

def main():
    st.title("📊 Gaucho Insights: UCSB Grade Distribution")
    
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Error processing data: {e}")
        return

    st.sidebar.header("Navigation")
    mode = st.sidebar.selectbox("Choose Department", ["PSTAT Analysis", "CS Analysis"])
    course_query = st.sidebar.text_input("Enter Course Number (e.g., 10, 120A)", "").strip()

    if mode == "PSTAT Analysis":
        dept_prefix = "PSTAT"
        data = process_pstat(df)
    else:
        # Check your CSV to see if CS is listed as 'CMPSC' or 'CS'
        dept_prefix = "CMPSC" 
        data = process_cs(df)

    if course_query:
        target = f"{dept_prefix} {course_query.upper()}"
        # Exact match logic (solves the 10 vs 110 bug)
        data = data[data['course'] == target]
        
        if data.empty:
            st.warning(f"No exact match found for '{target}'.")

    st.header(f"Results for {dept_prefix}")
    if not data.empty:
        # Show recent quarters first in the table
        st.metric("Total Records Found", len(data))
        st.dataframe(data, use_container_width=True)
        
        # Visualization
        st.subheader("Professor Average GPA")
        prof_chart = data.groupby('instructor')['avgGPA'].mean().sort_values()
        st.bar_chart(prof_chart)
    else:
        st.info("Search for a course number in the sidebar to see results.")

if __name__ == "__main__":
    main()
