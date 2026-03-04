import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px
import streamlit.components.v1 as components

# --- 1. CONFIG & CSS ---
st.set_page_config(page_title="Gaucho Insights", layout="wide", page_icon="🎓")

def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

# --- 2. DATA ENGINE (The RMP Connection Fix) ---
@st.cache_data
def load_and_clean_data():
    def find_file(name):
        for p in [name, os.path.join('data', name)]:
            if os.path.exists(p): return p
        return None

    csv_path = find_file('courseGrades.csv')
    rmp_path = find_file('rmp_final_data.csv')
    
    if not csv_path:
        st.error("Missing 'courseGrades.csv'. Please upload it to the directory.")
        st.stop()
        
    df = pd.read_csv(csv_path)
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Standardize Registrar Names for Joining
    def get_join_key(name):
        if pd.isna(name): return "UNKNOWN"
        # Clean punctuation and split: "GAUCHO, GARY" -> ["GAUCHO", "GARY"]
        parts = str(name).upper().replace(',', '').replace('.', '').split()
        if len(parts) >= 2:
            return f"{parts[0]} {parts[1][0]}" # Returns "GAUCHO G"
        return parts[0] if parts else "UNKNOWN"

    df['join_key'] = df['instructor'].apply(get_join_key)
    
    # Process RMP Data
    if rmp_path:
        rmp_df = pd.read_csv(rmp_path)
        rmp_df.columns = [c.strip().lower() for c in rmp_df.columns]
        
        # Standardize RMP Names
        rmp_df['join_key'] = rmp_df['instructor'].apply(get_join_key)
        rmp_df = rmp_df.drop_duplicates(subset=['join_key'], keep='first')
        
        # Rename RMP columns clearly
        rmp_df = rmp_df.rename(columns={
            'rating': 'rmp_rating', 
            'difficulty': 'rmp_diff', 
            'tags': 'rmp_tags', 
            'url': 'rmp_url'
        })
        
        # Merge RMP info into the main Grades dataframe
        df = pd.merge(df, rmp_df[['join_key', 'rmp_rating', 'rmp_diff', 'rmp_tags', 'rmp_url']], on='join_key', how='left')

    # Undergrad Filter (Classes <= 198)
    df['course_num'] = df['course'].apply(lambda x: int(re.search(r'(\d+)', str(x)).group(1)) if re.search(r'(\d+)', str(x)) else None)
    df = df[(df['course_num'].notna()) & (df['course_num'] <= 198) & (df['course_num'] != 99)]

    for col in ['instructor', 'quarter', 'course', 'dept']:
        if col in df.columns: df[col] = df[col].astype(str).str.upper().str.strip()

    gpa_col = next((c for c in ['avggpa', 'avg_gpa'] if c in df.columns), 'avggpa')
    return df, gpa_col

# --- 3. SESSION STATE ---
if 'selected_prof' not in st.session_state: st.session_state.selected_prof = None

def reset_filters():
    st.session_state.dept_query = " "
    st.session_state.course_query = ""
    st.session_state.prof_query = ""
    st.session_state.selected_prof = None

# --- 4. HEADER ---
hero_html = """<div style="text-align:center;"><h1 style="color:#FFD700; font-family:'Orbitron'; font-size:clamp(1.5rem, 5vw, 3rem);">(つ▀¯▀ )つ GAUCHO INSIGHTS ⊂(▀¯▀⊂ )</h1></div>"""
components.html(hero_html, height=100)

