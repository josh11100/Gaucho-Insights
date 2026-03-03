import streamlit as st
import streamlit.components.v1 as components
import os

# --- 1. LOAD EXTERNAL CSS ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Important: Run this right after set_page_config
st.set_page_config(page_title="Gaucho Insights", layout="wide")
local_css("style.css")

# --- 2. THE 3D WELCOME BOX HTML ---
# I've set the frame height to 760 and card to 680 to give the borders room to breathe.
stats_3d_html = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    .welcome-perspective { 
        perspective: 2000px; 
        width: 100%; height: 740px; 
        display: flex; justify-content: center; align-items: center;
    }
    .welcome-card { 
        width: 96%; height: 680px; 
        background: rgba(0, 31, 63, 0.8); 
        border-radius: 25px; 
        border: 2px solid #FFD700; 
        position: relative; overflow: hidden; 
        box-shadow: 0 20px 50px rgba(0,0,0,0.8); 
        transform-style: preserve-3d; 
        transition: transform 0.1s ease-out;
        padding: 50px 40px;
    }
    #statsCanvas { position: absolute; top: 0; left: 0; z-index: 1; width: 100%; height: 100%; }
    .content { position: relative; z-index: 2; color: white; pointer-events: none; }
</style>
<div class="welcome-perspective" id="cont">
    <div class="welcome-card" id="card">
        <canvas id="statsCanvas"></canvas>
        <div class="content">
            <h1 style="font-family: 'Orbitron'; font-size: 2.5em; color: #FFD700;">WELCOME GAUCHOS!</h1>
            <p style="font-size: 1.2em; line-height: 1.6;">Numbers don't lie. Use this tool to navigate UCSB curriculum with actual registrar data.</p>
        </div>
    </div>
</div>
<script>
    const card = document.getElementById('card');
    const cont = document.getElementById('cont');
    cont.onmousemove = (e) => {
        let rect = cont.getBoundingClientRect();
        card.style.transform = `rotateY(${(e.clientX - rect.left - rect.width/2)/40}deg) rotateX(${-(e.clientY - rect.top - rect.height/2)/40}deg)`;
    };
    cont.onmouseleave = () => card.style.transform = 'rotateY(0deg) rotateX(0deg)';
    
    // Canvas Logic
    const canvas = document.getElementById('statsCanvas');
    const ctx = canvas.getContext('2d');
    function resize() { canvas.width = card.clientWidth; canvas.height = card.clientHeight; }
    window.onresize = resize; resize();
    
    let dots = Array(60).fill().map(() => ({
        x: Math.random()*canvas.width, y: Math.random()*canvas.height,
        vx: (Math.random()-0.5)*1.2, vy: (Math.random()-0.5)*1.2
    }));

    function draw() {
        ctx.clearRect(0,0,canvas.width,canvas.height);
        dots.forEach(d => {
            d.x += d.vx; d.y += d.vy;
            if(d.x<0 || d.x>canvas.width) d.vx*=-1;
            if(d.y<0 || d.y>canvas.height) d.vy*=-1;
            ctx.fillStyle = 'rgba(255,215,0,0.3)';
            ctx.beginPath(); ctx.arc(d.x, d.y, 2, 0, 7); ctx.fill();
        });
        requestAnimationFrame(draw);
    }
    draw();
</script>
"""

# --- 3. APP LAYOUT ---
st.title("(つ▀¯▀ )つ GAUCHO INSIGHTS")

tab1, tab2 = st.tabs(["HOME", "SEARCH"])

with tab1:
    col1, col2 = st.columns([2, 1])
    with col1:
        # Wrap in a div to apply the fix from style.css
        st.markdown('<div class="welcome-3d-frame">', unsafe_allow_html=True)
        components.html(stats_3d_html, height=750)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.metric(label="Data Recency", value="Summer 2025")
        st.write("Check the sidebar for filters!")
