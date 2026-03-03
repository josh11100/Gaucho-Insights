import streamlit as st
import streamlit.components.v1 as components
import os

# --- 1. LOAD EXTERNAL CSS ---
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.set_page_config(page_title="Gaucho Insights", layout="wide", page_icon="🎓")
local_css("style.css")

# --- 2. FULL 3D WELCOME BOX HTML (RESTORED CONTENT) ---
stats_3d_html = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    .welcome-perspective { 
        perspective: 2000px; width: 100%; height: 740px; 
        display: flex; justify-content: center; align-items: center;
    }
    .welcome-card { 
        width: 98%; height: 680px; background: rgba(0, 31, 63, 0.8); 
        border-radius: 25px; border: 2px solid #FFD700; 
        position: relative; overflow: hidden; transform-style: preserve-3d; 
        transition: transform 0.1s ease-out; padding: 50px 40px;
    }
    #statsCanvas { position: absolute; top: 0; left: 0; z-index: 1; width: 100%; height: 100%; }
    .content { position: relative; z-index: 2; color: white; font-family: sans-serif; pointer-events: none; }
    .grid-box { 
        background: rgba(255,255,255,0.08); padding: 25px; border-radius: 15px; 
        backdrop-filter: blur(8px); pointer-events: auto;
    }
</style>
<div class="welcome-perspective" id="cont">
    <div class="welcome-card" id="card">
        <canvas id="statsCanvas"></canvas>
        <div class="content">
            <h1 style="font-family: 'Orbitron'; font-size: 2.5em; color: #FFD700; margin-bottom: 20px;">WELCOME GAUCHOS! ٩(◕‿◕)۶</h1>
            <p style="font-size: 1.2em; line-height: 1.6; margin-bottom: 40px; max-width: 90%;">
                <b>WHAT IS THIS?</b><br>
                Gaucho Insights is a tool designed to help you survive your schedule. This dashboard helps you see exactly how stressful 
                certain classes are with specific professors. <b>Numbers don't lie!</b>
            </p>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div class="grid-box" style="border-left: 5px solid #FFD700;">
                    <b style="color: #FFD700;">( 📍 ) MISSION</b><br>
                    Empowering students to make informed decisions about their academic path.
                </div>
                <div class="grid-box" style="border-left: 5px solid #0074D9;">
                    <b style="color: #0074D9;">( 🔍 ) THE TECH</b><br>
                    Utilizing Python, Streamlit, and mesh networks to visualize grade distributions.
                </div>
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

# Restored LinkedIn Box HTML
linkedin_html = """
<style>
    .li-card { 
        width: 100%; height: 100px; background: #0077b5; border-radius: 15px; border: 2px solid #FFD700;
        display: flex; align-items: center; justify-content: center; text-decoration: none;
        color: white; font-weight: bold; font-family: sans-serif; transition: 0.2s;
    }
    .li-card:hover { transform: scale(1.02); background: #008fdb; }
</style>
<a href="https://www.linkedin.com/in/joshua-chung858/" target="_blank" class="li-card">Follow on LinkedIn</a>
"""

# --- 3. APP LAYOUT ---
st.title("(つ▀¯▀ )つ GAUCHO INSIGHTS")

tab1, tab2 = st.tabs(["HOME", "SEARCH TOOL"])

with tab1:
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        # Putting it back in the frame to prevent cutoff
        st.markdown('<div class="welcome-3d-frame">', unsafe_allow_html=True)
        components.html(stats_3d_html, height=750)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_right:
        # Gaucho Info restoration
        st.markdown("""
        <div style="background: linear-gradient(135deg, #001f3f 0%, #0074D9 100%); padding: 30px; border-radius: 20px; border: 2px solid #FFD700; color: white; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #FFD700 !important;">📊 Gaucho Info</h3>
            <p><b>Data:</b> Thru Summer 2025</p>
            <p><b>Source:</b> Registrar & RMP</p>
            <p><b>Created By:</b> Joshua Chung</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Metric box (using your style.css formatting)
        st.metric(label="Data Recency", value="Summer 2025")
        
        # LinkedIn Box
        components.html(linkedin_html, height=120)

with tab2:
    st.info("The Search Tool is ready! Add your filter logic here.")
