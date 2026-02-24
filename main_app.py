import streamlit as st
import pandas as pd
import os
import sqlite3
from queries import (
    GET_RECENT_LECTURES, 
    GET_EASIEST_LOWER_DIV, 
    GET_EASIEST_UPPER_DIV, 
    GET_EASIEST_DEPTS,  # Added missing comma here
    GET_BEST_GE_PROFS,    # Ensure this matches your name in queries.py
)

# ... (Logic Imports remain the same) ...

@st.cache_data
def load_and_query_data():
    csv_path = os.path.join('data', 'courseGrades.csv')
    if not os.path.exists(csv_path):
        st.error("CSV file not found.")
        st.stop()
        
    df_raw = pd.read_csv(csv_path)
    
    # --- PRE-PROCESSING ---
    df_raw['dept'] = df_raw['dept'].str.strip()
    df_raw['course'] = df_raw['course'].str.replace(r'\s+', ' ', regex=True).str.strip()
    df_raw['course_num'] = df_raw['course'].str.extract(r'(\d+)').astype(float)
    
    q_order = {'FALL': 4, 'SUMMER': 3, 'SPRING': 2, 'WINTER': 1}
    temp_split = df_raw['quarter'].str.upper().str.split(' ')
    df_raw['q_year'] = pd.to_numeric(temp_split.str[1], errors='coerce').fillna(0).astype(int)
    df_raw['q_rank'] = temp_split.str[0].map(q_order).fillna(0).astype(int)

    # --- SQLITE WORKFLOW ---
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    df_raw.drop(columns=['temp_split'], errors='ignore').to_sql('courses', conn, index=False, if_exists='replace')
    
    # Run all 5 queries
    df_sorted = pd.read_sql_query(GET_RECENT_LECTURES, conn)
    lower_div_df = pd.read_sql_query(GET_EASIEST_LOWER_DIV, conn)
    upper_div_df = pd.read_sql_query(GET_EASIEST_UPPER_DIV, conn)
    dept_df = pd.read_sql_query(GET_EASIEST_DEPTS, conn)
    ge_profs_df = pd.read_sql_query(GET_BEST_GE_PROFS, conn) # Added this query
    
    conn.close()
    # Return all 5 DataFrames
    return df_sorted, lower_div_df, upper_div_df, dept_df, ge_profs_df

def main():
    st.title("(｡•̀ᴗ-)✧ Gaucho Insights: UCSB Grade Distribution")
    
    # Load all 5 data sources (Unpack all 5 here!)
    df, lower_div_df, upper_div_df, dept_df, ge_profs_df = load_and_query_data()

    # --- LEADERBOARD EXPANDER ---
    with st.expander("°˖✧◝(⁰▿⁰)◜✧˖° View University Leaderboards", expanded=False):
        # Added the 4th tab for GE Professors
        tab1, tab2, tab3, tab4 = st.tabs([
            "(─‿‿─)♡ Lower Div", 
            "(⌒_⌒;) Upper Div", 
            "( ﾉ･o･ )ﾉ Depts",
            "(¬‿¬) Best GE Profs"
        ])
        
        with tab1:
            st.table(lower_div_df.rename(columns={'course': 'Course', 'mean_gpa': 'Avg GPA'}))
        with tab2:
            st.table(upper_div_df.rename(columns={'course': 'Course', 'mean_gpa': 'Avg GPA'}))
        with tab3:
            st.table(dept_df.rename(columns={'dept': 'Department', 'dept_avg_gpa': 'Avg GPA', 'total_records': 'Count'}))
        with tab4:
            st.table(ge_profs_df.rename(columns={'instructor': 'Professor', 'avg_instructor_gpa': 'Avg GPA', 'classes_taught': 'Records'}))
    st.divider()

    # --- SIDEBAR ---
    st.sidebar.header("Search Filters")
    options = ["PSTAT", "CS", "MCDB", "CHEM", "All Departments"]
    mode = st.sidebar.selectbox("Choose Department", options)
    
    prefix_map = {"PSTAT": "PSTAT", "CS": "CMPSC", "MCDB": "MCDB", "CHEM": "CHEM"}
    
    # Search logic
    if mode == "All Departments":
        course_query = st.sidebar.text_input("Global Search (e.g., MATH 3A)", "").strip().upper()
        data = df.copy() # df is already sorted by GET_RECENT_LECTURES
    else:
        course_query = st.sidebar.text_input(f"Enter {mode} Number (e.g., 10)", "").strip().upper()
        if mode == "PSTAT": data = process_pstat(df)
        elif mode == "CS": data = process_cs(df)
        elif mode == "MCDB": data = process_mcdb(df)
        elif mode == "CHEM": data = process_chem(df)

    # --- FILTERING ---
# --- FILTERING (Strict Number Matching) ---
    if course_query:
        if mode == "All Departments":
            # This regex looks for the query as a standalone word
            # Example: Searching "JAPAN 1" won't match "JAPAN 114"
            pattern = rf"\b{course_query}\b"
            data = data[data['course'].str.contains(pattern, case=False, na=False, regex=True)]
        else:
            # This regex looks for the specific Department Prefix + Exact Number
            # \s+ matches any space, \b matches the end of the number
            pattern = rf"{prefix_map[mode]}\s+{course_query}\b"
            data = data[data['course'].str.contains(pattern, case=False, na=False, regex=True)]

    # --- RESULTS DISPLAY (The main organized table) ---
    st.header(f"Results for {mode}")
    
    if not data.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Avg GPA", f"{data['avgGPA'].mean():.2f}")
        m2.metric("Classes Found", len(data))
        m3.metric("Professors", len(data['instructor'].unique()))

        st.subheader("Historical Records (Sorted by Most Recent)")
        # Show the data organized by your first SQL query
        display_df = data.drop(columns=['q_year', 'q_rank', 'course_num'], errors='ignore')
        st.dataframe(display_df, use_container_width=True)
        
        st.subheader("Instructor Performance")
        prof_chart = data.groupby('instructor')['avgGPA'].mean().sort_values()
        st.bar_chart(prof_chart)
    else:
        st.info("Adjust the sidebar filters to see results.")

if __name__ == "__main__":
    main()
