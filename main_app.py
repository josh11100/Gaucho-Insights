import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px

# 1. Logic File Imports
try:
    import pstat_logic, cs_logic, mcdb_logic, chem_logic
except ImportError:
    st.error("Logic files (pstat_logic.py, etc.) are missing.")
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
        st.error(f"Missing data: {csv_path}")
        st.stop()
        
    df = pd.read_csv(csv_path)
    df.columns = [str(c).strip().lower() for c in df.columns]

    # --- UPDATED SUPER-CLEAN ENGINE ---
    def super_clean(name):
        if pd.isna(name) or str(name).strip() == "": return "UNKNOWN"
        # Standardize: Upper and letters only
        name = re.sub(r'[^A-Z ]', ' ', str(name).upper())
        # Filter out single-letter initials (e.g., 'U' in 'RAVAT U')
        parts = [p for p in name.split() if len(p) > 1]
        if not parts: parts = name.split() # Fallback for short names
        return " ".join(sorted(parts))

    df['join_key'] = df['instructor'].apply(super_clean)

    if os.path.exists(rmp_path):
        rmp_df = pd.read_csv(rmp_path)
        rmp_df['rmp_join_key'] = rmp_df['instructor'].apply(super_clean)
        # Merge Grade Data with RMP Data
        df = pd.merge(df, rmp_df, left_on='join_key', right_on='rmp_join_key', how='left', suffixes=('', '_rmp'))
    
    # Standardize columns
    for col in ['instructor', 'quarter', 'course', 'dept']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()

    gpa_col = next((c for c in ['avggpa', 'avg_gpa', 'avg gpa'] if c in df.columns), 'avggpa')
    for col in [gpa_col, 'a', 'b', 'c', 'd', 'f']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # --- AGGREGATION ---
    group_cols = ['instructor', 'join_key', 'quarter', 'course', 'dept']
    agg_dict = {gpa_col: 'mean', 'a': 'sum', 'b': 'sum', 'c': 'sum', 'd': 'sum', 'f': 'sum'}
    
    # Explicitly preserve RMP columns
    for rmp_c in ['rmp_rating', 'rmp_difficulty', 'rmp_take_again', 'rmp_tags', 'rmp_url']:
        if rmp_c in df.columns:
            agg_dict[rmp_c] = 'first'

    df = df.groupby(group_cols).agg(agg_dict).reset_index()

    # Time sorting
    def get_time_score(row):
        q_str = str(row.get('quarter', '')).upper()
        four_digit = re.findall(r'\b(202[1-9]|2030)\b', q_str)
        year_val = int(four_digit[0]) if four_digit else 2000
        q_weight = 4 if "FALL" in q_str else 3 if "SUMMER" in q_str else 2 if "SPRING" in q_str else 1
        return year_val, q_weight

    time_results = df.apply(lambda r: pd.Series(get_time_score(r)), axis=1)
    df['year_val'], df['q_weight'] = time_results[0].astype(int), time_results[1].astype(int)
    
    return df, gpa_col

