import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px
import streamlit.components.v1 as components

# --- 1. CONFIG & CSS ---
st.set_page_config(page_title="Gaucho Insights", layout="wide", page_icon="🎓")

def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

# --- 2. DATA ENGINE ---
@st.cache_data
def load_and_clean_data():
    def find_file(names):
        for name in names:
            paths = [name, os.path.join('data', name)]
            for p in paths:
                if os.path.exists(p): return p
        return None

    csv_path = find_file(['courseGrades.csv'])
    rmp_path = find_file(['rmp_final_data (1).csv', 'rmp_final_data.csv'])
    
    if not csv_path:
        st.error("Missing 'courseGrades.csv'.")
        st.stop()
        
    df = pd.read_csv(csv_path)
    df.columns = [str(c).strip().lower() for c in df.columns]

    def get_join_key(name):
        if pd.isna(name): return "UNKNOWN"
        parts = str(name).upper().replace(',', '').replace('.', '').replace('-', ' ').split()
        return f"{parts[0]} {parts[1][0]}" if len(parts) >= 2 else (parts[0] if parts else "UNKNOWN")

    df['join_key'] = df['instructor'].apply(get_join_key)
    
    if rmp_path:
        rmp_df = pd.read_csv(rmp_path)
        rmp_df.columns = [c.strip().lower() for c in rmp_df.columns]
        rmp_df['join_key'] = rmp_df['instructor'].apply(get_join_key)
        rmp_df = rmp_df.drop_duplicates(subset=['join_key'])

        if 'rmp_difficulty' in rmp_df.columns:
            rmp_df = rmp_df.rename(columns={'rmp_difficulty': 'rmp_diff'})
            
        rmp_cols = [c for c in rmp_df.columns if c.startswith('rmp_') or c == 'join_key']
        df = pd.merge(df, rmp_df[rmp_cols], on='join_key', how='left')

    df['course_num'] = df['course'].apply(lambda x: int(re.search(r'(\d+)', str(x)).group(1)) if re.search(r'(\d+)', str(x)) else None)
    df = df[(df['course_num'].notna()) & (df['course_num'] <= 198)]

    for col in ['instructor', 'quarter', 'course', 'dept']:
        if col in df.columns: df[col] = df[col].astype(str).str.upper().str.strip()

    gpa_col = next((c for c in ['avggpa', 'avg_gpa'] if c in df.columns), 'avggpa')
    return df, gpa_col

# --- 3. UI LOGIC ---
if 'selected_prof' not in st.session_state: st.session_state.selected_prof = None

