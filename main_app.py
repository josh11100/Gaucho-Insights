import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px
import streamlit.components.v1 as components 

st.set_page_config(page_title="Gaucho Insights", layout="wide", page_icon="🎓")

# --- CSS INJECTION FOR BETTER TABS ---
st.markdown("""
    <style>
        .stTabs [data-baseweb="tab-list"] {
            gap: 50px;
            justify-content: center;
            background-color: rgba(0, 0, 0, 0.2);
            padding: 10px;
            border-radius: 15px;
            margin-bottom: 20px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 60px;
            white-space: pre-wrap;
            background-color: transparent;
            border-radius: 10px;
            color: #888;
            font-size: 22px !important;
            font-weight: 700;
            font-family: 'Orbitron', sans-serif;
            transition: all 0.3s ease;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: #FFD700;
            background-color: rgba(255, 215, 0, 0.1);
        }
        .stTabs [aria-selected="true"] {
            color: #FFD700 !important;
            border-bottom: 3px solid #FFD700 !important;
            text-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
        }
    </style>
""", unsafe_allow_html=True)

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

    df['join_key'] = df['instructor'].apply(get_registrar_key)
    
    if rmp_path:
        rmp_df = pd.read_csv(rmp_path)
        rmp_df.columns = [c.strip().lower() for c in rmp_df.columns]
        rmp_df = rmp_df.rename(columns={'instructor': 'instructor_rmp', 'rating': 'rmp_rating', 'difficulty': 'rmp_difficulty', 'take_again': 'rmp_take_again', 'tags': 'rmp_tags', 'url': 'rmp_url'})
        df = pd.merge(df, rmp_df, left_on='join_key', right_on='instructor_rmp', how='left')
    
    for col in ['instructor', 'quarter', 'course', 'dept']:
        if col in df.columns: df[col] = df[col].astype(str).str.upper().str.strip()

    gpa_col = next((c for c in ['avggpa', 'avg_gpa', 'avg gpa'] if c in df.columns), 'avggpa')
    group_cols = ['instructor', 'quarter', 'year', 'course', 'dept']
    agg_dict = {gpa_col: 'mean', 'a': 'sum', 'b': 'sum', 'c': 'sum', 'd': 'sum', 'f': 'sum'}
    if 'rmp_url' in df.columns:
        agg_dict['rmp_url'] = 'first'
        
    df = df.groupby(group_cols).agg(agg_dict).reset_index()
    return df, gpa_col

def reset_filters():
    st.session_state.dept_query = " "
    st.session_state.course_query = ""
    st.session_state.prof_query = ""

