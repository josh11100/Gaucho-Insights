import streamlit as st
import pandas as pd
import os
import sqlite3
import re

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
    st.error("❌ 'queries.py' missing!")
    st.stop()

# 2. Logic File Imports
try:
    import pstat_logic, cs_logic, mcdb_logic, chem_logic
except ImportError as e:
    st.error(f"❌ Logic File Missing: {e}")
    st.stop()

st.set_page_config(page_title="Gaucho Insights", layout="wide")

@st.cache_data
def load_and_query_data():
    csv_path = os.path.join('data', 'courseGrades.csv')
    rmp_path = os.path.join('data', 'rmp_ratings.csv')
    
    if not os.path.exists(csv_path):
        st.error(f"❌ CSV not found at {csv_path}")
        st.stop()
        
    df_raw = pd.read_csv(csv_path)
    df_raw.columns = [str(c).strip() for c in df_raw.columns]
    
    # --- SANITIZATION ---
    def force_clean(x):
        return str(x).strip().upper()

    df_raw['instructor'] = df_raw['instructor'].apply(force_clean)
    df_raw['quarter'] = df_raw['quarter'].apply(force_clean)
    df_raw['dept'] = df_raw['dept'].apply(lambda x: str(x).strip().upper())
    df_raw['course'] = df_raw['course'].apply(lambda x: " ".join(str(x).split()).strip().upper())
    
    # Ensure grade columns and GPA are numeric
    grade_cols = ['avgGPA', 'nLetterStudents', 'a', 'b', 'c', 'd', 'f']
    for col in grade_cols:
        if col in df_raw.columns:
            df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce').fillna(0)

    # --- YEAR & QUARTER LOGIC ---
    q_order = {'FALL': 4, 'SUMMER': 3, 'SPRING': 2, 'WINTER': 1}
    
    def extract_year(q_str):
        match = re.search(r'(\d{4})', q_str)
        return int(match.group(1)) if match else 0

    def extract_q_rank(q_str):
        for q_name in q_order:
            if q_name in q_str:
                return q_order[q_name]
        return 0

    df_raw['q_year'] = df_raw['quarter'].apply(extract_year)
    df_raw['q_rank'] = df_raw['quarter'].apply(extract_q_rank)
    df_raw['year'] = df_raw['q_year'] # For display
    df_raw['course_num'] = df_raw['course'].str.extract(r'(\d+)').astype(float).fillna(0)

    # --- RMP INTEGRATION ---
    if os.path.exists(rmp_path):
        try:
            rmp_df = pd.read_csv(rmp_path)
            rmp_df.columns = [str(c).strip() for c in rmp_df.columns]
            rmp_df['match_key'] = rmp_df['instructor'].apply(lambda x: str(x).split()[-1].upper() if len(str(x).split()) > 0 else "")
            rmp_df['rmp_rating'] = pd.to_numeric(rmp_df['rmp_rating'], errors='coerce')
            rmp_df = rmp_df.sort_values('rmp_rating', ascending=False).drop_duplicates('match_key')
            
            df_raw['match_key'] = df_raw['instructor'].apply(lambda x: str(x).split()[0].upper() if len(str(x).split()) > 0 else "")
            df_raw = pd.merge(df_raw, rmp_df[['match_key', 'rmp_rating']], on="match_key", how="left")
            df_raw = df_raw.drop(columns=['match_key'])
        except:
            pass

    # --- SQLITE WORKFLOW ---
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    df_raw.to_sql('courses', conn, index=False, if_exists='replace')
    
    try:
        results = (
            pd.read_sql_query(GET_RECENT_LECTURES, conn),
            pd.read_sql_query(GET_EASIEST_LOWER_DIV, conn),
            pd.read_sql_query(GET_EASIEST_UPPER_DIV, conn),
            pd.read_sql_query(GET_EASIEST_DEPTS, conn),
            pd.read_sql_query(GET_BEST_GE_PROFS, conn)
        )
    except Exception as e:
        st.error(f"SQL Error: {e}")
        st.stop()
    finally:
        conn.close()
        
    return results

def main():
    st.title("(｡•̀ᴗ-)✧ Gaucho Insights")
    
    df, lower_div_df, upper_div_df, dept_df, ge_profs_df = load_and_query_data()

    with st.expander("°˖✧ View Leaderboards"):
        t1, t2, t3, t4 = st.tabs(["🐣 Lower Div", "🎓 Upper Div", "🏢 Depts", "👨‍🏫 Best GE Profs"])
        t1.table(lower_div_df.head(5))
        t2.table(upper_div_df.head(5))
        t3.table(dept_df.head(5))
        t4.table(ge_profs_df.head(5))

    st.sidebar.header("🔍 Search Filters")
    mode = st.sidebar.selectbox("Choose Department", ["All Departments", "PSTAT", "CS", "MCDB", "CHEM"])
    course_q = st.sidebar.text_input("Course Number", "").strip().upper()
    prof_q = st.sidebar.text_input("Instructor Name", "").strip().upper()
    
    data = df.copy()
    if mode == "PSTAT": data = pstat_logic.process_pstat(data)
    elif mode == "CS": data = cs_logic.process_cs(data)
    elif mode == "MCDB": data = mcdb_logic.process_mcdb(data)
    elif mode == "CHEM": data = chem_logic.process_chem(data)

    if course_q:
        data = data[data['course'].str.contains(course_q, case=False, na=False)]
    if prof_q:
        data = data[data['instructor'].str.contains(prof_q, case=False, na=False)]

    if not data.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Avg GPA", f"{data['avgGPA'].mean():.2f}")
        m2.metric("Sections", len(data))
        if 'rmp_rating' in data.columns:
            avg_rmp = data['rmp_rating'].dropna().mean()
            m3.metric("Avg RMP", f"{avg_rmp:.1f}/5.0" if not pd.isna(avg_rmp) else "N/A")

        st.subheader("Course History & Grade Distribution")
        
        # Added A, B, C, D, F back to the column list
        final_cols = ['course', 'instructor', 'year', 'quarter', 'avgGPA', 'a', 'b', 'c', 'd', 'f', 'rmp_rating']
        available_cols = [c for c in final_cols if c in data.columns]
        
        display_data = data[available_cols].sort_values(by=['year', 'avgGPA'], ascending=[False, False])
        
        # Formatting for a cleaner table
        st.dataframe(display_data, use_container_width=True)
    else:
        st.info("No records found.")

if __name__ == "__main__":
    main()
