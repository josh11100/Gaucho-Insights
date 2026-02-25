import streamlit as st
import pandas as pd
import os
import sqlite3
import plotly.express as px

# 1. Database Queries Import
try:
    from queries import (
        GET_RECENT_LECTURES, 
        GET_EASIEST_LOWER_DIV, 
        GET_EASIEST_UPPER_DIV, 
        GET_EASIEST_DEPTS, 
        GET_BEST_GE_PROFS
    )
except ImportError:
    st.error("❌ 'queries.py' missing! Please ensure it is in the same folder.")
    st.stop()

# 2. Logic File Imports
try:
    import pstat_logic
    import cs_logic
    import mcdb_logic
    import chem_logic
except ImportError as e:
    st.error(f"❌ Logic File Missing: {e}")
    st.stop()

st.set_page_config(page_title="Gaucho Insights", layout="wide")

@st.cache_data
def load_and_query_data():
    csv_path = os.path.join('data', 'courseGrades.csv')
    rmp_path = os.path.join('data', 'rmp_ratings.csv')
    
    if not os.path.exists(csv_path):
        st.error(f"❌ Main CSV not found at {csv_path}")
        st.stop()
        
    df_raw = pd.read_csv(csv_path)
    
    # --- SANITIZATION (The Nuke Fix) ---
    # Clean headers
    df_raw.columns = [str(c).strip() for c in df_raw.columns]
    
    # Clean string columns using .apply to avoid AttributeError
    def force_clean(x):
        return str(x).strip().upper()

    df_raw['instructor'] = df_raw['instructor'].apply(force_clean)
    df_raw['quarter'] = df_raw['quarter'].apply(force_clean)
    df_raw['dept'] = df_raw['dept'].apply(lambda x: str(x).strip().upper())
    df_raw['course'] = df_raw['course'].apply(lambda x: " ".join(str(x).split()).strip().upper())
    
    # Course Number for sorting
    df_raw['course_num'] = df_raw['course'].str.extract(r'(\d+)').astype(float).fillna(0)
    
    # Quarter Ranking logic
    q_order = {'FALL': 4, 'SUMMER': 3, 'SPRING': 2, 'WINTER': 1}
    def split_q_rank(q_val):
        parts = q_val.split()
        return q_order.get(parts[0], 0) if len(parts) > 0 else 0
    
    def split_q_year(q_val):
        parts = q_val.split()
        if len(parts) > 1 and parts[1].isdigit():
            return int(parts[1])
        return 0

    df_raw['q_rank'] = df_raw['quarter'].apply(split_q_rank)
    df_raw['q_year'] = df_raw['quarter'].apply(split_q_year)

    # --- RMP INTEGRATION ---
    if os.path.exists(rmp_path):
        try:
            rmp_df = pd.read_csv(rmp_path)
            rmp_df.columns = [str(c).strip() for c in rmp_df.columns]
            
            # Key for RMP: Last name from "First Last"
            rmp_df['match_key'] = rmp_df['instructor'].apply(lambda x: str(x).split()[-1].upper() if len(str(x).split()) > 0 else "")
            rmp_df['rmp_rating'] = pd.to_numeric(rmp_df['rmp_rating'], errors='coerce')
            rmp_df = rmp_df.sort_values('rmp_rating', ascending=False).drop_duplicates('match_key')
            
            # Key for Grades: Last name from "Last F"
            df_raw['match_key'] = df_raw['instructor'].apply(lambda x: str(x).split()[0].upper() if len(str(x).split()) > 0 else "")
            
            df_raw = pd.merge(df_raw, rmp_df[['match_key', 'rmp_rating']], on="match_key", how="left")
            df_raw = df_raw.drop(columns=['match_key'])
        except Exception as e:
            st.sidebar.warning(f"RMP Link failed: {e}")

    # --- SQLITE WORKFLOW ---
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    df_raw.to_sql('courses', conn, index=False, if_exists='replace')
    
    df_sorted = pd.read_sql_query(GET_RECENT_LECTURES, conn)
    lower_div_df = pd.read_sql_query(GET_EASIEST_LOWER_DIV, conn)
    upper_div_df = pd.read_sql_query(GET_EASIEST_UPPER_DIV, conn)
    dept_df = pd.read_sql_query(GET_EASIEST_DEPTS, conn)
    ge_profs_df = pd.read_sql_query(GET_BEST_GE_PROFS, conn)
    
    conn.close()
    return df_sorted, lower_div_df, upper_div_df, dept_df, ge_profs_df

