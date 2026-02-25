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

# 2. Page Configuration
st.set_page_config(page_title="Gaucho Insights", layout="wide")

# 3. Load CSS
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

# 4. Data Processing Engine
@st.cache_data
def load_and_clean_data():
    csv_path = os.path.join('data', 'courseGrades.csv')
    if not os.path.exists(csv_path):
        st.error("❌ Data file missing at 'data/courseGrades.csv'")
        st.stop()
        
    df = pd.read_csv(csv_path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # Standardize Text
    for col in ['instructor', 'quarter', 'course', 'dept']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()

    # Advanced Year/Quarter Extraction
    def get_time_score(row):
        year_val = 0
        q_str = str(row.get('quarter', '')).upper()
        
        # Check for year in any column containing 'year'
        potential_year_cols = [c for c in row.index if 'year' in c or 'yr' in c]
        for col in potential_year_cols:
            found = re.findall(r'\d+', str(row[col]))
            if found:
                val = int(found[0])
                year_val = val if val > 100 else 2000 + val
                break
        
        # Fallback: search the quarter string
        if year_val == 0:
            found = re.findall(r'\d+', q_str)
            if found:
                val = int(found[-1])
                year_val = val if val > 100 else 2000 + val

        # Seasonal Weighting
        q_weight = 0
        if any(x in q_str for x in ["FALL", " F"]): q_weight = 4
        elif any(x in q_str for x in ["SUMMER", " M"]): q_weight = 3
        elif any(x in q_str for x in ["SPRING", " S"]): q_weight = 2
        elif any(x in q_str for x in ["WINTER", " W"]): q_weight = 1
        
        return year_val, q_weight

    time_df = df.apply(lambda r: pd.Series(get_time_score(r)), axis=1)
    df['year_val'] = time_df[0].astype(int)
    df['q_weight'] = time_df[1].astype(int)
    
    gpa_col = next((c for c in ['avggpa', 'avg_gpa', 'avg gpa'] if c in df.columns), 'avggpa')
    for col in [gpa_col, 'a', 'b', 'c', 'd', 'f']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    return df, gpa_col

# 5. UI Main Function
def main():
    st.title("⚡ GAUCHO INSIGHTS ⚡")
    full_df, gpa_col = load_and_clean_data()

    # Sidebar
    st.sidebar.header("🔍 FILTERS")
    mode = st.sidebar.selectbox("DEPARTMENT", ["All Departments", "PSTAT", "CS", "MCDB", "CHEM"])
    course_q = st.sidebar.text_input("COURSE #").strip().upper()
    prof_q = st.sidebar.text_input("PROFESSOR").strip().upper()
    
    # Filtering Logic
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

        # Summary Row
        m1, m2 = st.columns(2)
        m1.metric("MEAN GPA", f"{data[gpa_col].mean():.2f}")
        m2.metric("SECTIONS FOUND", len(data))

        st.markdown("---")

        # Result Cards
        display_limit = 40
        for i, (index, row) in enumerate(data.head(display_limit).iterrows()):
            vibe = "✨ EASY A" if row[gpa_col] >= 3.5 else "⚠️ WEED-OUT" if row[gpa_col] <= 3.0 else "⚖️ BALANCED"
            year_label = int(row['year_val']) if row['year_val'] > 0 else "N/A"
            header = f"{year_label} | {vibe} | {row['course']} | {row['instructor']}"
            
            with st.expander(header):
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.markdown(f"### {year_label}")
                    st.write(f"**Term:** {row.get('quarter', 'N/A')}")
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
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"ch_{index}_{i}")
    else:
        st.info("No courses found. Use filters to explore.")
        with st.expander("🛠️ Debug Column Names"):
            st.write(list(full_df.columns))

# 6. Execute App
if __name__ == "__main__":
    main()
