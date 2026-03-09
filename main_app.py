import streamlit as st
import pandas as pd
import os
import re
import base64
import requests
import plotly.express as px
import plotly.graph_objects as go
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
#  JOIN KEY HELPERS
# ─────────────────────────────────────────────
def parse_name(name: str) -> tuple[str, str]:
    """
    Parse an instructor name into (last, first_tokens) regardless of format.

    Handles:
      "RAVAT, UMA"       → ("RAVAT",  "UMA")
      "RAVAT U V"        → ("RAVAT",  "U V")   ← last name is first token
      "SYLVESTER BRYANNA"→ ("SYLVESTER", "BRYANNA")
      "SMITH"            → ("SMITH",  "")
    """
    if not name or pd.isna(name):
        return ("UNKNOWN", "")
    s = str(name).upper().strip()
    if "," in s:
        parts = [p.strip() for p in s.split(",", 1)]
        return (parts[0], parts[1] if len(parts) > 1 else "")
    parts = s.split()
    return (parts[0], " ".join(parts[1:]) if len(parts) > 1 else "")


def name_similarity(first_a: str, first_b: str) -> float:
    """
    Compare two 'first name' strings and return a 0-1 similarity score.
    Works even when one side is initials ("U V") and the other is a full name ("UMA VANDANA").
    """
    if not first_a or not first_b:
        return 0.5  # neutral when one side is missing
    toks_a = first_a.upper().split()
    toks_b = first_b.upper().split()
    if not toks_a or not toks_b:
        return 0.5
    # Compare token by token up to the shorter side
    matches = 0
    for ta, tb in zip(toks_a, toks_b):
        # Both are initials (single char) → must match exactly
        # One is initial, other is full token → match if initial == first char of full
        # Both are full words → must match exactly
        if ta == tb:
            matches += 1
        elif len(ta) == 1 and tb.startswith(ta):
            matches += 0.9
        elif len(tb) == 1 and ta.startswith(tb):
            matches += 0.9
        else:
            matches += 0  # mismatch
    total = max(len(toks_a), len(toks_b))
    return matches / total if total else 0.5


def make_join_key(name: str) -> str:
    """Stable per-row key = LAST||first_tokens (used only inside grades df)."""
    last, first = parse_name(name)
    return f"{last}||{first}"


# ─────────────────────────────────────────────
#  DATA LOADING
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    def find(fname):
        for p in [fname, os.path.join("data", fname)]:
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

    df["join_key"] = df["instructor"].apply(make_join_key)

    # ── Build RMP lookup via similarity matching ─────────────────────────
    rmp_lookup = {}   # grades join_key → rmp entry dict

    if rmp_path:
        rmp = pd.read_csv(rmp_path)
        rmp.columns = [c.strip().lower() for c in rmp.columns]

        # Normalise column names: strip "rmp_" prefix so we handle both variants
        col_alias = {}
        for c in rmp.columns:
            col_alias[c.replace("rmp_", "")] = c

        def get_rmp(row, field):
            return row.get(col_alias.get(field, field))

        # Build list of (last, first, entry) from RMP for matching
        rmp_entries = []
        for _, r in rmp.iterrows():
            raw_name = str(r.get("instructor", ""))
            last, first = parse_name(raw_name)
            entry = {
                "rating":      get_rmp(r, "rating"),
                "difficulty":  get_rmp(r, "difficulty"),
                "take_again":  get_rmp(r, "take_again"),
                "num_ratings": get_rmp(r, "num_ratings"),
                "tags":        get_rmp(r, "tags"),
                "url":         get_rmp(r, "url"),
                "dept":        get_rmp(r, "dept"),
                "full_name":   raw_name,
                "_last":       last,
                "_first":      first,
            }
            rmp_entries.append(entry)

        # Last-name bucket for fast lookup
        rmp_by_last: dict = {}
        for e in rmp_entries:
            rmp_by_last.setdefault(e["_last"], []).append(e)

        # For each unique grades instructor find the best-matching RMP entry
        unique_instructors = df[["instructor", "join_key"]].drop_duplicates()
        for _, urow in unique_instructors.iterrows():
            inst = urow["instructor"]
            jk   = urow["join_key"]
            g_last, g_first = parse_name(inst)

            candidates = rmp_by_last.get(g_last, [])
            if not candidates:
                continue

            if len(candidates) == 1:
                best = candidates[0]
            else:
                scored = sorted(
                    candidates,
                    key=lambda e: name_similarity(g_first, e["_first"]),
                    reverse=True,
                )
                best_score = name_similarity(g_first, scored[0]["_first"])
                if best_score < 0.4:
                    continue  # ambiguous match — skip
                best = scored[0]

            rmp_lookup[jk] = {k: v for k, v in best.items() if not k.startswith("_")}

        # Merge matched data back into grades df
        rmp_rows = [{"join_key": jk, **v} for jk, v in rmp_lookup.items()]
        if rmp_rows:
            rmp_df = pd.DataFrame(rmp_rows).rename(columns={
                "rating":      "rmp_rating",
                "difficulty":  "rmp_difficulty",
                "take_again":  "rmp_take_again",
                "num_ratings": "rmp_num_ratings",
                "tags":        "rmp_tags",
                "url":         "rmp_url",
                "dept":        "rmp_dept",
                "full_name":   "rmp_full_name",
            })
            df = pd.merge(df, rmp_df, on="join_key", how="left")

    gpa_col  = next((c for c in ["avggpa", "avg_gpa", "avg gpa"] if c in df.columns), "avggpa")
    grp_cols = ["instructor", "quarter", "year", "course", "dept", "join_key"]
    agg = {gpa_col: "mean", "a": "sum", "b": "sum", "c": "sum", "d": "sum", "f": "sum"}
    for ec in ["rmp_url", "rmp_rating", "rmp_difficulty", "rmp_take_again",
               "rmp_tags", "rmp_num_ratings", "rmp_full_name"]:
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
if "schedule_text" not in st.session_state:
    st.session_state.schedule_text = ""
