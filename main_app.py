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

    def get_time_score(row):
        year_val = 0
        q_str = str(row.get('quarter', '')).upper()
        potential_year_cols = [c for c in row.index if 'year' in c or 'yr' in c]
        for col in potential_year_cols:
            found = re.findall(r'\d+', str(row[col]))
            if found:
                val = int(found[0])
                year_val = val if val > 100 else 2000 + val
                break
        if year_val == 0:
            found = re.findall(r'\d+', q_str)
            if found:
                val = int(found[-1])
                year_val = val if val > 100 else 2000 + val
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

def main():
    st.title("⚡ GAUCHO INSIGHTS ⚡")
    full_df, gpa_col = load_and_clean_data()

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

        m1, m2 = st.columns(2)
        m1.metric("MEAN GPA", f"{data[gpa_col].mean():.2f}")
        m2.metric("SECTIONS FOUND", len(data))
        st.markdown("---")

        display_limit = 40
        rows_to_show = data.head(display_limit)
        
        # Grid loop
        for i in range(0, len(rows_to_show), 2):
            cols = st.columns(2) 
            
            for j in range(2):
                idx = i + j
                if idx < len(rows_to_show):
                    row = rows_to_show.iloc[idx]
                    with cols[j]:
                        # Added a hidden unique identifier to the header string 
                        # to ensure the expander doesn't mirror its neighbor
                        vibe = "✨ EASY A" if row[gpa_col] >= 3.5 else "⚠️ WEED-OUT" if row[gpa_col] <= 3.0 else "⚖️ BALANCED"
                        year_label = int(row['year_val']) if row['year_val'] > 0 else "N/A"
                        header = f"{year_label} | {row['course']} | {row['instructor']}"
                        
                        # Wrapping in a container can help isolate the state
                        with st.container():
                            # The key in st.expander is only available in recent Streamlit versions, 
                            # but unique titles usually solve the mirroring.
                            with st.expander(header):
                                st.markdown(f"**{vibe}**")
                                grade_df = pd.DataFrame({
                                    'Grade': ['A', 'B', 'C', 'D', 'F'],
                                    'Percent': [row['a'], row['b'], row['c'], row['d'], row['f']]
                                })
                                fig = px.bar(grade_df, x='Grade', y='Percent', color='Grade',
                                             color_discrete_map={'A':'#00CCFF','B':'#3498db','C':'#FFD700','D':'#e67e22','F':'#e74c3c'},
                                             template="plotly_dark", height=150)
                                fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
                                                  paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                                
                                # Use a very specific key for the chart
                                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"chart_grid_{idx}")
                                st.write(f"**GPA:** {row[gpa_col]:.2f} | **Term:** {row.get('quarter', 'N/A')}")
    else:
        st.info("No courses found.")

if __name__ == "__main__":
    main()
