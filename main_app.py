import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px

# 1. Logic File Imports
try:
    import pstat_logic, cs_logic, mcdb_logic, chem_logic
except ImportError:
    st.error("Logic files missing.")
    st.stop()

st.set_page_config(page_title="Gaucho Insights", layout="wide", page_icon="🎓")

# --- LOAD EXTERNAL CSS ---
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

@st.cache_data
def load_and_clean_data():
    csv_path = os.path.join('data', 'courseGrades.csv')
    rmp_path = os.path.join('data', 'rmp_final_data.csv')
    
    if not os.path.exists(csv_path):
        # Fallback if 'data' folder isn't used
        csv_path = 'courseGrades.csv'
        rmp_path = 'rmp_final_data.csv'

    df = pd.read_csv(csv_path)
    df.columns = [str(c).strip().lower() for c in df.columns]

    # --- THE SMART MATCHING ENGINE ---
    # Registrar: "RAVAT U V" -> RAVAT (Last) + U (First Init) -> RAVATU
    # RMP: "UMA RAVAT" -> RAVAT (Last) + U (First Init) -> RAVATU
    def get_registrar_key(name):
        if pd.isna(name): return "UNKNOWN"
        parts = str(name).upper().split()
        if not parts: return "UNKNOWN"
        last = parts[0]
        first_init = parts[1][0] if len(parts) > 1 else ""
        return f"{last}{first_init}"

    def get_rmp_key(name):
        if pd.isna(name): return "UNKNOWN"
        parts = str(name).upper().split()
        if not parts: return "UNKNOWN"
        last = parts[-1]
        first_init = parts[0][0] if len(parts) > 1 else ""
        return f"{last}{first_init}"

    df['join_key'] = df['instructor'].apply(get_registrar_key)

    if os.path.exists(rmp_path):
        rmp_df = pd.read_csv(rmp_path)
        rmp_df['rmp_join_key'] = rmp_df['instructor'].apply(get_rmp_key)
        
        # Merge Grade Data with RMP Data
        df = pd.merge(df, rmp_df, left_on='join_key', right_on='rmp_join_key', how='left', suffixes=('', '_rmp'))
    
    # Standardize basic text columns
    for col in ['instructor', 'quarter', 'course', 'dept']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()

    gpa_col = next((c for c in ['avggpa', 'avg_gpa', 'avg gpa'] if c in df.columns), 'avggpa')
    
    # Aggregate and clean
    group_cols = ['instructor', 'join_key', 'quarter', 'year', 'course', 'dept']
    agg_dict = {gpa_col: 'mean', 'a': 'sum', 'b': 'sum', 'c': 'sum', 'd': 'sum', 'f': 'sum'}
    for rmp_c in ['rmp_rating', 'rmp_difficulty', 'rmp_take_again', 'rmp_tags', 'rmp_url']:
        if rmp_c in df.columns: agg_dict[rmp_c] = 'first'

    df = df.groupby(group_cols).agg(agg_dict).reset_index()

    # Time sorting: Fixes the "ordering is wrong" issue
    q_map = {'FALL': 4, 'SUMMER': 3, 'SPRING': 2, 'WINTER': 1}
    df['q_score'] = df['quarter'].map(q_map).fillna(0)
    df = df.sort_values(by=['year', 'q_score'], ascending=False)
    
    return df, gpa_col

