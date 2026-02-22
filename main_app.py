import streamlit as st
import pandas as pd
import sys
import os

# This forces the app to look in the current directory for the processors folder
sys.path.append(os.path.dirname(__file__))

from processors.pstat_logic import process_pstat
from processors.cs_logic import process_cs
# Page Configuration
st.set_page_config(page_title="Gaucho Insights", layout="wide")

@st.cache_data
def load_data():
    """Load and clean data once to save memory and speed."""
    # Note: Ensure courseGrades.csv is in the same folder or update path
    df = pd.read_csv('courseGrades.csv')
    
    # CLEANING: This is the most important part for exact matching
    # 1. Strip leading/trailing spaces from all columns
    df['dept'] = df['dept'].str.strip()
    
    # 2. Fix 'course' column: Remove extra middle spaces and strip ends
    # This turns "PSTAT   10" into "PSTAT 10"
    df['course'] = df['course'].str.replace(r'\s+', ' ', regex=True).str.strip()
    
    return df

def main():
    st.title("📊 Gaucho Insights: UCSB Grade Distribution")
    
    # Load the cleaned data
    try:
        df = load_data()
    except FileNotFoundError:
        st.error("CSV file not found. Please ensure 'courseGrades.csv' is in your directory.")
        return

    # Sidebar Navigation
    st.sidebar.header("Navigation")
    mode = st.sidebar.selectbox("Choose Department", ["PSTAT Analysis", "CS Analysis"])

    # Sidebar Filters
    st.sidebar.subheader("Filter by Course")
    # We strip the user input immediately
    course_query = st.sidebar.text_input("Enter Course Number (e.g., 10, 120A, 5A)", "").strip()

    # Determine Department Prefix
    if mode == "PSTAT Analysis":
        dept_prefix = "PSTAT"
        data = process_pstat(df)
    else:
        dept_prefix = "CMPSC" # Or "CS" depending on your CSV's naming
        data = process_cs(df)

    # --- THE EXACT MATCH FIX ---
    if course_query:
        # Construct the target string (e.g., "PSTAT 10")
        # .upper() handles users typing '120a' instead of '120A'
        target_course = f"{dept_prefix} {course_query.upper()}"
        
        # We use == (Equality) instead of .str.contains() 
        # This prevents "10" from catching "109", "110", etc.
        data = data[data['course'] == target_course]
        
        if data.empty:
            st.warning(f"No exact match found for '{target_course}'. Please check the course number.")

    # --- DISPLAY RESULTS ---
    st.header(f"Results for {dept_prefix}")
    
    if not data.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Sections", len(data))
        with col2:
            st.metric("Average GPA", f"{data['avgGPA'].mean():.2f}")
        with col3:
            st.metric("Max GPA Found", f"{data['avgGPA'].max():.2f}")

        # Interactive Data Table
        st.dataframe(data, use_container_width=True)

        # Basic Visual: GPA by Instructor
        st.subheader("Professor Comparison")
        prof_chart = data.groupby('instructor')['avgGPA'].mean().sort_values()
        st.bar_chart(prof_chart)
    else:
        st.info("Use the sidebar to search for a specific course number.")

if __name__ == "__main__":
    main()