def main():
    full_df, gpa_col = load_and_clean_data()

    st.markdown('<div style="text-align:center; padding:10px;"><h1 style="color:#FFD700; font-family:\'Orbitron\'; font-size:clamp(1.5rem, 5vw, 3rem);">(つ▀¯▀ )つ GAUCHO INSIGHTS ⊂(▀¯▀⊂ )</h1></div>', unsafe_allow_html=True)

    # --- VIEW: PROFESSOR PROFILE ---
    if st.session_state.selected_prof:
        prof_name = st.session_state.selected_prof
        prof_data = full_df[full_df['instructor'] == prof_name]
        
        if st.button("⬅ BACK TO SEARCH"):
            st.session_state.selected_prof = None
            st.rerun()

        st.title(f"👤 {prof_name}")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Career GPA", f"{prof_data[gpa_col].mean():.2f}")
        
        first = prof_data.iloc[0]
        if 'rmp_rating' in prof_data.columns and pd.notna(first['rmp_rating']):
            m2.metric("RMP Quality", f"{first['rmp_rating']}/5.0")
            m3.metric("Difficulty", f"{first.get('rmp_diff', 'N/A')}/5.0")
            m4.metric("Take Again", f"{first.get('rmp_take_again', 'N/A')}")
            
            st.subheader("Career Grade Distribution")
            # Aggregated grades for all classes taught
            grades = ['a', 'b', 'c', 'd', 'f']
            total_grades = [prof_data[g].sum() for g in grades if g in prof_data.columns]
            fig_career = px.bar(x=[g.upper() for g in grades], y=total_grades, template="plotly_dark", color_discrete_sequence=['#00CCFF'])
            fig_career.update_layout(height=300, margin=dict(l=0,r=0,t=20,b=0))
            st.plotly_chart(fig_career, use_container_width=True)

            if 'rmp_tags' in prof_data.columns and pd.notna(first['rmp_tags']):
                st.subheader("Professor Tags")
                tags = str(first['rmp_tags']).replace('"', '').split(',')
                tag_html = "".join([f"<span class='tag-pill'>{t.strip()}</span>" for t in tags if t.strip().lower() != "none"])
                st.markdown(tag_html, unsafe_allow_html=True)
        else:
            st.info("No RMP data found.")

        st.subheader("Teaching History")
        st.dataframe(prof_data[['course', 'quarter', 'year', gpa_col]].sort_values('year', ascending=False), use_container_width=True)
        st.stop()

    # --- VIEW: SEARCH TABS ---
    tab1, tab2 = st.tabs(["🏠 HOME", "🔍 SEARCH TOOL"])

    with tab1:
        st.markdown("""<div style="background:rgba(0,31,63,0.7); border:2px solid #FFD700; border-radius:20px; padding:30px;">
            <h2 style="color:#FFD700; font-family:'Orbitron';">WELCOME GAUCHOS!</h2>
            <p>Now including <b>Professor Tags</b>. Search for "Amazing Lectures" or "Tough Grader" in the filters!</p>
        </div>""", unsafe_allow_html=True)

    with tab2:
        st.sidebar.header("( 🔍 ) FILTERS")
        
        # 1. Dept Filter
        all_depts = sorted(full_df['dept'].unique().tolist())
        sel_dept = st.sidebar.selectbox("Department", [" "] + all_depts, key="dept_query")
        
        # 2. Tag Filter
        all_tags = set()
        if 'rmp_tags' in full_df.columns:
            for t_str in full_df['rmp_tags'].dropna():
                for t in t_str.replace('"', '').split(','):
                    if t.strip().lower() != "none": all_tags.add(t.strip())
        sel_tags = st.sidebar.multiselect("Filter by RMP Tags", options=sorted(list(all_tags)))

        c_q = st.sidebar.text_input("Course #", key="course_query").strip().upper()
        p_q = st.sidebar.text_input("Professor Name", key="prof_query").strip().upper()

        # Apply logic
        results = full_df.copy()
        if sel_dept != " ": results = results[results['dept'] == sel_dept]
        if c_q: results = results[results['course'].str.contains(c_q, na=False)]
        if p_q: results = results[results['instructor'].str.contains(p_q, na=False)]
        if sel_tags:
            # Filter rows where at least one selected tag is present in rmp_tags string
            results = results[results['rmp_tags'].apply(lambda x: any(tag in str(x) for tag in sel_tags) if pd.notna(x) else False)]

        for idx, row in results.head(15).iterrows():
            with st.container(border=True):
                cA, cB = st.columns([2, 1])
                with cA:
                    st.markdown(f"### {row['course']} | {row['quarter']} {row['year']}")
                    if st.button(f"👤 {row['instructor']}", key=f"btn_{idx}"):
                        st.session_state.selected_prof = row['instructor']
                        st.rerun()
                    st.write(f"**GPA:** {row[gpa_col]:.2f}")
                with cB:
                    fig = px.bar(x=['A','B','C','D','F'], 
                                 y=[row.get('a',0), row.get('b',0), row.get('c',0), row.get('d',0), row.get('f',0)], 
                                 height=120, template="plotly_dark")
                    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True, key=f"f_{idx}", config={'displayModeBar': False})

if __name__ == "__main__":
    main()
