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

# --- HIGH-CONTRAST CSS (Fixes the White-on-White issue) ---
st.markdown("""
    <style>
    /* Force Dark Text for Readability */
    .stApp {
        color: #1a1a1a;
    }
    
    /* Style the Fold/Unfold Cards */
    div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 2px solid #e0e0e0 !important;
        border-radius: 8px !important;
        color: #1a1a1a !important;
    }

    /* Fix text inside the cards */
    div[data-testid="stExpander"] p, div[data-testid="stExpander"] label {
        color: #1a1a1a !important;
        font-weight: 500;
    }

    /* Style the Sidebar labels */
    .sidebar .sidebar-content {
        color: #1a1a1a;
    }
    
    /* Header Polish */
    h1, h2, h3 {
        color: #003660 !important;
    }
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
    
    # Simple Clean
    for col in ['instructor', 'quarter', 'course']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()

    # Smart Year
    df['year'] = df['quarter'].apply(lambda x: int(re.search(r'(\d{2,4})', x).group(1)) if re.search(r'(\d{2,4})', x) else 0)
    df['year'] = df['year'].apply(lambda x: 2000 + x if 0 < x < 100 else x)
    
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
        # Sort by Year and GPA
        data = data.sort_values(by=['year', gpa_col], ascending=[False, False])

        # --- FOLD/UNFOLD SECTION ---
        st.write("### Search Results")
        for i, row in data.head(30).iterrows():
            # Label for the folder
            is_weedout = "⚠️ Weed-out" if row[gpa_col] < 3.0 else "✨ Easy A" if row[gpa_col] > 3.5 else "⚖️ Balanced"
            label = f"{is_weedout} | {row['course']} - {row['instructor']} | GPA: {row[gpa_col]:.2f}"
            
            with st.expander(label):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown(f"**Year:** {row['year']}")
                    st.markdown(f"**Quarter:** {row['quarter']}")
                    st.metric("Avg GPA", f"{row[gpa_col]:.2f}")
                
                with col2:
                    # Grade Breakdown Chart
                    grade_df = pd.DataFrame({
                        'Grade': ['A', 'B', 'C', 'D', 'F'],
                        'Percent': [row['a'], row['b'], row['c'], row['d'], row['f']]
                    })
                    fig = px.bar(grade_df, x='Grade', y='Percent', color='Grade',
                                 color_discrete_map={'A':'#2ecc71','B':'#3498db','C':'#f1c40f','D':'#e67e22','F':'#e74c3c'},
                                 height=180)
                    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No records found. Use the sidebar to filter by course or professor.")

if __name__ == "__main__":
    main()
