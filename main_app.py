import streamlit as st
import pandas as pd
import os
import sqlite3
import re
import plotly.express as px  # New import for the heatmap

# 1. Database Queries Import
try:
    from queries import (
        GET_RECENT_LECTURES, GET_EASIEST_LOWER_DIV, 
        GET_EASIEST_UPPER_DIV, GET_EASIEST_DEPTS, GET_BEST_GE_PROFS
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
    if not os.path.exists(csv_path):
        st.error(f"❌ CSV not found at {csv_path}")
        st.stop()
        
    df_raw = pd.read_csv(csv_path)
    df_raw.columns = [str(c).strip().lower() for c in df_raw.columns]
    
    # --- DYNAMIC YEAR DISCOVERY ---
    def find_year_value(row):
        for val in row:
            match = re.search(r'(20[1-2]\d)', str(val))
            if match: return int(match.group(1))
        return 0

    if 'year' not in df_raw.columns:
        df_raw['year'] = df_raw.apply(find_year_value, axis=1)

    # Standard Cleaning
    df_raw['instructor'] = df_raw['instructor'].astype(str).str.upper().str.strip()
    df_raw['quarter'] = df_raw['quarter'].astype(str).str.upper().str.strip()
    df_raw['course'] = df_raw['course'].astype(str).str.upper().str.strip()
    
    gpa_col = next((c for c in ['avggpa', 'avg_gpa', 'avg gpa'] if c in df_raw.columns), None)
    
    for col in [gpa_col, 'a', 'b', 'c', 'd', 'f']:
        if col and col in df_raw.columns:
            df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce').fillna(0)

    # SQL Setup
    df_raw['q_year'] = df_raw['year']
    q_order = {'FALL': 4, 'SUMMER': 3, 'SPRING': 2, 'WINTER': 1}
    df_raw['q_rank'] = df_raw['quarter'].apply(lambda x: next((q_order[q] for q in q_order if q in x), 0))
    df_raw['course_num'] = df_raw['course'].str.extract(r'(\d+)').astype(float).fillna(0)

    conn = sqlite3.connect(':memory:', check_same_thread=False)
    df_raw.to_sql('courses', conn, index=False, if_exists='replace')
    results = (
        pd.read_sql_query(GET_RECENT_LECTURES, conn),
        pd.read_sql_query(GET_EASIEST_LOWER_DIV, conn),
        pd.read_sql_query(GET_EASIEST_UPPER_DIV, conn),
        pd.read_sql_query(GET_EASIEST_DEPTS, conn),
        pd.read_sql_query(GET_BEST_GE_PROFS, conn)
    )
    conn.close()
    return results, gpa_col

def main():
    st.title("(｡•̀ᴗ-)✧ Gaucho Insights")
    (df, l_div, u_div, depts, ge_profs), gpa_col = load_and_query_data()

    st.sidebar.header("🔍 Filters")
    mode = st.sidebar.selectbox("Department", ["All Departments", "PSTAT", "CS", "MCDB", "CHEM"])
    course_q = st.sidebar.text_input("Course #", "").strip().upper()
    prof_q = st.sidebar.text_input("Professor", "").strip().upper()
    
    data = df.copy()
    if mode == "PSTAT": data = pstat_logic.process_pstat(data)
    elif mode == "CS": data = cs_logic.process_cs(data)
    elif mode == "MCDB": data = mcdb_logic.process_mcdb(data)
    elif mode == "CHEM": data = chem_logic.process_chem(data)

    if course_q: data = data[data['course'].str.contains(course_q, na=False)]
    if prof_q: data = data[data['instructor'].str.contains(prof_q, na=False)]

    if not data.empty:
        # --- NEW HEATMAP SECTION ---
        st.subheader("📊 Grade Heatmap")
        
        # Prepare data for heatmap (Top 10 filtered results)
        viz_data = data.sort_values(by=['year', gpa_col], ascending=[False, False]).head(10)
        
        # Melt the grade columns for Plotly
        melted_grades = viz_data.melt(
            id_vars=['course', 'instructor', 'quarter', 'year'],
            value_vars=['a', 'b', 'c', 'd', 'f'],
            var_name='Grade', value_name='Percentage'
        )
        melted_grades['Grade'] = melted_grades['Grade'].str.upper()
        
        # Create the Heatmap
        fig = px.bar(
            melted_grades, 
            x="Percentage", 
            y="course", 
            color="Grade", 
            orientation='h',
            hover_data=["instructor", "quarter", "year"],
            color_discrete_map={'A':'#2ecc71', 'B':'#3498db', 'C':'#f1c40f', 'D':'#e67e22', 'F':'#e74c3c'},
            title="Grade Distribution (A-F)"
        )
        fig.update_layout(barmode='stack', yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

        # --- DATA TABLE ---
        st.subheader("📋 Historical Data")
        display_order = ['course', 'instructor', gpa_col, 'year', 'quarter', 'a', 'b', 'c', 'd', 'f']
        existing = [c for c in display_order if c in data.columns]
        
        final_df = data[existing].sort_values(by=['year', gpa_col], ascending=[False, False])
        final_df.columns = [c.replace('_', ' ').title() if c != gpa_col else 'Avg GPA' for c in final_df.columns]
        st.dataframe(final_df, use_container_width=True)
    else:
        st.info("No records found.")

if __name__ == "__main__":
    main()
