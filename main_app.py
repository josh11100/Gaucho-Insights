import streamlit as st
import pandas as pd
import os

# 1. Direct Imports (Since files are now in the root folder)
try:
    from pstat_logic import process_pstat
    from cs_logic import process_cs
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.info("Check if pstat_logic.py and cs_logic.py are in the root folder on GitHub.")
    st.stop()

st.set_page_config(page_title="Gaucho Insights", layout="wide")

@st.cache_data
def load_data():
    # Diagnostic: This will show us exactly what the Cloud Server sees
    # You can remove these next 2 lines once the CSV is working
    if not os.path.exists('courseGrades.csv'):
        st.warning(f"Current Directory Files: {os.listdir('.')}")
    
    df = pd.read_csv('courseGrades.csv')
    df['dept'] = df['dept'].str.strip()
    # Clean up spacing: 'PSTAT   10' -> 'PSTAT 10'
    df['course'] = df['course'].str.replace(r'\s+', ' ', regex=True).str.strip()
    return df

def main():
    st.title("📊 Gaucho Insights: UCSB Grade Distribution")
    
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        st.info("Ensure 'courseGrades.csv' is in your main GitHub folder (not inside a subfolder).")
        return

    # Sidebar
    st.sidebar.header("Navigation")
    mode = st.sidebar.selectbox("Choose Department", ["PSTAT Analysis", "CS Analysis"])
    course_query = st.sidebar.text_input("Enter Course Number (e.g., 10, 120A)", "").strip()

    if mode == "PSTAT Analysis":
        dept_prefix = "PSTAT"
        data = process_pstat(df)
    else:
        dept_prefix = "CMPSC"
        data = process_cs(df)

    # --- THE SEARCH FIX (EXACT MATCH) ---
    if course_query:
        target = f"{dept_prefix} {course_query.upper()}"
        # Using '==' prevents "10" from matching "110"
        data = data[data['course'] == target]
        
        if data.empty:
            st.warning(f"No exact match found for '{target}'.")

    # Display Results
    st.header(f"Results for {dept_prefix}")
    if not data.empty:
        st.metric("Average GPA", f"{data['avgGPA'].mean():.2f}")
        st.dataframe(data, use_container_width=True)
        
        st.subheader("Professor Comparison")
        prof_chart = data.groupby('instructor')['avgGPA'].mean().sort_values()
        st.bar_chart(prof_chart)
    else:
        st.info("Use the sidebar to search for a specific course number.")

if __name__ == "__main__":
    main()
