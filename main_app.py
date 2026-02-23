import streamlit as st
import pandas as pd
import os

# 1. Imports
try:
    from pstat_logic import process_pstat
    from cs_logic import process_cs
    from mcdb_logic import process_mcdb
    from chem_logic import process_chem
except ImportError as e:
    st.error(f"Logic File Missing: {e}")
    st.stop()

st.set_page_config(page_title="Gaucho Insights", layout="wide")

@st.cache_data
def load_data():
    # Resolve CSV path relative to this file's directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try common locations in order
    candidate_paths = [
        os.path.join(base_dir, "data", "grades.csv"),
        os.path.join(base_dir, "grades.csv"),
    ]
    
    csv_path = None
    for path in candidate_paths:
        if os.path.exists(path):
            csv_path = path
            break
    
    if csv_path is None:
        st.error(
            f"Could not find grades.csv. Looked in:\n"
            + "\n".join(f"  • {p}" for p in candidate_paths)
        )
        st.stop()

    df = pd.read_csv(csv_path)

    # 1. Clean up column names and text
    df['dept'] = df['dept'].str.strip()
    df['course'] = df['course'].str.replace(r'\s+', ' ', regex=True).str.strip()

    # 2. Extract Course Number and filter out 198+ (independent study, etc.)
    df['course_num'] = df['course'].str.extract(r'(\d+)').astype(float)
    df = df[df['course_num'] < 198]

    # 3. CHRONOLOGICAL REVERSE SORT (Newest Year at Top)
    q_order = {'FALL': 4, 'SUMMER': 3, 'SPRING': 2, 'WINTER': 1}

    df['temp_split'] = df['quarter'].str.upper().str.split(' ')
    df['q_year'] = pd.to_numeric(df['temp_split'].str.get(1), errors='coerce')
    df['q_rank'] = df['temp_split'].str.get(0).map(q_order).fillna(0)

    # Drop rows with unparseable quarters before sorting
    df = df.dropna(subset=['q_year'])

    df = df.sort_values(by=['q_year', 'q_rank'], ascending=[False, False])

    # 4. Drop all helper columns
    df = df.drop(columns=['course_num', 'temp_split', 'q_year', 'q_rank'])

    return df


def main():
    st.title("📊 Gaucho Insights: UCSB Grade Distribution")

    df = load_data()

    # --- SIDEBAR ---
    st.sidebar.header("Department Selection")
    options = ["PSTAT", "CS", "MCDB", "CHEM", "All Departments"]
    mode = st.sidebar.selectbox("Choose Department", options)

    prefix_map = {"PSTAT": "PSTAT", "CS": "CMPSC", "MCDB": "MCDB", "CHEM": "CHEM"}

    if mode == "All Departments":
        course_query = st.sidebar.text_input(
            "Global Search (e.g. CMPSC 16, MATH 3A)", ""
        ).strip().upper()
        data = df.copy()
    else:
        course_query = st.sidebar.text_input(
            f"Enter {mode} Course Number (e.g. 1A, 120)", ""
        ).strip().upper()
        if mode == "PSTAT":
            data = process_pstat(df)
        elif mode == "CS":
            data = process_cs(df)
        elif mode == "MCDB":
            data = process_mcdb(df)
        elif mode == "CHEM":
            data = process_chem(df)

    # --- FUZZY FILTERING ---
    if course_query:
        if mode == "All Departments":
            data = data[data['course'].str.contains(course_query, case=False, na=False)]
        else:
            pattern = rf"{prefix_map[mode]}\s+{course_query}"
            data = data[data['course'].str.contains(
                pattern, case=False, na=False, regex=True
            )]

    # --- DISPLAY ---
    st.header(f"Viewing: {mode}")

    if not data.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            avg = data['avgGPA'].mean()
            st.metric("Avg GPA", f"{avg:.2f}" if pd.notna(avg) else "N/A")
        with col2:
            st.metric("Classes Found", len(data['course'].unique()))
        with col3:
            st.metric("Total Records", len(data))

        st.dataframe(data, use_container_width=True)

        # Instructor Comparison (cap at top 20 for readability)
        st.subheader("Instructor Comparison")
        prof_chart = (
            data.groupby('instructor')['avgGPA']
            .mean()
            .sort_values(ascending=True)
            .tail(20)
        )
        st.bar_chart(prof_chart)
    else:
        if course_query:
            st.warning(f"No results found for **{course_query}**. Try a broader search.")
        else:
            st.info("Select a department or search for a course to begin.")


if __name__ == "__main__":
    main()
