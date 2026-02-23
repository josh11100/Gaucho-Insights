import streamlit as st
import pandas as pd
import os

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
        
    df = pd.read_csv(csv_path)
    
    # --- CLEANING & FORMATTING ---
    df['dept'] = df['dept'].str.strip()
    # Normalize spacing: 'PSTAT  120A' -> 'PSTAT 120A'
    df['course'] = df['course'].str.replace(r'\s+', ' ', regex=True).str.strip()
    
    # --- OUTLIER FILTER (Remove 198, 199, 200+) ---
    # Extract the first set of digits from the course string
    df['course_num'] = df['course'].str.extract(r'(\d+)').astype(float)
    # Keep only standard undergraduate lecture/lab courses
    df = df[df['course_num'] < 198]
    
    # --- CHRONOLOGICAL SORTING (Newest at Top) ---
    q_order = {'FALL': 4, 'SUMMER': 3, 'SPRING': 2, 'WINTER': 1}
    
    # Split 'FALL 2024' into ['FALL', '2024']
    df['temp_split'] = df['quarter'].str.upper().str.split(' ')
    # Create helper columns for sorting
    df['q_year'] = pd.to_numeric(df['temp_split'].str[1])
    df['q_rank'] = df['temp_split'].str[0].map(q_order)
    
    # Sort Descending (True for Year, True for Quarter Rank)
    df = df.sort_values(by=['q_year', 'q_rank'], ascending=[False, False])
    
    # Cleanup helper columns before returning to app
    return df.drop(columns=['course_num', 'temp_split', 'q_year', 'q_rank'])

def main():
    st.title("📊 Gaucho Insights: UCSB Grade Distribution")
    st.markdown("Discover historical grade trends for undergraduate courses.")
    
    df = load_data()

    # --- SIDEBAR SELECTION ---
    st.sidebar.header("Navigation")
    options = ["PSTAT", "CS", "MCDB", "CHEM", "All Departments"]
    mode = st.sidebar.selectbox("Choose Department", options)
    
    # Map selection to CSV codes
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
        
        # Route to logic processors
        if mode == "PSTAT": data = process_pstat(df)
        elif mode == "CS": data = process_cs(df)
        elif mode == "MCDB": data = process_mcdb(df)
        elif mode == "CHEM": data = process_chem(df)

    # --- FUZZY FILTERING ---
    if course_query:
        if mode == "All Departments":
            # Search anywhere in the course string
            data = data[data['course'].str.contains(course_query, case=False, na=False)]
        else:
            # Pattern matches Dept Prefix + Number (e.g., 'PSTAT 120')
            pattern = rf"{prefix_map[mode]}\s+{course_query}"
            data = data[data['course'].str.contains(pattern, case=False, na=False, regex=True)]

    # --- RESULTS DISPLAY ---
    st.header(f"Results for {mode}")
    
    if not data.empty:
        # Top-level stats
        m1, m2, m3 = st.columns(3)
        m1.metric("Avg GPA", f"{data['avgGPA'].mean():.2f}")
        m2.metric("Total Quarters", len(data))
        m3.metric("Unique Professors", len(data['instructor'].unique()))
        
        # Data Table
        st.subheader("Historical Records (Newest First)")
        st.dataframe(data, use_container_width=True)
        
        # Visualization
        st.subheader("Instructor GPA Comparison")
        prof_avg = data.groupby('instructor')['avgGPA'].mean().sort_values()
        st.bar_chart(prof_avg)
        
        # Export Option
        st.download_button(
            label="📥 Download Results as CSV",
            data=data.to_csv(index=False),
            file_name=f"{mode}_filtered_grades.csv",
            mime="text/csv"
        )
    else:
        st.info("Enter a course number in the sidebar to view data.")
        st.warning("Note: Courses numbered 198 and higher are hidden.")

if __name__ == "__main__":
    main()
