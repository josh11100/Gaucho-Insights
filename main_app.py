import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px
import streamlit.components.v1 as components 

st.set_page_config(page_title="Gaucho Insights", layout="wide", page_icon="🎓")

# --- DATA LOADING & CLEANING ---
@st.cache_data
def load_and_clean_data():
    def find_file(name):
        paths_to_check = [name, os.path.join('data', name)]
        for p in paths_to_check:
            if os.path.exists(p): return p
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
        rmp_df = rmp_df.rename(columns={'instructor': 'instructor_rmp', 'rating': 'rmp_rating', 'difficulty': 'rmp_difficulty', 'take_again': 'rmp_take_again', 'tags': 'rmp_tags', 'url': 'rmp_url'})
        rmp_df['rmp_join_key'] = rmp_df['instructor_rmp'].apply(get_rmp_key)
        df = pd.merge(df, rmp_df, left_on='join_key', right_on='rmp_join_key', how='left')
    
    for col in ['instructor', 'quarter', 'course', 'dept']:
        if col in df.columns: df[col] = df[col].astype(str).str.upper().str.strip()

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

def reset_filters():
    st.session_state.dept_query = " "
    st.session_state.course_query = ""
    st.session_state.prof_query = ""

# --- GLOBAL STYLES & FULL-SCREEN STATISTICAL MESH ---
st.markdown("""
    <style>
    .stApp { background-color: #000b1a; }
    /* Transparent backgrounds for standard Streamlit containers to show the mesh */
    [data-testid="stHeader"], [data-testid="stToolbar"] { background: transparent; }
    
    /* Glassmorphism for containers */
    div[data-testid="stVerticalBlock"] > div:has(div.stMarkdown) {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(8px);
        border-radius: 20px;
    }
    </style>
    <canvas id="meshCanvas" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -1; pointer-events: none;"></canvas>
    <script>
        const canvas = document.getElementById('meshCanvas');
        const ctx = canvas.getContext('2d');
        let particles = [];
        let mouse = { x: null, y: null, radius: 150 };

        function init() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            particles = [];
            for (let i = 0; i < 100; i++) {
                particles.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    vx: (Math.random() - 0.5) * 0.7,
                    vy: (Math.random() - 0.5) * 0.7,
                    radius: 2
                });
            }
        }

        window.addEventListener('mousemove', (e) => { mouse.x = e.x; mouse.y = e.y; });
        window.addEventListener('resize', init);

        function animate() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            particles.forEach((p, i) => {
                p.x += p.vx; p.y += p.vy;
                if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
                if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

                ctx.beginPath();
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.fillStyle = "rgba(255, 215, 0, 0.5)";
                ctx.fill();

                for (let j = i + 1; j < particles.length; j++) {
                    let p2 = particles[j];
                    let dist = Math.hypot(p.x - p2.x, p.y - p2.y);
                    if (dist < 120) {
                        ctx.strokeStyle = `rgba(0, 116, 217, ${1 - dist/120})`;
                        ctx.lineWidth = 0.5;
                        ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p2.x, p2.y); ctx.stroke();
                    }
                }
                
                if (mouse.x) {
                    let mdist = Math.hypot(p.x - mouse.x, p.y - mouse.y);
                    if (mdist < mouse.radius) {
                        ctx.strokeStyle = `rgba(255, 215, 0, ${1 - mdist/mouse.radius})`;
                        ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(mouse.x, mouse.y); ctx.stroke();
                    }
                }
            });
            requestAnimationFrame(animate);
        }
        init(); animate();
    </script>
""", unsafe_allow_html=True)