def main():
    st.title("(｡•̀ᴗ-)✧ Gaucho Insights: UCSB Grade Distribution")
    
    # Load Data
    df, lower_div_df, upper_div_df, dept_df, ge_profs_df = load_and_query_data()

    # --- LEADERBOARDS ---
    with st.expander("°˖✧◝(⁰▿⁰)◜✧˖° View University Leaderboards", expanded=False):
        tab1, tab2, tab3, tab4 = st.tabs(["🐣 Lower Div", "🎓 Upper Div", "🏢 Depts", "👨‍🏫 Best GE Profs"])
        with tab1: st.table(lower_div_df.rename(columns={'course': 'Course', 'mean_gpa': 'Avg GPA'}))
        with tab2: st.table(upper_div_df.rename(columns={'course': 'Course', 'mean_gpa': 'Avg GPA'}))
        with tab3: st.table(dept_df.rename(columns={'dept': 'Department', 'dept_avg_gpa': 'Avg GPA', 'total_records': 'Count'}))
        with tab4: st.table(ge_profs_df.rename(columns={'instructor': 'Professor', 'avg_instructor_gpa': 'Avg GPA'}))

    st.divider()

    # --- SIDEBAR ---
    st.sidebar.header("🔍 Search Filters")
    mode = st.sidebar.selectbox("Choose Department", ["All Departments", "PSTAT", "CS", "MCDB", "CHEM"])
    course_query = st.sidebar.text_input("Course Number (e.g., 120A)", "").strip().upper()
    prof_query = st.sidebar.text_input("Instructor Name (e.g., SOLIS)", "").strip().upper()
    
    prefix_map = {"PSTAT": "PSTAT", "CS": "CMPSC", "MCDB": "MCDB", "CHEM": "CHEM"}
    data = df.copy()

    # Apply Logics
    if mode == "PSTAT": data = pstat_logic.process_pstat(data)
    elif mode == "CS": data = cs_logic.process_cs(data)
    elif mode == "MCDB": data = mcdb_logic.process_mcdb(data)
    elif mode == "CHEM": data = chem_logic.process_chem(data)

    # Filtering
    if course_query:
        pattern = rf"\b{course_query}\b" if mode == "All Departments" else rf"{prefix_map[mode]}\s+{course_query}\b"
        data = data[data['course'].str.contains(pattern, case=False, na=False, regex=True)]

    if prof_query:
        data = data[data['instructor'].str.contains(prof_query, case=False, na=False)]

    # --- DISPLAY ---
    st.header(f"Results for {mode}")
    if not data.empty:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Avg GPA", f"{data['avgGPA'].mean():.2f}")
        m2.metric("Classes", len(data))
        m3.metric("Professors", len(data['instructor'].unique()))
        
        if 'rmp_rating' in data.columns:
            avg_rmp = data['rmp_rating'].dropna().mean()
            m4.metric("RMP Rating", f"{avg_rmp:.1f}/5.0" if not pd.isna(avg_rmp) else "N/A")

        st.dataframe(data.drop(columns=['q_year', 'q_rank', 'course_num'], errors='ignore'), use_container_width=True)
        
        if len(data['instructor'].unique()) > 1:
            st.subheader("Instructor Comparison")
            st.bar_chart(data.groupby('instructor')['avgGPA'].mean().sort_values())
    else:
        st.info("No records found. Try adjusting filters!")

if __name__ == "__main__":
    main()
