import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px
import streamlit.components.v1 as components

st.set_page_config(page_title="Gaucho Insights", layout="wide", page_icon="🎓")

# ─────────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;600;700&display=swap');

.stApp { background: #000 !important; color: #fff !important; }
html, body { background: #000 !important; }

.stTabs [data-baseweb="tab-list"] {
    gap: 40px; justify-content: center;
    background: rgba(255,255,255,0.03);
    padding: 10px 20px; border-radius: 16px; margin-bottom: 24px;
    border: 1px solid rgba(255,215,0,0.15);
}
.stTabs [data-baseweb="tab"] {
    height: 54px; background: transparent; border-radius: 10px;
    color: #666; font-size: 18px !important; font-weight: 700;
    font-family: 'Orbitron', sans-serif; transition: all 0.25s;
    padding: 0 20px;
}
.stTabs [data-baseweb="tab"]:hover { color: #FFD700; background: rgba(255,215,0,0.07); }
.stTabs [aria-selected="true"] {
    color: #FFD700 !important;
    border-bottom: 3px solid #FFD700 !important;
    text-shadow: 0 0 12px rgba(255,215,0,0.5);
}

[data-testid="stSidebar"] { background: #050a14 !important; border-right: 1px solid rgba(255,215,0,0.2) !important; }
[data-testid="stSidebar"] * { color: #ccc !important; font-family: 'Rajdhani', sans-serif !important; }
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #FFD700 !important; font-family: 'Orbitron', sans-serif !important; font-size: 0.9em !important; }

[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(0,20,45,0.8) !important;
    border: 1px solid rgba(0,116,217,0.3) !important;
    border-radius: 18px !important;
    transition: border-color 0.2s, box-shadow 0.2s;
    margin-bottom: 12px !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: rgba(255,215,0,0.45) !important;
    box-shadow: 0 0 24px rgba(255,215,0,0.08) !important;
}

.stButton > button {
    background: rgba(0,116,217,0.15) !important;
    border: 1px solid rgba(0,116,217,0.5) !important;
    color: #5bb8ff !important;
    border-radius: 10px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95em !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: rgba(255,215,0,0.12) !important;
    border-color: rgba(255,215,0,0.6) !important;
    color: #FFD700 !important;
}

.stTextInput > div > div > input, .stSelectbox > div > div {
    background: rgba(0,20,50,0.8) !important;
    border: 1px solid rgba(0,116,217,0.3) !important;
    color: #ddd !important;
    border-radius: 10px !important;
    font-family: 'Rajdhani', sans-serif !important;
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #000; }
::-webkit-scrollbar-thumb { background: rgba(255,215,0,0.3); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  DATA LOADING
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    def find(name):
        for p in [name, os.path.join("data", name)]:
            if os.path.exists(p):
                return p
        return None

    grades_path = find("courseGrades.csv")
    rmp_path    = find("rmp_final_data.csv")

    if not grades_path:
        st.error("Cannot find courseGrades.csv — put it in the same folder or a 'data/' subfolder.")
        st.stop()

    df = pd.read_csv(grades_path)
    df.columns = [c.strip().lower() for c in df.columns]

    def extract_num(s):
        m = re.search(r"(\d+)", str(s))
        return int(m.group(1)) if m else None

    df["_num"] = df["course"].apply(extract_num)
    df = df[df["_num"].notna() & (df["_num"] <= 198) & (df["_num"] != 99)]

    for col in ["instructor", "quarter", "course", "dept"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()

    def jkey(name):
        if pd.isna(name): return "UNKNOWN"
        p = str(name).upper().split()
        return f"{p[0]}{p[1][0] if len(p) > 1 else ''}"

    df["join_key"] = df["instructor"].apply(jkey)

    rmp_lookup = {}
    if rmp_path:
        rmp = pd.read_csv(rmp_path)
        rmp.columns = [c.strip().lower() for c in rmp.columns]
        for _, r in rmp.iterrows():
            name = str(r.get("instructor", ""))
            p    = name.upper().split()
            k    = f"{p[0]}{p[1][0] if len(p) > 1 else ''}" if p else "UNKNOWN"
            rmp_lookup[k] = {
                "rating":      r.get("rating"),
                "difficulty":  r.get("difficulty"),
                "take_again":  r.get("take_again"),
                "num_ratings": r.get("rmp_num_ratings"),
                "tags":        r.get("tags"),
                "url":         r.get("url"),
                "dept":        r.get("rmp_dept"),
                "full_name":   name,
            }

        rmp_renamed = rmp.rename(columns={
            "instructor":  "instructor_rmp",
            "rating":      "rmp_rating",
            "difficulty":  "rmp_difficulty",
            "take_again":  "rmp_take_again",
            "tags":        "rmp_tags",
            "url":         "rmp_url",
        })
        df = pd.merge(df, rmp_renamed, left_on="join_key", right_on="instructor_rmp", how="left")

    gpa_col   = next((c for c in ["avggpa", "avg_gpa", "avg gpa"] if c in df.columns), "avggpa")
    grp_cols  = ["instructor", "quarter", "year", "course", "dept", "join_key"]
    agg       = {gpa_col: "mean", "a": "sum", "b": "sum", "c": "sum", "d": "sum", "f": "sum"}
    for ec in ["rmp_url", "rmp_rating", "rmp_difficulty", "rmp_take_again", "rmp_tags", "rmp_num_ratings"]:
        if ec in df.columns:
            agg[ec] = "first"

    df = df.groupby(grp_cols).agg(agg).reset_index()
    return df, gpa_col, rmp_lookup


# ─────────────────────────────────────────────
#  SESSION STATE HELPERS
# ─────────────────────────────────────────────
for key in ["sel_prof_key", "sel_prof_name"]:
    if key not in st.session_state:
        st.session_state[key] = None
for key in ["dept_q", "course_q", "prof_q"]:
    if key not in st.session_state:
        st.session_state[key] = ""


def clear_filters():
    st.session_state.dept_q   = ""
    st.session_state.course_q = ""
    st.session_state.prof_q   = ""


def gpa_badge(gpa):
    if gpa < 2.5:
        return "STRESSFUL", "#FF4136", "rgba(255,65,54,0.35)"
    elif gpa > 3.3:
        return "EASY", "#2ECC40", "rgba(46,204,64,0.35)"
    else:
        return "CHILL", "#0074D9", "rgba(0,116,217,0.35)"


# ─────────────────────────────────────────────
#  HERO BANNER
# ─────────────────────────────────────────────
def render_hero():
    components.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@900&display=swap');
*{margin:0;padding:0;box-sizing:border-box}body{background:transparent;overflow:hidden}
.hero{perspective:1200px;height:150px;display:flex;justify-content:center;align-items:center;cursor:default}
.wrap{text-align:center}
.title{font-family:'Orbitron',sans-serif;font-size:clamp(1.6rem,4vw,3rem);font-weight:900;
       color:#FFD700;transform-style:preserve-3d;transition:transform .08s ease;white-space:nowrap;
       text-shadow:0 0 20px rgba(255,215,0,.6),0 0 40px rgba(255,215,0,.3),0 4px 16px rgba(0,0,0,.8);
       letter-spacing:2px}
.sub{font-family:'Orbitron',sans-serif;font-size:.62rem;color:rgba(255,215,0,.4);
     text-align:center;letter-spacing:6px;margin-top:10px;text-transform:uppercase}
</style>
<div class="hero" id="hero">
  <div class="wrap">
    <div class="title" id="title">⬡ GAUCHO INSIGHTS ⬡</div>
    <div class="sub">UCSB GRADE ANALYTICS DASHBOARD</div>
  </div>
</div>
<script>
const hero=document.getElementById('hero'),title=document.getElementById('title');
hero.addEventListener('mousemove',e=>{
  const r=hero.getBoundingClientRect();
  title.style.transform=`rotateY(${(e.clientX-r.left-r.width/2)/22}deg) rotateX(${-(e.clientY-r.top-r.height/2)/12}deg) translateZ(40px)`;
});
hero.addEventListener('mouseleave',()=>{title.style.transform='rotateY(0) rotateX(0) translateZ(0)';});
</script>
""", height=170)


# ─────────────────────────────────────────────
#  WELCOME PARTICLE CARD
# ─────────────────────────────────────────────
def render_welcome_card():
    components.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Rajdhani:wght@400;600&display=swap');
*{margin:0;padding:0;box-sizing:border-box}body{background:transparent;overflow:hidden}
.scene{perspective:1400px;width:100%;height:620px;display:flex;justify-content:center;align-items:center}
.card{width:97%;height:580px;background:rgba(0,18,40,.85);border-radius:26px;
      border:1.5px solid rgba(255,215,0,.35);
      box-shadow:0 30px 70px rgba(0,0,0,.7),0 0 60px rgba(0,116,217,.08);
      transform-style:preserve-3d;transition:transform .1s ease;
      position:relative;overflow:hidden;padding:50px 48px;color:white}
canvas{position:absolute;top:0;left:0;width:100%;height:100%;z-index:0}
.content{position:relative;z-index:1;height:100%;display:flex;flex-direction:column;justify-content:center}
h1{font-family:'Orbitron',sans-serif;font-size:2.1em;font-weight:900;color:#FFD700;
   text-shadow:0 0 20px rgba(255,215,0,.4);margin-bottom:18px}
p{font-family:'Rajdhani',sans-serif;font-size:1.15em;line-height:1.75;color:#c8d8ef;margin-bottom:32px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.box{background:rgba(255,255,255,.05);border-radius:16px;padding:20px 22px;backdrop-filter:blur(10px);transition:background .2s}
.box:hover{background:rgba(255,255,255,.09)}
.bt{font-family:'Orbitron',sans-serif;font-size:.82em;font-weight:700;margin-bottom:8px}
.bb{font-family:'Rajdhani',sans-serif;font-size:.98em;color:#9ab;line-height:1.6}
</style>
<div class="scene" id="sc">
  <div class="card" id="cd">
    <canvas id="cv"></canvas>
    <div class="content">
      <h1>WELCOME GAUCHOS! ٩(◕‿◕)۶</h1>
      <p>Gaucho Insights lets you see how stressful or easy any UCSB class is before you register —
         based on real historical grade distributions and RateMyProfessors data.
         <strong style="color:#FFD700">Search by department, course number, or professor name.</strong></p>
      <div class="grid">
        <div class="box" style="border-left:4px solid #FFD700;padding-left:18px">
          <div class="bt" style="color:#FFD700">📍 MISSION</div>
          <div class="bb">Help UCSB students make smarter scheduling decisions with real data.</div>
        </div>
        <div class="box" style="border-left:4px solid #5bb8ff;padding-left:18px">
          <div class="bt" style="color:#5bb8ff">🔍 SEARCH TOOL</div>
          <div class="bb">Filter classes and click any professor name to see their full RMP profile.</div>
        </div>
        <div class="box" style="border-left:4px solid #2ECC40;padding-left:18px">
          <div class="bt" style="color:#2ECC40">✅ EASY  › 3.3 avg GPA</div>
          <div class="bb">Class is known to be manageable. High average grades historically.</div>
        </div>
        <div class="box" style="border-left:4px solid #FF4136;padding-left:18px">
          <div class="bt" style="color:#FF4136">💀 STRESSFUL  ‹ 2.5 avg GPA</div>
          <div class="bb">Historically tough. Prepare carefully or choose a different section.</div>
        </div>
      </div>
    </div>
  </div>
</div>
<script>
const sc=document.getElementById('sc'),cd=document.getElementById('cd');
sc.addEventListener('mousemove',e=>{
  const r=sc.getBoundingClientRect();
  cd.style.transform=`rotateY(${(e.clientX-r.left-r.width/2)/48}deg) rotateX(${-(e.clientY-r.top-r.height/2)/36}deg)`;
});
sc.addEventListener('mouseleave',()=>{cd.style.transform='';});

const cv=document.getElementById('cv'),ctx=cv.getContext('2d');
function resize(){cv.width=cd.clientWidth;cv.height=cd.clientHeight;}
window.addEventListener('resize',resize);resize();setTimeout(resize,80);
const N=75,pts=Array.from({length:N},()=>({
  x:Math.random()*cv.width,y:Math.random()*cv.height,
  vx:(Math.random()-.5)*1.2,vy:(Math.random()-.5)*1.2
}));
(function loop(){
  ctx.clearRect(0,0,cv.width,cv.height);
  pts.forEach(p=>{
    p.x+=p.vx;p.y+=p.vy;
    if(p.x<0||p.x>cv.width)p.vx*=-1;
    if(p.y<0||p.y>cv.height)p.vy*=-1;
    ctx.beginPath();ctx.arc(p.x,p.y,1.8,0,Math.PI*2);
    ctx.fillStyle='rgba(255,215,0,.45)';ctx.fill();
  });
  for(let i=0;i<N;i++)for(let j=i+1;j<N;j++){
    const d=Math.hypot(pts[i].x-pts[j].x,pts[i].y-pts[j].y);
    if(d<120){ctx.beginPath();ctx.moveTo(pts[i].x,pts[i].y);ctx.lineTo(pts[j].x,pts[j].y);
      ctx.strokeStyle=`rgba(0,116,217,${(1-d/120)*.55})`;ctx.lineWidth=.7;ctx.stroke();}
  }
  requestAnimationFrame(loop);
})();
</script>
""", height=640)


def render_info_card():
    components.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Rajdhani:wght@500;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}body{background:transparent;overflow:hidden}
.sc{perspective:900px;width:100%;height:250px;display:flex;justify-content:center;align-items:center}
.cd{width:90%;height:215px;
    background:linear-gradient(140deg,#001428 0%,#002255 60%,#001e4a 100%);
    border-radius:22px;border:1.5px solid rgba(255,215,0,.5);
    box-shadow:0 20px 50px rgba(0,0,0,.6),inset 0 0 40px rgba(0,116,217,.07);
    transform-style:preserve-3d;transition:transform .1s ease;
    display:flex;flex-direction:column;justify-content:space-between;
    padding:24px 26px;color:white}
.t{font-family:'Orbitron',sans-serif;font-size:.95em;font-weight:700;color:#FFD700;margin-bottom:4px}
.b{font-family:'Rajdhani',sans-serif;font-size:1.02em;line-height:1.7;color:#8ab}
.h{font-family:'Rajdhani',sans-serif;font-size:.8em;color:rgba(255,255,255,.2);
   background:rgba(255,255,255,.04);border-radius:8px;padding:6px 10px;text-align:center}
</style>
<div class="sc" id="sc">
  <div class="cd" id="cd">
    <div><div class="t">📊 DATA INFO</div>
    <div class="b"><b>Coverage:</b> Through Summer 2025<br><b>Source:</b> UCSB Registrar + RMP<br><b>Built by:</b> Joshua Chung</div></div>
    <div class="h">Hover to tilt ↗</div>
  </div>
</div>
<script>
const sc=document.getElementById('sc'),cd=document.getElementById('cd');
sc.addEventListener('mousemove',e=>{const r=sc.getBoundingClientRect();
  cd.style.transform=`rotateY(${(e.clientX-r.left-r.width/2)/10}deg) rotateX(${-(e.clientY-r.top-r.height/2)/8}deg)`;});
sc.addEventListener('mouseleave',()=>{cd.style.transform='';});
</script>
""", height=270)


def render_linkedin_card():
    components.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}body{background:transparent;overflow:hidden}
.sc{perspective:800px;width:100%;height:80px;display:flex;justify-content:center;align-items:center}
a{width:90%;height:58px;display:flex;align-items:center;justify-content:center;
  background:#0077b5;border-radius:14px;border:1.5px solid rgba(255,215,0,.4);
  font-family:'Rajdhani',sans-serif;font-weight:700;font-size:1.05em;color:white;
  text-decoration:none;transform-style:preserve-3d;transition:transform .1s,background .2s;
  box-shadow:0 8px 24px rgba(0,0,0,.4)}
a:hover{background:#0087cc}
</style>
<div class="sc" id="sc">
  <a href="https://www.linkedin.com/in/joshua-chung858/" target="_blank" id="li">🔗 Follow on LinkedIn</a>
</div>
<script>
const sc=document.getElementById('sc'),li=document.getElementById('li');
sc.addEventListener('mousemove',e=>{const r=sc.getBoundingClientRect();
  li.style.transform=`rotateY(${(e.clientX-r.left-r.width/2)/8}deg) rotateX(${-(e.clientY-r.top-r.height/2)/5}deg)`;});
sc.addEventListener('mouseleave',()=>{li.style.transform='';});
</script>
""", height=100)


# ─────────────────────────────────────────────
#  PROFESSOR PROFILE CARD
# ─────────────────────────────────────────────
def render_prof_card(info, prof_name):
    rating     = info.get("rating")
    difficulty = info.get("difficulty")
    take_again = info.get("take_again")
    num_ratings= info.get("num_ratings")
    tags_raw   = info.get("tags", "")
    url        = info.get("url", "")
    dept       = info.get("dept", "")

    try:
        rv = float(rating)
        r_color = "#2ECC40" if rv >= 4.0 else ("#FFDC00" if rv >= 3.0 else "#FF4136")
    except Exception:
        r_color = "#888"

    ta_str  = str(take_again) if take_again and str(take_again) != "nan" else "N/A"
    if ta_str != "N/A" and "%" not in ta_str:
        ta_str += "%"
    num_str = f"{int(float(num_ratings))}" if num_ratings and str(num_ratings) != "nan" else "N/A"
    r_str   = str(rating) if rating and str(rating) != "nan" else "N/A"
    d_str   = str(difficulty) if difficulty and str(difficulty) != "nan" else "N/A"

    tags_html = ""
    if tags_raw and str(tags_raw) != "nan":
        raw   = str(tags_raw).strip("\"'[]")
        tags  = [t.strip().strip("\"'") for t in raw.split(",") if t.strip()]
        tags_html = "".join(f'<span class="tag">{t}</span>' for t in tags[:8])

    dept_badge = f'<span class="dept">{dept}</span>' if dept and str(dept) != "nan" else ""
    rmp_btn    = (
        f'<a href="{url}" target="_blank" class="rmp-btn">🔗 View Full RMP Profile</a>'
        if url and str(url) != "nan" else ""
    )

    components.html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Rajdhani:wght@400;600;700&display=swap');
*{{margin:0;padding:0;box-sizing:border-box}}body{{background:transparent}}
.pcard{{background:linear-gradient(140deg,#001428 0%,#00184a 60%,#002255 100%);
        border:2px solid rgba(255,215,0,.55);border-radius:22px;
        padding:30px 34px;margin:6px 0 16px;
        box-shadow:0 0 50px rgba(255,215,0,.08),0 24px 50px rgba(0,0,0,.55);
        font-family:'Rajdhani',sans-serif;color:white}}
.pname{{font-family:'Orbitron',sans-serif;font-size:1.3em;font-weight:700;color:#FFD700;margin-bottom:6px}}
.dept{{background:rgba(0,116,217,.22);color:#5bb8ff;border:1px solid #0074D9;
       padding:3px 14px;border-radius:20px;font-size:.82em;display:inline-block;margin-bottom:18px}}
.stats{{display:flex;gap:14px;margin-bottom:16px}}
.stat{{flex:1;background:rgba(255,255,255,.05);border-radius:14px;padding:16px 10px;
       text-align:center;border:1px solid rgba(255,255,255,.08)}}
.stat .v{{font-size:2em;font-weight:900;line-height:1;font-family:'Orbitron',sans-serif}}
.stat .l{{font-size:.67em;color:#667;margin-top:6px;text-transform:uppercase;letter-spacing:.6px}}
.num{{text-align:center;color:#445;font-size:.8em;margin:-8px 0 14px}}
.tag-lbl{{font-size:.7em;color:#445;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}}
.tag{{background:rgba(0,204,255,.1);color:#00CCFF;border:1px solid rgba(0,204,255,.35);
      padding:5px 13px;border-radius:20px;display:inline-block;margin:3px;font-size:.78em;font-weight:600}}
.rmp-btn{{display:inline-block;margin-top:16px;padding:12px 28px;
          background:linear-gradient(135deg,#0077b5,#00a0dc);color:white;text-decoration:none;
          border-radius:14px;font-weight:800;font-size:.93em;
          box-shadow:0 6px 20px rgba(0,119,181,.4);border:2px solid rgba(255,255,255,.15);
          font-family:'Rajdhani',sans-serif;transition:background .2s}}
.rmp-btn:hover{{background:linear-gradient(135deg,#0087cc,#00bbf5)}}
</style>
<div class="pcard">
  <div class="pname">👤 {prof_name}</div>
  {dept_badge}
  <div class="stats">
    <div class="stat"><div class="v" style="color:{r_color}">{r_str}</div><div class="l">Rating</div></div>
    <div class="stat"><div class="v" style="color:#FF851B">{d_str}</div><div class="l">Difficulty</div></div>
    <div class="stat"><div class="v" style="color:#2ECC40;font-size:1.45em">{ta_str}</div><div class="l">Would Retake</div></div>
  </div>
  <div class="num">Based on {num_str} student ratings</div>
  {"<div class='tag-lbl'>Student Tags</div><div>" + tags_html + "</div>" if tags_html else ""}
  {rmp_btn}
</div>
""", height=360)


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    full_df, gpa_col, rmp_lookup = load_data()

    render_hero()

    tab_home, tab_search = st.tabs(["🏠  HOME", "🔍  SEARCH TOOL"])

    # ── HOME ────────────────────────────────
    with tab_home:
        col_main, col_side = st.columns([5, 2])
        with col_main:
            render_welcome_card()
        with col_side:
            st.markdown("<br>", unsafe_allow_html=True)
            render_info_card()
            render_linkedin_card()
            st.markdown("""
<div style="background:rgba(0,18,40,.7);border:1px solid rgba(255,215,0,.2);
            border-radius:18px;padding:22px 24px;margin-top:16px;
            font-family:'Rajdhani',sans-serif;">
  <div style="font-family:'Orbitron',sans-serif;font-size:.78em;color:#FFD700;
              margin-bottom:14px;letter-spacing:1px;">📈 GRADING LEGEND</div>
  <div style="margin-bottom:10px">
    <span style="background:#2ECC40;color:#000;padding:3px 12px;border-radius:20px;
                 font-weight:700;font-size:.85em;">EASY</span>
    <span style="color:#8ab;font-size:.9em;margin-left:8px">Avg GPA &gt; 3.3</span>
  </div>
  <div style="margin-bottom:10px">
    <span style="background:#0074D9;color:#fff;padding:3px 12px;border-radius:20px;
                 font-weight:700;font-size:.85em;">CHILL</span>
    <span style="color:#8ab;font-size:.9em;margin-left:8px">Avg GPA 2.5 – 3.3</span>
  </div>
  <div>
    <span style="background:#FF4136;color:#fff;padding:3px 12px;border-radius:20px;
                 font-weight:700;font-size:.85em;">STRESSFUL</span>
    <span style="color:#8ab;font-size:.9em;margin-left:8px">Avg GPA &lt; 2.5</span>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── SEARCH TOOL ─────────────────────────
    with tab_search:

        # sidebar
        with st.sidebar:
            st.markdown("""
<div style="font-family:'Orbitron',sans-serif;color:#FFD700;font-size:.82em;
            letter-spacing:2px;padding:10px 0 6px;
            border-bottom:1px solid rgba(255,215,0,.2);margin-bottom:16px;">
  🔍 FILTERS
</div>
""", unsafe_allow_html=True)
            all_depts     = [""] + sorted(full_df["dept"].unique().tolist())
            selected_dept = st.selectbox(
                "Department", options=all_depts, index=0,
                key="dept_q",
                format_func=lambda x: "All Departments" if x == "" else x
            )
            course_q = st.text_input("Course Number (e.g. 120A, 5A, 10)", key="course_q").strip().upper()
            prof_q   = st.text_input("Professor Name", key="prof_q").strip().upper()
            st.button("✖  Clear Filters", on_click=clear_filters, use_container_width=True)
            st.markdown("---")
            st.markdown("""
<div style="font-family:'Rajdhani',sans-serif;font-size:.88em;color:#556;line-height:1.7;">
<b style="color:#FFD700;">⭐ RMP</b> badge = click professor name to view RateMyProfessors data.
</div>
""", unsafe_allow_html=True)

        # Prof card
        if st.session_state.sel_prof_key:
            info = rmp_lookup.get(st.session_state.sel_prof_key, {})
            if info:
                render_prof_card(info, st.session_state.sel_prof_name)
            else:
                st.info(f"No RMP data found for {st.session_state.sel_prof_name}.")
            if st.button("✖  Close Professor Card", key="close_prof"):
                st.session_state.sel_prof_key  = None
                st.session_state.sel_prof_name = None
                st.rerun()
            st.markdown("---")

        # Filter
        df = full_df.copy()
        if selected_dept:
            df = df[df["dept"] == selected_dept]
        if course_q:
            df = df[df["course"].str.contains(course_q, na=False)]
        if prof_q:
            df = df[df["instructor"].str.contains(prof_q, na=False)]

        if df.empty:
            st.warning("No results found. Try adjusting the filters.")
            return

        df   = df.sort_values(["course", "year"], ascending=[True, False])
        shown = df.head(25)

        st.markdown(f"""
<div style="font-family:'Orbitron',sans-serif;font-size:.75em;
            color:rgba(255,215,0,.45);letter-spacing:2px;margin-bottom:18px;">
  SHOWING {len(shown)} OF {len(df)} RESULTS
</div>""", unsafe_allow_html=True)

        for idx, row in shown.iterrows():
            gpa_val          = row[gpa_col]
            status, clr, shd = gpa_badge(gpa_val)
            prof_name        = row["instructor"]
            jk               = row.get("join_key", "")
            has_rmp          = jk in rmp_lookup

            with st.container(border=True):
                col_info, col_chart = st.columns([3, 2])

                with col_info:
                    st.markdown(
                        f'<div style="font-family:Orbitron,sans-serif;font-size:1.05em;'
                        f'font-weight:700;color:#e8f4ff;margin-bottom:4px;">'
                        f'{row["course"]}'
                        f'<span style="color:#445;font-size:.78em;margin-left:10px;">'
                        f'{row["quarter"]} {row["year"]}</span></div>',
                        unsafe_allow_html=True
                    )

                    if has_rmp:
                        pb_col, _ = st.columns([2, 3])
                        with pb_col:
                            if st.button(
                                f"👤  {prof_name}",
                                key=f"pb_{idx}",
                                help="Click to view RMP profile",
                            ):
                                st.session_state.sel_prof_key  = jk
                                st.session_state.sel_prof_name = prof_name
                                st.rerun()
                    else:
                        st.markdown(
                            f'<div style="font-family:Rajdhani,sans-serif;font-size:1em;'
                            f'color:#667;margin:4px 0 6px;">👤 {prof_name}</div>',
                            unsafe_allow_html=True
                        )

                    rmp_pill = (
                        '<span style="font-size:.7em;color:#FFD700;'
                        'background:rgba(255,215,0,.08);border:1px solid rgba(255,215,0,.22);'
                        'padding:2px 10px;border-radius:12px;margin-left:8px;">⭐ RMP</span>'
                        if has_rmp else ""
                    )
                    txt_col = "#000" if status == "EASY" else "#fff"
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:8px;margin-top:6px;">'
                        f'<span style="font-family:Orbitron,sans-serif;font-size:.88em;'
                        f'font-weight:700;color:#cde;">GPA {gpa_val:.2f}</span>'
                        f'<span style="background:{clr};color:{txt_col};'
                        f'padding:4px 14px;border-radius:20px;font-size:.76em;font-weight:900;'
                        f'box-shadow:0 0 14px {shd};letter-spacing:1px;">{status}</span>'
                        f'{rmp_pill}</div>',
                        unsafe_allow_html=True
                    )

                with col_chart:
                    grades = pd.DataFrame({
                        "Grade": ["A", "B", "C", "D", "F"],
                        "Count": [
                            row.get("a", 0), row.get("b", 0),
                            row.get("c", 0), row.get("d", 0), row.get("f", 0)
                        ],
                    })
                    fig = px.bar(
                        grades, x="Grade", y="Count", color="Grade",
                        color_discrete_map={
                            "A": "#2ECC40", "B": "#0074D9",
                            "C": "#FFDC00", "D": "#FF851B", "F": "#FF4136"
                        },
                        template="plotly_dark", height=120,
                    )
                    fig.update_layout(
                        margin=dict(l=0, r=0, t=4, b=0),
                        showlegend=False,
                        xaxis_title=None, yaxis_title=None,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        xaxis=dict(tickfont=dict(size=11, color="#aaa")),
                        yaxis=dict(tickfont=dict(size=10, color="#555")),
                    )
                    st.plotly_chart(
                        fig, use_container_width=True,
                        key=f"fig_{idx}",
                        config={"displayModeBar": False},
                    )


if __name__ == "__main__":
    main()
