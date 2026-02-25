import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px

# 1. Logic File Imports
try:
    import pstat_logic, cs_logic, mcdb_logic, chem_logic
except ImportError:
    st.error("❌ Logic files missing.")
    st.stop()

st.set_page_config(page_title="Gaucho Insights", layout="wide")

def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

@st.cache_data
def load_and_clean_data():
    csv_path = os.path.join('data', 'courseGrades.csv')
    if not os.path.exists(csv_path):
        st.error("❌ Data file missing.")
        st.stop()
        
    df = pd.read_csv(csv_path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    for col in ['instructor', 'quarter', 'course', 'dept']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()

    # --- THE UPDATED YEAR DETECTIVE ---
    def get_time_score(row):
        year_val = 0
        # Check every single column for a 2 or 4 digit number
        # because the year might be in 'quarter', 'term', or 'year'
        all_text = " ".join([str(val) for val in row.values])
        
        # Look for 4 digits (e.g., 2024)
        four_digit = re.findall(r'\b(20\d{2})\b', all_text)
        if four_digit:
            year_val = int(four_digit[0])
        else:
            # Look for 2 digits (e.g., F24, 24W)
            # We look for digits attached to letters or common term patterns
            two_digit = re.findall(r'\b(\d{2})\b|([A-Z](\d{2}))|((\d{2})[A-Z])', all_text)
            if two_digit:
                # Flatten the regex groups and find the first 2-digit number
                flattened = [g for groups in two_digit for g in groups if g and len(g) == 2]
                if flattened:
                    year_val = 2000 + int(flattened[0])

        # Seasonal Weighting (Fall > Winter)
        q_str = str(row.get('quarter', '')).upper()
        q_weight = 0
        if any(x in q_str for x in ["FALL", "F"]): q_weight = 4
        elif any(x in q_str for x in ["SUMMER", "M"]): q_weight = 3
        elif any(x in q_str for x in ["SPRING", "S"]): q_weight = 2
        elif any(x in q_str for x in ["WINTER", "W"]): q_weight = 1
        
        return year_val, q_weight

    time_df = df.apply(lambda r: pd.Series(get_time_score(r)), axis=1)
    df['year_val'] = time_df[0].astype(int)
    df['q_weight'] = time_df[1].astype(int)
    
    gpa_col = next((c for c in ['avggpa', 'avg_gpa', 'avg gpa'] if c in df.columns), 'avggpa')
    for col in [gpa_col, 'a', 'b', 'c', 'd', 'f']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    return df, gpa_col

def main():
    st.title("⚡ GAUCHO INSIGHTS ⚡")
    full_df, gpa_col = load_and_clean_data()

    # Sidebar
    st.sidebar.header("🔍 FILTERS")
    mode = st.sidebar.selectbox("DEPARTMENT", ["All Departments", "PSTAT", "CS", "MCDB", "CHEM"])
    course_q = st.sidebar.text_input("COURSE #").strip().upper()
    prof_q = st.sidebar.text_input("PROFESSOR").strip().upper()
    
    data = full_df.copy()
    if mode == "PSTAT": data = pstat_logic.process_pstat(data)
    elif mode == "CS": data = cs_logic.process_cs(data)
    elif mode == "MCDB": data = mcdb_logic.process_mcdb(data)
    elif mode == "CHEM": data = chem_logic.process_chem(data)

    if course_q: data = data[data['course'].str.contains(course_q, na=False)]
    if prof_q: data = data[data['instructor'].str.contains(prof_q, na=False)]

    if not data.empty:
        # Sort by Recency
        data = data.sort_values(by=['year_val', 'q_weight', gpa_col], ascending=[False, False, False])

        st.markdown("### 🏆 Top Rated in Selection")
        top_cols = st.columns(3)
        # Filter out professors with 0 GPA or only a few students to keep results quality high
        valid_profs = data[data[gpa_col] > 0]
        if not valid_profs.empty:
            top_profs = valid_profs.groupby('instructor')[gpa_col].mean().sort_values(ascending=False).head(3)
            for i, (prof, gpa) in enumerate(top_profs.items()):
                top_cols[i].metric(prof, f"{gpa:.2f} GPA")

        st.markdown("---")

        display_limit = 24
        rows = data.head(display_limit)
        
        for i in range(0, len(rows), 2):
            grid_cols = st.columns(2)
            for j in range(2):
                idx = i + j
                if idx < len(rows):
                    row = rows.iloc[idx]
                    with grid_cols[j]:
                        with st.container(border=True):
                            # Ensure year_label isn't 0
                            y_val = int(row['year_val'])
                            year_label = str(y_val) if y_val > 0 else "YEAR?"
                            
                            st.markdown(f"#### {year_label} | {row['course']}")
                            st.caption(f"Instructor: **{row['instructor']}**")
                            
                            c1, c2 = st.columns([1, 1.5])
                            with c1:
                                st.write(f"**GPA:** {row[gpa_col]:.2f}")
                                st.write(f"**Term:** {row.get('quarter', 'N/A')}")
                            
                            with c2:
                                grade_df = pd.DataFrame({
                                    'Grade': ['A', 'B', 'C', 'D', 'F'],
                                    'Percent': [row['a'], row['b'], row['c'], row['d'], row['f']]
                                })
                                fig = px.bar(grade_df, x='Grade', y='Percent', color='Grade',
                                             color_discrete_map={'A':'#00CCFF','B':'#3498db','C':'#FFD700','D':'#e67e22','F':'#e74c3c'},
                                             template="plotly_dark", height=120)
                                fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
                                                  paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"fixed_chart_{idx}")
    else:
        st.info("No courses found. Try a different search.")

if __name__ == "__main__":
    main()
