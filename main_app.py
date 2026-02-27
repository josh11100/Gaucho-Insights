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

    # Filter: Undergrad only (No 99, max 198)
    def get_course_num(course_str):
        match = re.search(r'(\d+)', str(course_str))
        return int(match.group(1)) if match else None

    df['course_num_val'] = df['course'].apply(get_course_num)
    df = df[df['course_num_val'].notna()]
    df = df[(df['course_num_val'] <= 198) & (df['course_num_val'] != 99)]

    # Matcher Logic
    def get_registrar_key(name):
        if pd.isna(name): return "UNKNOWN"
        parts = str(name).upper().split()
        return f"{parts[0]}{parts[1][0] if len(parts) > 1 else ''}"

    def get_rmp_key(name):
        if pd.isna(name): return "UNKNOWN"
        parts = str(name).upper().split()
        return f"{parts[-1]}{parts[0][0] if len(parts) > 1 else ''}"

    df['join_key'] = df['instructor'].apply(get_registrar_key)

    if rmp_path:
        rmp_df = pd.read_csv(rmp_path)
        rmp_df.columns = [c.strip().lower() for c in rmp_df.columns]
        rmp_df = rmp_df.rename(columns={
            'instructor': 'instructor_rmp',
            'rating': 'rmp_rating',
            'difficulty': 'rmp_difficulty',
            'take_again': 'rmp_take_again',
            'tags': 'rmp_tags',
            'url': 'rmp_url'
        })
        rmp_df['rmp_join_key'] = rmp_df['instructor_rmp'].apply(get_rmp_key)
        df = pd.merge(df, rmp_df, left_on='join_key', right_on='rmp_join_key', how='left')
    
    for col in ['instructor', 'quarter', 'course', 'dept']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()

    gpa_col = next((c for c in ['avggpa', 'avg_gpa', 'avg gpa'] if c in df.columns), 'avggpa')
    
    group_cols = ['instructor', 'join_key', 'quarter', 'year', 'course', 'dept']
    agg_dict = {gpa_col: 'mean', 'a': 'sum', 'b': 'sum', 'c': 'sum', 'd': 'sum', 'f': 'sum'}
    for rmp_c in ['rmp_rating', 'rmp_difficulty', 'rmp_take_again', 'rmp_tags', 'rmp_url']:
        if rmp_c in df.columns: 
            agg_dict[rmp_c] = 'first'

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

    # --- SIDEBAR ---
    st.sidebar.header("🔍 FILTERS")
    all_depts = sorted(full_df['dept'].unique().tolist())
    selected_dept = st.sidebar.selectbox("Select Department", options=[" "] + all_depts, key="dept_persist")
    course_q = st.sidebar.text_input("COURSE # (e.g. 120B, 16)", key="course_persist").strip().upper()
    prof_q = st.sidebar.text_input("PROFESSOR NAME", key="prof_persist").strip().upper()

    if st.sidebar.button("Clear All Filters"):
        st.session_state.dept_persist = " "
        st.session_state.course_persist = ""
        st.session_state.prof_persist = ""
        st.rerun()

    data = full_df.copy()
    has_active_filter = False

    if selected_dept != " ":
        data = data[data['dept'] == selected_dept]
        has_active_filter = True
    if course_q:
        query = course_q.replace("CS", "CMPSC")
        data = data[data['course'].str.contains(query, na=False)]
        has_active_filter = True
    if prof_q:
        data = data[data['instructor'].str.contains(prof_q, na=False)]
        has_active_filter = True

    # --- 1. PROFESSOR PROFILE VIEW ---
    if st.session_state.prof_view:
        prof_key = st.session_state.prof_view
        prof_history = full_df[full_df['join_key'] == prof_key]
        
        if st.button("⬅️ Back to Search"):
            st.session_state.prof_view = None
            st.rerun()
        
        if not prof_history.empty:
            rmp = prof_history.iloc[0]
            st.header(f"👨‍🏫 {rmp['instructor']}")
            
            c1, c2 = st.columns([1, 1.2])
            with c1:
                st.subheader("Rate My Professor")
                if pd.notna(rmp.get('rmp_rating')):
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Rating", f"{rmp['rmp_rating']}/5")
                    m2.metric("Difficulty", f"{rmp['rmp_difficulty']}/5")
                    m3.metric("Take Again", f"{rmp.get('rmp_take_again', 'N/A')}")
                    
                    if pd.notna(rmp.get('rmp_tags')) and rmp['rmp_tags'] != "":
                        st.write("**Student Tags:**")
                        tags = str(rmp['rmp_tags']).split(',')
                        tag_html = "".join([f'<span style="background-color: #FFD700; color: black; padding: 4px 10px; border-radius: 12px; margin-right: 6px; font-size: 0.75rem; font-weight: bold; display: inline-block; margin-bottom: 5px;">{tag.strip().upper()}</span>' for tag in tags if tag.strip()])
                        st.markdown(tag_html, unsafe_allow_html=True)
                    
                    if pd.notna(rmp.get('rmp_url')):
                        st.markdown(f"<br><a href='{rmp['rmp_url']}' target='_blank' style='color: #00CCFF; text-decoration: none;'>View Original Reviews on RMP 🔗</a>", unsafe_allow_html=True)
                else:
                    st.info("No RMP data found.")
            
            with c2:
                st.subheader("Course History")
                history = prof_history.groupby(['course', 'dept']).agg({gpa_col: 'mean', 'instructor': 'count'}).rename(columns={gpa_col: 'Avg GPA', 'instructor': 'Sections'}).reset_index()
                history['Avg GPA'] = history['Avg GPA'].map('{:,.2f}'.format)
                st.dataframe(history, hide_index=True, use_container_width=True)
            
            st.divider()
            st.subheader("Grade Trends")
            trend_df = prof_history.copy().sort_values(by=['year', 'q_score'])
            trend_df['label'] = trend_df['quarter'] + " " + trend_df['year'].astype(str)
            st.plotly_chart(px.line(trend_df, x='label', y=gpa_col, color='course', markers=True, template="plotly_dark"), use_container_width=True)
        return

    # --- 2. ABOUT / LANDING PAGE ---
    if not has_active_filter:
        st.markdown("---")
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.header("Welcome to Gaucho Insights! 🎓")
            st.markdown("""
            ### What is this?
            Gaucho Insights is a comprehensive dashboard for UCSB students to analyze academic trends. 
            By merging official Registrar data with student-led reviews, we provide a holistic 
            view of the Gaucho classroom experience.
            
            ### 📍 How to use the UI
            - **Sidebar Navigation:** Use the filters on the left to start your search. Filter by department (e.g., PSTAT), course numbers, or professor names.
            - **Result Cards:** See grade distributions at a glance. High blue bars mean more A's!
            - **Detailed Profiles:** Click a professor's name to view historical GPA trends and specific RateMyProfessor tags.

            ### 📖 Glossary & Terms
            - **RMP (Rate My Professors):** A review site where students rate instructors on a 1-5 scale.
            - **Difficulty:** An RMP metric showing how hard students found the coursework (5 = Hardest).
            - **Avg GPA:** The average grade point assigned in a specific section, pulled from official records.
            """)
        
        with col_right:
            st.success(f"""
            **📊 Project Info**
            - **Data Recency:** Grades through Summer 2025.
            - **Sources:** UCSB Registrar & RateMyProfessors.
            - **Created By:** Joshua Chung
            """)
            
            # LinkedIn Call-to-Action
            st.markdown("""
            <div style="background-color: #0077b5; padding: 15px; border-radius: 10px; color: white; text-align: center; margin-top: 10px;">
                <p style="margin-bottom: 10px; font-weight: bold;">🚀 Like this project?</p>
                <a href="https://www.linkedin.com/in/joshua-chung858/" target="_blank" style="color: white; text-decoration: none; background-color: #005582; padding: 8px 15px; border-radius: 5px; font-size: 0.9em; font-weight: bold;">
                    Follow me on LinkedIn
                </a>
                <p style="margin-top: 10px; font-size: 0.8em;">For more useful Gaucho tools!</p>
            </div>
            """, unsafe_allow_html=True)

            st.write("---")
            st.info("💡 **Tip:** Try searching for 'ANTH' to see Summer 2025 data!")

        st.image("https://brand.ucsb.edu/sites/default/files/styles/flexslider_full/public/2021-12/ucsb-campus.jpg", caption="Helping Gauchos pick the right path.")
        return

    # --- 3. SEARCH RESULTS VIEW ---
    if not data.empty:
        st.write(f"Showing results based on your filters:")
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
                    fig = px.bar(grades, x='Grade', y='Count', color='Grade', 
                                 color_discrete_map={'A':'#00CCFF','B':'#3498db','C':'#FFD700','D':'#e67e22','F':'#e74c3c'}, 
                                 template="plotly_dark", height=100)
                    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), showlegend=False, xaxis_visible=False, yaxis_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"fig_{idx}")
    else:
        st.warning("No matches found. Try clearing your filters!")

if __name__ == "__main__":
    main()
