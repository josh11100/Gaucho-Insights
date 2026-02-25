import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px

# Logic File Imports
try:
    import pstat_logic, cs_logic, mcdb_logic, chem_logic
except ImportError as e:
    st.error(f"❌ Logic File Missing: {e}")
    st.stop()

st.set_page_config(page_title="Gaucho Insights", layout="wide")

# --- LOAD CSS ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

if os.path.exists("style.css"):
    local_css("style.css")

@st.cache_data
def load_data():
    csv_path = os.path.join('data', 'courseGrades.csv')
    if not os.path.exists(csv_path):
        st.error(f"❌ CSV not found at {csv_path}")
        st.stop()
    df = pd.read_csv(csv_path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # Cleaning
    for col in ['instructor', 'quarter', 'course', 'dept']:
        df[col] = df[col].astype(str).str.upper().str.strip()

    # Smart Year
    df['year'] = df['quarter'].apply(lambda x: int(re.search(r'(\d{2,4})', x).group(1)) if re.search(r'(\d{2,4})', x) else 0)
    df['year'] = df['year'].apply(lambda x: 2000 + x if 0 < x < 100 else x)
    
    gpa_col = next((c for c in ['avggpa', 'avg_gpa', 'avg gpa'] if c in df.columns), 'avggpa')
    for col in [gpa_col, 'a', 'b', 'c', 'd', 'f']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    return df, gpa_col

def main():
    st.title("(｡•̀ᴗ-)✧ Gaucho Insights")
    full_df, gpa_col = load_data()

    # Sidebar
    st.sidebar.header("🔍 Filters")
    mode = st.sidebar.selectbox("Department", ["All Departments", "PSTAT", "CS", "MCDB", "CHEM"])
    course_q = st.sidebar.text_input("Course #", "").strip().upper()
    
    data = full_df.copy()
    if mode == "PSTAT": data = pstat_logic.process_pstat(data)
    elif mode == "CS": data = cs_logic.process_cs(data)
    # ... (other logic calls)

    if course_q: data = data[data['course'].str.contains(course_q, na=False)]

    if not data.empty:
        # Sort by newest
        data = data.sort_values(by=['year', gpa_col], ascending=[False, False])

        st.subheader(f"Found {len(data)} Sections")
        
        # Instead of a big table, we create expandable "Cards"
        for i, row in data.head(20).iterrows(): # Limits to top 20 for speed
            # The label for the "fold/unfold" part
            label = f"{row['course']} — {row['instructor']} | GPA: {row[gpa_col]:.2f} ({row['quarter']})"
            
            with st.expander(label):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.write(f"**Year:** {row['year']}")
                    st.write(f"**Professor:** {row['instructor']}")
                    st.metric("Avg GPA", f"{row[gpa_col]:.2f}")
                
                with col2:
                    # Mini bar graph for THIS specific class
                    grade_data = pd.DataFrame({
                        'Grade': ['A', 'B', 'C', 'D', 'F'],
                        'Percent': [row['a'], row['b'], row['c'], row['d'], row['f']]
                    })
                    fig = px.bar(grade_data, x='Grade', y='Percent', 
                                 color='Grade',
                                 color_discrete_map={'A':'#2ecc71','B':'#3498db','C':'#f1c40f','D':'#e67e22','F':'#e74c3c'},
                                 height=200)
                    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Search for a course to see insights!")

if __name__ == "__main__":
    main()
