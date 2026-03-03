import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px
import streamlit.components.v1 as components

# --- 1. INITIAL CONFIG & CSS ---
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.set_page_config(page_title="Gaucho Insights", layout="wide", page_icon="🎓")
local_css("style.css")

# --- 2. DATA LOADING & CLEANING (RESTORING THE ENGINE) ---
@st.cache_data
def load_and_clean_data():
    def find_file(name):
        paths = [name, os.path.join('data', name)]
        for p in paths:
            if os.path.exists(p): return p
        return None

    csv_path = find_file('courseGrades.csv')
    rmp_path = find_file('rmp_final_data.csv')
    
    if not csv_path:
        st.error("Missing 'courseGrades.csv'. Please check your directory.")
        st.stop()
        
    df = pd.read_csv(csv_path)
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Filter for standard undergraduate courses
    def get_course_num(course_str):
        match = re.search(r'(\d+)', str(course_str))
        return int(match.group(1)) if match else None

    df['course_num_val'] = df['course'].apply(get_course_num)
    df = df[df['course_num_val'].notna()]
    df = df[(df['course_num_val'] <= 198) & (df['course_num_val'] != 99)]

    # RMP Join Logic
    def get_registrar_key(name):
        if pd.isna(name): return "UNKNOWN"
        parts = str(name).upper().split()
        return f"{parts[0]}{parts[1][0] if len(parts) > 1 else ''}"

    df['join_key'] = df['instructor'].apply(get_registrar_key)
    
    if rmp_path:
        rmp_df = pd.read_csv(rmp_path)
        rmp_df.columns = [c.strip().lower() for c in rmp_df.columns]
        rmp_df = rmp_df.rename(columns={'instructor': 'instructor_rmp', 'url': 'rmp_url'})
        df = pd.merge(df, rmp_df[['instructor_rmp', 'rmp_url']], left_on='join_key', right_on='instructor_rmp', how='left')
    
    for col in ['instructor', 'quarter', 'course', 'dept']:
        if col in df.columns: df[col] = df[col].astype(str).str.upper().str.strip()

    gpa_col = next((c for c in ['avggpa', 'avg_gpa'] if c in df.columns), 'avggpa')
    return df, gpa_col

full_df, gpa_col = load_and_clean_data()

# --- 3. SIDEBAR FILTERS (RESTORING THE SEARCH BAR) ---
st.sidebar.header("( 🔍 ) FILTERS")

def reset_filters():
    st.session_state.dept_query = " "
    st.session_state.course_query = ""
    st.session_state.prof_query = ""

all_depts = sorted(full_df['dept'].unique().tolist())
selected_dept = st.sidebar.selectbox("Select Department", options=[" "] + all_depts, key="dept_query")
course_q = st.sidebar.text_input("COURSE #", key="course_query").strip().upper()
prof_q = st.sidebar.text_input("PROFESSOR NAME", key="prof_query").strip().upper()

if st.sidebar.button("( ✖ ) Clear All"):
    reset_filters()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("( 📝 ) GRADING SYSTEM")
st.sidebar.markdown("* **STRESSFUL:** GPA < 2.5\n* **CHILL:** GPA 2.5 - 3.3\n* **EASY:** GPA > 3.3")

# --- 4. 3D HTML COMPONENTS ---
# (Using the 750px height fix we discussed earlier)
stats_3d_html = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    .welcome-perspective { perspective: 2000px; width: 100%; height: 740px; display: flex; justify-content: center; align-items: center; }
    .welcome-card { 
        width: 98%; height: 680px; background: rgba(0, 31, 63, 0.8); border-radius: 25px; border: 2px solid #FFD700; 
        position: relative; overflow: hidden; transform-style: preserve-3d; transition: transform 0.1s ease-out; padding: 50px 40px;
    }
    #statsCanvas { position: absolute; top: 0; left: 0; z-index: 1; width: 100%; height: 100%; }
    .content { position: relative; z-index: 2; color: white; font-family: sans-serif; pointer-events: none; }
    .grid-box { background: rgba(255,255,255,0.08); padding: 25px; border-radius: 15px; backdrop-filter: blur(8px); pointer-events: auto; }
</style>
<div class="welcome-perspective" id="cont">
    <div class="welcome-card" id="card">
        <canvas id="statsCanvas"></canvas>
        <div class="content">
            <h1 style="font-family: 'Orbitron'; font-size: 2.5em; color: #FFD700; margin-bottom: 20px;">WELCOME GAUCHOS! ٩(◕‿◕)۶</h1>
            <p style="font-size: 1.2em; line-height: 1.6; margin-bottom: 40px; max-width: 90%;"><b>Numbers don't lie!</b> Navigate your schedule with registrar data.</p>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div class="grid-box" style="border-left: 5px solid #FFD700;"><b>( 📍 ) MISSION</b><br>Informed decisions for academic paths.</div>
                <div class="grid-box" style="border-left: 5px solid #0074D9;"><b>( 🔍 ) THE TECH</b><br>Python, Streamlit, and Mesh Networks.</div>
            </div>
        </div>
    </div>
