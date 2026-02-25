import streamlit as st
import pandas as pd
import os
import re

# Logic File Imports
try:
    import pstat_logic, cs_logic, mcdb_logic, chem_logic
except ImportError as e:
    st.error(f"❌ Logic File Missing: {e}")
    st.stop()

st.set_page_config(page_title="Gaucho Insights", layout="wide")

@st.cache_data
def load_data():
    csv_path = os.path.join('data', 'courseGrades.csv')
    if not os.path.exists(csv_path):
        st.error(f"❌ CSV not found at {csv_path}")
        st.stop()
        
    df = pd.read_csv(csv_path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # Simple Clean
    df['instructor'] = df['instructor'].astype(str).str.upper().str.strip()
    df['quarter'] = df['quarter'].astype(str).str.upper().str.strip()
    df['course'] = df['course'].astype(str).str.upper().str.strip()
    df['dept'] = df['dept'].astype(str).str.upper().str.strip()

    # Dynamic Year Extraction
    def extract_year(q_str):
        match = re.search(r'(\d{2,4})', q_str)
        if match:
            year_val = match.group(1)
            return int("20" + year_val) if len(year_val) == 2 else int(year_val)
        return 0

    df['year'] = df['quarter'].apply(extract_year)
    
    # Identify GPA column
    gpa_col = next((c for c in ['avggpa', 'avg_gpa', 'avg gpa'] if c in df.columns), 'avggpa')
    
    # Ensure numbers are numbers
    for col in [gpa_col, 'a', 'b', 'c', 'd', 'f']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    return df, gpa_col

def main():
    st.title("(｡•̀ᴗ-)✧ Gaucho Insights")
    
    full_df, gpa_col = load_data()

    # Sidebar Filters
    st.sidebar.header("🔍 Filters")
    mode = st.sidebar.selectbox("Department", ["All Departments", "PSTAT", "CS", "MCDB", "CHEM"])
    course_q = st.sidebar.text_input("Course #", "").strip().upper()
    prof_q = st.sidebar.text_input("Professor", "").strip().upper()
    
    # Filter Logic
    data = full_df.copy()
    if mode == "PSTAT": data = pstat_logic.process_pstat(data)
    elif mode == "CS": data = cs_logic.process_cs(data)
    elif mode == "MCDB": data = mcdb_logic.process_mcdb(data)
    elif mode == "CHEM": data = chem_logic.process_chem(data)

    if course_q: data = data[data['course'].str.contains(course_q, na=False)]
    if prof_q: data = data[data['instructor'].str.contains(prof_q, na=False)]

    if not data.empty:
        # Reorder Columns for the user: Course, Instructor, GPA, Year, Quarter, then Grades
        display_cols = ['course', 'instructor', gpa_col, 'year', 'quarter', 'a', 'b', 'c', 'd', 'f']
        existing = [c for c in display_cols if c in data.columns]
        
        final_df = data[existing].sort_values(by=['year', gpa_col], ascending=[False, False])
        
        # Clean up column headers for display
        final_df.columns = [c.replace('_', ' ').title() if c != gpa_col else 'Avg GPA' for c in final_df.columns]
        
        # Simple Metrics
        m1, m2 = st.columns(2)
        m1.metric("Avg GPA of Search", f"{data[gpa_col].mean():.2f}")
        m2.metric("Classes Found", len(data))

        # Show the data
        st.dataframe(final_df, use_container_width=True)
    else:
        st.info("No records found. Try adjusting your filters!")

if __name__ == "__main__":
    main()
