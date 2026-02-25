import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px

# 1. Logic File Imports
try:
    import pstat_logic, cs_logic, mcdb_logic, chem_logic
except ImportError as e:
    st.error(f"❌ Logic File Missing: {e}")
    st.stop()

# 2. Page Configuration
st.set_page_config(page_title="Gaucho Insights", layout="wide")

# 3. Load CSS from style.css
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

# 4. Data Engine
@st.cache_data
def load_and_clean_data():
    csv_path = os.path.join('data', 'courseGrades.csv')
    if not os.path.exists(csv_path):
        st.error("❌ CSV file not found in 'data/' folder.")
        st.stop()
        
    df = pd.read_csv(csv_path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # Standardize Text
    for col in ['instructor', 'quarter', 'course', 'dept']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()

    # --- THE AGGRESSIVE YEAR FIX ---
    def extract_year(q_val):
        nums = re.findall(r'\d+', str(q_val))
        if nums:
            y = nums[0]
            if len(y) == 2: return int("20" + y)
            if len(y) == 4: return int(y)
        return 0 # Fallback for sorting

    df['year_int'] = df['quarter'].apply(extract_year)
    # Create a display version of Year
    df['display_year'] = df['year_int'].apply(lambda x: str(x) if x > 0 else "N/A")
    
    # GPA and Grades to Numeric
    gpa_col = next((c for c in ['avggpa', 'avg_gpa', 'avg gpa'] if c in df.columns), 'avggpa')
    for col in [gpa_col, 'a', 'b', 'c', 'd', 'f']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    return df, gpa_col

def main():
    st.title("⚡ GAUCHO INSIGHTS ⚡")
    
    full_df, gpa_col = load_and_clean_data()

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("🔍 FILTERS")
    mode = st.sidebar.selectbox("DEPARTMENT", ["All Departments", "PSTAT", "CS", "MCDB", "CHEM"])
    course_q = st.sidebar.text_input("COURSE # (e.g. 120A)").strip().upper()
    prof_q = st.sidebar.text_input("PROFESSOR NAME").strip().upper()
    
    # Filter Routing
    data = full_df.copy()
    if mode == "PSTAT": data = pstat_logic.process_pstat(data)
    elif mode == "CS": data = cs_logic.process_cs(data)
    elif mode == "MCDB": data = mcdb_logic.process_mcdb(data)
    elif mode == "CHEM": data = chem_logic.process_chem(data)

    if course_q: data = data[data['course'].str.contains(course_q, na=False)]
    if prof_q: data = data[data['instructor'].str.contains(prof_q, na=False)]

    if not data.empty:
        # Sort by Year (Newest) then GPA
        data = data.sort_values(by=['year_int', gpa_col], ascending=[False, False])

        # Top Summary Metrics
        m1, m2 = st.columns(2)
        with m1:
            st.metric("SEARCH AVG GPA", f"{data[gpa_col].mean():.2f}")
        with m2:
            st.metric("SECTIONS FOUND", len(data))

        st.markdown("---")

        # --- FOLD/UNFOLD CARDS ---
        for i, row in data.head(30).iterrows():
            # Color label based on GPA
            vibe = "✨ EASY A" if row[gpa_col] >= 3.5 else "⚠️ WEED-OUT" if row[gpa_col] <= 3.0 else "⚖️ BALANCED"
            
            # This is the header of the Fold/Unfold card
            header = f"{vibe} | {row['course']} | {row['instructor']} | {row['quarter']}"
            
            with st.expander(header):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.write(f"**Professor:** {row['instructor']}")
                    st.write(f"**Term:** {row['quarter']}")
                    st.write(f"**Year:** {row['display_year']}")
                    st.write(f"**Average GPA:** {row[gpa_col]:.2f}")
                
                with col2:
                    # Specific Grade Graph for this Card
                    grade_map = {'A': row['a'], 'B': row['b'], 'C': row['c'], 'D': row['d'], 'F': row['f']}
                    grade_df = pd.DataFrame(list(grade_map.items()), columns=['Grade', 'Percent'])
                    
                    fig = px.bar(
                        grade_df, x='Grade', y='Percent', color='Grade',
                        color_discrete_map={
                            'A':'#00CCFF', 'B':'#3498db', 'C':'#FFD700', 
                            'D':'#e67e22', 'F':'#e74c3c'
                        },
                        template="plotly_dark", height=200
                    )
                    fig.update_layout(
                        margin=dict(l=0, r=0, t=0, b=0),
                        showlegend=False,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("No courses found matching those filters.")

if __name__ == "__main__":
    main()
