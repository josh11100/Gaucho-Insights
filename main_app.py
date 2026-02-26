import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px

# 1. Logic File Imports
try:
    import pstat_logic, cs_logic, mcdb_logic, chem_logic
except ImportError:
    st.error("Logic files missing. Please ensure pstat_logic.py, etc. are in the root folder.")
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
        st.error(f"Missing grade data at {csv_path}")
        st.stop()
        
    df = pd.read_csv(csv_path)
    df.columns = [str(c).strip().lower() for c in df.columns]

    # --- ADVANCED CLEANING ENGINE ---
    def get_join_key(name):
        if pd.isna(name): return "UNKNOWN"
        # Remove everything except letters, make uppercase
        clean = re.sub(r'[^A-Z]', '', str(name).upper())
        return clean

    df['join_key'] = df['instructor'].apply(get_join_key)

    if os.path.exists(rmp_path):
        rmp_df = pd.read_csv(rmp_path)
        rmp_df['rmp_join_key'] = rmp_df['instructor'].apply(get_join_key)
        
        # MANUAL OVERRIDE: If the key 'RAVATU' is in Grades but 'UMARAVAT' is in RMP
        # We force them to be 'RAVAT'
        overrides = {
            "RAVATU": "RAVAT",
            "UMARAVAT": "RAVAT",
            "UMAIRRAVAT": "RAVAT",
            "RAVATUMA": "RAVAT"
        }
        df['join_key'] = df['join_key'].replace(overrides)
        rmp_df['rmp_join_key'] = rmp_df['rmp_join_key'].replace(overrides)

        # Merge
        df = pd.merge(df, rmp_df, left_on='join_key', right_on='rmp_join_key', how='left', suffixes=('', '_rmp'))
    
    # Standardize columns
    for col in ['instructor', 'quarter', 'course', 'dept']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()

    gpa_col = next((c for c in ['avggpa', 'avg_gpa', 'avg gpa'] if c in df.columns), 'avggpa')
    for col in [gpa_col, 'a', 'b', 'c', 'd', 'f']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Aggregation
    group_cols = ['instructor', 'join_key', 'quarter', 'course', 'dept']
    agg_dict = {gpa_col: 'mean', 'a': 'sum', 'b': 'sum', 'c': 'sum', 'd': 'sum', 'f': 'sum'}
    for rmp_c in ['rmp_rating', 'rmp_difficulty', 'rmp_take_again', 'rmp_tags', 'rmp_url']:
        if rmp_c in df.columns: agg_dict[rmp_c] = 'first'

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

    # --- THE TRUTH FINDER (DEBUG) ---
    with st.expander("🛠️ DEVELOPER TRUTH-FINDER"):
        st.write("Checking for Ravat in Merged Data...")
        ravat_test = full_df[full_df['instructor'].str.contains("RAVAT", na=False)]
        st.dataframe(ravat_test[['instructor', 'join_key', 'rmp_rating']])
        
        st.write("Checking Raw RMP File names...")
        rmp_path = os.path.join('data', 'rmp_final_data.csv')
        if os.path.exists(rmp_path):
            raw_rmp = pd.read_csv(rmp_path)
            st.write(raw_rmp[raw_rmp['instructor'].str.contains("RAVAT", case=False, na=False)])

    if 'prof_view' not in st.session_state:
        st.session_state.prof_view = None

    # --- 1. PROFESSOR PROFILE MODE ---
    if st.session_state.prof_view:
        prof_key = st.session_state.prof_view
        prof_history = full_df[full_df['join_key'] == prof_key]
        
        if prof_history.empty:
            st.warning("Data lost on refresh. Returning to search...")
            st.session_state.prof_view = None
            st.rerun()

        rmp = prof_history.sort_values(['year_val', 'q_weight'], ascending=False).iloc[0]

        if st.button("⬅️ Back to Search"):
            st.session_state.prof_view = None
            st.rerun()

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
                if tags and tags not in ["nan", "None"]:
                    tag_html = "".join([f'<span style="background-color:#FFD700; color:#000; padding:6px 12px; border-radius:15px; margin:4px; display:inline-block; font-size:12px; font-weight:bold;">{t.strip().upper()}</span>' for t in tags.split(",")])
                    st.markdown(tag_html, unsafe_allow_html=True)
            else:
                st.info("No RMP match found for this instructor.")

        with c2:
            st.subheader("Teaching History")
            history = prof_history.groupby('course').agg({gpa_col: 'mean', 'quarter': 'count'}).rename(columns={gpa_col: 'Avg GPA', 'quarter': 'Sections'}).reset_index()
            history['Avg GPA'] = history['Avg GPA'].map('{:,.2f}'.format)
            st.dataframe(history.sort_values('Sections', ascending=False), hide_index=True, use_container_width=True)

        st.divider()
        st.subheader("GPA Trends")
        st.plotly_chart(px.line(prof_history.sort_values(['year_val', 'q_weight']), x='quarter', y=gpa_col, color='course', markers=True, template="plotly_dark"), use_container_width=True)
        return

    # --- 2. SEARCH MODE ---
    st.sidebar.header("🔍 FILTERS")
    dept = st.sidebar.selectbox("DEPARTMENT", ["All Departments", "PSTAT", "CS", "MCDB", "CHEM"])
    course_q = st.sidebar.text_input("COURSE #").strip().upper()
    prof_q = st.sidebar.text_input("PROFESSOR").strip().upper()
    
    data = full_df.copy()
    if dept == "PSTAT": data = pstat_logic.process_pstat(data)
    elif dept == "CS": data = cs_logic.process_cs(data)
    elif dept == "MCDB": data = mcdb_logic.process_mcdb(data)
    elif dept == "CHEM": data = chem_logic.process_chem(data)

    if course_q: data = data[data['course'].str.contains(course_q, na=False)]
    if prof_q: data = data[data['instructor'].str.contains(prof_q, na=False)]

    if not data.empty:
        data = data.sort_values(by=['year_val', 'q_weight', gpa_col], ascending=[False, False, False])
        for idx, row in data.head(30).iterrows():
            with st.container(border=True):
                colA, colB = st.columns([2, 1])
                with colA:
                    st.markdown(f"### {row['course']} | {row['quarter']}")
                    if st.button(f"{row['instructor']}", key=f"btn_{idx}"):
                        st.session_state.prof_view = row['join_key']
                        st.rerun()
                    
                    rating = f"⭐ {row['rmp_rating']}" if pd.notna(row.get('rmp_rating')) else "No RMP"
                    st.write(f"**GPA:** `{row[gpa_col]:.2f}` | **RMP:** {rating}")
                
                with colB:
                    grades = pd.DataFrame({'Grade': ['A', 'B', 'C', 'D', 'F'], 'Count': [row['a'], row['b'], row['c'], row['d'], row['f']]})
                    fig = px.bar(grades, x='Grade', y='Count', color='Grade', 
                                 color_discrete_map={'A':'#00CCFF','B':'#3498db','C':'#FFD700','D':'#e67e22','F':'#e74c3c'}, 
                                 template="plotly_dark", height=100)
                    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), showlegend=False, xaxis_visible=False, yaxis_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"fig_{idx}")
    else:
        st.info("No courses found.")

if __name__ == "__main__":
    main()
