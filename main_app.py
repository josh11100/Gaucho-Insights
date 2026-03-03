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

# --- GLOBAL STYLES & FULL-SCREEN MESH ---
st.markdown("""
    <style>
    .stApp { background-color: #000b1a; }
    /* Hide default Streamlit borders for a cleaner look */
    [data-testid="stMetricContainer"] { background: rgba(255, 255, 255, 0.05); border-radius: 10px; padding: 10px; }
    </style>
    <canvas id="fullScreenMesh" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -1; pointer-events: none;"></canvas>
    <script>
        const canvas = document.getElementById('fullScreenMesh');
        const ctx = canvas.getContext('2d');
        let particles = [];
        let mouse = { x: null, y: null, radius: 150 };

        function initCanvas() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            particles = [];
            for (let i = 0; i < 80; i++) {
                particles.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    vx: (Math.random() - 0.5) * 0.6,
                    vy: (Math.random() - 0.5) * 0.6,
                    size: Math.random() * 2 + 1
                });
            }
        }
        window.addEventListener('mousemove', (e) => { mouse.x = e.x; mouse.y = e.y; });
        window.addEventListener('resize', initCanvas);

        function animate() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            particles.forEach((p, i) => {
                p.x += p.vx; p.y += p.vy;
                if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
                if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(255, 215, 0, 0.4)';
                ctx.fill();

                for (let j = i + 1; j < particles.length; j++) {
                    let p2 = particles[j];
                    let dist = Math.hypot(p.x - p2.x, p.y - p2.y);
                    if (dist < 130) {
                        ctx.strokeStyle = `rgba(0, 116, 217, ${1 - dist/130})`;
                        ctx.lineWidth = 0.6;
                        ctx.beginPath();
                        ctx.moveTo(p.x, p.y);
                        ctx.lineTo(p2.x, p2.y);
                        ctx.stroke();
                    }
                }
                if (mouse.x) {
                    let mdist = Math.hypot(p.x - mouse.x, p.y - mouse.y);
                    if (mdist < mouse.radius) {
                        ctx.strokeStyle = 'rgba(255, 215, 0, 0.15)';
                        ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(mouse.x, mouse.y); ctx.stroke();
                    }
                }
            });
            requestAnimationFrame(animate);
        }
        initCanvas();
        animate();
    </script>
""", unsafe_allow_html=True)

