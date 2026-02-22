import streamlit as st
import pandas as pd

# We removed the 'processors.' prefix because the files are now in the same folder
try:
    from pstat_logic import process_pstat
    from cs_logic import process_cs
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.stop()

# Page Configuration
st.set_page_config(page_title="Gaucho Insights", layout="wide")

@st.cache_data
def load_data():
    """Load and clean data once."""
    df = pd.read_csv('courseGrades.csv')
    df['dept'] = df['dept'].str.strip()
    # This cleans up the course names so 'PSTAT   10' becomes 'PSTAT 10'
    df['course'] = df['course'].str.replace(r'\s+', ' ', regex=True).str.strip()
    return df

def main():
    st.title("📊 Gaucho Insights: UCSB Grade Distribution")
    
    try:
        df = load_data()
    except FileNotFoundError:
        st.error("CSV file 'courseGrades.csv' not found. Please upload it to your GitHub.")
        return

    # Sidebar Navigation
    st.sidebar.header("Navigation")
    mode = st.sidebar.selectbox("Choose Department", ["PSTAT Analysis", "CS Analysis"])
    course_query = st.sidebar.text_input("Enter Course Number (e.g., 10, 120A)", "").strip()

    # Routing based on selection
    if mode == "PSTAT Analysis":
        dept_prefix = "PSTAT"
        data = process_pstat(df)
    else:
        dept_prefix = "CMPSC"
        data = process_cs(df)

    # --- EXACT MATCH LOGIC ---
    if course_query:
        # Construct exact string: e.g., "PSTAT 10"
        target = f"{dept_prefix} {course_query.upper()}"
        
        # This fixes the "10 vs 110" bug by using '=='
        data = data[data['course'] == target]
        
        if data.empty:
            st.warning(f"No exact match found for '{target}'. Check your course number.")

    # Display Results
    st.header(f"Results for {dept_prefix}")
    if not data.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Sections", len(data))
        with col2:
            st.metric("Average GPA", f"{data['avgGPA'].mean():.2f}")

        st.dataframe(data, use_container_width=True)
        
        # Simple Visualization
        st.subheader("Professor Comparison")
        prof_chart = data.groupby('instructor')['avgGPA'].mean().sort_values()
        st.bar_chart(prof_chart)
    else:
        st.info("Use the sidebar to search for a specific course (e.g., type '10' for PSTAT 10).")

if __name__ == "__main__":
    main()
