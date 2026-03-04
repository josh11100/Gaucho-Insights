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

# --- 2. DATA ENGINE (The KeyError Fix) ---
@st.cache_data
def load_and_clean_data():
    def find_file(name):
        for p in [name, os.path.join('data', name)]:
            if os.path.exists(p): return p
        return None

    csv_path = find_file('courseGrades.csv')
    rmp_path = find_file('rmp_final_data.csv')
    
    if not csv_path:
        st.error("Missing 'courseGrades.csv'.")
        st.stop()
        
    df = pd.read_csv(csv_path)
    df.columns = [str(c).strip().lower() for c in df.columns]

    def get_join_key(name):
        if pd.isna(name): return "UNKNOWN"
        parts = str(name).upper().replace(',', '').replace('.', '').split()
        return f"{parts[0]} {parts[1][0]}" if len(parts) >= 2 else (parts[0] if parts else "UNKNOWN")

    df['join_key'] = df['instructor'].apply(get_join_key)
    
    if rmp_path:
        rmp_df = pd.read_csv(rmp_path)
        rmp_df.columns = [c.strip().lower() for c in rmp_df.columns]
        rmp_df['join_key'] = rmp_df['instructor'].apply(get_join_key)
        rmp_df = rmp_df.drop_duplicates(subset=['join_key'])

        # SAFE RENAME: Only rename columns that actually exist to avoid KeyError
        rename_map = {
            'rating': 'rmp_rating',
            'avg_rating': 'rmp_rating',
            'difficulty': 'rmp_diff',
            'avg_difficulty': 'rmp_diff',
            'tags': 'rmp_tags',
            'url': 'rmp_url'
        }
        
        # Filter the map to only include columns present in rmp_df
        actual_rename = {k: v for k, v in rename_map.items() if k in rmp_df.columns}
        rmp_df = rmp_df.rename(columns=actual_rename)

        # Merge only columns that now exist in the dataframe
        rmp_cols = ['join_key'] + [v for v in actual_rename.values()]
        df = pd.merge(df, rmp_df[rmp_cols], on='join_key', how='left')

    # Cleaning course numbers
    df['course_num'] = df['course'].apply(lambda x: int(re.search(r'(\d+)', str(x)).group(1)) if re.search(r'(\d+)', str(x)) else None)
    df = df[(df['course_num'].notna()) & (df['course_num'] <= 198) & (df['course_num'] != 99)]

    for col in ['instructor', 'quarter', 'course', 'dept']:
        if col in df.columns: df[col] = df[col].astype(str).str.upper().str.strip()

    gpa_col = next((c for c in ['avggpa', 'avg_gpa', 'avg gpa'] if c in df.columns), 'avggpa')
    return df, gpa_col

# --- 3. SESSION STATE ---
if 'selected_prof' not in st.session_state: st.session_state.selected_prof = None

def reset_filters():
    for key in ['dept_query', 'course_query', 'prof_query']:
        if key in st.session_state: st.session_state[key] = "" if "query" in key else " "
    st.session_state.selected_prof = None

# --- 4. UI COMPONENTS ---
def main():
    full_df, gpa_col = load_and_clean_data()

    # HERO
    st.markdown('<div style="text-align:center;"><h1 style="color:#FFD700; font-family:\'Orbitron\'; font-size:clamp(1.5rem, 5vw, 3rem);">(つ▀¯▀ )つ GAUCHO INSIGHTS ⊂(▀¯▀⊂ )</h1></div>', unsafe_allow_html=True)

    # PROFILE VIEW
    if st.session_state.selected_prof:
        prof_name = st.session_state.selected_prof
        prof_data = full_df[full_df['instructor'] == prof_name]
        
        if st.button("⬅ BACK TO SEARCH"):
            st.session_state.selected_prof = None
            st.rerun()

        st.title(f"👤 {prof_name}")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Avg Course GPA", f"{prof_data[gpa_col].mean():.2f}")
        
        # Display RMP metrics if they were successfully merged
        if 'rmp_rating' in prof_data.columns and pd.notna(prof_data['rmp_rating'].iloc[0]):
            m2.metric("RMP Quality", f"{prof_data['rmp_rating'].iloc[0]}/5.0")
            m3.metric("RMP Difficulty", f"{prof_data['rmp_diff'].iloc[0]}/5.0")
            
            if 'rmp_tags' in prof_data.columns and pd.notna(prof_data['rmp_tags'].iloc[0]):
                st.subheader("Professor Tags")
                tags = str(prof_data['rmp_tags'].iloc[0]).split(',')
                tag_html = "".join([f"<span style='background:rgba(0,204,255,0.1); color:#00CCFF; padding:5px 12px; border-radius:15px; border:1px solid #00CCFF; margin:5px; display:inline-block; font-weight:bold;'>{t.strip()}</span>" for t in tags])
                st.markdown(tag_html, unsafe_allow_html=True)
        else:
            st.info("No RateMyProfessors data found for this name.")

        st.subheader("Teaching History")
        st.dataframe(prof_data[['course', 'quarter', 'year', gpa_col]].sort_values('year', ascending=False), use_container_width=True)
        st.stop()

    # SEARCH TABS
    tab1, tab2 = st.tabs(["🏠 HOME", "🔍 SEARCH TOOL"])

    with tab1:
        st.markdown("""<div style="background:rgba(0,31,63,0.7); border:2px solid #FFD700; border-radius:20px; padding:30px;">
            <h2 style="color:#FFD700;">WELCOME GAUCHOS!</h2>
            <p>Use the <b>Search Tool</b> to find professors and view their grade distributions.</p>
        </div>""", unsafe_allow_html=True)

    with tab2:
        st.sidebar.header("( 🔍 ) FILTERS")
        all_depts = sorted(full_df['dept'].unique().tolist())
        sel_dept = st.sidebar.selectbox("Select Department", options=[" "] + all_depts, key="dept_query")
        c_q = st.sidebar.text_input("COURSE #", key="course_query").strip().upper()
        p_q = st.sidebar.text_input("PROFESSOR NAME", key="prof_query").strip().upper()

        results = full_df.copy()
        if sel_dept != " ": results = results[results['dept'] == sel_dept]
        if c_q: results = results[results['course'].str.contains(c_q, na=False)]
        if p_q: results = results[results['instructor'].str.contains(p_q, na=False)]

        for idx, row in results.head(20).iterrows():
            with st.container(border=True):
                cA, cB = st.columns([2, 1])
                with cA:
                    st.markdown(f"### {row['course']} | {row['quarter']} {row['year']}")
                    if st.button(f"👤 {row['instructor']}", key=f"p_{idx}"):
                        st.session_state.selected_prof = row['instructor']
                        st.rerun()
                    st.write(f"**GPA:** {row[gpa_col]:.2f}")
                with cB:
                    fig = px.bar(x=['A','B','C','D','F'], y=[row.get('a',0), row.get('b',0), row.get('c',0), row.get('d',0), row.get('f',0)], height=120, template="plotly_dark")
                    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True, key=f"f_{idx}", config={'displayModeBar': False})

if __name__ == "__main__":
    main()