if "parsed_schedule" not in st.session_state:
    st.session_state.parsed_schedule = []


def clear_filters():
    st.session_state.dept_q        = ""
    st.session_state.course_q      = ""
    st.session_state.prof_q        = ""
    st.session_state.sel_prof_key  = None
    st.session_state.sel_prof_name = None


def dismiss_prof():
    """Called whenever a filter changes — closes the open professor card."""
    st.session_state.sel_prof_key  = None
    st.session_state.sel_prof_name = None


def gpa_badge(gpa):
    if gpa < 3.0:
        return "STRESSFUL", "#FF4136", "rgba(255,65,54,0.35)"
    elif gpa > 3.5:
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
      <h1>WELCOME GAUCHOS! ٩(＾◡＾)۶</h1>
      <p>Gaucho Insights lets you see how stressful or easy any UCSB class is before you register —
         based on real historical grade distributions and RateMyProfessors data.
         <strong style="color:#FFD700">Search by department, course number, or professor name.</strong></p>
      <div class="grid">
        <div class="box" style="border-left:4px solid #FFD700;padding-left:18px">
          <div class="bt" style="color:#FFD700">MISSION</div>
          <div class="bb">Help UCSB students make smarter scheduling decisions with real data.</div>
        </div>
        <div class="box" style="border-left:4px solid #5bb8ff;padding-left:18px">
          <div class="bt" style="color:#5bb8ff">SEARCH TOOL</div>
          <div class="bb">Filter classes and click any professor name to see their full RMP profile + GPA history.</div>
        </div>
        <div class="box" style="border-left:4px solid #2ECC40;padding-left:18px">
          <div class="bt" style="color:#2ECC40">EASY  › 3.5 avg GPA</div>
          <div class="bb">Class is known to be manageable. High average grades historically.</div>
        </div>
        <div class="box" style="border-left:4px solid #FF4136;padding-left:18px">
          <div class="bt" style="color:#FF4136">STRESSFUL ‹ 3.0 avg GPA</div>
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
    <div><div class="t">꒰✩‿✩꒱ DATA INFO</div>
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
#  PROFESSOR PROFILE CARD  (with GPA history)
# ─────────────────────────────────────────────
def render_prof_card(info: dict, prof_name: str, prof_history_df: pd.DataFrame, gpa_col: str):
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
        f'<a href="{url}" target="_blank" class="rmp-btn">(づ ◕‿◕ )づ View Full RMP Profile</a>'
        if url and str(url) != "nan" else ""
    )

    # Dynamic height: base + extra for tags row
    has_tags   = bool(tags_html)
    card_h     = 420 + (70 if has_tags else 0)
    scene_h    = card_h + 40

    components.html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Rajdhani:wght@400;600;700&display=swap');
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:transparent;overflow:hidden}}
.scene{{perspective:1100px;width:100%;height:{scene_h}px;
        display:flex;justify-content:center;align-items:center}}
