import streamlit as st
import pandas as pd
import os

# 1. Imports
try:
    from pstat_logic import process_pstat
    from cs_logic import process_cs
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.stop()

st.set_page_config(page_title="Gaucho Insights", layout="wide")

@st.cache_data
def load_data():
    # Points to your 'data' folder
    csv_path = os.path.join('data', 'courseGrades.csv')
    
    if not os.path.exists(csv_path):
        st.error(f"File not found at {csv_path}")
        st.stop()
        
    df = pd.read_csv(csv_path)
    
    # --- CLEANING & SORTING LOGIC ---
    df['dept'] = df['dept'].str.strip()
    df['course'] = df['course'].str.replace(r'\s+', ' ', regex=True).str.strip()
    
    # Create a helper column to sort Quarters (Winter < Spring < Summer < Fall)
    q_map = {'WINTER': 1, 'SPRING': 2, 'SUMMER': 3, 'FALL': 4}
    
    # Split "WINTER 2024" into ["WINTER", "2024"]
    quarter_split = df['quarter'].str.split(' ', expand=True)
    df['q_name'] = quarter_split[0]
    df['q_year'] = pd.to_numeric(quarter_split[1])
    df['q_val'] = df['q_name'].map(q_map)
    
    # Sort by Year (Descending) then Quarter Value (Descending)
    df = df.sort_values(by=['q_year', 'q_val'], ascending=False)
    
    # Remove the helper columns before returning
    return df.drop(columns=['q_name', 'q_year', 'q_val'])

def main():
    st.title("📊 Gaucho Insights: UCSB Grade Distribution")
    
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return

    st.sidebar.header("Navigation")
    mode = st.sidebar.selectbox("Choose Department", ["PSTAT Analysis", "CS Analysis"])
    course_query = st.sidebar.text_input("Enter Course Number (e.g., 10, 120A)", "").strip()

    if mode == "PSTAT Analysis":
        dept_prefix = "PSTAT"
        data = process_pstat(df)
    else:
        dept_prefix = "CMPSC" # Or "CS" depending on your CSV
        data = process_cs(df)

    if course_query:
        target = f"{dept_prefix} {course_query.upper()}"
        data = data[data['course'] == target]
        
        if data.empty:
            st.warning(f"No exact match found for '{target}'.")

    st.header(f"Results for {dept_prefix} (Sorted by Most Recent)")
    if not data.empty:
        # Metrics
        st.metric("Average GPA", f"{data['avgGPA'].mean():.2f}")
        
        # Displaying the DataFrame - it is already sorted from load_data
        st.dataframe(data, use_container_width=True)
        
        # Chart
        st.subheader("Professor Comparison")
        prof_chart = data.groupby('instructor')['avgGPA'].mean().sort_values()
        st.bar_chart(prof_chart)
    else:
        st.info("Enter a course number in the sidebar to begin.")

if __name__ == "__main__":
    main()
