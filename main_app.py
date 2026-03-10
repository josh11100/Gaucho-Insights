import streamlit as st
import pandas as pd
import os
import re
import io
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components

st.set_page_config(page_title="Gaucho Insights", layout="wide", page_icon="🎓", menu_items={})

# ─────────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;600;700&display=swap');

/* ── Base background ── */
.stApp { background: #000814 !important; color: #fff !important; }
html, body { background: #000814 !important; }

/* Hide the app filename shown in sidebar header and top bar */
[data-testid="stSidebarHeader"],
header[data-testid="stHeader"],
#MainMenu,
.stDeployButton,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
footer { display: none !important; }
.stApp > * { position: relative; z-index: 1; }
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="block-container"],
section[data-testid="stMain"] > div:first-child {
    background: transparent !important;
    position: relative !important;
    z-index: 1 !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 20px; justify-content: center;
    background: rgba(255,255,255,0.03);
    padding: 8px 12px; border-radius: 16px; margin-bottom: 24px;
    border: 1px solid rgba(255,215,0,0.15);
    flex-wrap: wrap;
}
.stTabs [data-baseweb="tab"] {
    height: 48px; background: transparent; border-radius: 10px;
    color: #666; font-size: clamp(12px, 2.5vw, 18px) !important; font-weight: 700;
    font-family: 'Orbitron', sans-serif; transition: all 0.25s;
    padding: 0 12px; white-space: nowrap;
}
.stTabs [data-baseweb="tab"]:hover { color: #FFD700; background: rgba(255,215,0,0.07); }
.stTabs [aria-selected="true"] {
    color: #FFD700 !important;
    border-bottom: 3px solid #FFD700 !important;
    text-shadow: 0 0 12px rgba(255,215,0,0.5);
}

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: #050a14 !important; border-right: 1px solid rgba(255,215,0,0.2) !important; }
[data-testid="stSidebar"] * { color: #ccc !important; font-family: 'Rajdhani', sans-serif !important; }
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #FFD700 !important; font-family: 'Orbitron', sans-serif !important; font-size: 0.9em !important; }

/* Sidebar scroll & spacing */
[data-testid="stSidebar"] > div:first-child {
    overflow-y: auto !important;
    height: 100vh !important;
    padding-bottom: 2rem !important;
}
[data-testid="stSidebar"] > div > div > div { padding-top: 1.5rem !important; }
[data-testid="stSidebar"] .stSelectbox { margin-bottom: 0.8rem !important; }
[data-testid="stSidebar"] .stTextInput { margin-bottom: 0.8rem !important; }
[data-testid="stSidebar"] .stButton { margin-top: 0.2rem !important; margin-bottom: 0.8rem !important; }
[data-testid="stSidebar"] label { margin-bottom: 4px !important; }
[data-testid="stSidebar"] hr { margin: 1rem 0 !important; }

/* ── Cards ── */
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

/* ── Buttons ── */
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

/* ── Inputs ── */
.stTextInput > div > div > input, .stSelectbox > div > div {
    background: rgba(0,20,50,0.8) !important;
    border: 1px solid rgba(0,116,217,0.3) !important;
    color: #ddd !important;
    border-radius: 10px !important;
    font-family: 'Rajdhani', sans-serif !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #000; }
::-webkit-scrollbar-thumb { background: rgba(255,215,0,0.3); border-radius: 3px; }

/* ════════════════════════════════════
   MOBILE / NARROW SCREEN FIXES
   ════════════════════════════════════ */

@media (max-width: 640px) {
    /* Stack search result info+chart columns on mobile */
    [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        flex-wrap: wrap !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 0 !important;
    }
    /* Shrink tab font on very small screens */
    .stTabs [data-baseweb="tab"] {
        font-size: 10px !important;
        padding: 0 6px !important;
        height: 38px !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px !important;
        padding: 4px 6px !important;
    }
}

/* Prevent column overflow at any screen size */
[data-testid="stColumn"] {
    min-width: 0 !important;
    overflow: hidden !important;
}
[data-testid="stColumn"] > div {
    min-width: 0 !important;
    overflow: hidden !important;
    word-break: break-word !important;
}
    overflow-x: hidden !important;
}
section[data-testid="stMain"] > div {
    overflow-x: hidden !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  JOIN KEY HELPERS
# ─────────────────────────────────────────────
def parse_name(name: str) -> tuple[str, str]:
    if not name or pd.isna(name):
        return ("UNKNOWN", "")
    s = str(name).upper().strip()
    if "," in s:
        parts = [p.strip() for p in s.split(",", 1)]
        return (parts[0], parts[1] if len(parts) > 1 else "")
    parts = s.split()
    return (parts[0], " ".join(parts[1:]) if len(parts) > 1 else "")


def name_similarity(first_a: str, first_b: str) -> float:
    if not first_a or not first_b:
        return 0.5
    toks_a = first_a.upper().split()
    toks_b = first_b.upper().split()
    if not toks_a or not toks_b:
        return 0.5

    # ── Initials-vs-full-name matching ──────────────────────────────────────
    # e.g. "Y D" (initials from Y-D) vs "YUEDONG" (full name in RMP)
    # Check if one side looks like initials (all single chars) and the other is a full name
    a_is_initials = all(len(t) == 1 for t in toks_a)
    b_is_initials = all(len(t) == 1 for t in toks_b)

    if a_is_initials and not b_is_initials:
        # toks_a = ['Y','D'], toks_b = ['YUEDONG']
        # Try: does the full name start with the first initial?
        full_name = "".join(toks_b)  # e.g. YUEDONG
        initials  = toks_a           # e.g. ['Y','D']
        # Check first initial matches first letter of full name
        if full_name and initials[0] == full_name[0]:
            # Check second initial (if present) appears somewhere in the name after position 0
            if len(initials) > 1:
                if initials[1] in full_name[1:]:
                    return 0.95  # strong match: Y-D → YUEDONG (Y start, D inside)
                else:
                    return 0.7   # first initial matches
            return 0.85  # single initial matches first letter
        return 0.1  # first initial doesn't match — very unlikely same person

    if b_is_initials and not a_is_initials:
        # Flip and recurse
        return name_similarity(first_b, first_a)

    # ── Standard token-by-token similarity (both full names or both initials) ──
    matches = 0
    for ta, tb in zip(toks_a, toks_b):
        if ta == tb:
            matches += 1
        elif len(ta) == 1 and tb.startswith(ta):
            matches += 0.9
        elif len(tb) == 1 and ta.startswith(tb):
            matches += 0.9
    total = max(len(toks_a), len(toks_b))
    return matches / total if total else 0.5


def make_join_key(name: str) -> str:
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

    rmp_lookup = {}

    if rmp_path:
        rmp = pd.read_csv(rmp_path)
        rmp.columns = [c.strip().lower() for c in rmp.columns]

        col_alias = {}
        for c in rmp.columns:
            col_alias[c.replace("rmp_", "")] = c

        def get_rmp(row, field):
            return row.get(col_alias.get(field, field))

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

        rmp_by_last: dict = {}
        for e in rmp_entries:
            rmp_by_last.setdefault(e["_last"], []).append(e)

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
                scored = sorted(candidates,
                                key=lambda e: name_similarity(g_first, e["_first"]),
                                reverse=True)
                if name_similarity(g_first, scored[0]["_first"]) < 0.4:
                    continue
                best = scored[0]

            rmp_lookup[jk] = {k: v for k, v in best.items() if not k.startswith("_")}

        rmp_rows = [{"join_key": jk, **v} for jk, v in rmp_lookup.items()]
        if rmp_rows:
            rmp_df = pd.DataFrame(rmp_rows).rename(columns={
                "rating": "rmp_rating", "difficulty": "rmp_difficulty",
                "take_again": "rmp_take_again", "num_ratings": "rmp_num_ratings",
                "tags": "rmp_tags", "url": "rmp_url",
                "dept": "rmp_dept", "full_name": "rmp_full_name",
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
#  SESSION STATE
# ─────────────────────────────────────────────
for key in ["sel_prof_key", "sel_prof_name", "sel_prof_course"]:
    if key not in st.session_state:
        st.session_state[key] = None
for key in ["dept_q", "course_q", "prof_q"]:
    if key not in st.session_state:
        st.session_state[key] = ""
if "parsed_schedule" not in st.session_state:
    st.session_state.parsed_schedule = []
if "gpa3d_active_courses" not in st.session_state:
    st.session_state.gpa3d_active_courses = set()
if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0
if "force_search_tab" not in st.session_state:
    st.session_state.force_search_tab = False


def clear_filters():
    st.session_state.dept_q = ""
    st.session_state.course_q = ""
    st.session_state.prof_q = ""
    st.session_state.sel_prof_key = None
    st.session_state.sel_prof_name = None


def dismiss_prof():
    st.session_state.sel_prof_key = None
    st.session_state.sel_prof_name = None
    st.session_state.active_tab = 1  # switch to Search Tool tab


def filter_changed():
    """Called when any sidebar filter changes — jump to Search Tool."""
    st.session_state.active_tab = 1
    st.session_state.force_search_tab = True
    dismiss_prof()


def gpa_badge(gpa):
    if gpa < 3.0:
        return "STRESSFUL", "#FF4136", "rgba(255,65,54,0.35)"
    elif gpa > 3.5:
        return "EASY", "#2ECC40", "rgba(46,204,64,0.35)"
    else:
        return "CHILL", "#0074D9", "rgba(0,116,217,0.35)"


# ─────────────────────────────────────────────
#  HERO
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
try{const el=window.frameElement;if(el){el.style.zIndex='10';el.style.position='relative';}}
catch(e){}
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
.scene{perspective:1400px;width:100%;min-height:480px;height:auto;display:flex;justify-content:center;align-items:center;padding:10px 0}
.card{width:97%;background:rgba(0,18,40,.85);border-radius:26px;
      border:1.5px solid rgba(255,215,0,.35);
      box-shadow:0 30px 70px rgba(0,0,0,.7),0 0 60px rgba(0,116,217,.08);
      transform-style:preserve-3d;transition:transform .1s ease;
      position:relative;overflow:hidden;padding:clamp(24px,5vw,50px) clamp(20px,5vw,48px);color:white}
canvas{position:absolute;top:0;left:0;width:100%;height:100%;z-index:0}
.content{position:relative;z-index:1;display:flex;flex-direction:column;justify-content:center}
h1{font-family:'Orbitron',sans-serif;font-size:clamp(1.2em,3vw,2.1em);font-weight:900;color:#FFD700;
   text-shadow:0 0 20px rgba(255,215,0,.4);margin-bottom:14px}
p{font-family:'Rajdhani',sans-serif;font-size:clamp(.95em,2vw,1.15em);line-height:1.75;color:#c8d8ef;margin-bottom:24px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px}
.box{background:rgba(255,255,255,.05);border-radius:16px;padding:16px 18px;backdrop-filter:blur(10px);transition:background .2s}
.box:hover{background:rgba(255,255,255,.09)}
.bt{font-family:'Orbitron',sans-serif;font-size:clamp(.7em,.9vw,.82em);font-weight:700;margin-bottom:8px}
.bb{font-family:'Rajdhani',sans-serif;font-size:clamp(.88em,1.5vw,.98em);color:#9ab;line-height:1.6}
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
        <div class="box" style="border-left:4px solid rgba(255,215,0,.4);padding-left:18px;background:rgba(255,215,0,.04)">
          <div class="bt" style="color:rgba(255,215,0,.7)">💻 BEST ON DESKTOP</div>
          <div class="bb" style="color:#778;">For the full experience, open on a <b style="color:#99a">computer or laptop</b>. Mobile layout may vary.</div>
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
""", height=700)


def render_info_card():
    components.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Rajdhani:wght@500;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}body{background:transparent;overflow:hidden}
.sc{perspective:900px;width:100%;height:auto;min-height:200px;display:flex;justify-content:center;align-items:center;padding:8px 0}
.cd{width:90%;background:linear-gradient(140deg,#001428 0%,#002255 60%,#001e4a 100%);
    border-radius:22px;border:1.5px solid rgba(255,215,0,.5);
    box-shadow:0 20px 50px rgba(0,0,0,.6),inset 0 0 40px rgba(0,116,217,.07);
    transform-style:preserve-3d;transition:transform .1s ease;
    display:flex;flex-direction:column;justify-content:space-between;
    padding:20px 22px;color:white;word-break:break-word;overflow:hidden}
.t{font-family:'Orbitron',sans-serif;font-size:clamp(.75em,.9vw,.95em);font-weight:700;
   color:#FFD700;margin-bottom:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.b{font-family:'Rajdhani',sans-serif;font-size:clamp(.88em,1.2vw,1.02em);line-height:1.8;color:#8ab}
.h{font-family:'Rajdhani',sans-serif;font-size:.78em;color:rgba(255,255,255,.2);
   background:rgba(255,255,255,.04);border-radius:8px;padding:5px 10px;
   text-align:center;margin-top:12px}
</style>
<div class="sc" id="sc"><div class="cd" id="cd">
  <div>
    <div class="t">( ˘▽˘)っ♨ DATA INFO</div>
    <div class="b">
      <b>Coverage:</b> Through Summer 2025<br>
      <b>Source:</b> UCSB Registrar + RMP<br>
      <b>Built by:</b> Joshua Chung
    </div>
  </div>
  <div class="h">Hover to tilt ↗</div>
</div></div>
<script>
const sc=document.getElementById('sc'),cd=document.getElementById('cd');
sc.addEventListener('mousemove',e=>{const r=sc.getBoundingClientRect();
  cd.style.transform=`rotateY(${(e.clientX-r.left-r.width/2)/10}deg) rotateX(${-(e.clientY-r.top-r.height/2)/8}deg)`;});
sc.addEventListener('mouseleave',()=>{cd.style.transform='';});
</script>
""", height=240)


def render_linkedin_card():
    components.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}body{background:transparent;overflow:hidden}
.sc{perspective:800px;width:100%;height:80px;display:flex;justify-content:center;align-items:center}
a{width:90%;height:58px;display:flex;align-items:center;justify-content:center;
  background:#0077b5;border-radius:14px;border:1.5px solid rgba(255,215,0,.4);
  font-family:'Rajdhani',sans-serif;font-weight:700;
  font-size:clamp(.85em,1.5vw,1.05em);color:white;white-space:nowrap;
  text-decoration:none;transform-style:preserve-3d;transition:transform .1s,background .2s;
  box-shadow:0 8px 24px rgba(0,0,0,.4);padding:0 16px;overflow:hidden;text-overflow:ellipsis}
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
def render_prof_card(info: dict, prof_name: str, prof_history_df: pd.DataFrame, gpa_col: str):
    rating      = info.get("rating")
    difficulty  = info.get("difficulty")
    take_again  = info.get("take_again")
    num_ratings = info.get("num_ratings")
    tags_raw    = info.get("tags", "")
    url         = info.get("url", "")
    dept        = info.get("dept", "")

    try:
        rv = float(rating)
        r_color = "#2ECC40" if rv >= 4.0 else ("#FFDC00" if rv >= 3.0 else "#FF4136")
    except Exception:
        r_color = "#888"

    ta_str  = str(take_again) if take_again and str(take_again) != "nan" else "N/A"
    if ta_str != "N/A" and "%" not in ta_str:
        ta_str += "%"
    num_str = f"{int(float(num_ratings))}" if num_ratings and str(num_ratings) != "nan" else "N/A"
    r_str   = str(rating)    if rating     and str(rating)     != "nan" else "N/A"
    d_str   = str(difficulty) if difficulty and str(difficulty) != "nan" else "N/A"

    tags_html = ""
    if tags_raw and str(tags_raw) != "nan":
        raw       = str(tags_raw).strip("\"'[]")
        tags      = [t.strip().strip("\"'") for t in raw.split(",") if t.strip()]
        tags_html = "".join(f'<span class="tag">{t}</span>' for t in tags[:8])

    dept_badge = f'<span class="dept">{dept}</span>' if dept and str(dept) != "nan" else ""
    rmp_btn    = (f'<a href="{url}" target="_blank" class="rmp-btn">(づ ◕‿◕ )づ View Full RMP Profile</a>'
                  if url and str(url) != "nan" else "")

    has_tags = bool(tags_html)
    card_h   = 420 + (70 if has_tags else 0)
    scene_h  = card_h + 40

    components.html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Rajdhani:wght@400;600;700&display=swap');
*{{margin:0;padding:0;box-sizing:border-box}}body{{background:transparent;overflow:hidden}}
.scene{{perspective:1100px;width:100%;height:{scene_h}px;display:flex;justify-content:center;align-items:center}}
.pcard{{width:98%;background:linear-gradient(140deg,#001428 0%,#001e4a 55%,#002255 100%);
        border:2px solid rgba(255,215,0,.55);border-radius:22px;padding:28px 32px 24px;
        box-shadow:0 0 60px rgba(255,215,0,.07),0 30px 60px rgba(0,0,0,.65),inset 0 0 40px rgba(0,116,217,.05);
        font-family:'Rajdhani',sans-serif;color:white;transform-style:preserve-3d;transition:transform .1s ease;
        position:relative;overflow:hidden}}
.pcard::before{{content:'';position:absolute;top:0;left:-60%;width:40%;height:100%;
  background:linear-gradient(105deg,transparent 40%,rgba(255,215,0,.06) 50%,transparent 60%);
  animation:shimmer 4s infinite;pointer-events:none}}
@keyframes shimmer{{0%{{left:-60%}}100%{{left:130%}}}}
.pname{{font-family:'Orbitron',sans-serif;font-size:1.25em;font-weight:900;color:#FFD700;
        margin-bottom:8px;text-shadow:0 0 14px rgba(255,215,0,.35)}}
.dept{{background:rgba(0,116,217,.22);color:#5bb8ff;border:1px solid rgba(0,116,217,.5);
       padding:3px 14px;border-radius:20px;font-size:.8em;display:inline-block;margin-bottom:20px}}
.stats{{display:flex;gap:12px;margin-bottom:14px}}
.stat{{flex:1;background:rgba(255,255,255,.05);border-radius:14px;padding:18px 10px;text-align:center;
       border:1px solid rgba(255,255,255,.07);transition:background .2s,border-color .2s}}
.stat:hover{{background:rgba(255,255,255,.09);border-color:rgba(255,215,0,.25)}}
.stat .v{{font-size:2em;font-weight:900;line-height:1;font-family:'Orbitron',sans-serif}}
.stat .l{{font-size:.65em;color:#556;margin-top:7px;text-transform:uppercase;letter-spacing:.8px}}
.num{{text-align:center;color:#445;font-size:.78em;margin:-4px 0 16px}}
.tag-lbl{{font-size:.68em;color:#445;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}}
.tag{{background:rgba(0,204,255,.1);color:#00CCFF;border:1px solid rgba(0,204,255,.3);
      padding:4px 12px;border-radius:20px;display:inline-block;margin:3px;font-size:.76em;font-weight:600}}
.rmp-btn{{display:inline-block;margin-top:18px;padding:11px 26px;
          background:linear-gradient(135deg,#0077b5,#00a0dc);color:white;text-decoration:none;
          border-radius:14px;font-weight:800;font-size:.9em;box-shadow:0 6px 22px rgba(0,119,181,.45);
          border:1.5px solid rgba(255,255,255,.15);font-family:'Rajdhani',sans-serif;
          transition:background .2s,transform .15s}}
.rmp-btn:hover{{background:linear-gradient(135deg,#0087cc,#00bbf5);transform:translateY(-2px)}}
</style>
<div class="scene" id="sc"><div class="pcard" id="cd">
  <div class="pname">{prof_name}</div>{dept_badge}
  <div class="stats">
    <div class="stat"><div class="v" style="color:{r_color}">{r_str}<span style="font-size:0.45em;color:#556;font-weight:400">/5</span></div><div class="l">Rating</div></div>
    <div class="stat"><div class="v" style="color:#FF851B">{d_str}<span style="font-size:0.45em;color:#556;font-weight:400">/5</span></div><div class="l">Difficulty</div></div>
    <div class="stat"><div class="v" style="color:#2ECC40;font-size:1.4em">{ta_str}</div><div class="l">Would Retake</div></div>
  </div>
  <div class="num">Based on {num_str} student ratings</div>
  {"<div class='tag-lbl'>Student Tags</div><div>" + tags_html + "</div>" if tags_html else ""}
  {rmp_btn}
</div></div>
<script>
const sc=document.getElementById('sc'),cd=document.getElementById('cd');
sc.addEventListener('mousemove',e=>{{
  const r=sc.getBoundingClientRect();
  cd.style.transform=`rotateY(${{(e.clientX-r.left-r.width/2)/36}}deg) rotateX(${{-(e.clientY-r.top-r.height/2)/24}}deg) translateZ(18px)`;
}});
sc.addEventListener('mouseleave',()=>{{cd.style.transform='rotateY(0) rotateX(0) translateZ(0)';}});
</script>
""", height=scene_h)

    if not prof_history_df.empty and gpa_col in prof_history_df.columns:
        st.markdown('<div style="font-family:Orbitron,sans-serif;font-size:.78em;color:#FFD700;'
                    'letter-spacing:2px;margin:24px 0 4px;">GPA HISTORY — INTERACTIVE 3D</div>',
                    unsafe_allow_html=True)
        st.markdown('<div style="font-family:Rajdhani,sans-serif;font-size:.82em;color:#556;margin:0 0 14px;">'
                    'Drag to rotate · Scroll to zoom · Hover dots for details'
                    ' &nbsp;|&nbsp; <b style="color:#aaa">X</b> = Term &nbsp;'
                    '<b style="color:#aaa">Y</b> = Course &nbsp;<b style="color:#aaa">Z</b> = Avg GPA</div>',
                    unsafe_allow_html=True)

        hist = prof_history_df.copy()
        hist["term"] = hist["quarter"].astype(str) + " " + hist["year"].astype(str)
        q_ord = {"WINTER":0,"SPRING":1,"SUMMER":2,"FALL":3}
        hist["_qord"] = hist["quarter"].map(q_ord).fillna(9)
        hist = hist.sort_values(["year","_qord"]).reset_index(drop=True)

        courses = sorted(hist["course"].unique())
        terms   = list(dict.fromkeys(hist["term"].tolist()))
        term_idx   = {t: i for i, t in enumerate(terms)}
        course_idx = {c: i for i, c in enumerate(courses)}
        palette = ["#FF4136","#0074D9","#FFD700","#2ECC40","#FF851B","#B10DC9",
                   "#00CCFF","#FF69B4","#AAAAAA","#01FF70","#F012BE","#7FDBFF"]

        fig = go.Figure()
        for ci, course in enumerate(courses):
            sub   = hist[hist["course"] == course].copy()
            color = palette[ci % len(palette)]
            xs = [term_idx[t] for t in sub["term"]]
            ys = [course_idx[c] for c in sub["course"]]
            zs = sub[gpa_col].tolist()

            fig.add_trace(go.Scatter3d(x=xs, y=ys, z=zs, mode="markers+lines", name=course,
                legendgroup=course, showlegend=False,
                line=dict(color=color, width=2, dash="dot"),
                marker=dict(size=6, color=color, opacity=0.95, symbol="circle",
                            line=dict(color="rgba(255,255,255,0.4)", width=1)),
                hovertemplate=(f"<b>{course}</b><br>Term: <b>%{{customdata}}</b><br>"
                               "Avg GPA: <b>%{z:.2f}</b><extra></extra>"),
                customdata=sub["term"].tolist()))

            dx, dy, dz = [], [], []
            for x, y, z in zip(xs, ys, zs):
                dx += [x,x,None]; dy += [y,y,None]; dz += [2.0,z,None]
            fig.add_trace(go.Scatter3d(x=dx, y=dy, z=dz, mode="lines",
                line=dict(color=color,width=1,dash="dot"), opacity=0.25,
                showlegend=False, hoverinfo="skip", legendgroup=course))
            fig.add_trace(go.Scatter3d(x=xs, y=ys, z=[z+0.13 for z in zs], mode="text",
                text=[f"{z:.2f}" for z in zs],
                textfont=dict(size=13,color="white",family="Orbitron"),
                showlegend=False, hoverinfo="skip", legendgroup=course))

        xr=[-0.5, len(terms)-0.5]; yr=[-0.5, len(courses)-0.5]
        for ref_z, ref_color, ref_name in [
            (3.5,"rgba(46,204,64,0.15)","── EASY ≥ 3.5"),
            (3.0,"rgba(255,65,54,0.15)","── STRESSFUL < 3.0")]:
            fig.add_trace(go.Surface(
                x=[[xr[0],xr[1]],[xr[0],xr[1]]], y=[[yr[0],yr[0]],[yr[1],yr[1]]],
                z=[[ref_z,ref_z],[ref_z,ref_z]], colorscale=[[0,ref_color],[1,ref_color]],
                showscale=False, opacity=0.55, name=ref_name, showlegend=True, hoverinfo="skip"))

        fig.update_layout(
            template="plotly_dark", height=540, margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            scene=dict(
                bgcolor="rgba(0,6,18,1)",
                xaxis=dict(tickvals=list(range(len(terms))), ticktext=terms,
                           tickfont=dict(size=11,color="#bbc"), gridcolor="rgba(255,255,255,0.03)",
                           showbackground=True, backgroundcolor="rgba(0,8,24,0.5)",
                           title=dict(text="Term",font=dict(size=13,color="#ccd"))),
                yaxis=dict(tickvals=list(range(len(courses))), ticktext=courses,
                           tickfont=dict(size=11,color="#ddd"), gridcolor="rgba(255,255,255,0.03)",
                           showbackground=True, backgroundcolor="rgba(0,8,24,0.5)",
                           title=dict(text="Course",font=dict(size=13,color="#ccd"))),
                zaxis=dict(range=[2.0,4.3], tickfont=dict(size=11,color="#bbc"),
                           gridcolor="rgba(255,255,255,0.03)", showbackground=True,
                           backgroundcolor="rgba(0,10,28,0.7)",
                           title=dict(text="Avg GPA",font=dict(size=13,color="#ccd"))),
                camera=dict(eye=dict(x=1.8,y=-1.8,z=1.0), up=dict(x=0,y=0,z=1)),
                aspectmode="manual",
                aspectratio=dict(x=max(1.4,len(terms)*0.28), y=max(0.7,len(courses)*0.22), z=0.9)),
            legend=dict(x=0.01,y=0.99, font=dict(family="Rajdhani",size=11,color="#aaa"),
                        bgcolor="rgba(0,0,0,0)", itemsizing="constant",
                        bordercolor="rgba(255,215,0,0.15)", borderwidth=1, visible=False))

        # ── Course filter state ──────────────────────────────────────────────
        prof_key = st.session_state.sel_prof_key
        state_key = f"gpa3d_active_{prof_key}"
        if state_key not in st.session_state or st.session_state[state_key] is None:
            st.session_state[state_key] = set(courses)

        active_courses = st.session_state[state_key]

        # ── Re-build fig with only active courses visible ────────────────────
        fig2 = go.Figure()
        filtered_courses = [c for c in courses if c in active_courses]

        if not filtered_courses:
            filtered_courses = courses  # fallback: show all if all deselected

        for ci, course in enumerate(courses):
            if course not in active_courses:
                continue
            sub   = hist[hist["course"] == course].copy()
            color = palette[ci % len(palette)]
            xs = [term_idx[t] for t in sub["term"]]
            ys = [course_idx[c] for c in sub["course"]]
            zs = sub[gpa_col].tolist()

            fig2.add_trace(go.Scatter3d(x=xs, y=ys, z=zs, mode="markers+lines", name=course,
                legendgroup=course, showlegend=False,
                line=dict(color=color, width=2, dash="dot"),
                marker=dict(size=6, color=color, opacity=0.95, symbol="circle",
                            line=dict(color="rgba(255,255,255,0.4)", width=1)),
                hovertemplate=(f"<b>{course}</b><br>Term: <b>%{{customdata}}</b><br>"
                               "Avg GPA: <b>%{z:.2f}</b><extra></extra>"),
                customdata=sub["term"].tolist()))

            dx, dy, dz = [], [], []
            for x, y, z in zip(xs, ys, zs):
                dx += [x,x,None]; dy += [y,y,None]; dz += [2.0,z,None]
            fig2.add_trace(go.Scatter3d(x=dx, y=dy, z=dz, mode="lines",
                line=dict(color=color,width=1,dash="dot"), opacity=0.25,
                showlegend=False, hoverinfo="skip", legendgroup=course))
            fig2.add_trace(go.Scatter3d(x=xs, y=ys, z=[z+0.13 for z in zs], mode="text",
                text=[f"{z:.2f}" for z in zs],
                textfont=dict(size=13,color="white",family="Orbitron"),
                showlegend=False, hoverinfo="skip", legendgroup=course))

        xr=[-0.5, len(terms)-0.5]; yr=[-0.5, len(courses)-0.5]
        for ref_z, ref_color, ref_name in [
            (3.5,"rgba(46,204,64,0.15)","── EASY ≥ 3.5"),
            (3.0,"rgba(255,65,54,0.15)","── STRESSFUL < 3.0")]:
            fig2.add_trace(go.Surface(
                x=[[xr[0],xr[1]],[xr[0],xr[1]]], y=[[yr[0],yr[0]],[yr[1],yr[1]]],
                z=[[ref_z,ref_z],[ref_z,ref_z]], colorscale=[[0,ref_color],[1,ref_color]],
                showscale=False, opacity=0.55, name=ref_name, showlegend=True, hoverinfo="skip"))

        fig2.update_layout(
            template="plotly_dark", height=540, margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            scene=dict(
                bgcolor="rgba(0,6,18,1)",
                xaxis=dict(tickvals=list(range(len(terms))), ticktext=terms,
                           tickfont=dict(size=11,color="#bbc"), gridcolor="rgba(255,255,255,0.03)",
                           showbackground=True, backgroundcolor="rgba(0,8,24,0.5)",
                           title=dict(text="Term",font=dict(size=13,color="#ccd"))),
                yaxis=dict(tickvals=list(range(len(courses))), ticktext=courses,
                           tickfont=dict(size=11,color="#ddd"), gridcolor="rgba(255,255,255,0.03)",
                           showbackground=True, backgroundcolor="rgba(0,8,24,0.5)",
                           title=dict(text="Course",font=dict(size=13,color="#ccd"))),
                zaxis=dict(range=[2.0,4.3], tickfont=dict(size=11,color="#bbc"),
                           gridcolor="rgba(255,255,255,0.03)", showbackground=True,
                           backgroundcolor="rgba(0,10,28,0.7)",
                           title=dict(text="Avg GPA",font=dict(size=13,color="#ccd"))),
                camera=dict(eye=dict(x=1.8,y=-1.8,z=1.0), up=dict(x=0,y=0,z=1)),
                aspectmode="manual",
                aspectratio=dict(x=max(1.4,len(terms)*0.28), y=max(0.7,len(courses)*0.22), z=0.9)),
            legend=dict(x=0.01,y=0.99, font=dict(family="Rajdhani",size=11,color="#aaa"),
                        bgcolor="rgba(0,0,0,0)", itemsizing="constant",
                        bordercolor="rgba(255,215,0,0.15)", borderwidth=1, visible=False))

        st.plotly_chart(fig2, use_container_width=True,
                        key=f"prof_hist_{prof_key}_{len(active_courses)}",
                        config={"displayModeBar":True,"displaylogo":False,
                                "modeBarButtonsToRemove":["toImage"]})

        # ── Clickable course filter legend ───────────────────────────────────
        st.markdown(f'<div style="font-family:Orbitron,sans-serif;font-size:.68em;color:#FFD700;'
                    f'letter-spacing:2px;margin:10px 0 8px;">COURSES '
                    f'<span style="font-family:Rajdhani,sans-serif;font-size:.85em;color:#556;'
                    f'letter-spacing:0;font-weight:400;">'
                    f'— click to show/hide</span></div>', unsafe_allow_html=True)

        num_cols = min(len(courses), 6)
        btn_cols = st.columns(num_cols)
        for ci, course in enumerate(courses):
            color = palette[ci % len(palette)]
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            is_active = course in active_courses
            col = btn_cols[ci % num_cols]
            with col:
                dot_color = color if is_active else f"rgba({r},{g},{b},0.35)"
                dot_shadow = f"0 0 8px {color}" if is_active else "none"
                st.markdown(
                    f'<div style="text-align:center;font-size:18px;color:{dot_color};'
                    f'line-height:1;margin-bottom:2px;'
                    f'text-shadow:{dot_shadow};">●</div>',
                    unsafe_allow_html=True
                )
                clicked = st.button(
                    course,
                    key=f"course_btn_{prof_key}_{ci}",
                    use_container_width=True,
                    help=f"{'Hide' if is_active else 'Show'} {course} on the 3D chart"
                )
                if clicked:
                    new_active = set(st.session_state[state_key])
                    if course in new_active:
                        if len(new_active) > 1:
                            new_active.discard(course)
                    else:
                        new_active.add(course)
                    st.session_state[state_key] = new_active
                    st.rerun()

        # Show/hide all controls
        searched_course = st.session_state.get("sel_prof_course", "")
        # Pin the searched course — fall back to first course if not found in this prof's history
        pin_course = searched_course if searched_course in courses else courses[0]
        ctrl_col1, ctrl_col2, _ = st.columns([1, 1, 4])
        with ctrl_col1:
            if st.button("◉ Show All", key=f"show_all_{prof_key}", use_container_width=True):
                st.session_state[state_key] = set(courses)
                st.rerun()
        with ctrl_col2:
            if st.button("○ Hide All", key=f"hide_all_{prof_key}", use_container_width=True):
                st.session_state[state_key] = {pin_course}
                st.rerun()

        summary = (hist.groupby("course")[gpa_col].agg(["mean","count"]).reset_index()
                   .rename(columns={"mean":"Avg GPA","count":"Sections"})
                   .sort_values("Avg GPA", ascending=False))
        summary["Avg GPA"] = summary["Avg GPA"].map("{:.2f}".format)
        st.markdown('<div style="font-family:Orbitron,sans-serif;font-size:.72em;color:#FFD700;'
                    'letter-spacing:2px;margin:14px 0 8px;">( ˘▽˘)っ♨ COURSE SUMMARY</div>',
                    unsafe_allow_html=True)
        st.dataframe(summary, hide_index=True, use_container_width=True)


# ─────────────────────────────────────────────
#  TEXT-BASED SCHEDULE PARSER  (regex)
# ─────────────────────────────────────────────
def clean_instructor_name(raw: str) -> str:
    """
    Robustly clean an instructor name extracted from OCR or copy-paste.
    Handles: junk characters, bracket noise, extra spaces, missing initials,
    OCR artifacts like }] or |, numbers leaking in, hyphenated names like Y-D, etc.
    Returns cleaned LASTNAME F M style string, or "" if invalid.

    GOLD format examples:
        WANG Y-D        → WANG Y D
        GARFIELD P M    → GARFIELD P M
        MOEHLIS J M     → MOEHLIS J M
        NAKAYAMA M T    → NAKAYAMA M T
        GARFIELD P M ]  → GARFIELD P M
        }SMITH A        → SMITH A
    """
    if not raw:
        return ""

    s = raw.upper().strip()

    # Replace hyphens BETWEEN single letters with a space (e.g. Y-D → Y D)
    # This handles hyphenated initials like "Y-D" or "M-T"
    s = re.sub(r'\b([A-Z])-([A-Z])\b', r'\1 \2', s)

    # Remove anything that isn't a letter or space (strips }, ], |, digits, punctuation)
    s = re.sub(r"[^A-Z\s]", " ", s)

    # Collapse multiple spaces
    s = re.sub(r"\s+", " ", s).strip()

    # Split into tokens, drop any that have no letters
    tokens = [t for t in s.split() if t.isalpha()]

    if not tokens:
        return ""

    # GOLD name format: first token = last name (can be long), rest = initials (1 char each)
    # Anything after the last name that is 1 character is an initial
    last = tokens[0]
    initials = []
    for t in tokens[1:]:
        if len(t) == 1:
            initials.append(t)
        # Longer token after last name = probably noise or second last-name word — stop
        else:
            break
        if len(initials) >= 2:
            break

    parts = [last] + initials
    return " ".join(parts)


def parse_gold_schedule(text: str) -> list[dict]:
    """
    Parse UCSB GOLD schedule text (from OCR or copy-paste).
    Handles the exact 'My Class Schedule' table layout.
    """
    results = []
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]

    # Course header: "DEPT NUM - TITLE"  e.g. "MATH 3A - CALC WITH APPLI 1"
    course_pat  = re.compile(r'^([A-Z][A-Z\s&]+?)\s+(\d+[A-Z]*)\s*[-–]\s*(.+)$')
    # Section line starts with a 5-digit enrollment code
    section_pat = re.compile(r'^\d{5}\b')
    # Days pattern — used to find where instructor name ends
    day_pat     = re.compile(r'\b([MTWRF]{1,5}|T\.B\.A\.?|TBA)\b')

    current_course = current_dept = current_num = None

    for line in lines:
        m = course_pat.match(line)
        if m:
            current_dept   = m.group(1).strip()
            current_num    = m.group(2).strip()
            current_course = f"{current_dept} {current_num}"
            continue

        if section_pat.match(line) and current_course:
            units_idx = line.find("Units")
            instructor_raw = ""
            if units_idx != -1:
                after = line[units_idx + 5:].strip()
                dm = day_pat.search(after)
                if dm:
                    instructor_raw = after[:dm.start()].strip().rstrip(",").strip()
                else:
                    # No day found — take everything up to first digit (time) or end
                    m2 = re.search(r'\d', after)
                    instructor_raw = after[:m2.start()].strip() if m2 else after.strip()

            instructor = clean_instructor_name(instructor_raw)
            if instructor and instructor not in ("T B A", "TBA", ""):
                results.append({"course": current_course, "dept": current_dept,
                                 "num": current_num, "instructor": instructor})

        # Also handle lines that are just an instructor name (multi-instructor OCR lines)
        # e.g. a line like "FENG X" or "NAKAYAMA M T" appearing after a section line
        elif current_course and not section_pat.match(line):
            # If the line looks like a name (all caps, no digits, short), try to use it
            # but only if we haven't already captured an instructor for this course
            pass

    # Deduplicate — keep first occurrence of each (course, instructor) pair
    seen, unique = set(), []
    for r in results:
        key = (r["course"], r["instructor"])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


# ─────────────────────────────────────────────
#  OCR SCHEDULE PARSER  (no API — uses tesseract)
# ─────────────────────────────────────────────
def parse_schedule_from_image(image_bytes: bytes) -> list[dict]:
    """
    Extract courses + instructors from a UCSB GOLD screenshot.

    Uses pytesseract (free, local OCR) — zero API calls, zero cost.

    Setup:
      pip install pytesseract Pillow
      Tesseract binary:
        Mac:                  brew install tesseract
        Linux/Streamlit Cloud: add 'tesseract-ocr' to packages.txt
        Windows:              https://github.com/UB-Mannheim/tesseract/wiki
    """
    try:
        from PIL import Image
        import pytesseract
    except ImportError:
        st.error("Missing packages. Add 'pytesseract' and 'Pillow' to requirements.txt, "
                 "and 'tesseract-ocr' to packages.txt (Streamlit Cloud).")
        return []

    try:
        image    = Image.open(io.BytesIO(image_bytes))
        # Upscale for better OCR accuracy on small/retina screenshots
        w, h     = image.size
        image    = image.resize((w * 2, h * 2), Image.LANCZOS)
        raw_text = pytesseract.image_to_string(image, config="--psm 6")
        return parse_gold_schedule(raw_text)
    except Exception as ex:
        st.error(f"OCR error: {ex}")
        return []


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    full_df, gpa_col, rmp_lookup = load_data()
    render_hero()

    # ── Mobile warning banner ─────────────────────────────────────────────
    components.html("""
<script>
(function() {
    if (window.parent.innerWidth < 768) {
        const banner = window.parent.document.createElement('div');
        banner.id = 'mobile-warn';
        banner.innerHTML = `
            <span style="font-size:1.3em;">💻</span>
            <span style="flex:1">
                <strong style="color:#FFD700;font-family:'Orbitron',sans-serif;font-size:.8em;letter-spacing:1px;">
                BEST ON DESKTOP
                </strong><br>
                <span style="font-size:.85em;color:#aac;">
                Gaucho Insights is optimized for laptop/desktop. Some features may look off on mobile.
                </span>
            </span>
            <span id="close-warn" style="cursor:pointer;font-size:1.2em;color:#556;padding-left:8px;">✕</span>
        `;
        banner.style.cssText = `
            position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
            background: rgba(0,10,30,0.97);
            border-bottom: 1px solid rgba(255,215,0,0.3);
            padding: 12px 18px;
            display: flex; align-items: center; gap: 12px;
            font-family: 'Rajdhani', sans-serif; color: #cde;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        `;
        window.parent.document.body.appendChild(banner);
        window.parent.document.getElementById('close-warn').onclick = () => {
            banner.style.display = 'none';
        };
    }
})();
</script>
""", height=0)
    components.html("""
<script>
(function hideAppName() {
    function tryHide() {
        try {
            const parent = window.parent.document;
            // Only hide stSidebarHeader (the filename bar at the very top)
            parent.querySelectorAll('[data-testid="stSidebarHeader"]')
                  .forEach(el => el.style.display = 'none');
            // Hide the top header bar (share/github icons row)
            parent.querySelectorAll('header[data-testid="stHeader"]')
                  .forEach(el => el.style.display = 'none');
        } catch(e) {}
    }
    tryHide();
    setTimeout(tryHide, 300);
    setTimeout(tryHide, 1000);
})();
</script>
""", height=0)

    # ── 3D Animated Space Background ─────────────────────────────────────────
    # Strategy: render Three.js inside the iframe, then use window.parent JS
    # to reposition the iframe itself as a fixed full-screen background layer.
    components.html("""
<!DOCTYPE html>
<html>
<head>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  html, body { width:100%; height:100%; background:#000814; overflow:hidden; }
  canvas { display:block; width:100% !important; height:100% !important; }
</style>
</head>
<body>
<canvas id="c"></canvas>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
// ── Reposition this iframe as a fixed full-screen background ──
(function positionIframe() {
    const el = window.frameElement;
    if (!el) return;
    el.style.position = 'fixed';
    el.style.top = '0';
    el.style.left = '0';
    el.style.width = '100vw';
    el.style.height = '100vh';
    el.style.zIndex = '-10';
    el.style.pointerEvents = 'none';
    el.style.border = 'none';
    el.style.background = 'transparent';
    // Also ensure all sibling iframes (hero, content) sit above
    try {
        const allFrames = window.parent.document.querySelectorAll('iframe');
        allFrames.forEach(f => {
            if (f !== el && (!f.style.zIndex || parseInt(f.style.zIndex) < 1)) {
                f.style.zIndex = '1';
            }
        });
    } catch(e) {}
})();

// ── Three.js scene ──
const canvas   = document.getElementById('c');
const W = () => window.innerWidth, H = () => window.innerHeight;

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(W(), H());
renderer.setClearColor(0x000814, 1);

const scene  = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(70, W()/H(), 0.1, 3000);
camera.position.set(0, 0, 60);

// ── 1. Star field — 3 depth layers ──
function makeStars(n, spread, size, color, opacity) {
    const geo = new THREE.BufferGeometry();
    const pos = new Float32Array(n * 3);
    for (let i = 0; i < n * 3; i++) pos[i] = (Math.random() - .5) * spread;
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    const mat = new THREE.PointsMaterial({ color, size, sizeAttenuation:true, transparent:true, opacity });
    return new THREE.Points(geo, mat);
}
const s1 = makeStars(4000, 2000, 0.18, 0xffffff, 0.8);
const s2 = makeStars(1500, 1200, 0.22, 0xc8dcff, 0.7);
const s3 = makeStars(500,  600,  0.28, 0xffe8a0, 0.9);
scene.add(s1, s2, s3);

// ── 2. Wireframe geometry accents ──
function wire(GeoClass, args, color, x, y, z, op) {
    const m = new THREE.Mesh(
        new GeoClass(...args),
        new THREE.MeshBasicMaterial({ color, wireframe:true, transparent:true, opacity:op })
    );
    m.position.set(x,y,z);
    return m;
}
const geo1 = wire(THREE.IcosahedronGeometry, [8, 0], 0xffd700,  25,-10,-30, 0.10);
const geo2 = wire(THREE.OctahedronGeometry,  [6, 0], 0x0088ff, -22, 12,-25, 0.12);
const geo3 = wire(THREE.TetrahedronGeometry, [5, 0], 0xff4488,  10, 18,-20, 0.09);
const geo4 = wire(THREE.IcosahedronGeometry, [4, 1], 0x00ccff, -30,-18,-35, 0.07);
scene.add(geo1, geo2, geo3, geo4);



// ── 5. Mouse parallax ──
let mx=0, my=0;
try {
    window.parent.document.addEventListener('mousemove', e => {
        mx = (e.clientX/window.parent.innerWidth  - .5) * 2;
        my = (e.clientY/window.parent.innerHeight - .5) * 2;
    });
} catch(e) {}

window.addEventListener('resize', () => {
    camera.aspect = W()/H();
    camera.updateProjectionMatrix();
    renderer.setSize(W(), H());
});

// ── Animate ──
let f = 0;
(function tick() {
    requestAnimationFrame(tick);
    f++;
    const t = f * 0.0008;

    s1.rotation.y = t * 0.05;  s1.rotation.x = t * 0.018;
    s2.rotation.y = -t * 0.03; s2.rotation.x = t * 0.012;
    s3.rotation.y = t * 0.08;  s3.rotation.z = t * 0.02;

    geo1.rotation.y += 0.004; geo1.rotation.x += 0.002;
    geo2.rotation.y -= 0.005; geo2.rotation.z += 0.003;
    geo3.rotation.x += 0.006; geo3.rotation.z -= 0.004;
    geo4.rotation.y += 0.003; geo4.rotation.x -= 0.005;


    camera.position.x += (mx * 4 - camera.position.x) * 0.025;
    camera.position.y += (-my * 3 - camera.position.y) * 0.025;
    camera.lookAt(0, 0, 0);



    renderer.render(scene, camera);
})();
</script>
</body>
</html>
""", height=1, scrolling=False)

    tab_home, tab_search, tab_quarter = st.tabs(["HOME", "SEARCH TOOL", "MY QUARTER"])

    # Auto-switch to Search Tool tab whenever a filter is changed
    if st.session_state.get("force_search_tab") or st.session_state.active_tab == 1:
        components.html("""
<script>
(function() {
    function clickTab() {
        const tabs = window.parent.document.querySelectorAll('[data-baseweb="tab"]');
        if (tabs.length >= 2) {
            tabs[1].click();
        }
    }
    setTimeout(clickTab, 50);
    setTimeout(clickTab, 200);
    setTimeout(clickTab, 500);
})();
</script>
""", height=0)
        st.session_state.active_tab = 0
        st.session_state.force_search_tab = False

    # ── HOME ────────────────────────────────────────────────────────────────
    with tab_home:
        col_main, col_side = st.columns([5, 2], gap="large")
        with col_main:
            render_welcome_card()
        with col_side:
            st.markdown("<br>", unsafe_allow_html=True)
            render_info_card()
            render_linkedin_card()
            st.markdown("""
<div style="background:rgba(0,18,40,.7);border:1px solid rgba(255,215,0,.2);
            border-radius:18px;padding:16px;margin-top:16px;
            font-family:'Rajdhani',sans-serif;overflow:hidden;word-break:break-word;">
  <div style="font-family:'Orbitron',sans-serif;font-size:.72em;color:#FFD700;
              margin-bottom:12px;letter-spacing:1px;white-space:nowrap;
              overflow:hidden;text-overflow:ellipsis;">GRADING LEGEND</div>
  <div style="margin-bottom:8px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
    <span style="background:#2ECC40;color:#000;padding:3px 8px;border-radius:20px;
                 font-weight:700;font-size:.78em;white-space:nowrap;flex-shrink:0;">EASY</span>
    <span style="color:#8ab;font-size:.82em;">Avg GPA &gt; 3.5</span></div>
  <div style="margin-bottom:8px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
    <span style="background:#0074D9;color:#fff;padding:3px 8px;border-radius:20px;
                 font-weight:700;font-size:.78em;white-space:nowrap;flex-shrink:0;">CHILL</span>
    <span style="color:#8ab;font-size:.82em;">Avg GPA 3.1 – 3.5</span></div>
  <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
    <span style="background:#FF4136;color:#fff;padding:3px 8px;border-radius:20px;
                 font-weight:700;font-size:.78em;white-space:nowrap;flex-shrink:0;">STRESSFUL</span>
    <span style="color:#8ab;font-size:.82em;">Avg GPA &lt; 3.0</span></div>
</div>""", unsafe_allow_html=True)

    # ── SEARCH TOOL ─────────────────────────────────────────────────────────
    with tab_search:
        with st.sidebar:
            st.markdown("""
<div style="font-family:'Orbitron',sans-serif;color:#FFD700;font-size:.82em;letter-spacing:2px;
            padding:10px 0 6px;border-bottom:1px solid rgba(255,215,0,.2);margin-bottom:16px;">
  FILTERS</div>""", unsafe_allow_html=True)
            all_depts     = [""] + sorted(full_df["dept"].unique().tolist())
            selected_dept = st.selectbox("Department", options=all_depts, index=0,
                                         key="dept_q", on_change=filter_changed,
                                         format_func=lambda x: "All Departments" if x == "" else x)
            course_q = st.text_input("Course Number (e.g. 120A, 5A, 10)",
                                     key="course_q", on_change=filter_changed).strip().upper()
            prof_q   = st.text_input("Professor Name",
                                     key="prof_q", on_change=filter_changed).strip().upper()
            st.button("(シ_ _)シ  Clear Filters", on_click=clear_filters, use_container_width=True)
            st.markdown("---")
            st.markdown('<div style="font-family:Rajdhani,sans-serif;font-size:.88em;color:#556;line-height:1.7;">'
                        '<b style="color:#FFD700;">RMP</b> badge = click professor name to view '
                        'RateMyProfessors data + GPA history.</div>', unsafe_allow_html=True)
            st.markdown("""
<div style="margin-top:16px;background:rgba(255,215,0,0.05);border:1px solid rgba(255,215,0,0.15);
            border-radius:12px;padding:12px 14px;font-family:'Rajdhani',sans-serif;">
  <div style="font-size:.78em;color:#FFD700;font-weight:700;letter-spacing:1px;margin-bottom:4px;">
    💻 BEST ON DESKTOP
  </div>
  <div style="font-size:.82em;color:#445;line-height:1.6;">
    For the best experience, use a <b style="color:#556;">computer or laptop</b>.
    Mobile layout may vary.
  </div>
</div>""", unsafe_allow_html=True)

        if st.session_state.sel_prof_key:
            lk        = st.session_state.sel_prof_key
            info      = rmp_lookup.get(lk, {})
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

        # Sort: most recent first — year desc, then quarter desc (FALL > SUMMER > SPRING > WINTER)
        q_order = {"FALL": 3, "SUMMER": 2, "SPRING": 1, "WINTER": 0}
        df = df.copy()
        df["_qord"] = df["quarter"].str.upper().map(q_order).fillna(0)
        df = df.sort_values(["year", "_qord"], ascending=[False, False]).drop(columns=["_qord"])
        shown = df.head(25)

        st.markdown(f'<div style="font-family:Orbitron,sans-serif;font-size:.75em;'
                    f'color:rgba(255,215,0,.45);letter-spacing:2px;margin-bottom:18px;">'
                    f'SHOWING {len(shown)} OF {len(df)} RESULTS</div>', unsafe_allow_html=True)

        for idx, row in shown.iterrows():
            gpa_val          = row[gpa_col]
            status, clr, shd = gpa_badge(gpa_val)
            prof_name        = row["instructor"]
            jk               = row.get("join_key","")
            has_rmp          = jk in rmp_lookup
            txt_col          = "#000" if status == "EASY" else "#fff"
            rmp_pill         = ('<span style="font-size:.7em;color:#FFD700;background:rgba(255,215,0,.08);'
                                'border:1px solid rgba(255,215,0,.22);padding:2px 10px;border-radius:12px;'
                                'margin-left:8px;">RMP</span>' if has_rmp else "")

            with st.container(border=True):
                col_info, col_chart = st.columns([3, 2])
                with col_info:
                    st.markdown(
                        f'<div style="font-family:Orbitron,sans-serif;font-size:clamp(.85em,2vw,1.05em);'
                        f'font-weight:700;color:#e8f4ff;margin-bottom:4px;word-break:break-word;">'
                        f'{row["course"]}'
                        f'<span style="color:#445;font-size:.78em;margin-left:8px;">'
                        f'{row["quarter"]} {row["year"]}</span></div>', unsafe_allow_html=True)

                    if has_rmp:
                        pb_col, _ = st.columns([2, 3])
                        with pb_col:
                            if st.button(f"{prof_name}", key=f"pb_{idx}",
                                         help="Click to view RMP profile + GPA history"):
                                st.session_state.sel_prof_key    = jk
                                st.session_state.sel_prof_name   = prof_name
                                st.session_state.sel_prof_course = row["course"]
                                st.rerun()
                    else:
                        st.markdown(f'<div style="font-family:Rajdhani,sans-serif;font-size:.95em;'
                                    f'color:#667;margin:4px 0 6px;">{prof_name}</div>',
                                    unsafe_allow_html=True)

                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:6px;margin-top:6px;flex-wrap:wrap;">'
                        f'<span style="font-family:Orbitron,sans-serif;font-size:clamp(.75em,2vw,.88em);'
                        f'font-weight:700;color:#cde;">GPA {gpa_val:.2f}</span>'
                        f'<span style="background:{clr};color:{txt_col};padding:3px 10px;border-radius:20px;'
                        f'font-size:.74em;font-weight:900;box-shadow:0 0 14px {shd};letter-spacing:1px;white-space:nowrap;">'
                        f'{status}</span>{rmp_pill}</div>', unsafe_allow_html=True)

                with col_chart:
                    grades = pd.DataFrame({
                        "Grade": ["A","B","C","D","F"],
                        "Count": [row.get("a",0),row.get("b",0),row.get("c",0),
                                  row.get("d",0),row.get("f",0)],
                    })
                    fig = px.bar(grades, x="Grade", y="Count", color="Grade",
                                 color_discrete_map={"A":"#2ECC40","B":"#0074D9",
                                                     "C":"#FFDC00","D":"#FF851B","F":"#FF4136"},
                                 template="plotly_dark", height=120)
                    fig.update_layout(margin=dict(l=0,r=0,t=4,b=0), showlegend=False,
                                      xaxis_title=None, yaxis_title=None,
                                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                      xaxis=dict(tickfont=dict(size=11,color="#aaa")),
                                      yaxis=dict(tickfont=dict(size=10,color="#555")))
                    st.plotly_chart(fig, use_container_width=True, key=f"fig_{idx}",
                                    config={"displayModeBar": False})

    # ── MY QUARTER ──────────────────────────────────────────────────────────
    with tab_quarter:

        components.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Rajdhani:wght@500;600&display=swap');
*{margin:0;padding:0;box-sizing:border-box}body{background:transparent;overflow:hidden}
.sc{perspective:900px;width:100%;display:flex;justify-content:center;align-items:center;padding:8px 0}
.cd{width:96%;background:linear-gradient(135deg,#001428 0%,#001e4a 60%,#002255 100%);
    border-radius:18px;border:1.5px solid rgba(255,215,0,.4);
    box-shadow:0 16px 40px rgba(0,0,0,.5),inset 0 0 30px rgba(0,116,217,.06);
    transform-style:preserve-3d;transition:transform .1s ease;
    padding:18px 20px;color:white;display:flex;align-items:flex-start;gap:16px;
    overflow:hidden;word-break:break-word}
.icon{font-size:clamp(1.4em,4vw,2.4em);flex-shrink:0;padding-top:2px}
.title{font-family:'Orbitron',sans-serif;font-size:clamp(.7em,2vw,.95em);font-weight:900;
       color:#FFD700;margin-bottom:6px;text-shadow:0 0 10px rgba(255,215,0,.3);
       line-height:1.3}
.desc{font-family:'Rajdhani',sans-serif;font-size:clamp(.82em,2vw,.95em);color:#8ab;line-height:1.55}
</style>
<div class="sc" id="sc"><div class="cd" id="cd">
  <div class="icon">( ˘▽˘)っ♨</div>
  <div style="min-width:0;flex:1">
    <div class="title">MY QUARTER — INSTANT SCHEDULE INSIGHTS</div>
    <div class="desc">Upload a screenshot of your UCSB GOLD schedule.
    Local OCR reads it automatically — no API key, no cost.</div>
  </div>
</div></div>
<script>
const sc=document.getElementById('sc'),cd=document.getElementById('cd');
sc.addEventListener('mousemove',e=>{const r=sc.getBoundingClientRect();
  cd.style.transform=`rotateY(${(e.clientX-r.left-r.width/2)/30}deg) rotateX(${-(e.clientY-r.top-r.height/2)/20}deg)`;});
sc.addEventListener('mouseleave',()=>{cd.style.transform='';});
</script>
""", height=160)

        st.markdown("""
<div style="background:rgba(0,116,217,0.07);border:1px solid rgba(0,116,217,0.25);
            border-radius:14px;padding:16px 20px;margin-bottom:18px;
            font-family:'Rajdhani',sans-serif;font-size:.92em;color:#8ab;line-height:1.9;">
  <span style="font-family:'Orbitron',sans-serif;font-size:.75em;color:#5bb8ff;letter-spacing:1px;">HOW TO USE</span><br>
  1. Go to <b style="color:#fff">UCSB GOLD</b> → <b style="color:#fff">My Class Schedule</b><br>
  2. Take a <b style="color:#fff">screenshot</b> of the full schedule table<br>
  3. Upload it below — OCR scans it instantly, no API key needed ( ˘▽˘)っ♨<br>
  <span style="font-size:.85em;color:#445;">
    Deployment note: add <code>pytesseract</code> + <code>Pillow</code> to requirements.txt
    and <code>tesseract-ocr</code> to packages.txt
  </span>
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
            run_ocr = st.button("Analyze Schedule Image",
                                use_container_width=True,
                                disabled=(uploaded_img is None))
        with col_clear:
            if st.button("(シ_ _)シ  Clear", use_container_width=True):
                st.session_state.parsed_schedule = []
                st.rerun()

        if uploaded_img is not None:
            st.image(uploaded_img, caption="Your uploaded schedule", use_column_width=True)

        if run_ocr and uploaded_img is not None:
            img_bytes = uploaded_img.read()
            with st.spinner("꒰(･‿･)꒱ Reading your schedule with OCR..."):
                st.session_state.parsed_schedule = parse_schedule_from_image(img_bytes)
            if not st.session_state.parsed_schedule:
                st.warning("No courses detected. Make sure the screenshot clearly shows the full schedule table.")
            else:
                st.rerun()

        parsed = st.session_state.parsed_schedule
        if not parsed:
            st.stop()

        # ── Quarter summary ──────────────────────────────────────────────────
        n_courses  = len(parsed)
        n_with_rmp = sum(1 for p in parsed if make_join_key(p["instructor"]) in rmp_lookup)
        avg_gpas   = []
        for p in parsed:
            jk          = make_join_key(p["instructor"])
            course_name = p.get("course", "")   # e.g. "MATH 3B"
            sub         = full_df[full_df["join_key"] == jk]
            if course_name and not sub.empty:
                course_sub = sub[sub["course"] == course_name]
                if not course_sub.empty:
                    sub = course_sub
            if not sub.empty:
                # One representative value per course-professor pair (median across all their offerings of that class)
                avg_gpas.append(sub[gpa_col].median())
        overall_avg             = sum(avg_gpas) / len(avg_gpas) if avg_gpas else None
        ov_status, ov_clr, _    = gpa_badge(overall_avg) if overall_avg else ("N/A","#666","")

        st.markdown(f"""
<div style="display:flex;gap:14px;margin:18px 0 24px;flex-wrap:wrap;">
  <div style="flex:1;min-width:130px;background:rgba(255,215,0,.07);border:1px solid rgba(255,215,0,.2);
              border-radius:14px;padding:16px;text-align:center;">
    <div style="font-family:'Orbitron',sans-serif;font-size:1.8em;font-weight:900;color:#FFD700">{n_courses}</div>
    <div style="font-family:'Rajdhani',sans-serif;font-size:.8em;color:#556;letter-spacing:1px;margin-top:4px;">CLASSES DETECTED</div></div>
  <div style="flex:1;min-width:130px;background:rgba(0,116,217,.07);border:1px solid rgba(0,116,217,.2);
              border-radius:14px;padding:16px;text-align:center;">
    <div style="font-family:'Orbitron',sans-serif;font-size:1.8em;font-weight:900;color:#5bb8ff">{n_with_rmp}</div>
    <div style="font-family:'Rajdhani',sans-serif;font-size:.8em;color:#556;letter-spacing:1px;margin-top:4px;">PROFS WITH RMP</div></div>
  <div style="flex:1;min-width:130px;background:rgba(46,204,64,.06);border:1px solid rgba(46,204,64,.15);
              border-radius:14px;padding:16px;text-align:center;">
    <div style="font-family:'Orbitron',sans-serif;font-size:1.8em;font-weight:900;color:{ov_clr}">{f"{overall_avg:.2f}" if overall_avg else "N/A"}</div>
    <div style="font-family:'Rajdhani',sans-serif;font-size:.8em;color:#556;letter-spacing:1px;margin-top:4px;">PROJECTED AVG GPA</div></div>
  <div style="flex:1;min-width:130px;background:rgba(255,65,54,.06);border:1px solid rgba(255,65,54,.12);
              border-radius:14px;padding:16px;text-align:center;">
    <div style="font-family:'Orbitron',sans-serif;font-size:1.4em;font-weight:900;color:{ov_clr};margin-top:4px">{ov_status}</div>
    <div style="font-family:'Rajdhani',sans-serif;font-size:.8em;color:#556;letter-spacing:1px;margin-top:4px;">QUARTER VIBE</div></div>
</div>""", unsafe_allow_html=True)

        st.markdown(f'<div style="font-family:Orbitron,sans-serif;font-size:.75em;color:rgba(255,215,0,.5);'
                    f'letter-spacing:2px;margin-bottom:18px;">YOUR {n_courses} CLASSES THIS QUARTER</div>',
                    unsafe_allow_html=True)

        palette = ["#FF4136","#0074D9","#FFD700","#2ECC40","#FF851B","#B10DC9",
                   "#00CCFF","#FF69B4","#AAAAAA","#01FF70","#F012BE","#7FDBFF"]
        qmap    = {"WINTER":0,"SPRING":1,"SUMMER":2,"FALL":3}

        for pi, entry in enumerate(parsed):
            course_name  = entry["course"]
            instructor   = entry["instructor"]
            jk           = make_join_key(instructor)
            course_color = palette[pi % len(palette)]

            # ── Fuzzy instructor match fallback ──────────────────────────────
            # If exact join key not found, try matching by last name + initials
            def best_jk_match(instructor_str, df):
                exact = make_join_key(instructor_str)
                if exact in df["join_key"].values:
                    return exact

                last, first = parse_name(instructor_str)
                if not last:
                    return exact

                # Find all DB entries with the same last name
                candidates = df[df["join_key"].str.startswith(last + "||")]
                if candidates.empty:
                    return exact

                unique_jks = candidates["join_key"].unique()
                if len(unique_jks) == 1:
                    return unique_jks[0]

                # Multiple people share the last name — use first initial to disambiguate
                # Score each candidate: exact first-initial match wins
                first_initial = first[0] if first else ""
                best, best_score = exact, -1
                for jk_cand in unique_jks:
                    _, cand_first = jk_cand.split("||", 1)[0], jk_cand.split("||", 1)[1]
                    cand_initial  = cand_first[0] if cand_first else ""
                    # Exact first-initial match is a strong signal
                    if first_initial and cand_initial == first_initial:
                        score = name_similarity(first, cand_first) + 1.0  # boost
                    elif not first_initial:
                        score = 0.5  # no info, neutral
                    else:
                        score = name_similarity(first, cand_first)
                    if score > best_score:
                        best_score = score
                        best = jk_cand

                # Only return a fuzzy match if it's meaningfully better than nothing
                # If first initial was provided but no candidate matched it, return exact
                # (no match) rather than returning the wrong person
                if first_initial and best_score < 0.5:
                    return exact
                return best

            jk = best_jk_match(instructor, full_df)

            specific_hist = full_df[
                (full_df["join_key"] == jk) &
                (full_df["course"].str.contains(entry["num"], na=False))].copy()
            all_prof_hist = full_df[full_df["join_key"] == jk].copy()
            hist_for_gpa  = specific_hist if not specific_hist.empty else all_prof_hist

            avg_gpa              = hist_for_gpa[gpa_col].mean() if not hist_for_gpa.empty else None
            status, clr, shd     = gpa_badge(avg_gpa) if avg_gpa else ("N/A","#666","rgba(0,0,0,0)")
            txt_col              = "#000" if status == "EASY" else "#fff"

            rmp_info   = rmp_lookup.get(jk, {})
            has_rmp    = bool(rmp_info)
            rmp_rating = rmp_info.get("rating", "N/A")
            rmp_diff   = rmp_info.get("difficulty", "N/A")
            rmp_url    = rmp_info.get("url", "")
            rmp_ta     = rmp_info.get("take_again", "N/A")
            ta_str     = (f"{rmp_ta}%" if rmp_ta and str(rmp_ta) != "nan"
                          and "%" not in str(rmp_ta) else str(rmp_ta))
            try:
                r_clr = "#2ECC40" if float(rmp_rating) >= 4.0 else \
                        ("#FFDC00" if float(rmp_rating) >= 3.0 else "#FF4136")
            except Exception:
                r_clr = "#888"

            gpa_display = f"{avg_gpa:.2f}" if avg_gpa else "No Data"

            with st.container(border=True):
                st.markdown(f'''
<div style="display:flex;align-items:center;gap:12px;margin-bottom:2px;">
  <span style="display:inline-block;width:10px;height:10px;border-radius:50%;
               background:{course_color};box-shadow:0 0 8px {course_color};flex-shrink:0;"></span>
  <span style="font-family:Orbitron,sans-serif;font-size:1.05em;font-weight:900;color:#FFD700;">{course_name}</span>
  <span style="background:{clr};color:{txt_col};padding:2px 12px;border-radius:20px;
               font-size:.7em;font-weight:900;letter-spacing:1px;">{status}</span>
  <span style="font-family:Orbitron,sans-serif;font-size:.9em;color:#cde;margin-left:auto;">GPA {gpa_display}</span>
</div>
<div style="font-family:Rajdhani,sans-serif;font-size:.88em;color:#556;margin-bottom:10px;padding-left:22px;">
  Instructor: <b style="color:#aac;">{instructor}</b>
</div>''', unsafe_allow_html=True)

                tab_class, tab_prof = st.tabs([
                    f"📊  {course_name} — Class Stats",
                    f"👤  {instructor} — Professor"
                ])

                # ── CLASS STATS ─────────────────────────────────────────────
                with tab_class:
                    if specific_hist.empty and all_prof_hist.empty:
                        st.markdown('<div style="color:#445;font-family:Rajdhani,sans-serif;padding:16px 0;">'
                                    'No historical grade data found for this course.</div>',
                                    unsafe_allow_html=True)
                    else:
                        use_hist = (specific_hist if not specific_hist.empty else all_prof_hist).copy()
                        use_hist["term"]  = use_hist["quarter"].astype(str) + " " + use_hist["year"].astype(str)
                        use_hist["_qord"] = use_hist["quarter"].map(qmap).fillna(9)
                        use_hist          = use_hist.sort_values(["year","_qord"])

                        n_sections  = len(use_hist)
                        best_gpa    = use_hist[gpa_col].max()
                        worst_gpa   = use_hist[gpa_col].min()
                        latest_gpa  = use_hist.iloc[-1][gpa_col]
                        latest_term = use_hist.iloc[-1]["term"]

                        st.markdown(f'''
<div style="display:flex;gap:10px;flex-wrap:wrap;margin:10px 0 16px;">
  <div style="flex:1;min-width:100px;background:rgba(255,255,255,.04);border-radius:12px;padding:12px;text-align:center;border:1px solid rgba(255,255,255,.07);">
    <div style="font-family:Orbitron,sans-serif;font-size:1.4em;font-weight:900;color:{clr}">{avg_gpa:.2f}</div>
    <div style="font-size:.65em;color:#445;margin-top:4px;letter-spacing:.8px;">AVG GPA</div></div>
  <div style="flex:1;min-width:100px;background:rgba(255,255,255,.04);border-radius:12px;padding:12px;text-align:center;border:1px solid rgba(255,255,255,.07);">
    <div style="font-family:Orbitron,sans-serif;font-size:1.4em;font-weight:900;color:#2ECC40">{best_gpa:.2f}</div>
    <div style="font-size:.65em;color:#445;margin-top:4px;letter-spacing:.8px;">BEST TERM</div></div>
  <div style="flex:1;min-width:100px;background:rgba(255,255,255,.04);border-radius:12px;padding:12px;text-align:center;border:1px solid rgba(255,255,255,.07);">
    <div style="font-family:Orbitron,sans-serif;font-size:1.4em;font-weight:900;color:#FF4136">{worst_gpa:.2f}</div>
    <div style="font-size:.65em;color:#445;margin-top:4px;letter-spacing:.8px;">TOUGHEST TERM</div></div>
  <div style="flex:1;min-width:100px;background:rgba(255,255,255,.04);border-radius:12px;padding:12px;text-align:center;border:1px solid rgba(255,255,255,.07);">
    <div style="font-family:Orbitron,sans-serif;font-size:1.4em;font-weight:900;color:#5bb8ff">{n_sections}</div>
    <div style="font-size:.65em;color:#445;margin-top:4px;letter-spacing:.8px;">SECTIONS</div></div>
  <div style="flex:1;min-width:120px;background:rgba(255,255,255,.04);border-radius:12px;padding:12px;text-align:center;border:1px solid rgba(255,255,255,.07);">
    <div style="font-family:Orbitron,sans-serif;font-size:1.2em;font-weight:900;color:#FFD700">{latest_gpa:.2f}</div>
    <div style="font-size:.65em;color:#445;margin-top:4px;letter-spacing:.8px;">LAST: {latest_term}</div></div>
</div>''', unsafe_allow_html=True)

                        trend_fig = go.Figure()
                        trend_fig.add_trace(go.Scatter(
                            x=use_hist["term"], y=use_hist[gpa_col],
                            mode="lines+markers+text",
                            text=[f"{v:.2f}" for v in use_hist[gpa_col]],
                            textposition="top center",
                            textfont=dict(size=9, color="#ccc"),
                            line=dict(color=course_color, width=2.5),
                            marker=dict(size=8, color=course_color,
                                        line=dict(color="rgba(255,255,255,0.5)", width=1.5)),
                            fill="tozeroy",
                            fillcolor=(f"rgba({int(course_color[1:3],16)},"
                                       f"{int(course_color[3:5],16)},"
                                       f"{int(course_color[5:7],16)},0.07)"),
                            hovertemplate="<b>%{x}</b><br>Avg GPA: <b>%{y:.2f}</b><extra></extra>"))
                        trend_fig.add_hline(y=3.5, line_dash="dot",
                                            line_color="rgba(46,204,64,0.4)", line_width=1.5,
                                            annotation_text="EASY", annotation_font_color="#2ECC40",
                                            annotation_font_size=9)
                        trend_fig.add_hline(y=3.0, line_dash="dot",
                                            line_color="rgba(255,65,54,0.4)", line_width=1.5,
                                            annotation_text="STRESSFUL", annotation_font_color="#FF4136",
                                            annotation_font_size=9)
                        trend_fig.update_layout(
                            template="plotly_dark", height=200,
                            margin=dict(l=0,r=40,t=20,b=0),
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,8,22,0.5)",
                            showlegend=False,
                            xaxis=dict(tickfont=dict(size=9,color="#778"), showgrid=False, tickangle=-30),
                            yaxis=dict(tickfont=dict(size=9,color="#556"),
                                       gridcolor="rgba(255,255,255,0.04)",
                                       range=[max(1.5,use_hist[gpa_col].min()-0.4),4.3]))
                        st.plotly_chart(trend_fig, use_container_width=True,
                                        key=f"ctrend_{pi}", config={"displayModeBar": False})

                        latest     = use_hist.iloc[-1]
                        grade_vals = {"A":latest.get("a",0),"B":latest.get("b",0),
                                      "C":latest.get("c",0),"D":latest.get("d",0),"F":latest.get("f",0)}
                        if sum(grade_vals.values()) > 0:
                            st.markdown(f'<div style="font-family:Orbitron,sans-serif;font-size:.65em;'
                                        f'color:#FFD700;letter-spacing:2px;margin:8px 0 6px;">'
                                        f'GRADE DISTRIBUTION — {latest_term}</div>', unsafe_allow_html=True)
                            dist_fig = px.bar(
                                pd.DataFrame({"Grade":list(grade_vals.keys()),
                                              "Students":list(grade_vals.values())}),
                                x="Grade", y="Students", color="Grade",
                                color_discrete_map={"A":"#2ECC40","B":"#0074D9",
                                                    "C":"#FFDC00","D":"#FF851B","F":"#FF4136"},
                                template="plotly_dark", height=140)
                            dist_fig.update_layout(
                                margin=dict(l=0,r=0,t=0,b=0), showlegend=False,
                                xaxis_title=None, yaxis_title=None,
                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,8,22,0.5)",
                                xaxis=dict(tickfont=dict(size=11,color="#aaa")),
                                yaxis=dict(tickfont=dict(size=9,color="#445")))
                            st.plotly_chart(dist_fig, use_container_width=True,
                                            key=f"cdist_{pi}", config={"displayModeBar": False})

                # ── PROFESSOR ────────────────────────────────────────────────
                with tab_prof:
                    col_rmp, col_history = st.columns([1, 2])

                    with col_rmp:
                        if has_rmp:
                            st.markdown(f'''
<div style="display:flex;flex-direction:column;gap:10px;margin-bottom:14px;">
  <div style="background:rgba(255,255,255,.05);border-radius:14px;padding:16px;text-align:center;border:1px solid rgba(255,255,255,.08);">
    <div style="font-family:Orbitron,sans-serif;font-size:2em;font-weight:900;color:{r_clr}">{rmp_rating}<span style="font-size:0.4em;color:#556;font-weight:400">/5</span></div>
    <div style="font-size:.7em;color:#445;margin-top:5px;letter-spacing:.8px;">OVERALL RATING</div></div>
  <div style="display:flex;gap:8px;">
    <div style="flex:1;background:rgba(255,255,255,.05);border-radius:12px;padding:12px;text-align:center;border:1px solid rgba(255,255,255,.07);">
      <div style="font-family:Orbitron,sans-serif;font-size:1.3em;font-weight:900;color:#FF851B">{rmp_diff}<span style="font-size:0.45em;color:#556;font-weight:400">/5</span></div>
      <div style="font-size:.6em;color:#445;margin-top:4px;">DIFFICULTY</div></div>
    <div style="flex:1;background:rgba(255,255,255,.05);border-radius:12px;padding:12px;text-align:center;border:1px solid rgba(255,255,255,.07);">
      <div style="font-family:Orbitron,sans-serif;font-size:1.3em;font-weight:900;color:#2ECC40">{ta_str}</div>
      <div style="font-size:.6em;color:#445;margin-top:4px;">RETAKE</div></div>
  </div>
</div>''', unsafe_allow_html=True)

                            tags_raw = rmp_info.get("tags","")
                            if tags_raw and str(tags_raw) != "nan":
                                raw  = str(tags_raw).strip('"\'[]\'').strip("\'")
                                tags = [t.strip().strip("\"'") for t in raw.split(",") if t.strip()][:8]
                                pills = "".join(
                                    f'<span style="background:rgba(0,204,255,.1);color:#00CCFF;'
                                    f'border:1px solid rgba(0,204,255,.3);padding:3px 10px;'
                                    f'border-radius:20px;display:inline-block;margin:3px 3px 0 0;'
                                    f'font-size:.72em;">{t}</span>' for t in tags)
                                st.markdown(
                                    f'<div style="font-family:Orbitron,sans-serif;font-size:.6em;'
                                    f'color:#FFD700;letter-spacing:1px;margin-bottom:6px;">STUDENT TAGS</div>'
                                    f'<div style="margin-bottom:12px;">{pills}</div>',
                                    unsafe_allow_html=True)
                            num_r = rmp_info.get("num_ratings","")
                            if num_r and str(num_r) != "nan":
                                st.markdown(f'<div style="font-family:Rajdhani,sans-serif;font-size:.8em;'
                                            f'color:#445;margin-bottom:10px;">Based on {int(float(num_r))} student ratings</div>',
                                            unsafe_allow_html=True)
                            if rmp_url and str(rmp_url) != "nan":
                                st.markdown(f'<a href="{rmp_url}" target="_blank" style="font-family:Rajdhani,'
                                            f'sans-serif;font-size:.85em;color:#5bb8ff;text-decoration:none;">'
                                            f'(づ ◕‿◕ )づ Full RMP Profile →</a>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div style="font-family:Rajdhani,sans-serif;font-size:.9em;'
                                        'color:#445;padding:16px 0;">No RMP data found for this professor.</div>',
                                        unsafe_allow_html=True)

                    with col_history:
                        if all_prof_hist.empty:
                            st.markdown('<div style="font-family:Rajdhani,sans-serif;font-size:.9em;'
                                        'color:#445;padding:16px 0;">No teaching history found.</div>',
                                        unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div style="font-family:Orbitron,sans-serif;font-size:.65em;'
                                        f'color:#FFD700;letter-spacing:2px;margin-bottom:10px;">'
                                        f'ALL COURSES TAUGHT BY {instructor}</div>', unsafe_allow_html=True)

                            ph = all_prof_hist.copy()
                            ph["term"]  = ph["quarter"].astype(str) + " " + ph["year"].astype(str)
                            ph["_qord"] = ph["quarter"].map(qmap).fillna(9)
                            ph          = ph.sort_values(["year","_qord"])

                            hist_fig = go.Figure()
                            for ci, c in enumerate(sorted(ph["course"].unique())):
                                sub  = ph[ph["course"] == c]
                                cc   = palette[ci % len(palette)]
                                lw   = 3.0 if c.startswith(entry["num"]) else 1.5
                                opac = 1.0 if c.startswith(entry["num"]) else 0.55
                                hist_fig.add_trace(go.Scatter(
                                    x=sub["term"], y=sub[gpa_col],
                                    mode="lines+markers", name=c,
                                    line=dict(color=cc, width=lw),
                                    marker=dict(size=6 if lw>2 else 4, color=cc, opacity=opac),
                                    opacity=opac,
                                    hovertemplate=f"<b>{c}</b><br>%{{x}}<br>GPA: <b>%{{y:.2f}}</b><extra></extra>"))
                            hist_fig.add_hline(y=3.5, line_dash="dot",
                                               line_color="rgba(46,204,64,0.35)", line_width=1)
                            hist_fig.add_hline(y=3.0, line_dash="dot",
                                               line_color="rgba(255,65,54,0.35)", line_width=1)
                            hist_fig.update_layout(
                                template="plotly_dark", height=260,
                                margin=dict(l=0,r=0,t=10,b=0),
                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,8,22,0.5)",
                                legend=dict(font=dict(size=10,color="#aaa"), bgcolor="rgba(0,0,0,0)",
                                            orientation="h", y=-0.25),
                                xaxis=dict(tickfont=dict(size=8,color="#667"), showgrid=False, tickangle=-30),
                                yaxis=dict(tickfont=dict(size=9,color="#556"),
                                           gridcolor="rgba(255,255,255,0.04)", range=[2.0,4.3],
                                           title=dict(text="Avg GPA",font=dict(size=10,color="#778"))))
                            st.plotly_chart(hist_fig, use_container_width=True,
                                            key=f"phist_{pi}", config={"displayModeBar": False})

                            summary = (ph.groupby("course")[gpa_col].agg(["mean","count"]).reset_index()
                                       .rename(columns={"mean":"Avg GPA","count":"Sections"})
                                       .sort_values("Avg GPA", ascending=False))
                            summary["Avg GPA"] = summary["Avg GPA"].map("{:.2f}".format)
                            st.dataframe(summary, hide_index=True, use_container_width=True)


if __name__ == "__main__":
    main()