</div>
<script>
    const card = document.getElementById('card'); const cont = document.getElementById('cont');
    cont.onmousemove = (e) => {
        let rect = cont.getBoundingClientRect();
        card.style.transform = `rotateY(${(e.clientX - rect.left - rect.width/2)/50}deg) rotateX(${-(e.clientY - rect.top - rect.height/2)/40}deg)`;
    };
    cont.onmouseleave = () => card.style.transform = 'rotateY(0deg) rotateX(0deg)';
    const canvas = document.getElementById('statsCanvas'); const ctx = canvas.getContext('2d');
    function resize() { canvas.width = card.clientWidth; canvas.height = card.clientHeight; }
    window.onresize = resize; resize();
    let dots = Array(70).fill().map(() => ({x: Math.random()*canvas.width, y: Math.random()*canvas.height, vx: (Math.random()-0.5)*1.2, vy: (Math.random()-0.5)*1.2}));
    function draw() {
        ctx.clearRect(0,0,canvas.width,canvas.height);
        dots.forEach((d, i) => {
            d.x += d.vx; d.y += d.vy;
            if(d.x<0 || d.x>canvas.width) d.vx*=-1; if(d.y<0 || d.y>canvas.height) d.vy*=-1;
            ctx.fillStyle = 'rgba(255,215,0,0.3)'; ctx.beginPath(); ctx.arc(d.x, d.y, 2, 0, 7); ctx.fill();
            for(let j=i+1; j<dots.length; j++) {
                let dist = Math.hypot(d.x-dots[j].x, d.y-dots[j].y);
                if(dist < 120) { ctx.strokeStyle = `rgba(0,116,217,${1-dist/120})`; ctx.lineWidth=0.5; ctx.beginPath(); ctx.moveTo(d.x,d.y); ctx.lineTo(dots[j].x,dots[j].y); ctx.stroke(); }
            }
        });
        requestAnimationFrame(draw);
    }
    draw(); setTimeout(resize, 200);
</script>
"""

# --- 5. MAIN APP LAYOUT ---
st.title("(つ▀¯▀ )つ GAUCHO INSIGHTS")
tab1, tab2 = st.tabs(["🏠 HOME", "🔍 SEARCH TOOL"])

with tab1:
    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.markdown('<div class="welcome-3d-frame">', unsafe_allow_html=True)
        components.html(stats_3d_html, height=750)
        st.markdown('</div>', unsafe_allow_html=True)
    with col_right:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #001f3f 0%, #0074D9 100%); padding: 30px; border-radius: 20px; border: 2px solid #FFD700; color: white; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #FFD700 !important;">📊 Gaucho Info</h3>
            <p><b>Data:</b> Thru Summer 2025</p>
            <p><b>Source:</b> Registrar & RMP</p>
            <p><b>By:</b> Joshua Chung</p>
        </div>
        """, unsafe_allow_html=True)
        st.metric(label="Data Recency", value="Summer 2025")

with tab2:
    # Filtering Logic
    data = full_df.copy()
    if selected_dept != " ": data = data[data['dept'] == selected_dept]
    if course_q: data = data[data['course'].str.contains(course_q, na=False)]
    if prof_q: data = data[data['instructor'].str.contains(prof_q, na=False)]

    if not data.empty:
        for idx, row in data.head(25).iterrows():
            gpa_val = row[gpa_col]
            if gpa_val < 2.5: status, color = "STRESSFUL", "#FF4136"
            elif gpa_val > 3.3: status, color = "EASY", "#2ECC40"
            else: status, color = "CHILL", "#0074D9"

            with st.container(border=True):
                cA, cB = st.columns([2, 1])
                with cA:
                    st.subheader(f"{row['course']} | {row['quarter']} {row['year']}")
                    st.write(f"**Instructor:** {row['instructor']}")
                    st.markdown(f"**GPA:** {gpa_val:.2f} <span style='background:{color}; padding:2px 8px; border-radius:10px;'>{status}</span>", unsafe_allow_html=True)
                with cB:
                    grades = pd.DataFrame({'G':['A','B','C','D','F'], 'V':[row['a'],row['b'],row['c'],row['d'],row['f']]})
                    fig = px.bar(grades, x='G', y='V', color='G', template="plotly_dark", height=150)
                    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True, key=f"p_{idx}")
    else:
        st.warning("No courses match those filters. Try clearing them!")
