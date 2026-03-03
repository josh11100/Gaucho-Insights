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

# --- GLOBAL STYLES & BACKGROUND MESH ---
# This injects a full-screen canvas behind the Streamlit app
st.markdown("""
    <style>
    .stApp {
        background-color: #000b1a;
    }
    /* Frosted glass effect for containers */
    [data-testid="stVerticalBlock"] > div:has(div.stAlert) {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
    }
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
            for (let i = 0; i < 100; i++) {
                particles.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    vx: (Math.random() - 0.5) * 0.8,
                    vy: (Math.random() - 0.5) * 0.8,
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
                ctx.fillStyle = 'rgba(255, 215, 0, 0.5)';
                ctx.fill();

                for (let j = i + 1; j < particles.length; j++) {
                    let p2 = particles[j];
                    let dx = p.x - p2.x;
                    let dy = p.y - p2.y;
                    let dist = Math.sqrt(dx*dx + dy*dy);
                    if (dist < 120) {
                        ctx.strokeStyle = `rgba(0, 116, 217, ${1 - dist/120})`;
                        ctx.lineWidth = 0.5;
                        ctx.beginPath();
                        ctx.moveTo(p.x, p.y);
                        ctx.lineTo(p2.x, p2.y);
                        ctx.stroke();
                    }
                }
                // Mouse interaction
                if (mouse.x) {
                    let mdx = p.x - mouse.x;
                    let mdy = p.y - mouse.y;
                    let mdist = Math.sqrt(mdx*mdx + mdy*mdy);
                    if (mdist < mouse.radius) {
                        ctx.strokeStyle = 'rgba(255, 215, 0, 0.2)';
                        ctx.beginPath();
                        ctx.moveTo(p.x, p.y);
                        ctx.lineTo(mouse.x, mouse.y);
                        ctx.stroke();
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
            font-size: 4rem;
            color: #FFD700;
            text-align: center;
            perspective: 1000px;
            padding: 40px 0;
            cursor: pointer;
        }
        .inner-text { transition: transform 0.1s; display: inline-block; }
    </style>
    <div class="hero-title" id="hb"><span class="inner-text" id="ht">(つ▀¯▀ )つ GAUCHO INSIGHTS ⊂(▀¯▀⊂ )</span></div>
    <script>
        const hb = document.getElementById('hb');
        const ht = document.getElementById('ht');
        hb.onmousemove = (e) => {
            let r = hb.getBoundingClientRect();
            let x = (e.clientX - r.left - r.width/2)/15;
            let y = (e.clientY - r.top - r.height/2)/5;
            ht.style.transform = `rotateY(${x}deg) rotateX(${-y}deg) scale(1.05)`;
        }
        hb.onmouseleave = () => ht.style.transform = 'rotateY(0) rotateX(0) scale(1)';
    </script>
    """
    components.html(hero_html, height=180)

    tab1, tab2 = st.tabs(["( 🏠 ) Home", "( 🔍 ) Search Tool"])

    with tab1:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.markdown(f"""
                <div style="background: rgba(0, 31, 63, 0.6); padding: 40px; border-radius: 20px; border: 1px solid rgba(255, 215, 0, 0.4); backdrop-filter: blur(12px);">
                    <h1 style="color: #FFD700; font-family: 'Orbitron'; margin-bottom: 20px;">WELCOME GAUCHOS!</h1>
                    <p style="font-size: 1.2em; color: white;">This is <b>Gaucho Insights</b>—where data meets the classroom. As a Stats and Data Science major, I built this to help you navigate UCSB's curriculum using actual registrar data and student sentiment.</p>
                    <hr style="border: 0.5px solid rgba(255,215,0,0.2); margin: 30px 0;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
                        <div>
                            <h3 style="color: #0074D9;">( 📍 ) MISSION</h3>
                            <p style="color: #ddd;">Empowering students to make informed decisions about their quarterly schedules and academic path.</p>
                        </div>
                        <div>
                            <h3 style="color: #0074D9;">( 🔍 ) THE TECH</h3>
                            <p style="color: #ddd;">Utilizing Python, Streamlit, and D3-inspired mesh networks to visualize grade distributions.</p>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with col_right:
            # Reusing your 3D card for continuity
            gaucho_info_3d = """
            <style>
                .card {
                    width: 300px; height: 350px; background: linear-gradient(135deg, rgba(0,31,63,0.9), rgba(0,116,217,0.8));
                    border-radius: 20px; border: 2px solid #FFD700; transform-style: preserve-3d; transition: transform 0.1s;
                    display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; text-align: center; padding: 20px;
                }
            </style>
            <div style="perspective: 1000px; display: flex; justify-content: center; height: 380px;">
                <div class="card" id="c">
                    <h2 style="color:#FFD700">📊 Gaucho Info</h2>
                    <p><b>Data:</b> Thru Summer 2025<br><br><b>Source:</b> Registrar & RMP</p>
                    <p style="font-size: 0.8em; margin-top: 20px;">Move cursor to tilt!</p>
                </div>
            </div>
            <script>
                const c = document.getElementById('c');
                c.onmousemove = (e) => {
                    let r = c.getBoundingClientRect();
                    let x = (e.clientX - r.left - r.width/2)/10;
                    let y = (e.clientY - r.top - r.height/2)/10;
                    c.style.transform = `rotateY(${x}deg) rotateX(${-y}deg)`;
                }
                c.onmouseleave = () => c.style.transform = 'rotateY(0) rotateX(0)';
            </script>
            """
            components.html(gaucho_info_3d, height=400)
            
            # LinkedIn
            st.markdown("""<a href="https://www.linkedin.com/in/joshua-chung858/" target="_blank" style="text-decoration: none;">
                <div style="background: #0077b5; padding: 15px; border-radius: 10px; text-align: center; color: white; font-weight: bold; border: 2px solid #FFD700;">Follow me on LinkedIn</div>
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
            for idx, row in data.head(20).iterrows():
                with st.container(border=True):
                    colA, colB = st.columns([2, 1])
                    with colA:
                        st.markdown(f"### {row['course']} | {row['quarter']} {row['year']}")
                        st.write(f"**Instructor:** {row['instructor']}")
                        gpa_val = row[gpa_col]
                        st.write(f"**GPA:** `{gpa_val:.2f}`")
                    with colB:
                        grades = pd.DataFrame({'Grade': ['A', 'B', 'C', 'D', 'F'], 'Count': [row['a'], row['b'], row['c'], row['d'], row['f']]})
                        fig = px.bar(grades, x='Grade', y='Count', color='Grade', template="plotly_dark", height=120)
                        fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
                        st.plotly_chart(fig, use_container_width=True, key=f"fig_{idx}")

if __name__ == "__main__":
    main()