def main():
    full_df, gpa_col = load_and_clean_data()

    # --- VIEW: PROFESSOR PROFILE ---
    if st.session_state.selected_prof:
        prof_name = st.session_state.selected_prof
        prof_data = full_df[full_df['instructor'] == prof_name]
        first_row = prof_data.iloc[0]

        if st.button("⬅ BACK TO SEARCH"):
            st.session_state.selected_prof = None
            st.rerun()

        st.title(f"👤 {prof_name}")
        
        # RMP Metrics Row
        m1, m2, m3 = st.columns(3)
        m1.metric("Avg Course GPA", f"{prof_data[gpa_col].mean():.2f}")
        
        if 'rmp_rating' in full_df.columns and pd.notna(first_row['rmp_rating']):
            m2.metric("RMP Quality", f"{first_row['rmp_rating']}/5.0")
            m3.metric("RMP Difficulty", f"{first_row['rmp_diff']}/5.0")
            
            st.subheader("What Students Say (Tags)")
            tags = str(first_row['rmp_tags']).split(',') if pd.notna(first_row['rmp_tags']) else []
            tag_html = "".join([f"<span class='tag-pill' style='background:rgba(0,204,255,0.1); color:#00CCFF; padding:5px 12px; border-radius:15px; border:1px solid #00CCFF; margin:5px; display:inline-block; font-weight:bold;'>{t.strip()}</span>" for t in tags])
            st.markdown(tag_html, unsafe_allow_html=True)
            
            if pd.notna(first_row['rmp_url']):
                st.link_button("View on RateMyProfessors", first_row['rmp_url'])
        else:
            st.info("No RMP data found for this instructor.")

        st.subheader("Teaching History")
        st.dataframe(prof_data[['course', 'quarter', 'year', gpa_col]].sort_values('year', ascending=False), use_container_width=True)
        st.stop()

    # --- VIEW: TABS (HOME & SEARCH) ---
    tab1, tab2 = st.tabs(["🏠 HOME", "🔍 SEARCH TOOL"])

    with tab1:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.markdown("""
            <div style="background:rgba(0,31,63,0.7); border:2px solid #FFD700; border-radius:20px; padding:30px;">
                <h2 style="color:#FFD700;">WELCOME GAUCHOS!</h2>
                <p>Select the <b>Search Tool</b> to find professors and view their RMP tags.</p>
            </div>
            """, unsafe_allow_html=True)
        with col_right:
            st.metric("Data Recency", "Summer 2025")

    with tab2:
        # Sidebar
        st.sidebar.header("( 🔍 ) FILTERS")
        all_depts = sorted(full_df['dept'].unique().tolist())
        sel_dept = st.sidebar.selectbox("Select Department", options=[" "] + all_depts, key="dept_query")
        c_q = st.sidebar.text_input("COURSE #", key="course_query").strip().upper()
        p_q = st.sidebar.text_input("PROFESSOR NAME", key="prof_query").strip().upper()
        if st.sidebar.button("Clear All"):
            reset_filters()
            st.rerun()

        # Filtering Logic
        results = full_df.copy()
        if sel_dept != " ": results = results[results['dept'] == sel_dept]
        if c_q: results = results[results['course'].str.contains(c_q, na=False)]
        if p_q: results = results[results['instructor'].str.contains(p_q, na=False)]

        # Render Results
        if not results.empty:
            for idx, row in results.head(20).iterrows():
                with st.container(border=True):
                    cA, cB = st.columns([2, 1])
                    with cA:
                        st.markdown(f"### {row['course']} | {row['quarter']} {row['year']}")
                        # Clickable Prof Name
                        if st.button(f"👤 {row['instructor']}", key=f"p_{idx}"):
                            st.session_state.selected_prof = row['instructor']
                            st.rerun()
                        st.write(f"**GPA:** {row[gpa_col]:.2f}")
                    with cB:
                        fig = px.bar(x=['A','B','C','D','F'], y=[row.get('a',0), row.get('b',0), row.get('c',0), row.get('d',0), row.get('f',0)], height=120, template="plotly_dark")
                        fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
                        st.plotly_chart(fig, use_container_width=True, key=f"f_{idx}", config={'displayModeBar': False})
        else:
            st.warning("No data found for these filters.")

if __name__ == "__main__":
    main()