def main():
    full_df, gpa_col = load_and_clean_data()

    # --- 3D HERO HEADER ---
    hero_html = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&display=swap');
        .hero-container { perspective: 1000px; display: flex; justify-content: center; align-items: center; height: 160px; margin-bottom: 20px; }
        .hero-title { font-family: 'Orbitron', sans-serif; font-size: 3.5rem; font-weight: 900; color: #FFD700; text-shadow: 0 10px 20px rgba(0,0,0,0.4); transform-style: preserve-3d; transition: transform 0.1s ease; cursor: default; white-space: nowrap; }
    </style>
    <div class="hero-container" id="heroBox">
        <div class="hero-title" id="heroText">(つ▀¯▀ )つ GAUCHO INSIGHTS ⊂(▀¯▀⊂ )</div>
    </div>
    <script>
        const heroBox = document.getElementById('heroBox');
        const heroText = document.getElementById('heroText');
        heroBox.addEventListener('mousemove', (e) => {
            let rect = heroBox.getBoundingClientRect();
            let x = (e.clientX - rect.left - rect.width / 2) / 20;
            let y = (e.clientY - rect.top - rect.height / 2) / 10;
            heroText.style.transform = `rotateY(${x}deg) rotateX(${-y}deg) translateZ(50px)`;
        });
        heroBox.addEventListener('mouseleave', () => { heroText.style.transform = `rotateY(0deg) rotateX(0deg) translateZ(0px)`; });
    </script>
    """
    components.html(hero_html, height=200)

    tab1, tab2 = st.tabs(["🏠 HOME", "🔍 SEARCH TOOL"])

    with tab1:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            # --- FIXED 3D WELCOME BOX ---
            stats_3d_html = """
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
                .welcome-perspective { perspective: 1500px; width: 100%; height: 700px; display: flex; justify-content: center; align-items: center; }
                .welcome-card { 
                    width: 98%; height: 640px; 
                    background: rgba(0, 31, 63, 0.7); 
                    border-radius: 25px; 
                    border: 2px solid rgba(255, 215, 0, 0.4); 
                    position: relative; 
                    overflow: hidden; 
                    box-shadow: 0 20px 50px rgba(0,0,0,0.6); 
                    transform-style: preserve-3d; 
                    transition: transform 0.1s ease-out;
                    padding: 50px 40px; /* Added more top padding to prevent cutoff */
                }
                .content-layer { position: relative; z-index: 2; color: white; font-family: 'sans-serif'; pointer-events: none; }
                #statsCanvas { 
                    position: absolute; 
                    top: 0; 
                    left: 0; 
                    z-index: 1; 
                    width: 100% !important; 
                    height: 100% !important; 
                }
            </style>
            <div class="welcome-perspective" id="welcomeCont">
                <div class="welcome-card" id="welcomeCard">
                    <canvas id="statsCanvas"></canvas>
                    <div class="content-layer">
                        <h2 style="color: #FFD700; font-family: 'Orbitron', sans-serif; font-size: 2.5em; margin-bottom: 30px; text-shadow: 0 0 15px rgba(255,215,0,0.4);">WELCOME GAUCHOS! ٩(◕‿◕)۶</h2>
                        <p style="font-size: 1.25em; line-height: 1.8; margin-bottom: 40px; max-width: 95%;">
                            <b>WHAT IS THIS?</b><br>
                            Gaucho Insights is a tool designed to help you survive your schedule. This dashboard helps you see exactly how stressful 
                            certain classes are with specific professors. <b>Numbers don't lie!</b>
                        </p>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; pointer-events: auto;">
                            <div style="background: rgba(255,255,255,0.08); padding: 30px; border-radius: 15px; border-left: 5px solid #FFD700; backdrop-filter: blur(8px);">
                                <b style="color: #FFD700; font-size: 1.2em;">( 📍 ) MISSION</b><br>
                                Empowering students to make informed decisions about their quarterly schedules and academic path.
                            </div>
                            <div style="background: rgba(255,255,255,0.08); padding: 30px; border-radius: 15px; border-left: 5px solid #0074D9; backdrop-filter: blur(8px);">
                                <b style="color: #0074D9; font-size: 1.2em;">( 🔍 ) THE TECH</b><br>
                                Utilizing Python, Streamlit, and D3-inspired mesh networks to visualize grade distributions.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <script>
                const card = document.getElementById('welcomeCard');
                const cont = document.getElementById('welcomeCont');
                
                // Tilt logic
                cont.addEventListener('mousemove', (e) => {
                    let rect = cont.getBoundingClientRect();
                    let x = (e.clientX - rect.left - rect.width / 2) / 45;
                    let y = (e.clientY - rect.top - rect.height / 2) / 35;
                    card.style.transform = `rotateY(${x}deg) rotateX(${-y}deg)`;
                });
                cont.addEventListener('mouseleave', () => card.style.transform = `rotateY(0deg) rotateX(0deg)`);

                // Canvas Mesh logic - Ensuring full coverage
                const canvas = document.getElementById('statsCanvas'); 
                const ctx = canvas.getContext('2d');
                let particles = [];

                function resize() {
                    canvas.width = card.clientWidth;
                    canvas.height = card.clientHeight;
                }
                
                window.addEventListener('resize', resize);
                resize();

                class Particle {
                    constructor() {
                        this.x = Math.random() * canvas.width; 
                        this.y = Math.random() * canvas.height;
                        this.vx = (Math.random() - 0.5) * 1.4; 
                        this.vy = (Math.random() - 0.5) * 1.4;
                        this.radius = 2;
                    }
                    update() {
                        this.x += this.vx; this.y += this.vy;
                        if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
                        if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
                    }
                    draw() {
                        ctx.beginPath(); ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                        ctx.fillStyle = "rgba(255, 215, 0, 0.4)"; ctx.fill();
                    }
                }

                for (let i = 0; i < 70; i++) particles.push(new Particle());

                function animate() {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    particles.forEach((p, idx) => {
                        p.update(); p.draw();
                        for (let j = idx + 1; j < particles.length; j++) {
                            const p2 = particles[j]; 
                            const d = Math.hypot(p.x - p2.x, p.y - p2.y);
                            if (d < 130) {
                                ctx.beginPath(); 
                                ctx.strokeStyle = `rgba(0, 116, 217, ${1 - d/130})`;
                                ctx.lineWidth = 0.8; 
                                ctx.moveTo(p.x, p.y); 
                                ctx.lineTo(p2.x, p2.y); 
                                ctx.stroke();
                            }
                        }
                    });
                    requestAnimationFrame(animate);
                }
                animate();
                setTimeout(resize, 100); // Secondary check for final sizing
            </script>
            """
            components.html(stats_3d_html, height=720)

        with col_right:
            # Gaucho Info & LinkedIn boxes kept consistent with previous 3D logic
            gaucho_info_3d = """
            <style>
                .container { perspective: 1000px; display: flex; justify-content: center; align-items: center; height: 350px; margin-bottom: 20px; }
                .card { width: 280px; height: 310px; background: linear-gradient(135deg, #001f3f 0%, #0074D9 100%); border-radius: 20px; border: 2px solid #FFD700; box-shadow: 0 15px 30px rgba(0,0,0,0.5); transform-style: preserve-3d; transition: transform 0.1s ease; display: flex; flex-direction: column; justify-content: space-between; padding: 25px; color: white; text-align: center; }
            </style>
            <div class="container"><div class="card" id="card">
                <div style="font-size: 1.4em; font-weight: bold; color: #FFD700;">📊 Gaucho Info</div>
                <div style="font-size: 1em; line-height: 1.5;"><b>Data:</b> Thru Summer 2025<br><b>Source:</b> Registrar & RMP<br><b>By:</b> Joshua Chung</div>
                <div style="font-size: 0.85em; background: rgba(255,255,255,0.1); padding: 8px; border-radius: 10px;">Move cursor to tilt!</div>
            </div></div>
            <script>
                const card = document.getElementById('card'); const container = card.parentElement;
                container.addEventListener('mousemove', (e) => {
                    let rect = container.getBoundingClientRect();
                    card.style.transform = `rotateY(${(e.clientX-rect.left-rect.width/2)/10}deg) rotateX(${-(e.clientY-rect.top-rect.height/2)/10}deg)`;
                });
                container.addEventListener('mouseleave', () => card.style.transform = `rotateY(0deg) rotateX(0deg)`);
            </script>
            """
            components.html(gaucho_info_3d, height=380)

            linkedin_3d = """
            <style>
                .li-container { perspective: 1000px; display: flex; justify-content: center; align-items: center; height: 110px; padding-top: 10px; }
                .li-card { width: 280px; background: #0077b5; border-radius: 15px; border: 2px solid #FFD700; padding: 15px; color: white; text-align: center; text-decoration: none; font-weight: bold; transform-style: preserve-3d; transition: transform 0.1s ease; box-shadow: 0 10px 20px rgba(0,0,0,0.3); }
                .li-card:hover { background: #008fdb; border-color: white; }
            </style>
            <div class="li-container">
                <a href="https://www.linkedin.com/in/joshua-chung858/" target="_blank" class="li-card" id="liCard">Follow on LinkedIn</a>
            </div>
            <script>
                const liCard = document.getElementById('liCard'); const liCont = liCard.parentElement;
                liCont.addEventListener('mousemove', (e) => {
                    let rect = liCont.getBoundingClientRect();
                    liCard.style.transform = `rotateY(${(e.clientX-rect.left-rect.width/2)/10}deg) rotateX(${-(e.clientY-rect.top-rect.height/2)/5}deg)`;
                });
                liCont.addEventListener('mouseleave', () => liCard.style.transform = `rotateY(0deg) rotateX(0deg)`);
            </script>
            """
            components.html(linkedin_3d, height=160)

    with tab2:
        # Search Tool Filters & Display logic
        st.sidebar.header("( 🔍 ) FILTERS")
        all_depts = sorted(full_df['dept'].unique().tolist())
        selected_dept = st.sidebar.selectbox("Select Department", options=[" "] + all_depts, key="dept_query")
        course_q = st.sidebar.text_input("COURSE #", key="course_query").strip().upper()
        prof_q = st.sidebar.text_input("PROFESSOR NAME", key="prof_query").strip().upper()
        if st.sidebar.button("( ✖ ) Clear All", on_click=reset_filters): st.rerun()

        st.sidebar.markdown("---")
        st.sidebar.subheader("( 📝 ) GRADING SYSTEM")
        st.sidebar.markdown("* **STRESSFUL:** GPA < 2.5\n* **CHILL:** GPA 2.5 - 3.3\n* **EASY:** GPA > 3.3")

        data = full_df.copy()
        if selected_dept != " ": data = data[data['dept'] == selected_dept]
        if course_q: data = data[data['course'].str.contains(course_q, na=False)]
        if prof_q: data = data[data['instructor'].str.contains(prof_q, na=False)]

        if not data.empty:
            for idx, row in data.head(20).iterrows():
                gpa_val = row[gpa_col]
                if gpa_val < 2.5: status, color, shadow = "STRESSFUL", "#FF4136", "rgba(255, 65, 54, 0.4)"
                elif gpa_val > 3.3: status, color, shadow = "EASY", "#2ECC40", "rgba(46, 204, 64, 0.4)"
                else: status, color, shadow = "CHILL", "#0074D9", "rgba(0, 116, 217, 0.4)"

                prof_display = row['instructor']
                prof_html = f"<a href='{row['rmp_url']}' target='_blank' style='color:#FFD700; text-decoration:none;'>{prof_display} 🔗</a>" if 'rmp_url' in row and pd.notna(row['rmp_url']) else f"<span>{prof_display}</span>"

                with st.container(border=True):
                    colA, colB = st.columns([2, 1])
                    with colA:
                        st.markdown(f"### {row['course']} | {row['quarter']} {row['year']}")
                        st.markdown(f"**Instructor:** {prof_html}", unsafe_allow_html=True)
                        st.markdown(f"""<div style="display: flex; align-items: center; gap: 10px; margin-top: 10px;"><span style="font-weight: bold; color: white;">GPA: {gpa_val:.2f}</span><span style="background: {color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: 900; box-shadow: 0 0 10px {shadow}; text-transform: uppercase;">{status}</span></div>""", unsafe_allow_html=True)
                    with colB:
                        grades = pd.DataFrame({'Grade': ['A', 'B', 'C', 'D', 'F'], 'Count': [row['a'], row['b'], row['c'], row['d'], row['f']]})
                        fig = px.bar(grades, x='Grade', y='Count', color='Grade', color_discrete_map={'A':'#2ECC40','B':'#0074D9','C':'#FFDC00','D':'#FF851B','F':'#FF4136'}, template="plotly_dark", height=130)
                        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), showlegend=False, xaxis_title=None, yaxis_title=None)
                        st.plotly_chart(fig, use_container_width=True, key=f"fig_{idx}", config={'displayModeBar': False})
        else:
            st.warning("No matches found.")

if __name__ == "__main__":
    main()