.pcard{{width:98%;
        background:linear-gradient(140deg,#001428 0%,#001e4a 55%,#002255 100%);
        border:2px solid rgba(255,215,0,.55);border-radius:22px;
        padding:28px 32px 24px;
        box-shadow:0 0 60px rgba(255,215,0,.07),0 30px 60px rgba(0,0,0,.65),
                   inset 0 0 40px rgba(0,116,217,.05);
        font-family:'Rajdhani',sans-serif;color:white;
        transform-style:preserve-3d;transition:transform .1s ease;
        position:relative;overflow:hidden}}
/* animated shimmer line */
.pcard::before{{content:'';position:absolute;top:0;left:-60%;width:40%;height:100%;
  background:linear-gradient(105deg,transparent 40%,rgba(255,215,0,.06) 50%,transparent 60%);
  animation:shimmer 4s infinite;pointer-events:none}}
@keyframes shimmer{{0%{{left:-60%}}100%{{left:130%}}}}
.pname{{font-family:'Orbitron',sans-serif;font-size:1.25em;font-weight:900;
        color:#FFD700;margin-bottom:8px;
        text-shadow:0 0 14px rgba(255,215,0,.35)}}
.dept{{background:rgba(0,116,217,.22);color:#5bb8ff;border:1px solid rgba(0,116,217,.5);
       padding:3px 14px;border-radius:20px;font-size:.8em;display:inline-block;margin-bottom:20px}}
.stats{{display:flex;gap:12px;margin-bottom:14px}}
.stat{{flex:1;background:rgba(255,255,255,.05);border-radius:14px;padding:18px 10px;
       text-align:center;border:1px solid rgba(255,255,255,.07);
       transition:background .2s,border-color .2s}}
.stat:hover{{background:rgba(255,255,255,.09);border-color:rgba(255,215,0,.25)}}
.stat .v{{font-size:2em;font-weight:900;line-height:1;font-family:'Orbitron',sans-serif}}
.stat .l{{font-size:.65em;color:#556;margin-top:7px;text-transform:uppercase;letter-spacing:.8px}}
.num{{text-align:center;color:#445;font-size:.78em;margin:-4px 0 16px}}
.tag-lbl{{font-size:.68em;color:#445;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}}
.tag{{background:rgba(0,204,255,.1);color:#00CCFF;border:1px solid rgba(0,204,255,.3);
      padding:4px 12px;border-radius:20px;display:inline-block;margin:3px;
      font-size:.76em;font-weight:600}}
.rmp-btn{{display:inline-block;margin-top:18px;padding:11px 26px;
          background:linear-gradient(135deg,#0077b5,#00a0dc);color:white;
          text-decoration:none;border-radius:14px;font-weight:800;font-size:.9em;
          box-shadow:0 6px 22px rgba(0,119,181,.45);
          border:1.5px solid rgba(255,255,255,.15);
          font-family:'Rajdhani',sans-serif;transition:background .2s,transform .15s}}
.rmp-btn:hover{{background:linear-gradient(135deg,#0087cc,#00bbf5);transform:translateY(-2px)}}
</style>
<div class="scene" id="sc">
  <div class="pcard" id="cd">
    <div class="pname">{prof_name}</div>
    {dept_badge}
    <div class="stats">
      <div class="stat"><div class="v" style="color:{r_color}">{r_str}</div><div class="l">Rating</div></div>
      <div class="stat"><div class="v" style="color:#FF851B">{d_str}</div><div class="l">Difficulty</div></div>
      <div class="stat"><div class="v" style="color:#2ECC40;font-size:1.4em">{ta_str}</div><div class="l">Would Retake</div></div>
    </div>
    <div class="num">Based on {num_str} student ratings</div>
    {"<div class='tag-lbl'>Student Tags</div><div>" + tags_html + "</div>" if tags_html else ""}
    {rmp_btn}
  </div>
</div>
<script>
const sc=document.getElementById('sc'),cd=document.getElementById('cd');
sc.addEventListener('mousemove',e=>{{
  const r=sc.getBoundingClientRect();
  cd.style.transform=`rotateY(${{(e.clientX-r.left-r.width/2)/36}}deg) rotateX(${{-(e.clientY-r.top-r.height/2)/24}}deg) translateZ(18px)`;
}});
sc.addEventListener('mouseleave',()=>{{cd.style.transform='rotateY(0) rotateX(0) translateZ(0)';}});
</script>
""", height=scene_h)

    # ── GPA History 3D Scatter Chart ───────────────────────────────
    if not prof_history_df.empty and gpa_col in prof_history_df.columns:
        st.markdown(
            '<div style="font-family:Orbitron,sans-serif;font-size:.78em;'
            'color:#FFD700;letter-spacing:2px;margin:24px 0 4px;">GPA HISTORY — INTERACTIVE 3D</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div style="font-family:Rajdhani,sans-serif;font-size:.82em;color:#556;'
            'margin:0 0 14px;">Drag to rotate · Scroll to zoom · Hover dots for details'
            ' &nbsp;|&nbsp; <b style="color:#aaa">X</b> = Term &nbsp;'
            '<b style="color:#aaa">Y</b> = Course &nbsp;'
            '<b style="color:#aaa">Z</b> = Avg GPA</div>',
            unsafe_allow_html=True,
        )

        hist = prof_history_df.copy()
        hist["term"] = hist["quarter"].astype(str) + " " + hist["year"].astype(str)

        quarter_order = {"WINTER": 0, "SPRING": 1, "SUMMER": 2, "FALL": 3}
        hist["_qord"] = hist["quarter"].map(quarter_order).fillna(9)
        hist = hist.sort_values(["year", "_qord"]).reset_index(drop=True)

        courses = sorted(hist["course"].unique())
        terms   = list(dict.fromkeys(hist["term"].tolist()))

        term_idx   = {t: i for i, t in enumerate(terms)}
        course_idx = {c: i for i, c in enumerate(courses)}

        palette = [
            "#FF4136", "#0074D9", "#FFD700", "#2ECC40",
            "#FF851B", "#B10DC9", "#00CCFF", "#FF69B4",
            "#AAAAAA", "#01FF70", "#F012BE", "#7FDBFF",
        ]

        fig = go.Figure()

        for ci, course in enumerate(courses):
            sub   = hist[hist["course"] == course].copy()
            color = palette[ci % len(palette)]

            xs = [term_idx[t]   for t in sub["term"]]
            ys = [course_idx[c] for c in sub["course"]]
            zs = sub[gpa_col].tolist()

            # Main dots + connecting line — solid course color, no GPA colorscale
            fig.add_trace(go.Scatter3d(
                x=xs, y=ys, z=zs,
                mode="markers+lines",
                name=course,
                legendgroup=course,
                showlegend=False,          # legend handled externally below chart
                line=dict(color=color, width=2, dash="dot"),
                marker=dict(
                    size=6,
                    color=color,
                    opacity=0.95,
                    symbol="circle",
                    line=dict(color="rgba(255,255,255,0.4)", width=1),
                ),
                hovertemplate=(
                    f"<b>{course}</b><br>"
                    "Term: <b>%{customdata}</b><br>"
                    "Avg GPA: <b>%{z:.2f}</b>"
                    "<extra></extra>"
                ),
                customdata=sub["term"].tolist(),
            ))

            # Vertical drop lines from dot down to floor
            drop_x, drop_y, drop_z = [], [], []
            for x, y, z in zip(xs, ys, zs):
                drop_x += [x, x, None]
                drop_y += [y, y, None]
                drop_z += [2.0, z, None]

            fig.add_trace(go.Scatter3d(
                x=drop_x, y=drop_y, z=drop_z,
                mode="lines",
                line=dict(color=color, width=1, dash="dot"),
                opacity=0.25,
                showlegend=False,
                hoverinfo="skip",
                legendgroup=course,
            ))

            # Floating GPA labels above each dot
            fig.add_trace(go.Scatter3d(
                x=xs, y=ys, z=[z + 0.13 for z in zs],
                mode="text",
                text=[f"{z:.2f}" for z in zs],
                textfont=dict(size=13, color="white", family="Orbitron"),
                showlegend=False,
                hoverinfo="skip",
                legendgroup=course,
            ))

        # Reference planes for EASY and STRESSFUL thresholds
        xr = [-0.5, len(terms) - 0.5]
        yr = [-0.5, len(courses) - 0.5]
        for ref_z, ref_color, ref_name in [
            (3.5, "rgba(46,204,64,0.15)",  "── EASY ≥ 3.5"),
            (3.0, "rgba(255,65,54,0.15)",  "── STRESSFUL < 3.0"),
        ]:
            fig.add_trace(go.Surface(
                x=[[xr[0], xr[1]], [xr[0], xr[1]]],
                y=[[yr[0], yr[0]], [yr[1], yr[1]]],
                z=[[ref_z, ref_z], [ref_z, ref_z]],
                colorscale=[[0, ref_color], [1, ref_color]],
                showscale=False,
                opacity=0.55,
                name=ref_name,
                showlegend=True,
                hoverinfo="skip",
            ))

        fig.update_layout(
            template="plotly_dark",
            height=540,
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            scene=dict(
                bgcolor="rgba(0,6,18,1)",
                xaxis=dict(
                    tickvals=list(range(len(terms))),
                    ticktext=terms,
                    tickfont=dict(size=11, color="#bbc"),
                    gridcolor="rgba(255,255,255,0.1)",
                    showbackground=True,
                    backgroundcolor="rgba(0,8,24,0.5)",
                    title=dict(text="Term", font=dict(size=13, color="#ccd")),
                ),
                yaxis=dict(
                    tickvals=list(range(len(courses))),
                    ticktext=courses,
                    tickfont=dict(size=11, color="#ddd"),
                    gridcolor="rgba(255,255,255,0.1)",
                    showbackground=True,
                    backgroundcolor="rgba(0,8,24,0.5)",
                    title=dict(text="Course", font=dict(size=13, color="#ccd")),
                ),
                zaxis=dict(
                    range=[2.0, 4.3],
                    tickfont=dict(size=11, color="#bbc"),
                    gridcolor="rgba(255,255,255,0.1)",
                    showbackground=True,
                    backgroundcolor="rgba(0,10,28,0.7)",
                    title=dict(text="Avg GPA", font=dict(size=13, color="#ccd")),
                ),
                camera=dict(
                    eye=dict(x=1.8, y=-1.8, z=1.0),
                    up=dict(x=0, y=0, z=1),
                ),
                aspectmode="manual",
                aspectratio=dict(
                    x=max(1.4, len(terms) * 0.28),
                    y=max(0.7, len(courses) * 0.22),
                    z=0.9,
                ),
            ),
            legend=dict(
                x=0.01, y=0.99,
                font=dict(family="Rajdhani", size=11, color="#aaa"),
                bgcolor="rgba(0,0,0,0)",
                itemsizing="constant",
                bordercolor="rgba(255,215,0,0.15)",
                borderwidth=1,
                visible=False,
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            key=f"prof_hist_{st.session_state.sel_prof_key}",
            config={"displayModeBar": True, "displaylogo": False,
                    "modeBarButtonsToRemove": ["toImage"]},
        )

        # ── External legend below the chart ──────────────────────────
        legend_items = "".join([
            f'<div style="display:flex;align-items:center;gap:8px;padding:6px 14px;'
            f'background:rgba(255,255,255,0.04);border-radius:10px;'
            f'border:1px solid rgba(255,255,255,0.07);">'
            f'<span style="display:inline-block;width:12px;height:12px;border-radius:50%;'
            f'background:{palette[ci % len(palette)]};'
            f'box-shadow:0 0 6px {palette[ci % len(palette)]};flex-shrink:0;"></span>'
            f'<span style="font-family:Rajdhani,sans-serif;font-size:.88em;'
            f'color:#ccc;white-space:nowrap;">{course}</span>'
            f'</div>'
            for ci, course in enumerate(courses)
        ])
        st.markdown(
            f'<div style="margin:10px 0 20px;">'
            f'<div style="font-family:Orbitron,sans-serif;font-size:.68em;color:#FFD700;'
            f'letter-spacing:2px;margin-bottom:10px;">COURSES</div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:8px;">{legend_items}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Summary table below chart
        summary = (
            hist.groupby("course")[gpa_col]
            .agg(["mean", "count"])
            .reset_index()
            .rename(columns={"mean": "Avg GPA", "count": "Sections"})
            .sort_values("Avg GPA", ascending=False)
        )
        summary["Avg GPA"] = summary["Avg GPA"].map("{:.2f}".format)
        st.markdown(
            '<div style="font-family:Orbitron,sans-serif;font-size:.72em;'
            'color:#FFD700;letter-spacing:2px;margin:14px 0 8px;">꒰✩‿✩꒱ COURSE SUMMARY</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(
            summary,
            hide_index=True,
            use_container_width=True,
        )


# ─────────────────────────────────────────────
#  SCHEDULE PARSER
# ─────────────────────────────────────────────
def parse_gold_schedule(text: str) -> list[dict]:
    """
    Parse pasted UCSB GOLD schedule text.
    Returns list of dicts: {course, dept, num, instructor, raw_line}

    Handles formats like:
      PSTAT 122 - DESIGN OF EXPERMNTS
      40220  Grading: L  4.0 Units  ABUZAID A H  M W  8:00 AM-9:15 AM  ILP, 1101
    """
    results = []
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]

    course_pat  = re.compile(r'^([A-Z][A-Z &]+?)\s+(\d+[A-Z]*)\s*[-–]\s*(.+)$')
    section_pat = re.compile(r'^\d{5}\s+Grading')

    current_course = None
    current_dept   = None
    current_num    = None

    for line in lines:
        m = course_pat.match(line)
        if m:
            current_dept   = m.group(1).strip()
            current_num    = m.group(2).strip()
            current_course = f"{current_dept} {current_num}"
            continue

        if section_pat.match(line) and current_course:
            # Extract instructor: after "Units" token, grab the name before day codes
            day_pat = re.compile(r'([MTWRF]{1,5}|T\.B\.A)')
            units_idx = line.find("Units")
            instructor = ""
            if units_idx != -1:
                after = line[units_idx + 5:].strip()
                # instructor is everything before the first day-of-week pattern
                dm = day_pat.search(after)
                if dm:
                    raw_inst = after[:dm.start()].strip().rstrip(",").strip()
                    # clean up: remove leading/trailing punctuation
                    instructor = raw_inst.strip()
                else:
                    instructor = after.split()[0] if after else ""

            if instructor and instructor.upper() not in ("T.B.A", "TBA", ""):
                results.append({
                    "course":     current_course,
                    "dept":       current_dept,
                    "num":        current_num,
                    "instructor": instructor.upper(),
                })

    # Deduplicate by course+instructor
    seen = set()
    unique = []
    for r in results:
        key = (r["course"], r["instructor"])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique



# ─────────────────────────────────────────────
#  VISION SCHEDULE PARSER (Claude API)
# ─────────────────────────────────────────────
def parse_schedule_from_image(image_bytes: bytes, mime_type: str = "image/png") -> list[dict]:
    """
    Send a screenshot to Claude claude-sonnet-4-20250514 and extract
    course + instructor pairs from the UCSB GOLD schedule image.
    Returns list of dicts: {course, dept, num, instructor}
    """
    b64 = base64.b64encode(image_bytes).decode()

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": b64,
                    }
                },
                {
                    "type": "text",
                    "text": (
                        "This is a UCSB GOLD 'My Class Schedule' screenshot. "
                        "Extract every course and its instructor. "
                        "Return ONLY valid JSON — an array of objects, each with exactly these keys: "
                        "course (e.g. 'PSTAT 122'), dept (e.g. 'PSTAT'), num (e.g. '122'), instructor (e.g. 'ABUZAID A H'). "
                        "If a section shows 'T.B.A' as instructor, skip it. "
                        "Deduplicate: if the same course+instructor appears more than once, include it only once. "
                        "Return ONLY the JSON array, no explanation, no markdown fences."
                    )
                }
            ]
        }]
    }

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        text = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        ).strip()

        # Strip possible markdown fences
        text = re.sub(r"^```[a-z]*\n?", "", text).rstrip("`").strip()

        import json
        entries = json.loads(text)
        results = []
        for e in entries:
            course = str(e.get("course", "")).upper().strip()
            dept   = str(e.get("dept",   "")).upper().strip()
            num    = str(e.get("num",    "")).upper().strip()
            inst   = str(e.get("instructor", "")).upper().strip()
            if course and inst and inst not in ("T.B.A", "TBA", ""):
                results.append({"course": course, "dept": dept,
                                 "num": num, "instructor": inst})
        return results

    except Exception as ex:
        st.error(f"Vision API error: {ex}")
        return []


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    full_df, gpa_col, rmp_lookup = load_data()

    render_hero()

    tab_home, tab_search, tab_quarter = st.tabs(["HOME", "SEARCH TOOL", "MY QUARTER"])

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
              margin-bottom:14px;letter-spacing:1px;">GRADING LEGEND</div>
  <div style="margin-bottom:10px">
    <span style="background:#2ECC40;color:#000;padding:3px 12px;border-radius:20px;
                 font-weight:700;font-size:.85em;">EASY</span>
    <span style="color:#8ab;font-size:.9em;margin-left:8px">Avg GPA &gt; 3.5</span>
  </div>
  <div style="margin-bottom:10px">
    <span style="background:#0074D9;color:#fff;padding:3px 12px;border-radius:20px;
                 font-weight:700;font-size:.85em;">CHILL</span>
    <span style="color:#8ab;font-size:.9em;margin-left:8px">Avg GPA 3.1 – 3.5</span>
  </div>
  <div>
    <span style="background:#FF4136;color:#fff;padding:3px 12px;border-radius:20px;
                 font-weight:700;font-size:.85em;">STRESSFUL</span>
    <span style="color:#8ab;font-size:.9em;margin-left:8px">Avg GPA &lt; 3.0</span>
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
  FILTERS
</div>
""", unsafe_allow_html=True)
            all_depts     = [""] + sorted(full_df["dept"].unique().tolist())
            selected_dept = st.selectbox(
                "Department", options=all_depts, index=0,
                key="dept_q",
                on_change=dismiss_prof,
                format_func=lambda x: "All Departments" if x == "" else x
            )
            course_q = st.text_input("Course Number (e.g. 120A, 5A, 10)", key="course_q", on_change=dismiss_prof).strip().upper()
            prof_q   = st.text_input("Professor Name", key="prof_q", on_change=dismiss_prof).strip().upper()
            st.button("(シ_ _)シ  Clear Filters", on_click=clear_filters, use_container_width=True)
            st.markdown("---")
            st.markdown("""
<div style="font-family:'Rajdhani',sans-serif;font-size:.88em;color:#556;line-height:1.7;">
<b style="color:#FFD700;">RMP</b> badge = click professor name to view RateMyProfessors data + GPA history.
</div>
""", unsafe_allow_html=True)

        # ── Prof card (shown at top when selected) ────────────
        if st.session_state.sel_prof_key:
            lk = st.session_state.sel_prof_key
            info = rmp_lookup.get(lk, {})

            # Pull all historical rows for this professor from the FULL dataset
            prof_hist = full_df[full_df["join_key"] == lk].copy()

            if info:
                render_prof_card(info, st.session_state.sel_prof_name, prof_hist, gpa_col)
            else:
                st.info(f"No RMP data found for {st.session_state.sel_prof_name}.")
                if not prof_hist.empty:
                    render_prof_card({}, st.session_state.sel_prof_name, prof_hist, gpa_col)

            if st.button("(シ_ _)シ  Close Professor Card", key="close_prof"):
                st.session_state.sel_prof_key  = None
                st.session_state.sel_prof_name = None
                st.rerun()
            st.markdown("---")

        # ── Filter ────────────────────────────────────────────
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

            # ── Resolve RMP membership with fuzzy fallback ──
            has_rmp = jk in rmp_lookup

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
                                f"{prof_name}",
                                key=f"pb_{idx}",
                                help="Click to view RMP profile + GPA history",
                            ):
                                st.session_state.sel_prof_key  = jk
                                st.session_state.sel_prof_name = prof_name
                                st.rerun()
                    else:
                        st.markdown(
                            f'<div style="font-family:Rajdhani,sans-serif;font-size:1em;'
                            f'color:#667;margin:4px 0 6px;">{prof_name}</div>',
                            unsafe_allow_html=True
                        )

                    rmp_pill = (
                        '<span style="font-size:.7em;color:#FFD700;'
                        'background:rgba(255,215,0,.08);border:1px solid rgba(255,215,0,.22);'
                        'padding:2px 10px;border-radius:12px;margin-left:8px;">꒰✩‿✩꒱ RMP</span>'
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


    # ── MY QUARTER ──────────────────────────────────────────────────────────
    with tab_quarter:

        # ── Intro card ──────────────────────────────────────────────────────
        components.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Rajdhani:wght@500;600&display=swap');
*{margin:0;padding:0;box-sizing:border-box}body{background:transparent;overflow:hidden}
.sc{perspective:900px;width:100%;height:165px;display:flex;justify-content:center;align-items:center}
.cd{width:96%;height:140px;
    background:linear-gradient(135deg,#001428 0%,#001e4a 60%,#002255 100%);
    border-radius:18px;border:1.5px solid rgba(255,215,0,.4);
    box-shadow:0 16px 40px rgba(0,0,0,.5),inset 0 0 30px rgba(0,116,217,.06);
    transform-style:preserve-3d;transition:transform .1s ease;
    padding:20px 26px;color:white;display:flex;align-items:center;gap:24px}
.icon{font-size:2.4em;flex-shrink:0}
.title{font-family:'Orbitron',sans-serif;font-size:.95em;font-weight:900;
       color:#FFD700;margin-bottom:6px;text-shadow:0 0 10px rgba(255,215,0,.3)}
.desc{font-family:'Rajdhani',sans-serif;font-size:.95em;color:#8ab;line-height:1.55}
</style>
<div class="sc" id="sc">
  <div class="cd" id="cd">
    <div class="icon">꒰✩‿✩꒱</div>
    <div>
      <div class="title">MY QUARTER — INSTANT SCHEDULE INSIGHTS</div>
      <div class="desc">Upload a screenshot of your UCSB GOLD schedule. Claude reads it automatically
      and shows GPA history + RMP data for every class instantly.</div>
    </div>
  </div>
</div>
<script>
const sc=document.getElementById('sc'),cd=document.getElementById('cd');
sc.addEventListener('mousemove',e=>{const r=sc.getBoundingClientRect();
  cd.style.transform=`rotateY(${(e.clientX-r.left-r.width/2)/30}deg) rotateX(${-(e.clientY-r.top-r.height/2)/20}deg)`;});
sc.addEventListener('mouseleave',()=>{cd.style.transform='';});
</script>
""", height=185)

        # ── How-to instructions ──────────────────────────────────────────────
        st.markdown("""
<div style="background:rgba(0,116,217,0.07);border:1px solid rgba(0,116,217,0.25);
            border-radius:14px;padding:16px 20px;margin-bottom:18px;
            font-family:'Rajdhani',sans-serif;font-size:.92em;color:#8ab;line-height:1.9;">
  <span style="font-family:'Orbitron',sans-serif;font-size:.75em;color:#5bb8ff;
               letter-spacing:1px;">HOW TO USE</span><br>
  1. Go to <b style="color:#fff">UCSB GOLD</b> → <b style="color:#fff">My Class Schedule</b><br>
  2. Take a <b style="color:#fff">screenshot</b> of the schedule table (the whole page or just the class list)<br>
  3. Upload it below — Claude reads the image and pulls insights for every class ꒰✩‿✩꒱
</div>
""", unsafe_allow_html=True)

        # ── Image uploader ───────────────────────────────────────────────────
        uploaded_img = st.file_uploader(
            "Upload your GOLD schedule screenshot",
            type=["png", "jpg", "jpeg", "webp"],
            label_visibility="collapsed",
        )

        col_analyze, col_clear = st.columns([2, 1])
        with col_analyze:
            run_vision = st.button("Analyze Schedule Image",
                                   use_container_width=True,
                                   disabled=(uploaded_img is None))
        with col_clear:
            if st.button("(シ_ _)シ  Clear", use_container_width=True):
                st.session_state.parsed_schedule = []
                st.rerun()

        # Show the uploaded image preview
        if uploaded_img is not None:
            st.image(uploaded_img, caption="Your uploaded schedule", use_column_width=True)

        if run_vision and uploaded_img is not None:
            mime = uploaded_img.type or "image/png"
            img_bytes = uploaded_img.read()
            with st.spinner("꒰(･‿･)꒱ Claude is reading your schedule..."):
                st.session_state.parsed_schedule = parse_schedule_from_image(img_bytes, mime)
            if not st.session_state.parsed_schedule:
                st.warning("No courses detected. Make sure the screenshot shows the class list clearly.")
            else:
                st.rerun()

        parsed = st.session_state.parsed_schedule

        if not parsed:
            st.stop()

        # ── Quarter summary strip ────────────────────────────────────────────
        n_courses  = len(parsed)
        n_with_rmp = sum(1 for p in parsed if make_join_key(p["instructor"]) in rmp_lookup)
        avg_gpas   = []
        for p in parsed:
            jk  = make_join_key(p["instructor"])
            sub = full_df[full_df["join_key"] == jk]
            if not sub.empty:
                avg_gpas.append(sub[gpa_col].mean())
        overall_avg = sum(avg_gpas) / len(avg_gpas) if avg_gpas else None
        ov_status, ov_clr, _ = gpa_badge(overall_avg) if overall_avg else ("N/A", "#666", "")

        st.markdown(f"""
<div style="display:flex;gap:14px;margin:18px 0 24px;flex-wrap:wrap;">
  <div style="flex:1;min-width:130px;background:rgba(255,215,0,.07);border:1px solid rgba(255,215,0,.2);
              border-radius:14px;padding:16px;text-align:center;">
    <div style="font-family:'Orbitron',sans-serif;font-size:1.8em;font-weight:900;color:#FFD700">{n_courses}</div>
    <div style="font-family:'Rajdhani',sans-serif;font-size:.8em;color:#556;letter-spacing:1px;margin-top:4px;">CLASSES DETECTED</div>
  </div>
  <div style="flex:1;min-width:130px;background:rgba(0,116,217,.07);border:1px solid rgba(0,116,217,.2);
              border-radius:14px;padding:16px;text-align:center;">
    <div style="font-family:'Orbitron',sans-serif;font-size:1.8em;font-weight:900;color:#5bb8ff">{n_with_rmp}</div>
    <div style="font-family:'Rajdhani',sans-serif;font-size:.8em;color:#556;letter-spacing:1px;margin-top:4px;">PROFS WITH RMP</div>
  </div>
  <div style="flex:1;min-width:130px;background:rgba(46,204,64,.06);border:1px solid rgba(46,204,64,.15);
              border-radius:14px;padding:16px;text-align:center;">
    <div style="font-family:'Orbitron',sans-serif;font-size:1.8em;font-weight:900;color:{ov_clr}">{f"{overall_avg:.2f}" if overall_avg else "N/A"}</div>
    <div style="font-family:'Rajdhani',sans-serif;font-size:.8em;color:#556;letter-spacing:1px;margin-top:4px;">PROJECTED AVG GPA</div>
  </div>
  <div style="flex:1;min-width:130px;background:rgba(255,65,54,.06);border:1px solid rgba(255,65,54,.12);
              border-radius:14px;padding:16px;text-align:center;">
    <div style="font-family:'Orbitron',sans-serif;font-size:1.4em;font-weight:900;color:{ov_clr};margin-top:4px">{ov_status}</div>
    <div style="font-family:'Rajdhani',sans-serif;font-size:.8em;color:#556;letter-spacing:1px;margin-top:4px;">QUARTER VIBE</div>
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown(
            f'<div style="font-family:Orbitron,sans-serif;font-size:.75em;'
            f'color:rgba(255,215,0,.5);letter-spacing:2px;margin-bottom:18px;">'
            f'YOUR {n_courses} CLASSES THIS QUARTER</div>',
            unsafe_allow_html=True
        )

        # ── One card per detected class ──────────────────────────────────────
        for pi, entry in enumerate(parsed):
            course_name = entry["course"]
            instructor  = entry["instructor"]
            dept        = entry["dept"]
            jk          = make_join_key(instructor)

            # Get GPA data for this specific course+instructor combo
            course_hist = full_df[
                (full_df["join_key"] == jk) &
                (full_df["course"].str.contains(entry["num"], na=False))
            ].copy()

            # Fallback: all courses by this instructor
            if course_hist.empty:
                course_hist = full_df[full_df["join_key"] == jk].copy()

            # Compute avg gpa for this course
            avg_gpa = course_hist[gpa_col].mean() if not course_hist.empty else None
            status, clr, shd = gpa_badge(avg_gpa) if avg_gpa else ("N/A", "#666", "rgba(0,0,0,0)")
            txt_col = "#000" if status == "EASY" else "#fff"

            # RMP info
            rmp_info    = rmp_lookup.get(jk, {})
            has_rmp     = bool(rmp_info)
            rmp_rating  = rmp_info.get("rating", "N/A")
            rmp_diff    = rmp_info.get("difficulty", "N/A")
            rmp_url     = rmp_info.get("url", "")
            try:
                rv = float(rmp_rating)
                r_clr = "#2ECC40" if rv >= 4.0 else ("#FFDC00" if rv >= 3.0 else "#FF4136")
            except Exception:
                r_clr = "#888"

            with st.container(border=True):
                # Course header
                st.markdown(
                    f'<div style="font-family:Orbitron,sans-serif;font-size:1.1em;font-weight:900;'
                    f'color:#FFD700;margin-bottom:4px;">{course_name}</div>'
                    f'<div style="font-family:Rajdhani,sans-serif;font-size:.95em;color:#8ab;margin-bottom:10px;">'
                    f'Instructor: <b style="color:#ddd">{instructor}</b></div>',
                    unsafe_allow_html=True
                )

                col_stats, col_chart = st.columns([2, 3])

                with col_stats:
                    # GPA badge
                    gpa_display = f"{avg_gpa:.2f}" if avg_gpa else "No Data"
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">'
                        f'<span style="font-family:Orbitron,sans-serif;font-size:1.1em;font-weight:700;color:#cde;">Avg GPA: {gpa_display}</span>'
                        f'<span style="background:{clr};color:{txt_col};padding:3px 12px;border-radius:20px;'
                        f'font-size:.72em;font-weight:900;box-shadow:0 0 12px {shd};letter-spacing:1px;">{status}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                    # RMP mini stats
                    if has_rmp:
                        rmp_ta = rmp_info.get("take_again", "N/A")
                        ta_str = f"{rmp_ta}%" if rmp_ta and str(rmp_ta) != "nan" and "%" not in str(rmp_ta) else str(rmp_ta)
                        st.markdown(
                            f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;">'
                            f'<div style="background:rgba(255,255,255,.05);border-radius:10px;padding:8px 14px;text-align:center;border:1px solid rgba(255,255,255,.07);">'
                            f'<div style="font-family:Orbitron,sans-serif;font-size:1.1em;font-weight:900;color:{r_clr}">{rmp_rating}</div>'
                            f'<div style="font-size:.6em;color:#445;margin-top:3px;">RATING</div></div>'
                            f'<div style="background:rgba(255,255,255,.05);border-radius:10px;padding:8px 14px;text-align:center;border:1px solid rgba(255,255,255,.07);">'
                            f'<div style="font-family:Orbitron,sans-serif;font-size:1.1em;font-weight:900;color:#FF851B">{rmp_diff}</div>'
                            f'<div style="font-size:.6em;color:#445;margin-top:3px;">DIFFICULTY</div></div>'
                            f'<div style="background:rgba(255,255,255,.05);border-radius:10px;padding:8px 14px;text-align:center;border:1px solid rgba(255,255,255,.07);">'
                            f'<div style="font-family:Orbitron,sans-serif;font-size:1.0em;font-weight:900;color:#2ECC40">{ta_str}</div>'
                            f'<div style="font-size:.6em;color:#445;margin-top:3px;">RETAKE</div></div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        if rmp_url and str(rmp_url) != "nan":
                            st.markdown(
                                f'<a href="{rmp_url}" target="_blank" style="font-family:Rajdhani,sans-serif;'
                                f'font-size:.82em;color:#5bb8ff;text-decoration:none;">'
                                f'(づ ◕‿◕ )づ View RMP Profile →</a>',
                                unsafe_allow_html=True
                            )

                        # Tags
                        tags_raw = rmp_info.get("tags", "")
                        if tags_raw and str(tags_raw) != "nan":
                            raw  = str(tags_raw).strip('"[]').strip("'")
                            tags = [t.strip().strip("\"'") for t in raw.split(",") if t.strip()][:5]
                            pills = "".join(
                                f'<span style="background:rgba(0,204,255,.1);color:#00CCFF;'
                                f'border:1px solid rgba(0,204,255,.3);padding:3px 10px;'
                                f'border-radius:20px;display:inline-block;margin:3px 3px 0 0;'
                                f'font-size:.72em;font-weight:600;">{t}</span>'
                                for t in tags
                            )
                            st.markdown(
                                f'<div style="margin-top:8px;">{pills}</div>',
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown(
                            '<div style="font-family:Rajdhani,sans-serif;font-size:.85em;'
                            'color:#445;margin-top:4px;">No RMP data available</div>',
                            unsafe_allow_html=True
                        )

                with col_chart:
                    if not course_hist.empty:
                        # Mini GPA trend line for this course
                        quarter_order_map = {"WINTER": 0, "SPRING": 1, "SUMMER": 2, "FALL": 3}
                        ch = course_hist.copy()
                        ch["term"] = ch["quarter"].astype(str) + " " + ch["year"].astype(str)
                        ch["_qord"] = ch["quarter"].map(quarter_order_map).fillna(9)
                        ch = ch.sort_values(["year", "_qord"])

                        trend_fig = go.Figure()
                        trend_fig.add_trace(go.Scatter(
                            x=ch["term"], y=ch[gpa_col],
                            mode="lines+markers",
                            line=dict(color=clr, width=2),
                            marker=dict(size=6, color=clr,
                                        line=dict(color="rgba(255,255,255,0.4)", width=1)),
                            fill="tozeroy",
                            fillcolor=f"rgba({int(clr[1:3],16) if clr.startswith('#') else 0},"
                                      f"{int(clr[3:5],16) if clr.startswith('#') else 116},"
                                      f"{int(clr[5:7],16) if clr.startswith('#') else 217},0.08)",
                            hovertemplate="<b>%{x}</b><br>Avg GPA: <b>%{y:.2f}</b><extra></extra>",
                        ))
                        trend_fig.add_hline(y=3.5, line_dash="dot",
                                            line_color="rgba(46,204,64,0.3)", line_width=1)
                        trend_fig.add_hline(y=3.0, line_dash="dot",
                                            line_color="rgba(255,65,54,0.3)", line_width=1)
                        trend_fig.update_layout(
                            template="plotly_dark", height=130,
                            margin=dict(l=0, r=0, t=4, b=0),
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,8,22,0.5)",
                            showlegend=False,
                            xaxis=dict(tickfont=dict(size=8, color="#556"),
                                       showgrid=False, tickangle=-30),
                            yaxis=dict(tickfont=dict(size=8, color="#445"),
                                       gridcolor="rgba(255,255,255,0.04)",
                                       range=[max(0, ch[gpa_col].min()-0.3), 4.2]),
                        )
                        st.plotly_chart(trend_fig, use_container_width=True,
                                        key=f"qtrend_{pi}",
                                        config={"displayModeBar": False})
                    else:
                        st.markdown(
                            '<div style="font-family:Rajdhani,sans-serif;font-size:.85em;'
                            'color:#334;text-align:center;padding:30px 0;">No grade history found</div>',
                            unsafe_allow_html=True
                        )


if __name__ == "__main__":
    main()