def main():
    full_df, gpa_col = load_and_clean_data()

    # --- 3D HERO HEADER ---
    hero_html = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@900&display=swap');
        .hero-container { perspective: 1000px; display: flex; justify-content: center; height: 120px; align-items: center; }
        .hero-title { font-family: 'Orbitron', sans-serif; font-size: 3.5rem; color: #FFD700; transform-style: preserve-3d; transition: transform 0.1s; cursor: default; }
    </style>
    <div class="hero-container" id="hBox">
        <div class="hero-title" id="hText">(つ▀¯▀ )つ GAUCHO INSIGHTS ⊂(▀¯▀⊂ )</div>
    </div>
    <script>
        const hBox = document.getElementById('hBox'); const hText = document.getElementById('hText');
        hBox.onmousemove = (e) => {
            let r = hBox.getBoundingClientRect();
            hText.style.transform = `rotateY(${(e.clientX - r.left - r.width/2)/15}deg) rotateX(${-(e.clientY - r.top - r.height/2)/5}deg) translateZ(30px)`;
        }
        hBox.onmouseleave = () => hText.style.transform = 'rotateY(0) rotateX(0)';
    </script>
    """
    components.html(hero_html, height=140)

    tab1, tab2 = st.tabs(["( 🏠 ) Home", "( 🔍 ) Search Tool"])

    with tab1:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.markdown(f"""
                <div style="background: rgba(0, 31, 63, 0.6); padding: 35px; border-radius: 20px; border: 1px solid rgba(255, 215, 0, 0.3); backdrop-filter: blur(12px); color: white;">
                    <h2 style="color: #FFD700; font-family: 'Orbitron';">WELCOME GAUCHOS! ٩(◕‿◕)۶</h2>
                    <p style="font-size: 1.1em; line-height: 1.6;">
                        <b>WHAT IS THIS?</b><br>
                        Gaucho Insights is a tool designed to help you survive your schedule. As a Stats and Data Science major, I built this to visualize exactly how stressful 
                        certain classes are. <b>The mesh background represents live data nodes connecting in real-time.</b>
                    </p>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 30px;">
                        <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 15px; border-left: 4px solid #FFD700;">
                            <b>( 📍 ) HOW TO USE</b><br>Filter by dept/prof in the Search Tool to see grade distributions.
                        </div>
                        <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 15px; border-left: 4px solid #0074D9;">
                            <b>( 📖 ) GLOSSARY</b><br>Avg GPA and RMP ratings help you gauge difficulty.
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with col_right:
            # 3D Project Info Card
            components.html("""
            <style>
                .card { width: 280px; height: 320px; background: linear-gradient(135deg, #001f3f 0%, #0074D9 100%); border-radius: 20px; border: 2px solid #FFD700; transform-style: preserve-3d; transition: transform 0.1s; display: flex; flex-direction: column; justify-content: space-around; padding: 20px; color: white; text-align: center; }
            </style>
            <div style="perspective: 1000px; display: flex; justify-content: center;">
                <div class="card" id="c">
                    <h2 style="color: #FFD700">📊 Info</h2>
                    <p><b>Data:</b> Thru 2025<br><b>Created By:</b> Joshua Chung</p>
                    <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 10px;">ദ്ദി(˵ •̀ ᴗ - ˵ ) ✧</div>
                </div>
            </div>
            <script>
                const c = document.getElementById('c');
                window.onmousemove = (e) => {
                    let r = c.getBoundingClientRect();
                    c.style.transform = `rotateY(${(e.clientX - r.left - r.width/2)/12}deg) rotateX(${-(e.clientY - r.top - r.height/2)/12}deg)`;
                }
            </script>
            """, height=350)
            
            st.markdown("""<a href="https://www.linkedin.com/in/joshua-chung858/" target="_blank" style="text-decoration: none;">
                <div style="background: #0077b5; padding: 12px; border-radius: 12px; text-align: center; color: white; font-weight: bold; border: 1px solid #FFD700;">Follow on LinkedIn</div>
            </a>""", unsafe_allow_html=True)

    with tab2:
        st.sidebar.header("( 🔍 ) FILTERS")
        all_depts = sorted(full_df['dept'].unique().tolist())
        selected_dept = st.sidebar.selectbox("Select Department", options=[" "] + all_depts, key="dept_query")
        course_q = st.sidebar.text_input("COURSE #", key="course_query").strip().upper()
        prof_q = st.sidebar.text_input("PROFESSOR NAME", key="prof_query").strip().upper()

        data = full_df.copy()
        if selected_dept != " ": data = data[data['dept'] == selected_dept]
        if course_q: data = data[data['course'].str.contains(course_q.replace("CS", "CMPSC"), na=False)]
        if prof_q: data = data[data['instructor'].str.contains(prof_q, na=False)]

        if not data.empty:
            for idx, row in data.head(15).iterrows():
                gpa_val = row[gpa_col]
                color = "#2ecc71" if gpa_val >= 3.5 else "#f1c40f" if gpa_val >= 3.0 else "#e74c3c"
                
                with st.container():
                    c1, c2 = st.columns([1.5, 1])
                    with c1:
                        st.markdown(f"""
                            <div style="background: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 15px; border-left: 5px solid {color}; margin-bottom: 15px;">
                                <h3 style="margin: 0; color: white;">{row['course']}</h3>
                                <p style="color: #FFD700; font-weight: bold; margin: 5px 0;">{row['instructor']}</p>
                                <p style="font-size: 0.9em; color: #bbb;">{row['quarter']} {row['year']} | GPA: {gpa_val:.2f}</p>
                            </div>
                        """, unsafe_allow_html=True)
                    with c2:
                        grades = pd.DataFrame({'Grade': ['A', 'B', 'C', 'D', 'F'], 'Count': [row['a'], row['b'], row['c'], row['d'], row['f']]})
                        fig = px.bar(grades, x='Grade', y='Count', color='Grade', template="plotly_dark", height=130)
                        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_visible=False, yaxis_visible=False)
                        st.plotly_chart(fig, use_container_width=True, key=f"f_{idx}")
        else:
            st.warning("( ⊙_⊙ ) No matches found.")

if __name__ == "__main__":
    main()
