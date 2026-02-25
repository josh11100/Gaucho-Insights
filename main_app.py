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

# --- CUSTOM CSS INJECTION ---
st.markdown("""
    <style>
    /* Main Background */
    .main { background-color: #f0f2f6; }
    
    /* Custom Card Styling */
    div[data-testid="stExpander"] {
        background-color: white !important;
        border: 1px solid #d1d5db !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        margin-bottom: 15px !important;
    }
    
    /* Metrics Styling */
    [data-testid="stMetricValue"] { font-size: 24px !important; color: #1f3a93 !important; }
    
    /* Header Polish */
    h1 { color: #1f3a93; font-family: 'Inter', sans-serif; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

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
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()

    # Smart Year Extraction
    def extract_year(q_str):
        match = re.search(r'(\d{2,4})', q_str)
        if match:
            y = match.group(1)
            return int("20" + y) if len(y) == 2 else int(y)
        return 0
    df['year'] = df['quarter'].apply(extract_year)
    
    gpa_col = next((c for c in ['avggpa', 'avg_gpa', 'avg gpa'] if c in df.columns), 'avggpa')
    for col in [gpa_col, 'a', 'b', 'c', 'd', 'f']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    return df, gpa_col

def main():
    st.title("(｡•̀ᴗ-)✧ Gaucho Insights")
    full_df, gpa_col = load_data()

    # Sidebar
    st.sidebar.header("🔍 Filters")
    mode = st.sidebar.selectbox("Department", ["All Departments", "PSTAT", "CS", "MCDB", "CHEM"])
    course_q = st.sidebar.text_input("Course #", "").strip().upper()
    prof_q = st.sidebar.text_input("Professor", "").strip().upper()
    
    data = full_df.copy()
    if mode == "PSTAT": data = pstat_logic.process_pstat(data)
    elif mode == "CS": data = cs_logic.process_cs(data)
    elif mode == "MCDB": data = mcdb_logic.process_mcdb(data)
    elif mode == "CHEM": data = chem_logic.process_chem(data)

    if course_q: data = data[data['course'].str.contains(course_q, na=False)]
    if prof_q: data = data[data['instructor'].str.contains(prof_q, na=False)]

    if not data.empty:
        # Metrics for the search
        col1, col2, col3 = st.columns(3)
        col1.metric("Results", len(data))
        col2.metric("Mean GPA", f"{data[gpa_col].mean():.2f}")
        col3.metric("Top Term", data['quarter'].iloc[0])

        st.markdown("---")
        
        # Sort by year
        sorted_data = data.sort_values(by=['year', gpa_col], ascending=[False, False])

        # --- FOLD/UNFOLD SECTION ---
        for i, row in sorted_data.head(25).iterrows(): # Limiting to 25 for speed
            # The label of the card
            vibe = "✨ Easy A" if row[gpa_col] >= 3.5 else "⚠️ Weed-out" if row[gpa_col] <= 3.0 else "⚖️ Balanced"
            card_label = f"{vibe} | {row['course']} — {row['instructor']} ({row['quarter']}) | GPA: {row[gpa_col]:.2f}"
            
            with st.expander(card_label):
                c1, c2 = st.columns([1, 2])
                
                with c1:
                    st.write(f"**Instructor:** {row['instructor']}")
                    st.write(f"**Quarter:** {row['quarter']}")
                    st.write(f"**Year:** {row['year']}")
                    st.write(f"**Average GPA:** {row[gpa_col]:.2f}")
                
                with c2:
                    # Grade Graph for this specific row
                    grade_df = pd.DataFrame({
                        'Grade': ['A', 'B', 'C', 'D', 'F'],
                        'Percent': [row['a'], row['b'], row['c'], row['d'], row['f']]
                    })
                    fig = px.bar(grade_df, x='Grade', y='Percent', 
                                 color='Grade',
                                 color_discrete_map={'A':'#2ecc71','B':'#3498db','C':'#f1c40f','D':'#e67e22','F':'#e74c3c'},
                                 height=200)
                    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No records found. Try adjusting your search!")

if __name__ == "__main__":
    main()
