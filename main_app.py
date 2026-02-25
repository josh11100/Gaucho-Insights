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
    
    def force_clean(x):
        return str(x).strip().upper()

    df_raw['instructor'] = df_raw['instructor'].apply(force_clean)
    df_raw['quarter'] = df_raw['quarter'].apply(force_clean)
    df_raw['dept'] = df_raw['dept'].apply(lambda x: str(x).strip().upper())
    df_raw['course'] = df_raw['course'].apply(lambda x: " ".join(str(x).split()).strip().upper())
    
    # Extract Year and Quarter Rank
    q_order = {'FALL': 4, 'SUMMER': 3, 'SPRING': 2, 'WINTER': 1}
    df_raw['year'] = df_raw['quarter'].apply(lambda x: int(x.split()[1]) if len(x.split()) > 1 and x.split()[1].isdigit() else 0)
    df_raw['q_rank'] = df_raw['quarter'].apply(lambda x: q_order.get(x.split()[0], 0) if len(x.split()) > 0 else 0)
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
    
    # Fetch results
    results = (
        pd.read_sql_query(GET_RECENT_LECTURES, conn),
        pd.read_sql_query(GET_EASIEST_LOWER_DIV, conn),
        pd.read_sql_query(GET_EASIEST_UPPER_DIV, conn),
        pd.read_sql_query(GET_EASIEST_DEPTS, conn),
        pd.read_sql_query(GET_BEST_GE_PROFS, conn)
    )
    conn.close()
    return results

def main():
    st.title("(｡•̀ᴗ-)✧ Gaucho Insights")
    df, lower_div_df, upper_div_df, dept_df, ge_profs_df = load_and_query_data()

    with st.expander("°˖✧ View Leaderboards"):
        t1, t2, t3, t4 = st.tabs(["🐣 Lower Div", "🎓 Upper Div", "🏢 Depts", "👨‍🏫 Best GE Profs"])
        t1.table(lower_div_df[['course', 'mean_gpa']].head(5))
        t2.table(upper_div_df[['course', 'mean_gpa']].head(5))
        t3.table(dept_df[['dept', 'dept_avg_gpa']].head(5))
        t4.table(ge_profs_df[['instructor', 'avg_instructor_gpa']].head(5))

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

        # --- SIMPLIFIED TABLE ---
        st.subheader("Course History")
        
        # Select and order the specific columns the user wants
        # 'rmp_rating' is included to keep the scraper data visible
        final_cols = ['course', 'instructor', 'year', 'quarter', 'avgGPA', 'rmp_rating']
        
        # Filter to only show columns that actually exist in the dataframe
        available_cols = [c for c in final_cols if c in data.columns]
        
        # Display the simple dataframe
        st.dataframe(
            data[available_cols].sort_values(by=['year', 'avgGPA'], ascending=[False, False]), 
            use_container_width=True
        )
    else:
        st.info("No records found.")

if __name__ == "__main__":
    main()