def main():
    full_df, gpa_col = load_and_clean_data()

    # --- 3D HERO HEADER ---
    hero_html = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@900&display=swap');
        .hero-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 3.5rem; color: #FFD700; text-align: center;
            perspective: 1000px; padding: 20px 0;
        }
        .inner-text { transition: transform 0.1s; display: inline-block; cursor: default; }
    </style>
    <div class="hero-title" id="hb"><span class="inner-text" id="ht">(つ▀¯▀ )つ GAUCHO INSIGHTS ⊂(▀¯▀⊂ )</span></div>
    <script>
        const hb = document.getElementById('hb'); const ht = document.getElementById('ht');
        hb.onmousemove = (e) => {
            let r = hb.getBoundingClientRect();
            let x = (e.clientX - r.left - r.width/2)/20;
            let y = (e.clientY - r.top - r.height/2)/10;
            ht.style.transform = `rotateY(${x}deg) rotateX(${-y}deg) translateZ(30px)`;
        }
        hb.onmouseleave = () => ht.style.transform = 'rotateY(0) rotateX(0)';
    </script>
    """
    components.html(hero_html, height=140)

    tab1, tab2 = st.tabs(["( 🏠 ) Home", "( 🔍 ) Search Tool"])

    with tab1:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.markdown(f"""
                <div style="background: rgba(0, 31, 63, 0.6); padding: 35px; border-radius: 20px; border: 1px solid rgba(255, 215, 0, 0.3); backdrop-filter: blur(15px);">
                    <h1 style="color: #FFD700; font-family: 'Orbitron'; margin-bottom: 15px;">WELCOME GAUCHOS!</h1>
                    <p style="font-size: 1.15em; color: white; line-height: 1.6;">
                        This is <b>Gaucho Insights</b>—the intersection of registrar data and student experience. 
                        As a Stats and Data Science major, I built this dashboard to provide transparency into grading trends and professor ratings.
                    </p>
                    <hr style="border: 0.5px solid rgba(255,215,0,0.2); margin: 25px 0;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div style="background: rgba(255,255,255,0.03); padding: 15px; border-radius: 12px; border-left: 4px solid #FFD700;">
                            <h4 style="color: #FFD700; margin-top:0;">( 📍 ) MISSION</h4>
                            <p style="color: #ccc; font-size: 0.95em; margin-bottom:0;">Empowering students to optimize their schedules using historical success metrics.</p>
                        </div>
                        <div style="background: rgba(255,255,255,0.03); padding: 15px; border-radius: 12px; border-left: 4px solid #0074D9;">
                            <h4 style="color: #0074D9; margin-top:0;">( 🔍 ) THE TECH</h4>
                            <p style="color: #ccc; font-size: 0.95em; margin-bottom:0;">Built with Python and live JavaScript mesh networking to represent complex data structures.</p>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with col_right:
            gaucho_info_3d = """
            <style>
                .card {
                    width: 280px; height: 320px; background: linear-gradient(135deg, rgba(0,31,63,0.9), rgba(0,116,217,0.8));
                    border-radius: 20px; border: 2px solid #FFD700; transform-style: preserve-3d; transition: transform 0.1s;
                    display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; text-align: center; padding: 20px;
                }
            </style>
            <div style="perspective: 1000px; display: flex; justify-content: center; height: 350px;">
                <div class="card" id="c">
                    <h2 style="color:#FFD700; margin-bottom: 10px;">📊 Project Info</h2>
                    <p style="font-size: 0.9em;"><b>Data:</b> Through 2025<br><b>Source:</b> UCSB & RMP<br><b>Created By:</b> Joshua Chung</p>
                    <div style="margin-top: 20px; background: rgba(255,255,255,0.1); padding: 8px; border-radius: 10px; font-size: 0.8em;">Stats & Data Science</div>
                </div>
            </div>
            <script>
                const c = document.getElementById('c');
                c.onmousemove = (e) => {
                    let r = c.getBoundingClientRect();
                    c.style.transform = `rotateY(${(e.clientX - r.left - r.width/2)/10}deg) rotateX(${-(e.clientY - r.top - r.height/2)/10}deg)`;
                }
                c.onmouseleave = () => c.style.transform = 'rotateY(0) rotateX(0)';
            </script>
            """
            components.html(gaucho_info_3d, height=360)
            
            st.markdown("""<a href="https://www.linkedin.com/in/joshua-chung858/" target="_blank" style="text-decoration: none;">
                <div style="background: #0077b5; padding: 12px; border-radius: 12px; text-align: center; color: white; font-weight: bold; border: 1px solid #FFD700; transition: 0.3s;" onmouseover="this.style.background='#005e93'" onmouseout="this.style.background='#0077b5'">
                    Follow on LinkedIn 🎓
                </div>
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
                # Dynamic Stress Badging
                if gpa_val >= 3.5: status, color = "CHILL", "#2ecc71"
                elif gpa_val >= 3.0: status, color = "MODERATE", "#f1c40f"
                else: status, color = "STRESSFUL", "#e74c3c"

                c1, c2 = st.columns([1.5, 1])
                with c1:
                    st.markdown(f"""
                        <div style="background: rgba(255, 255, 255, 0.04); backdrop-filter: blur(10px); border-left: 5px solid {color}; padding: 18px; border-radius: 12px; margin-bottom: 15px; border-top: 1px solid rgba(255,255,255,0.05); border-right: 1px solid rgba(255,255,255,0.05);">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <h3 style="margin: 0; color: white; font-family: 'Orbitron';">{row['course']}</h3>
                                <span style="background: {color}; color: black; padding: 2px 10px; border-radius: 20px; font-weight: 800; font-size: 0.75em;">{status}</span>
                            </div>
                            <p style="margin: 8px 0 2px 0; color: #FFD700; font-weight: bold; font-size: 1.1em;">{row['instructor']}</p>
                            <p style="margin: 0; color: #bbb; font-size: 0.85em;">{row['quarter']} {row['year']} | Avg GPA: <b style="color: white;">{gpa_val:.2f}</b></p>
                        </div>
                    """, unsafe_allow_html=True)
                with c2:
                    grades = pd.DataFrame({'Grade': ['A', 'B', 'C', 'D', 'F'], 'Count': [row['a'], row['b'], row['c'], row['d'], row['f']]})
                    fig = px.bar(grades, x='Grade', y='Count', color='Grade', color_discrete_sequence=["#0074D9", "#00458b", "#FFD700", "#c0c0c0", "#e74c3c"], template="plotly_dark", height=130)
                    fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_visible=False, yaxis_visible=False)
                    st.plotly_chart(fig, use_container_width=True, key=f"f_{idx}")
        else:
            st.warning("( ⊙_⊙ ) No matches found.")

if __name__ == "__main__":
    main()
