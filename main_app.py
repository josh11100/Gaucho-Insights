import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px
import streamlit.components.v1 as components 

st.set_page_config(page_title="Gaucho Insights", layout="wide", page_icon="🎓")

# --- INITIALIZE SESSION STATE ---
if 'selected_prof' not in st.session_state:
    st.session_state.selected_prof = None

# --- CSS INJECTION ---
st.markdown("""
    <style>
        .stTabs [data-baseweb="tab-list"] { gap: 50px; justify-content: center; background-color: rgba(0, 0, 0, 0.2); padding: 10px; border-radius: 15px; margin-bottom: 20px; }
        .stTabs [data-baseweb="tab"] { height: 60px; color: #888; font-size: 22px !important; font-weight: 700; font-family: 'Orbitron', sans-serif; transition: all 0.3s ease; }
        .stTabs [aria-selected="true"] { color: #FFD700 !important; border-bottom: 3px solid #FFD700 !important; }
        /* Profile Card Styling */
        .prof-card { background: rgba(255, 215, 0, 0.05); border: 1px solid #FFD700; border-radius: 15px; padding: 20px; margin-bottom: 20px; }
        .tag-pill { background: #FFD700; color: black; padding: 2px 10px; border-radius: 10px; font-size: 0.8em; font-weight: bold; margin-right: 5px; display: inline-block; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_and_clean_data():
    path = 'rmp_final_data.csv'
    if not os.path.exists(path):
        st.error(f"Missing {path}")
        st.stop()
        
    df = pd.read_csv(path)
    # Standardize column names
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Ensure all essential columns exist (fill with N/A if missing from scrape)
    cols = ['instructor', 'rmp_rating', 'rmp_difficulty', 'rmp_take_again', 'rmp_tags', 'rmp_url', 'dept', 'course', 'quarter', 'year', 'avggpa', 'a', 'b', 'c', 'd', 'f']
    for c in cols:
        if c not in df.columns: df[c] = 0 if c in ['a','b','c','d','f','avggpa'] else "N/A"

    # Data Cleaning
    df['instructor'] = df['instructor'].str.upper().str.strip()
    df['dept'] = df['dept'].str.upper().str.strip()
    return df

def reset_filters():
    st.session_state.dept_query = " "
    st.session_state.course_query = ""
    st.session_state.prof_query = ""
    st.session_state.selected_prof = None

def main():
    df = load_and_clean_data()

    # --- HERO HEADER (Same as your script) ---
    hero_html = """<div style="text-align:center;"><h1 style='font-family:Orbitron; color:#FFD700;'>(つ▀¯▀ )つ GAUCHO INSIGHTS ⊂(▀¯▀⊂ )</h1></div>"""
    st.markdown(hero_html, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🏠 HOME", "🔍 SEARCH TOOL"])

    with tab1:
        st.info("Welcome! Head over to the Search Tool to find your professors.")

    with tab2:
        # Sidebar Filters
        st.sidebar.header("( 🔍 ) FILTERS")
        depts = sorted(df['dept'].unique().tolist())
        sel_dept = st.sidebar.selectbox("Department", [" "] + depts, key="dept_query")
        course_q = st.sidebar.text_input("COURSE #", key="course_query").strip().upper()
        prof_q = st.sidebar.text_input("PROFESSOR", key="prof_query").strip().upper()
        
        if st.sidebar.button("Clear All"): reset_filters(); st.rerun()

        # Filtering Logic
        data = df.copy()
        if sel_dept != " ": data = data[data['dept'] == sel_dept]
        if course_q: data = data[data['course'].str.contains(course_q, na=False)]
        if prof_q: data = data[data['instructor'].str.contains(prof_q, na=False)]

        # --- PROFESSOR PROFILE VIEW ---
        if st.session_state.selected_prof:
            prof_name = st.session_state.selected_prof
            prof_data = df[df['instructor'] == prof_name].iloc[0]
            
            st.markdown(f"## 👤 Professor Profile: {prof_name}")
            if st.button("⬅ Back to Search"):
                st.session_state.selected_prof = None
                st.rerun()

            p_col1, p_col2, p_col3 = st.columns(3)
            p_col1.metric("RMP Quality", f"⭐ {prof_data['rmp_rating']}")
            p_col2.metric("Difficulty", f"🔥 {prof_data['rmp_difficulty']}")
            p_col3.metric("Would Take Again", prof_data['rmp_take_again'])

            st.markdown("#### 🏷️ Student Tags")
            tags = str(prof_data['rmp_tags']).split(",")
            if tags and tags[0] != "None":
                tag_html = "".join([f'<span class="tag-pill">{t.strip()}</span>' for t in tags])
                st.markdown(tag_html, unsafe_allow_html=True)
            else:
                st.write("No tags available.")

            st.markdown("---")
            st.markdown("#### 📚 Teaching History")
            hist = df[df['instructor'] == prof_name][['course', 'quarter', 'year', 'avggpa']].sort_values(['year', 'quarter'], ascending=False)
            st.dataframe(hist, use_container_width=True)
            st.markdown(f"[Go to RateMyProfessor Profile 🔗]({prof_data['rmp_url']})")
            st.divider()

        # --- SEARCH RESULTS ---
        if not data.empty:
            for idx, row in data.head(15).iterrows():
                gpa = row['avggpa']
                color = "#FF4136" if gpa < 2.5 else "#2ECC40" if gpa > 3.3 else "#0074D9"
                
                with st.container(border=True):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.subheader(f"{row['course']} ({row['quarter']} {row['year']})")
                        
                        # The Trigger: Clicking this button sets the session state
                        if st.button(f"👨‍🏫 {row['instructor']}", key=f"btn_{idx}"):
                            st.session_state.selected_prof = row['instructor']
                            st.rerun()
                            
                        st.markdown(f"**GPA:** <span style='color:{color}; font-weight:bold;'>{gpa:.2f}</span>", unsafe_allow_html=True)
                    
                    with c2:
                        grades = pd.DataFrame({'G':['A','B','C','D','F'], 'V':[row['a'],row['b'],row['c'],row['d'],row['f']]})
                        fig = px.bar(grades, x='G', y='V', color='G', height=120, template="plotly_dark",
                                     color_discrete_map={'A':'#2ECC40','B':'#0074D9','C':'#FFDC00','D':'#FF851B','F':'#FF4136'})
                        fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), showlegend=False, xaxis_title=None, yaxis_title=None)
                        st.plotly_chart(fig, use_container_width=True, key=f"chart_{idx}", config={'displayModeBar': False})
        else:
            st.warning("No matches found.")

if __name__ == "__main__":
    main()