def main():
    st.title("(つ▀¯▀ )つ GAUCHO INSIGHTS ⊂(▀¯▀⊂ )")
    full_df, gpa_col = load_and_clean_data()

    if 'prof_view' not in st.session_state:
        st.session_state.prof_view = None

    # --- 1. PROFESSOR PROFILE MODE ---
    if st.session_state.prof_view:
        prof_key = st.session_state.prof_view
        prof_history = full_df[full_df['join_key'] == prof_key]
        
        if st.button("⬅️ Back to Search"):
            st.session_state.prof_view = None
            st.rerun()

        if prof_history.empty:
            st.error("No data found.")
            return

        rmp = prof_history.iloc[0] # Newest record
        st.header(f"👨‍🏫 Professor Profile: {rmp['instructor']}")
        
        c1, c2 = st.columns([1, 1.2])
        with c1:
            st.subheader("Rate My Professor Insights")
            if pd.notna(rmp.get('rmp_rating')):
                m1, m2, m3 = st.columns(3)
                m1.metric("Rating", f"{rmp['rmp_rating']}/5")
                m2.metric("Difficulty", f"{rmp['rmp_difficulty']}/5")
                m3.metric("Take Again", rmp.get('rmp_take_again', 'N/A'))
                
                tags = str(rmp.get('rmp_tags', ''))
                if tags and tags != "None":
                    tag_html = "".join([f'<span style="background-color:#FFD700; color:#000; padding:5px 10px; border-radius:12px; margin:3px; display:inline-block; font-size:11px; font-weight:bold;">{t.strip().upper()}</span>' for t in tags.split(",")])
                    st.markdown(tag_html, unsafe_allow_html=True)
            else:
                st.info("No RMP data found.")

        with c2:
            st.subheader("Teaching Record")
            # Filter history to show meaningful averages per course
            history = prof_history.groupby(['course', 'dept']).agg({gpa_col: 'mean', 'instructor': 'count'}).rename(columns={gpa_col: 'Avg GPA', 'instructor': 'Sections'}).reset_index()
            history['Avg GPA'] = history['Avg GPA'].map('{:,.2f}'.format)
            st.dataframe(history.sort_values('Sections', ascending=False), hide_index=True, use_container_width=True)

        st.divider()
        st.subheader("Quarterly GPA Trends")
        # Line chart of GPA over time
        trend_df = prof_history.copy()
        trend_df['q_label'] = trend_df['quarter'] + " " + trend_df['year'].astype(str)
        st.plotly_chart(px.line(trend_df.iloc[::-1], x='q_label', y=gpa_col, color='course', markers=True, template="plotly_dark"), use_container_width=True)
        return

    # --- 2. SEARCH MODE ---
    st.sidebar.header("🔍 FILTERS")
    dept_choice = st.sidebar.selectbox("DEPARTMENT", ["All Departments", "PSTAT", "CS", "MCDB", "CHEM"])
    prof_q = st.sidebar.text_input("PROFESSOR NAME").strip().upper()
    
    data = full_df.copy()
    if dept_choice != "All Departments":
        # Handle PSTAT and PSTATW (Web) as the same
        if dept_choice == "PSTAT":
            data = data[data['dept'].str.startswith("PSTAT")]
        else:
            data = data[data['dept'] == dept_choice]

    if prof_q:
        data = data[data['instructor'].str.contains(prof_q, na=False)]

    if not data.empty:
        # Display results
        for idx, row in data.head(20).iterrows():
            with st.container(border=True):
                colA, colB = st.columns([2, 1])
                with colA:
                    st.markdown(f"### {row['course']} | {row['quarter']} {row['year']}")
                    if st.button(f"{row['instructor']}", key=f"btn_{idx}"):
                        st.session_state.prof_view = row['join_key']
                        st.rerun()
                    
                    rating = f"⭐ {row['rmp_rating']}" if pd.notna(row.get('rmp_rating')) else "No RMP"
                    st.write(f"**GPA:** `{row[gpa_col]:.2f}` | **RMP:** {rating}")
                
                with colB:
                    grades = pd.DataFrame({'Grade': ['A', 'B', 'C', 'D', 'F'], 'Count': [row['a'], row['b'], row['c'], row['d'], row['f']]})
                    st.plotly_chart(px.bar(grades, x='Grade', y='Count', color='Grade', 
                                     color_discrete_map={'A':'#00CCFF','B':'#3498db','C':'#FFD700','D':'#e67e22','F':'#e74c3c'}, 
                                     template="plotly_dark", height=100).update_layout(margin=dict(l=0,r=0,t=0,b=0), showlegend=False, xaxis_visible=False, yaxis_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'), use_container_width=True, config={'displayModeBar': False}, key=f"fig_{idx}")
    else:
        st.info("No matching courses found.")

if __name__ == "__main__":
    main()
