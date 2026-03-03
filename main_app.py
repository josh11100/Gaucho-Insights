import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px
import streamlit.components.v1 as components 

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

    def get_course_num(course_str):
        match = re.search(r'(\d+)', str(course_str))
        return int(match.group(1)) if match else None

    df['course_num_val'] = df['course'].apply(get_course_num)
    df = df[df['course_num_val'].notna()]
    df = df[(df['course_num_val'] <= 198) & (df['course_num_val'] != 99)]

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

def reset_filters():
    st.session_state.dept_query = " "
    st.session_state.course_query = ""
    st.session_state.prof_query = ""

def main():
    st.title("(つ▀¯▀ )つ GAUCHO INSIGHTS ⊂(▀¯▀⊂ )")
    full_df, gpa_col = load_and_clean_data()

    if 'prof_view' not in st.session_state:
        st.session_state.prof_view = None

    tab1, tab2 = st.tabs(["( 🏠 ) Home", "( 🔍 ) Search Tool"])

    with tab1:
        st.markdown("---")
        
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.header("WELCOME TO GAUCHO INSIGHTS! ٩(◕‿◕)۶")
            st.markdown("""
            ### WHAT IS THIS?
            Gaucho Insights is a tool designed to help you survive your schedule. This dashboard helps you see exactly how stressful 
            certain classes are with specific professors **(ノಠ益ಠ)ノ彡┻━┻**. 
            
            By merging official UCSB Registrar data with RMP reviews, we let you see if that "Easy GE" is actually a GPA killer.
            
            ### ( 📍 ) HOW TO USE THE UI
            - **Sidebar Navigation:** Head to the 'Search Tool' tab and use the filters.
            - **Result Cards:** High blue bars mean more A's! Low bars mean... well, you know.
            - **Detailed Profiles:** Click a professor's name to see their historical "Stress Levels" (GPA trends).

            ### ( 📖 ) GLOSSARY & TERMS
            - **RMP (Rate My Professors):** The student bible for avoiding bad vibes.
            - **Difficulty:** A 1-5 scale of how much sleep you'll lose (5 = Hardest).
            - **Avg GPA:** The actual average grade awarded. Numbers don't lie.
            """)
        
        with col_right:
            # --- RESTORED 3D GAUCHO INFO CARD ---
            gaucho_info_3d = """
            <style>
                .container { perspective: 1000px; display: flex; justify-content: center; align-items: center; height: 360px; }
                .card {
                    width: 300px; height: 340px; background: linear-gradient(135deg, #001f3f 0%, #0074D9 100%);
                    border-radius: 20px; border: 2px solid #FFD700; box-shadow: 0 20px 20px rgba(0,0,0,0.5);
                    transform-style: preserve-3d; transition: transform 0.1s ease;
                    display: flex; flex-direction: column; justify-content: space-between; padding: 20px; color: white; text-align: center;
                }
                .card-title { font-size: 1.5em; font-weight: bold; color: #FFD700; transform: translateZ(50px); }
                .card-body { font-size: 1em; transform: translateZ(30px); line-height: 1.5; }
                .card-footer { font-size: 0.9em; transform: translateZ(20px); background: rgba(255,255,255,0.1); padding: 10px; border-radius: 10px; }
            </style>
            <div class="container">
                <div class="card" id="card">
                    <div class="card-title">📊 Gaucho Info</div>
                    <div class="card-body">
                        <b>Data Recency:</b> Through Summer 2025.<br><br>
                        <b>Sources:</b> UCSB Registrar & RMP.<br><br>
                        <b>Created By:</b> Joshua Chung
                    </div>
                    <div class="card-footer">Move cursor to rotate!<br>ദ്ദി(˵ •̀ ᴗ - ˵ ) ✧</div>
                </div>
            </div>
            <script>
                const card = document.getElementById('card');
                const container = card.parentElement;
                container.addEventListener('mousemove', (e) => {
                    let rect = container.getBoundingClientRect();
                    let x = e.clientX - rect.left - rect.width / 2;
                    let y = e.clientY - rect.top - rect.height / 2;
                    card.style.transform = `rotateY(${x / 10}deg) rotateX(${-y / 10}deg)`;
                });
                container.addEventListener('mouseleave', () => {
                    card.style.transform = `rotateY(0deg) rotateX(0deg)`;
                    card.style.transition = 'transform 0.5s ease';
                });
                container.addEventListener('mouseenter', () => { card.style.transition = 'transform 0.1s ease'; });
            </script>
            """
            components.html(gaucho_info_3d, height=360)

            # --- 3D LINKEDIN BUTTON WITH PHYSICS ---
            linkedin_3d = """
            <style>
                .li-container { perspective: 1000px; display: flex; justify-content: center; padding: 10px; }
                .li-card {
                    width: 100%; max-width: 300px; background: #0077b5; border-radius: 15px; border: 2px solid #FFD700;
                    padding: 15px; color: white; text-align: center; text-decoration: none; font-weight: bold;
                    transform-style: preserve-3d; transition: transform 0.1s ease;
                }
                .li-text { transform: translateZ(30px); display: block; }
            </style>
            <div class="li-container">
                <a href="https://www.linkedin.com/in/joshua-chung858/" target="_blank" class="li-card" id="liCard">
                    <span class="li-text">
                        ദ്ദി(˵ •̀ ᴗ - ˵ ) ✧ Like this project?<br>
                        Follow me on LinkedIn
                    </span>
                </a>
            </div>
            <script>
                const liCard = document.getElementById('liCard');
                const liContainer = liCard.parentElement;
                liContainer.addEventListener('mousemove', (e) => {
                    let rect = liContainer.getBoundingClientRect();
                    let x = e.clientX - rect.left - rect.width / 2;
                    let y = e.clientY - rect.top - rect.height / 2;
                    liCard.style.transform = `rotateY(${x / 15}deg) rotateX(${-y / 15}deg)`;
                });
                liContainer.addEventListener('mouseleave', () => {
                    liCard.style.transform = `rotateY(0deg) rotateX(0deg)`;
                    liCard.style.transition = 'transform 0.5s ease';
                });
                liContainer.addEventListener('mouseenter', () => { liCard.style.transition = 'transform 0.1s ease'; });
            </script>
            """
            components.html(linkedin_3d, height=120)

            st.write("---")
            st.info("( 💡 ) Tip: Switch to the 'Search Tool' tab to check your schedule!")

    with tab2:
        # --- (Existing Search Tool Logic remains the same) ---
        st.sidebar.header("( 🔍 ) FILTERS")
        all_depts = sorted(full_df['dept'].unique().tolist())
        selected_dept = st.sidebar.selectbox("Select Department", options=[" "] + all_depts, key="dept_query")
        course_q = st.sidebar.text_input("COURSE #", key="course_query").strip().upper()
        prof_q = st.sidebar.text_input("PROFESSOR NAME", key="prof_query").strip().upper()

        if st.sidebar.button("( ✖ ) Clear All", on_click=reset_filters):
            st.rerun()

        data = full_df.copy()
        if selected_dept != " ":
            data = data[data['dept'] == selected_dept]
        if course_q:
            query = course_q.replace("CS", "CMPSC")
            data = data[data['course'].str.contains(query, na=False)]
        if prof_q:
            data = data[data['instructor'].str.contains(prof_q, na=False)]

        if not data.empty:
            st.write(f"( ─‿─ ) Showing results:")
            for idx, row in data.head(25).iterrows():
                with st.container(border=True):
                    colA, colB = st.columns([2, 1])
                    with colA:
                        st.markdown(f"### {row['course']} | {row['quarter']} {row['year']}")
                        st.write(f"**Instructor:** {row['instructor']}")
                        gpa_val = row[gpa_col]
                        gpa_emo = "°˖✧◝(⁰▿⁰)◜✧˖°" if gpa_val > 3.4 else "┐(~ー~;)┌" if gpa_val >= 3.1 else "(╥﹏╥)"
                        st.write(f"**GPA:** {gpa_emo} `{gpa_val:.2f}`")
                    with colB:
                        grades = pd.DataFrame({'Grade': ['A', 'B', 'C', 'D', 'F'], 'Count': [row['a'], row['b'], row['c'], row['d'], row['f']]})
                        fig = px.bar(grades, x='Grade', y='Count', color='Grade', template="plotly_dark", height=120)
                        fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), showlegend=False, xaxis_visible=False, yaxis_visible=False)
                        st.plotly_chart(fig, use_container_width=True, key=f"fig_{idx}")
        else:
            st.warning("( ⊙_⊙ ) No matches found.")

if __name__ == "__main__":
    main()
