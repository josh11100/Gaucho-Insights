import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px
import streamlit.components.v1 as components

st.set_page_config(page_title="Gaucho Insights", layout="wide", page_icon="🎓")

# --- CSS INJECTION ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');

        .stApp { background-color: #000000 !important; color: #FFFFFF !important; }

        .stTabs [data-baseweb="tab-list"] {
            gap: 50px; justify-content: center;
            background-color: rgba(0,0,0,0.2); padding: 10px;
            border-radius: 15px; margin-bottom: 20px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 60px; background-color: transparent; border-radius: 10px;
            color: #888; font-size: 22px !important; font-weight: 700;
            font-family: 'Orbitron', sans-serif; transition: all 0.3s ease;
        }
        .stTabs [data-baseweb="tab"]:hover { color: #FFD700; background-color: rgba(255,215,0,0.1); }
        .stTabs [aria-selected="true"] {
            color: #FFD700 !important; border-bottom: 3px solid #FFD700 !important;
            text-shadow: 0 0 10px rgba(255,215,0,0.5);
        }

        /* Professor modal overlay */
        .prof-modal-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.7); z-index: 9998; backdrop-filter: blur(4px);
        }
        .prof-modal {
            position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
            width: 420px; background: linear-gradient(135deg, #001a3a 0%, #001f3f 60%, #002a50 100%);
            border: 2px solid rgba(255,215,0,0.6); border-radius: 25px;
            padding: 35px; z-index: 9999; box-shadow: 0 0 60px rgba(255,215,0,0.2), 0 30px 60px rgba(0,0,0,0.8);
            font-family: sans-serif;
        }
        .prof-modal h2 { color: #FFD700; font-family: 'Orbitron', sans-serif; font-size: 1.3em; margin-bottom: 5px; }
        .prof-modal .dept-badge {
            background: rgba(0,116,217,0.3); color: #0074D9; border: 1px solid #0074D9;
            padding: 3px 12px; border-radius: 20px; font-size: 0.8em; display: inline-block; margin-bottom: 20px;
        }
        .stat-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin: 18px 0; }
        .stat-box {
            background: rgba(255,255,255,0.06); border-radius: 14px; padding: 15px 10px;
            text-align: center; border: 1px solid rgba(255,255,255,0.1);
        }
        .stat-box .val { font-size: 1.8em; font-weight: 900; }
        .stat-box .lbl { font-size: 0.7em; color: #aaa; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
        .tags-section { margin: 16px 0; }
        .tag-pill {
            background: rgba(0,204,255,0.12); color: #00CCFF;
            border: 1px solid rgba(0,204,255,0.4); padding: 5px 12px;
            border-radius: 20px; display: inline-block; margin: 4px 3px; font-size: 0.78em; font-weight: 600;
        }
        .rmp-btn {
            display: block; width: 100%; padding: 14px; margin-top: 20px;
            background: linear-gradient(135deg, #0077b5, #00a0dc);
            color: white; text-align: center; text-decoration: none;
            border-radius: 14px; font-weight: 800; font-size: 1em;
            border: 2px solid rgba(255,255,255,0.2);
            box-shadow: 0 8px 20px rgba(0,119,181,0.4);
            transition: all 0.2s ease;
        }
        .close-btn {
            position: absolute; top: 15px; right: 20px; background: rgba(255,255,255,0.1);
            border: none; color: #aaa; font-size: 1.4em; cursor: pointer; border-radius: 50%;
            width: 34px; height: 34px; display: flex; align-items: center; justify-content: center;
        }

        /* Clickable professor name */
        .prof-link {
            color: #FFD700 !important; text-decoration: none; cursor: pointer;
            border-bottom: 1px dashed rgba(255,215,0,0.5); transition: all 0.2s;
            font-weight: 600;
        }
        .prof-link:hover { color: #fff !important; border-bottom-color: #fff; text-shadow: 0 0 8px rgba(255,215,0,0.6); }
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

    rmp_lookup = {}
    if rmp_path:
        rmp_df = pd.read_csv(rmp_path)
        rmp_df.columns = [c.strip().lower() for c in rmp_df.columns]

        # Build a lookup dict keyed by registrar key -> rmp row
        for _, row in rmp_df.iterrows():
            name = str(row.get('instructor', ''))
            parts = name.upper().split()
            key = f"{parts[0]}{parts[1][0] if len(parts) > 1 else ''}" if parts else "UNKNOWN"
            rmp_lookup[key] = {
                'rmp_rating': row.get('rating', None),
                'rmp_difficulty': row.get('difficulty', None),
                'rmp_take_again': row.get('take_again', None),
                'rmp_num_ratings': row.get('rmp_num_ratings', None),
                'rmp_tags': row.get('tags', None),
                'rmp_url': row.get('url', None),
                'rmp_dept': row.get('rmp_dept', None),
                'instructor_full': name,
            }

        rmp_df_renamed = rmp_df.rename(columns={
            'instructor': 'instructor_rmp', 'rating': 'rmp_rating',
            'difficulty': 'rmp_difficulty', 'take_again': 'rmp_take_again',
            'tags': 'rmp_tags', 'url': 'rmp_url'
        })
        df = pd.merge(df, rmp_df_renamed, left_on='join_key', right_on='instructor_rmp', how='left')

    for col in ['instructor', 'quarter', 'course', 'dept']:
        if col in df.columns: df[col] = df[col].astype(str).str.upper().str.strip()

    gpa_col = next((c for c in ['avggpa', 'avg_gpa', 'avg gpa'] if c in df.columns), 'avggpa')
    group_cols = ['instructor', 'quarter', 'year', 'course', 'dept', 'join_key']
    agg_dict = {gpa_col: 'mean', 'a': 'sum', 'b': 'sum', 'c': 'sum', 'd': 'sum', 'f': 'sum'}
    for extra_col in ['rmp_url', 'rmp_rating', 'rmp_difficulty', 'rmp_take_again', 'rmp_tags', 'rmp_num_ratings']:
        if extra_col in df.columns:
            agg_dict[extra_col] = 'first'

    df = df.groupby(group_cols).agg(agg_dict).reset_index()
    return df, gpa_col, rmp_lookup


def reset_filters():
    st.session_state.dept_query = " "
    st.session_state.course_query = ""
    st.session_state.prof_query = ""


def render_prof_modal(prof_key, rmp_lookup, prof_display_name):
    """Render the professor detail modal using session state."""
    info = rmp_lookup.get(prof_key, {})
    if not info:
        st.warning(f"No RMP data found for {prof_display_name}")
        if st.button("✖ Close"):
            st.session_state.selected_prof = None
            st.rerun()
        return

    rating = info.get('rmp_rating')
    difficulty = info.get('rmp_difficulty')
    take_again = info.get('rmp_take_again')
    num_ratings = info.get('rmp_num_ratings')
    tags_raw = info.get('rmp_tags', '')
    url = info.get('rmp_url', '')
    dept = info.get('rmp_dept', '')

    # Color-code rating
    if rating and float(rating) >= 4.0:
        rating_color = "#2ECC40"
    elif rating and float(rating) >= 3.0:
        rating_color = "#0074D9"
    else:
        rating_color = "#FF4136"

    # Parse tags
    tags_html = ""
    if tags_raw and str(tags_raw) != 'nan':
        raw = str(tags_raw).strip('"\'[]')
        tags = [t.strip().strip('"\'') for t in raw.split(',') if t.strip()]
        tags_html = "".join([f'<span class="tag-pill">{t}</span>' for t in tags[:8]])

    rmp_btn = f'<a href="{url}" target="_blank" class="rmp-btn">🔗 View Full RMP Profile</a>' if url and str(url) != 'nan' else ''

    take_again_display = f"{take_again}" if take_again and str(take_again) != 'nan' else "N/A"
    if '%' not in str(take_again_display) and take_again_display != 'N/A':
        take_again_display += '%'

    num_display = f"{int(float(num_ratings))}" if num_ratings and str(num_ratings) != 'nan' else "N/A"

    modal_html = f"""
    <div class="prof-modal-overlay" id="modalOverlay" onclick="if(event.target===this)closeModal()"></div>
    <div class="prof-modal" id="profModal">
        <button class="close-btn" onclick="closeModal()">✕</button>
        <h2>👤 {prof_display_name}</h2>
        {"<span class='dept-badge'>" + dept + "</span>" if dept and str(dept) != 'nan' else ""}
        
        <div class="stat-grid">
            <div class="stat-box">
                <div class="val" style="color:{rating_color}">{rating if rating and str(rating) != 'nan' else 'N/A'}</div>
                <div class="lbl">Rating</div>
            </div>
            <div class="stat-box">
                <div class="val" style="color:#FF851B">{difficulty if difficulty and str(difficulty) != 'nan' else 'N/A'}</div>
                <div class="lbl">Difficulty</div>
            </div>
            <div class="stat-box">
                <div class="val" style="color:#2ECC40;font-size:1.2em">{take_again_display}</div>
                <div class="lbl">Would Retake</div>
            </div>
        </div>
        
        <div style="text-align:center;color:#666;font-size:0.8em;margin-top:-6px;margin-bottom:14px;">
            Based on {num_display} ratings
        </div>

        {"<div class='tags-section'><div style='color:#aaa;font-size:0.78em;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;'>Student Tags</div>" + tags_html + "</div>" if tags_html else ""}
        
        {rmp_btn}
    </div>
    <script>
        function closeModal() {{
            // Trigger Streamlit to close modal via query param change
            const url = new URL(window.parent.location.href);
            url.searchParams.set('close_modal', Date.now());
            window.parent.history.replaceState(null, '', url);
            // Also try direct parent rerun via streamlit
            window.parent.postMessage({{type: 'streamlit:closeModal'}}, '*');
        }}
    </script>
    """

    components.html(modal_html, height=0)

    # Actual close button in Streamlit
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✖ Close Professor Card", use_container_width=True):
            st.session_state.selected_prof = None
            st.session_state.selected_prof_name = None
            st.rerun()


def main():
    full_df, gpa_col, rmp_lookup = load_and_clean_data()

    # Initialize session state
    if 'selected_prof' not in st.session_state:
        st.session_state.selected_prof = None
    if 'selected_prof_name' not in st.session_state:
        st.session_state.selected_prof_name = None

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
            stats_3d_html = """
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
                .welcome-perspective { perspective: 1500px; width: 100%; height: 700px; display: flex; justify-content: center; align-items: center; }
                .welcome-card {
                    width: 98%; height: 640px;
                    background: rgba(0, 31, 63, 0.7);
                    border-radius: 25px;
                    border: 2px solid rgba(255, 215, 0, 0.4);
                    position: relative; overflow: hidden;
                    box-shadow: 0 20px 50px rgba(0,0,0,0.6);
                    transform-style: preserve-3d;
                    transition: transform 0.1s ease-out;
                    padding: 50px 40px;
                }
                .content-layer { position: relative; z-index: 2; color: white; font-family: 'sans-serif'; pointer-events: none; }
                #statsCanvas { position: absolute; top: 0; left: 0; z-index: 1; width: 100% !important; height: 100% !important; }
            </style>
            <div class="welcome-perspective" id="welcomeCont">
                <div class="welcome-card" id="welcomeCard">
                    <canvas id="statsCanvas"></canvas>
                    <div class="content-layer">
                        <h2 style="color: #FFD700; font-family: 'Orbitron', sans-serif; font-size: 2.5em; margin-bottom: 30px; text-shadow: 0 0 15px rgba(255,215,0,0.4);">WELCOME GAUCHOS! ٩(◕‿◕)۶</h2>
                        <p style="font-size: 1.25em; line-height: 1.8; margin-bottom: 40px; max-width: 95%;">
                            <b>WHAT IS THIS?</b><br>
                            Gaucho Insights helps you survive your schedule. See how stressful classes are with specific professors — and now click any professor name to see their full RMP profile! <b>Numbers don't lie!</b>
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
                cont.addEventListener('mousemove', (e) => {
                    let rect = cont.getBoundingClientRect();
                    let x = (e.clientX - rect.left - rect.width / 2) / 45;
                    let y = (e.clientY - rect.top - rect.height / 2) / 35;
                    card.style.transform = `rotateY(${x}deg) rotateX(${-y}deg)`;
                });
                cont.addEventListener('mouseleave', () => card.style.transform = `rotateY(0deg) rotateX(0deg)`);
                const canvas = document.getElementById('statsCanvas');
                const ctx = canvas.getContext('2d');
                let particles = [];
                function resize() { canvas.width = card.clientWidth; canvas.height = card.clientHeight; }
                window.addEventListener('resize', resize);
                resize();
                class Particle {
                    constructor() {
                        this.x = Math.random() * canvas.width; this.y = Math.random() * canvas.height;
                        this.vx = (Math.random() - 0.5) * 1.4; this.vy = (Math.random() - 0.5) * 1.4;
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
                                ctx.moveTo(p.x, p.y); ctx.lineTo(p2.x, p2.y); ctx.stroke();
                            }
                        }
                    });
                    requestAnimationFrame(animate);
                }
                animate();
                setTimeout(resize, 100);
            </script>
            """
            components.html(stats_3d_html, height=720)

        with col_right:
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
        # --- PROFESSOR MODAL (shown when a prof is selected) ---
        if st.session_state.selected_prof:
            st.markdown("---")
            st.markdown(f"### 👤 Professor Profile: {st.session_state.selected_prof_name}")

            prof_key = st.session_state.selected_prof
            info = rmp_lookup.get(prof_key, {})

            if info:
                rating = info.get('rmp_rating')
                difficulty = info.get('rmp_difficulty')
                take_again = info.get('rmp_take_again', 'N/A')
                num_ratings = info.get('rmp_num_ratings')
                tags_raw = info.get('rmp_tags', '')
                url = info.get('rmp_url', '')
                dept = info.get('rmp_dept', '')

                # Color for rating
                try:
                    r_val = float(rating)
                    r_color = "#2ECC40" if r_val >= 4.0 else ("#FFDC00" if r_val >= 3.0 else "#FF4136")
                except:
                    r_color = "#aaa"

                # Parse take_again
                ta_display = str(take_again) if take_again and str(take_again) != 'nan' else 'N/A'
                if '%' not in ta_display and ta_display != 'N/A':
                    ta_display += '%'

                num_display = f"{int(float(num_ratings))}" if num_ratings and str(num_ratings) != 'nan' else 'N/A'

                # Parse tags
                tags_html = ""
                if tags_raw and str(tags_raw) != 'nan':
                    raw = str(tags_raw).strip('"\'[]')
                    tags = [t.strip().strip('"\'') for t in raw.split(',') if t.strip()]
                    tags_html = "".join([f'<span class="tag-pill">{t}</span>' for t in tags[:8]])

                card_html = f"""
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&display=swap');
                    .pcard {{
                        background: linear-gradient(135deg, #001a3a 0%, #001f3f 60%, #002a50 100%);
                        border: 2px solid rgba(255,215,0,0.5); border-radius: 22px;
                        padding: 30px 35px; margin: 10px 0 25px 0;
                        box-shadow: 0 0 40px rgba(255,215,0,0.1), 0 20px 40px rgba(0,0,0,0.5);
                        font-family: sans-serif; color: white;
                    }}
                    .pcard-name {{ color: #FFD700; font-family: 'Orbitron', sans-serif; font-size: 1.5em; font-weight: 700; margin-bottom: 6px; }}
                    .pcard-dept {{ background: rgba(0,116,217,0.25); color: #0074D9; border: 1px solid #0074D9; padding: 3px 14px; border-radius: 20px; font-size: 0.82em; display: inline-block; margin-bottom: 22px; }}
                    .pcard-stats {{ display: flex; gap: 16px; margin-bottom: 22px; }}
                    .pcard-stat {{ flex: 1; background: rgba(255,255,255,0.06); border-radius: 16px; padding: 18px 10px; text-align: center; border: 1px solid rgba(255,255,255,0.08); }}
                    .pcard-stat .v {{ font-size: 2.2em; font-weight: 900; line-height: 1; }}
                    .pcard-stat .l {{ font-size: 0.7em; color: #888; margin-top: 6px; text-transform: uppercase; letter-spacing: 0.5px; }}
                    .pcard-num {{ text-align: center; color: #555; font-size: 0.82em; margin: -14px 0 18px 0; }}
                    .tag-pill {{ background: rgba(0,204,255,0.1); color: #00CCFF; border: 1px solid rgba(0,204,255,0.35); padding: 5px 13px; border-radius: 20px; display: inline-block; margin: 4px 3px; font-size: 0.78em; font-weight: 600; }}
                    .pcard-tags-lbl {{ color: #555; font-size: 0.75em; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
                    .rmp-link {{ display: inline-block; margin-top: 18px; padding: 13px 28px; background: linear-gradient(135deg, #0077b5, #00a0dc); color: white; text-decoration: none; border-radius: 14px; font-weight: 800; font-size: 0.95em; box-shadow: 0 6px 20px rgba(0,119,181,0.4); border: 2px solid rgba(255,255,255,0.15); }}
                </style>
                <div class="pcard">
                    <div class="pcard-name">👤 {st.session_state.selected_prof_name}</div>
                    {"<div class='pcard-dept'>" + str(dept) + "</div>" if dept and str(dept) != 'nan' else ""}
                    <div class="pcard-stats">
                        <div class="pcard-stat"><div class="v" style="color:{r_color}">{rating if rating and str(rating) != 'nan' else 'N/A'}</div><div class="l">Rating</div></div>
                        <div class="pcard-stat"><div class="v" style="color:#FF851B">{difficulty if difficulty and str(difficulty) != 'nan' else 'N/A'}</div><div class="l">Difficulty</div></div>
                        <div class="pcard-stat"><div class="v" style="color:#2ECC40;font-size:1.4em">{ta_display}</div><div class="l">Would Retake</div></div>
                    </div>
                    <div class="pcard-num">Based on {num_display} student ratings</div>
                    {"<div class='pcard-tags-lbl'>Student Tags</div><div>" + tags_html + "</div>" if tags_html else ""}
                    {"<br><a href='" + str(url) + "' target='_blank' class='rmp-link'>🔗 View Full RMP Profile</a>" if url and str(url) != 'nan' else ""}
                </div>
                """
                components.html(card_html, height=420)
            else:
                st.info(f"No RMP data found for {st.session_state.selected_prof_name}.")

            if st.button("✖ Close Professor Card"):
                st.session_state.selected_prof = None
                st.session_state.selected_prof_name = None
                st.rerun()

            st.markdown("---")

        # --- FILTERS ---
        st.sidebar.header("( 🔍 ) FILTERS")
        all_depts = sorted(full_df['dept'].unique().tolist())
        selected_dept = st.sidebar.selectbox("Select Department", options=[" "] + all_depts, key="dept_query")
        course_q = st.sidebar.text_input("COURSE #", key="course_query").strip().upper()
        prof_q = st.sidebar.text_input("PROFESSOR NAME", key="prof_query").strip().upper()
        if st.sidebar.button("( ✖ ) Clear All", on_click=reset_filters): st.rerun()

        st.sidebar.markdown("---")
        st.sidebar.subheader("( 📝 ) GRADING SYSTEM")
        st.sidebar.markdown("* **STRESSFUL:** GPA < 2.5\n* **CHILL:** GPA 2.5 - 3.3\n* **EASY:** GPA > 3.3")

        # --- FILTER DATA ---
        data = full_df.copy()
        if selected_dept != " ": data = data[data['dept'] == selected_dept]
        if course_q: data = data[data['course'].str.contains(course_q, na=False)]
        if prof_q: data = data[data['instructor'].str.contains(prof_q, na=False)]

        if not data.empty:
            for idx, row in data.head(20).iterrows():
                gpa_val = row[gpa_col]
                if gpa_val < 2.5:
                    status, color, shadow = "STRESSFUL", "#FF4136", "rgba(255,65,54,0.4)"
                elif gpa_val > 3.3:
                    status, color, shadow = "EASY", "#2ECC40", "rgba(46,204,64,0.4)"
                else:
                    status, color, shadow = "CHILL", "#0074D9", "rgba(0,116,217,0.4)"

                prof_display = row['instructor']
                prof_key = row.get('join_key', '')
                has_rmp = prof_key in rmp_lookup

                with st.container(border=True):
                    colA, colB = st.columns([2, 1])
                    with colA:
                        st.markdown(f"### {row['course']} | {row['quarter']} {row['year']}")

                        # Professor name as clickable button if RMP data exists
                        if has_rmp:
                            btn_col, spacer = st.columns([3, 5])
                            with btn_col:
                                if st.button(
                                    f"👤 {prof_display}",
                                    key=f"prof_btn_{idx}",
                                    help="Click to view RMP profile",
                                    type="secondary"
                                ):
                                    st.session_state.selected_prof = prof_key
                                    st.session_state.selected_prof_name = prof_display
                                    st.rerun()
                        else:
                            st.markdown(f"**Instructor:** {prof_display}")

                        st.markdown(
                            f"""<div style="display:flex;align-items:center;gap:10px;margin-top:10px;">
                            <span style="font-weight:bold;color:white;">GPA: {gpa_val:.2f}</span>
                            <span style="background:{color};color:white;padding:4px 12px;border-radius:20px;font-size:0.8em;font-weight:900;box-shadow:0 0 10px {shadow};text-transform:uppercase;">{status}</span>
                            {"<span style='font-size:0.75em;color:#FFD700;'>⭐ RMP Available</span>" if has_rmp else ""}
                            </div>""",
                            unsafe_allow_html=True
                        )
                    with colB:
                        grades = pd.DataFrame({
                            'Grade': ['A', 'B', 'C', 'D', 'F'],
                            'Count': [row['a'], row['b'], row['c'], row['d'], row['f']]
                        })
                        fig = px.bar(
                            grades, x='Grade', y='Count', color='Grade',
                            color_discrete_map={'A': '#2ECC40', 'B': '#0074D9', 'C': '#FFDC00', 'D': '#FF851B', 'F': '#FF4136'},
                            template="plotly_dark", height=130
                        )
                        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), showlegend=False, xaxis_title=None, yaxis_title=None)
                        st.plotly_chart(fig, use_container_width=True, key=f"fig_{idx}", config={'displayModeBar': False})
        else:
            st.warning("No matches found.")


if __name__ == "__main__":
    main()
