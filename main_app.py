import streamlit as st
import pandas as pd

# The imports are now direct since the files are in the same folder
try:
    from pstat_logic import process_pstat
    from cs_logic import process_cs
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.info("Make sure pstat_logic.py and cs_logic.py are in the same folder as this file.")
    st.stop()

st.set_page_config(page_title="Gaucho Insights", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('courseGrades.csv')
    df['dept'] = df['dept'].str.strip()
    # Clean up weird spacing in course names (e.g. 'PSTAT   10' -> 'PSTAT 10')
    df['course'] = df['course'].str.replace(r'\s+', ' ', regex=True).str.strip()
    return df

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
        dept_prefix = "CMPSC"
        data = process_cs(df)

    # --- THE SEARCH FIX ---
    if course_query:
        target = f"{dept_prefix} {course_query.upper()}"
        # Using '==' ensures PSTAT 10 does NOT match PSTAT 110
        data = data[data['course'] == target]
        
        if data.empty:
            st.warning(f"No exact match found for '{target}'.")

    st.header(f"Results for {dept_prefix}")
    if not data.empty:
        st.metric("Average GPA", f"{data['avgGPA'].mean():.2f}")
        st.dataframe(data, use_container_width=True)
        
        st.subheader("Professor Comparison")
        prof_chart = data.groupby('instructor')['avgGPA'].mean().sort_values()
        st.bar_chart(prof_chart)
    else:
        st.info("Enter a course number in the sidebar to begin.")

if __name__ == "__main__":
    main()
