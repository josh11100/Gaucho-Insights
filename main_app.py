import streamlit as st
import pandas as pd
import os

# 1. Imports - Make sure you created mcdb_logic.py and chem_logic.py!
try:
    from pstat_logic import process_pstat
    from cs_logic import process_cs
    from mcdb_logic import process_mcdb
    from chem_logic import process_chem
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.info("Ensure all .py logic files (pstat, cs, mcdb, chem) are in the root folder.")
    st.stop()

st.set_page_config(page_title="Gaucho Insights", layout="wide")

@st.cache_data
def load_data():
    csv_path = os.path.join('data', 'courseGrades.csv')
    if not os.path.exists(csv_path):
        st.error(f"File not found at {csv_path}")
        st.stop()
        
    df = pd.read_csv(csv_path)
    df['dept'] = df['dept'].str.strip()
    df['course'] = df['course'].str.replace(r'\s+', ' ', regex=True).str.strip()
    
    # Chronological Sorting (Recent First)
    q_map = {'WINTER': 1, 'SPRING': 2, 'SUMMER': 3, 'FALL': 4}
    df['temp_q'] = df['quarter'].str.upper().str.split(' ')
    df['q_year'] = pd.to_numeric(df['temp_q'].str[1])
    df['q_val'] = df['temp_q'].str[0].map(q_map)
    df = df.sort_values(by=['q_year', 'q_val'], ascending=False)
    
    return df.drop(columns=['temp_q', 'q_year', 'q_val'])

def main():
    st.title("📊 Gaucho Insights: UCSB Grade Distribution")
    
    df = load_data()

    # --- THE TASK BAR (SIDEBAR) ---
    st.sidebar.header("Department Selection")
    
    # Adding MCDB and CHEM to the dropdown menu
    options = ["PSTAT", "CS", "MCDB", "CHEM", "All Departments"]
    mode = st.sidebar.selectbox("Choose Department", options)
    
    # Mapping the Sidebar labels to the actual Department Codes in your CSV
    prefix_map = {
        "PSTAT": "PSTAT", 
        "CS": "CMPSC",   # Change to "CS" if your CSV uses that instead
        "MCDB": "MCDB", 
        "CHEM": "CHEM"
    }
    
    # Dynamic Search Input
    if mode == "All Departments":
        st.sidebar.write("🔍 **Global Search**")
        course_query = st.sidebar.text_input("Full Name (e.g., MATH 3A)", "").strip().upper()
        data = df.copy()
    else:
        st.sidebar.write(f"🔍 **{mode} Search**")
        example = "1A" if mode == "CHEM" or mode == "MCDB" else "10"
        course_query = st.sidebar.text_input(f"Enter Course Number (e.g., {example})", "").strip().upper()
        
        # Route to the correct logic file
        if mode == "PSTAT": data = process_pstat(df)
        elif mode == "CS": data = process_cs(df)
        elif mode == "MCDB": data = process_mcdb(df)
        elif mode == "CHEM": data = process_chem(df)

    # --- FILTERING LOGIC ---
    if course_query:
        if mode == "All Departments":
            data = data[data['course'] == course_query]
        else:
            target = f"{prefix_map[mode]} {course_query}"
            data = data[data['course'] == target]
        
        if data.empty:
            st.warning(f"No match for '{course_query}' in {mode}. Try another number.")

    # --- DISPLAY ---
    st.header(f"Results: {mode}")
    if not data.empty:
        st.metric("Avg GPA", f"{data['avgGPA'].mean():.2f}")
        st.dataframe(data, use_container_width=True)
        
        st.subheader("Professor GPA Comparison")
        prof_chart = data.groupby('instructor')['avgGPA'].mean().sort_values()
        st.bar_chart(prof_chart)
    else:
        st.info(f"Please enter a course number to see the {mode} distribution.")

if __name__ == "__main__":
    main()