def main():
    st.title("(つ▀¯▀ )つ GAUCHO INSIGHTS ⊂(▀¯▀⊂ )")
    full_df, gpa_col = load_and_clean_data()

    if 'prof_view' not in st.session_state:
        st.session_state.prof_view = None

    # --- 1. PROFESSOR PROFILE MODE ---
    if st.session_state.prof_view:
        prof_key = st.session_state.prof_view
        # Filter all historical records for this professor key
        prof_history = full_df[full_df['join_key'] == prof_key]
        
        # SAFETY CHECK: If the key isn't found, reset and show error
        if prof_history.empty:
            st.error(f"No data found for the key: {prof_key}")
            if st.button("⬅️ Return to Search"):
                st.session_state.prof_view = None
                st.rerun()
            return

        # Grab RMP data from the most recent quarter taught
        rmp = prof_history.sort_values(['year_val', 'q_weight'], ascending=False).iloc[0]

        if st.button("⬅️ Back to Search"):
            st.session_state.prof_view = None
            st.rerun()

        st.header(f"👨‍🏫 Professor Profile: {rmp['instructor']}")
        
        col1, col2 = st.columns([1, 1.2])
        with col1:
            st.subheader("Rate My Professor Insights")
            if pd.notna(rmp.get('rmp_rating')):
                m1, m2, m3 = st.columns(3)
                m1.metric("Rating", f"{rmp['rmp_rating']}/5")
                m2.metric("Difficulty", f"{rmp['rmp_difficulty']}/5")
                m3.metric("Take Again", rmp.get('rmp_take_again', 'N/A'))
                
                # Render Tag Badges
                tags_str = str(rmp.get('rmp_tags', ''))
                if tags_str and tags_str not in ["nan", "None"]:
                    tags = tags_str.split(", ")
                    tag_html = "".join([f'<span style="background-color:#FFD700; color:#000; padding:6px 12px; border-radius:15px; margin:4px; display:inline-block; font-size:13px; font-weight:bold;">{t.upper()}</span>' for t in tags])
                    st.markdown(tag_html, unsafe_allow_html=True)
            else:
                st.info("No RMP data found for this instructor.")

        with col2:
            st.subheader("Teaching History Summary")
            history = prof_history.groupby('course').agg({
                gpa_col: 'mean', 
                'quarter': 'count'
            }).rename(columns={gpa_col: 'Avg GPA', 'quarter': 'Times Taught'}).reset_index()
            history['Avg GPA'] = history['Avg GPA'].map('{:,.2f}'.format)
            st.dataframe(history.sort_values('Times Taught', ascending=False), hide_index=True, use_container_width=True)

        st.divider()
        st.subheader("Full GPA History (By Quarter)")
        trend_data = prof_history.sort_values(['year_val', 'q_weight'])
        trend_fig = px.line(trend_data, x='quarter', y=gpa_col, color='course', markers=True, template="plotly_dark")
        st.plotly_chart(trend_fig, use_container_width=True)
        return

    # --- 2. SEARCH MODE ---
    st.sidebar.header("🔍 FILTERS")
    dept_choice = st.sidebar.selectbox("DEPARTMENT", ["All Departments", "PSTAT", "CS", "MCDB", "CHEM"])
    course_q = st.sidebar.text_input("COURSE #").strip().upper()
    prof_q = st.sidebar.text_input("PROFESSOR NAME").strip().upper()
    
    data = full_df.copy()
    if dept_choice == "PSTAT": data = pstat_logic.process_pstat(data)
    elif dept_choice == "CS": data = cs_logic.process_cs(data)
    elif dept_choice == "MCDB": data = mcdb_logic.process_mcdb(data)
    elif dept_choice == "CHEM": data = chem_logic.process_chem(data)

    if course_q: data = data[data['course'].str.contains(course_q, na=False)]
    if prof_q: data = data[data['instructor'].str.contains(prof_q, na=False)]

    if not data.empty:
        data = data.sort_values(by=['year_val', 'q_weight', gpa_col], ascending=[False, False, False])
        for idx, row in data.head(40).iterrows():
            with st.container(border=True):
                left, right = st.columns([2, 1])
                with left:
                    st.markdown(f"### {row['course']} | {row['quarter']}")
                    # Store the join_key for navigation
                    if st.button(f"{row['instructor']}", key=f"btn_{idx}_{row['join_key']}"):
                        st.session_state.prof_view = row['join_key']
                        st.rerun()
                    
                    rating = f"⭐ {row['rmp_rating']}" if pd.notna(row.get('rmp_rating')) else "No Rating"
                    st.write(f"**Section GPA:** `{row[gpa_col]:.2f}` | **RMP:** {rating}")
                
                with right:
                    grades = pd.DataFrame({'Grade': ['A', 'B', 'C', 'D', 'F'], 'Count': [row['a'], row['b'], row['c'], row['d'], row['f']]})
                    fig = px.bar(grades, x='Grade', y='Count', color='Grade', 
                                 color_discrete_map={'A':'#00CCFF','B':'#3498db','C':'#FFD700','D':'#e67e22','F':'#e74c3c'}, 
                                 template="plotly_dark", height=110)
                    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False, xaxis_visible=False, yaxis_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"fig_{idx}")
    else:
        st.info("No courses found.")

if __name__ == "__main__":
    main()
