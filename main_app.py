import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px

# Logic File Imports
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
    
    # Standardize Text
    for col in ['instructor', 'quarter', 'course', 'dept']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()

    # --- AGGRESSIVE YEAR EXTRACTION ---
    def get_time_score(row):
        q_str = str(row['quarter'])
        
        # 1. Find all numbers in the string
        nums = re.findall(r'\d+', q_str)
        year = 0
        
        if nums:
            # Take the last number (usually where the year is)
            val = nums[-1]
            if len(val) == 2:
                year = int("20" + val)
            elif len(val) == 4:
                year = int(val)
        
        # 2. If no numbers, look for Quarter names to at least rank them
        q_weight = 0
        if "FALL" in q_str or "F" in q_str: q_weight = 4
        elif "SUMMER" in q_str or "M" in q_str: q_weight = 3
        elif "SPRING" in q_str or "S" in q_str: q_weight = 2
        elif "WINTER" in q_str or "W" in q_str: q_weight = 1
        
        return year, q_weight

    # Apply the fix
    time_results = df.apply(lambda r: pd.Series(get_time_score(r)), axis=1)
    df['year_val'] = time_results[0]
    df['q_weight'] = time_results[1]
    
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
        # Sort: Most Recent Year -> Most Recent Quarter -> Highest GPA
        data = data.sort_values(by=['year_val', 'q_weight', gpa_col], ascending=[False, False, False])

        # Metrics
        m1, m2 = st.columns(2)
        m1.metric("AVG GPA", f"{data[gpa_col].mean():.2f}")
        m2.metric("SECTIONS", len(data))

        st.markdown("---")

        display_limit = 40
        for i, (index, row) in enumerate(data.head(display_limit).iterrows()):
            vibe = "✨ EASY A" if row[gpa_col] >= 3.5 else "⚠️ WEED-OUT" if row[gpa_col] <= 3.0 else "⚖️ BALANCED"
            
            # Display logic
            year_label = row['year_val'] if row['year_val'] > 0 else "YEAR?"
            header = f"{year_label} | {vibe} | {row['course']} | {row['instructor']}"
            
            with st.expander(header):
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write(f"**Year Found:** {year_label}")
                    st.write(f"**Raw Quarter:** {row['quarter']}")
                    st.write(f"**Instructor:** {row['instructor']}")
                    st.write(f"**GPA:** {row[gpa_col]:.2f}")
                
                with col2:
                    grade_df = pd.DataFrame({
                        'Grade': ['A', 'B', 'C', 'D', 'F'],
                        'Percent': [row['a'], row['b'], row['c'], row['d'], row['f']]
                    })
                    fig = px.bar(grade_df, x='Grade', y='Percent', color='Grade',
                                 color_discrete_map={'A':'#00CCFF','B':'#3498db','C':'#FFD700','D':'#e67e22','F':'#e74c3c'},
                                 template="plotly_dark", height=180)
                    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
                                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"chart_{index}_{i}")
    else:
        st.info("No courses found. If you see '0' for years, check your CSV's Quarter column format!")

if __name__ == "__main__":
    main()
