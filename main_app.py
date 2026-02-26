import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px

st.set_page_config(page_title="Gaucho Insights", layout="wide", page_icon="🎓")

# --- LOAD EXTERNAL CSS ---
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

@st.cache_data
def load_and_clean_data():
    def find_file(name):
        paths_to_check = [name, os.path.join('data', name)]
        for p in paths_to_check:
            if os.path.exists(p):
                return p
        return None

    csv_path = find_file('courseGrades.csv')
    rmp_path = find_file('rmp_final_data.csv')

    if not csv_path:
        st.error("Missing 'courseGrades.csv'.")
        st.stop()
        
    df = pd.read_csv(csv_path)
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Course Filter: Undergraduate only (No 99, max 198)
    def get_course_num(course_str):
        match = re.search(r'(\d+)', str(course_str))
        return int(match.group(1)) if match else None

    df['course_num_val'] = df['course'].apply(get_course_num)
    df = df[df['course_num_val'].notna()]
    df = df[(df['course_num_val'] <= 198) & (df['course_num_val'] != 99)]

    # Matching Logic
    def get_registrar_key(name):
        if pd.isna(name): return "UNKNOWN"
        parts = str(name).upper().split()
        if not parts: return "UNKNOWN"
        return f"{parts[0]}{parts[1][0] if len(parts) > 1 else ''}"

    def get_rmp_key(name):
        if pd.isna(name): return "UNKNOWN"
        parts = str(name).upper().split()
        if not parts: return "UNKNOWN"
        return f"{parts[-1]}{parts[0][0] if len(parts) > 1 else ''}"

    df['join_key'] = df['instructor'].apply(get_registrar_key)

    if rmp_path:
        rmp_df = pd.read_csv(rmp_path)
        rmp_df['rmp_join_key'] = rmp_df['instructor'].apply(get_rmp_key)
        df = pd.merge(df, rmp_df, left_on='join_key', right_on='rmp_join_key', how='left', suffixes=('', '_rmp'))
    
    for col in ['instructor', 'quarter', 'course', 'dept']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()

    gpa_col = next((c for c in ['avggpa', 'avg_gpa', 'avg gpa'] if c in df.columns), 'avggpa')
    
    group_cols = ['instructor', 'join_key', 'quarter', 'year', 'course', 'dept']
    agg_dict = {gpa_col: 'mean', 'a': 'sum', 'b': 'sum', 'c': 'sum', 'd': 'sum', 'f': 'sum'}
    for rmp_c in ['rmp_rating', 'rmp_difficulty', 'rmp_take_again', 'rmp_tags', 'rmp_url']:
        if rmp_c in df.columns: agg_dict[rmp_c] = 'first'

    df = df.groupby(group_cols).agg(agg_dict).reset_index()

    q_map = {'FALL': 4, 'SUMMER': 3, 'SPRING': 2, 'WINTER': 1}
    df['q_score'] = df['quarter'].map(q_map).fillna(0)
    df = df.sort_values(by=['year', 'q_score'], ascending=False)
    
    return df, gpa_col

def main():
    st.title("(つ▀¯▀ )つ GAUCHO INSIGHTS ⊂(▀¯▀⊂ )")
    full_df, gpa_col = load_and_clean_data()

    if 'prof_view' not in st.session_state:
        st.session_state.prof_view = None

    if st.session_state.prof_view:
        # Profile View Logic
        prof_key = st.session_state.prof_view
        prof_history = full_df[full_df['join_key'] == prof_key]
        if st.button("⬅️ Back to Search"):
            st.session_state.prof_view = None
            st.rerun()
        
        rmp = prof_history.iloc[0]
        st.header(f"👨‍🏫 {rmp['instructor']}")
        c1, c2 = st.columns([1, 1.2])
        with c1:
            st.subheader("Rate My Professor")
            if pd.notna(rmp.get('rmp_rating')):
                m1, m2, m3 = st.columns(3)
                m1.metric("Rating", f"{rmp['rmp_rating']}/5")
                m2.metric("Difficulty", f"{rmp['rmp_difficulty']}/5")
                m3.metric("Take Again", rmp.get('rmp_take_again', 'N/A'))
            else:
                st.info("No RMP data found.")
        with c2:
            st.subheader("Teaching Record")
            history = prof_history.groupby(['course', 'dept']).agg({gpa_col: 'mean', 'instructor': 'count'}).rename(columns={gpa_col: 'Avg GPA', 'instructor': 'Sections'}).reset_index()
            history['Avg GPA'] = history['Avg GPA'].map('{:,.2f}'.format)
            st.dataframe(history, hide_index=True, use_container_width=True)
        return

    # --- SIMPLIFIED SIDEBAR ---
    st.sidebar.header("🔍 FILTERS")
    
    # Get all depts and add a "blank" string instead of "ALL"
    all_depts = sorted(full_df['dept'].unique().tolist())
    
    # Using " " (space) as the default to make it look empty
    selected_dept = st.sidebar.selectbox(
        "Select Department",
        options=[" "] + all_depts,
        index=0
    )
    
    course_q = st.sidebar.text_input("COURSE # (e.g. 120B, 16)").strip().upper()
    prof_q = st.sidebar.text_input("PROFESSOR NAME").strip().upper()
    
    data = full_df.copy()
    
    # Check for empty space selection
    if selected_dept != " ":
        data = data[data['dept'] == selected_dept]

    if course_q:
        query = course_q.replace("CS", "CMPSC")
        data = data[data['course'].str.contains(query, na=False)]

    if prof_q:
        data = data[data['instructor'].str.contains(prof_q, na=False)]

    if not data.empty:
        st.write(f"Showing {min(len(data), 25)} undergraduate results:")
        for idx, row in data.head(25).iterrows():
            with st.container(border=True):
                colA, colB = st.columns([2, 1])
                with colA:
                    st.markdown(f"### {row['course']} | {row['quarter']} {row['year']}")
                    if st.button(f"{row['instructor']}", key=f"btn_{idx}"):
                        st.session_state.prof_view = row['join_key']
                        st.rerun()
                    r_val = f"⭐ {row['rmp_rating']}" if pd.notna(row.get('rmp_rating')) else "N/A"
                    st.write(f"**Dept:** {row['dept']} | **GPA:** `{row[gpa_col]:.2f}` | **RMP:** {r_val}")
                with colB:
                    grades = pd.DataFrame({'Grade': ['A', 'B', 'C', 'D', 'F'], 'Count': [row['a'], row['b'], row['c'], row['d'], row['f']]})
                    st.plotly_chart(px.bar(grades, x='Grade', y='Count', color='Grade', 
                                     color_discrete_map={'A':'#00CCFF','B':'#3498db','C':'#FFD700','D':'#e67e22','F':'#e74c3c'}, 
                                     template="plotly_dark", height=100).update_layout(margin=dict(l=0,r=0,t=0,b=0), showlegend=False, xaxis_visible=False, yaxis_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'), use_container_width=True, config={'displayModeBar': False}, key=f"fig_{idx}")
    else:
        st.info("No matching courses found.")

if __name__ == "__main__":
    main()
