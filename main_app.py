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

# --- 2. DATA ENGINE ---
@st.cache_data
def load_and_clean_data():
    def find_file(names):
        for name in names:
            paths = [name, os.path.join('data', name)]
            for p in paths:
                if os.path.exists(p): return p
        return None

    csv_path = find_file(['courseGrades.csv'])
    # Added your specific file name to the search list
    rmp_path = find_file(['rmp_final_data (1).csv', 'rmp_final_data.csv'])
    
    if not csv_path:
        st.error("Missing 'courseGrades.csv'.")
        st.stop()
        
    df = pd.read_csv(csv_path)
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Name Standardization for Joining
    def get_join_key(name):
        if pd.isna(name): return "UNKNOWN"
        parts = str(name).upper().replace(',', '').replace('.', '').replace('-', ' ').split()
        if len(parts) >= 2:
            return f"{parts[0]} {parts[1][0]}" # e.g. "CONRAD P"
        return parts[0] if parts else "UNKNOWN"

    df['join_key'] = df['instructor'].apply(get_join_key)
    
    if rmp_path:
        rmp_df = pd.read_csv(rmp_path)
        rmp_df.columns = [c.strip().lower() for c in rmp_df.columns]
        rmp_df['join_key'] = rmp_df['instructor'].apply(get_join_key)
        rmp_df = rmp_df.drop_duplicates(subset=['join_key'])

        # Robust Header Mapping (Fixes the KeyError)
        col_map = {}
        for col in rmp_df.columns:
            if 'rating' in col and 'rmp' not in col: col_map[col] = 'rmp_rating'
            if 'difficulty' in col and 'rmp' not in col: col_map[col] = 'rmp_diff'
            if 'tags' in col and 'rmp' not in col: col_map[col] = 'rmp_tags'
            if 'url' in col and 'rmp' not in col: col_map[col] = 'rmp_url'
        
        # If columns already have rmp_ prefix (like in your file), rename difficulty to diff for consistency
        if 'rmp_difficulty' in rmp_df.columns: col_map['rmp_difficulty'] = 'rmp_diff'
        
        rmp_df = rmp_df.rename(columns=col_map)
        
        # Select only the columns that actually exist now
        keep = ['join_key']
        for c in ['rmp_rating', 'rmp_diff', 'rmp_tags', 'rmp_url']:
            if c in rmp_df.columns: keep.append(c)
            
        df = pd.merge(df, rmp_df[keep], on='join_key', how='left')

    # Undergrad Filter
    df['course_num'] = df['course'].apply(lambda x: int(re.search(r'(\d+)', str(x)).group(1)) if re.search(r'(\d+)', str(x)) else None)
    df = df[(df['course_num'].notna()) & (df['course_num'] <= 198) & (df['course_num'] != 99)]

    for col in ['instructor', 'quarter', 'course', 'dept']:
        if col in df.columns: df[col] = df[col].astype(str).str.upper().str.strip()

    gpa_col = next((c for c in ['avggpa', 'avg_gpa'] if c in df.columns), 'avggpa')
    return df, gpa_col

# --- 3. UI LOGIC ---
if 'selected_prof' not in st.session_state: st.session_state.selected_prof = None

def main():
    full_df, gpa_col = load_and_clean_data()

    # Hero Title
    st.markdown('<div style="text-align:center;"><h1 style="color:#FFD700; font-family:\'Orbitron\'; font-size:clamp(1.5rem, 5vw, 3rem);">(つ▀¯▀ )つ GAUCHO INSIGHTS ⊂(▀¯▀⊂ )</h1></div>', unsafe_allow_html=True)

    # VIEW: PROFESSOR PROFILE
    if st.session_state.selected_prof:
        prof_name = st.session_state.selected_prof
        prof_data = full_df[full_df['instructor'] == prof_name]
        
        if st.button("⬅ BACK TO SEARCH"):
            st.session_state.selected_prof = None
            st.rerun()

        st.title(f"👤 {prof_name}")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Avg Career GPA", f"{prof_data[gpa_col].mean():.2f}")
        
        # Display RMP Data if merged
        first = prof_data.iloc[0]
        if 'rmp_rating' in prof_data.columns and pd.notna(first['rmp_rating']):
            m2.metric("RMP Quality", f"{first['rmp_rating']}/5.0")
            m3.metric("RMP Difficulty", f"{first.get('rmp_diff', 'N/A')}/5.0")
            
            if 'rmp_tags' in prof_data.columns and pd.notna(first['rmp_tags']):
                st.subheader("Professor Tags")
                tags = str(first['rmp_tags']).replace('"', '').split(',')
                tag_html = "".join([f"<span class='tag-pill'>{t.strip()}</span>" for t in tags if t.strip() != "None"])
                st.markdown(tag_html, unsafe_allow_html=True)
            
            if 'rmp_url' in prof_data.columns and pd.notna(first['rmp_url']):
                st.markdown(f"[Go to RateMyProfessors ↗]({first['rmp_url']})")
        else:
            st.info("No RMP data found for this instructor.")

        st.subheader("Teaching History")
        st.dataframe(prof_data[['course', 'quarter', 'year', gpa_col]].sort_values('year', ascending=False), use_container_width=True)
        st.stop()

    # VIEW: MAIN SEARCH
    tab1, tab2 = st.tabs(["🏠 HOME", "🔍 SEARCH TOOL"])

    with tab1:
        st.markdown("""<div style="background:rgba(0,31,63,0.7); border:2px solid #FFD700; border-radius:20px; padding:30px;">
            <h2 style="color:#FFD700;">WELCOME GAUCHOS!</h2>
            <p>Select the <b>Search Tool</b> to explore grades and professor ratings.</p>
        </div>""", unsafe_allow_html=True)

    with tab2:
        st.sidebar.header("( 🔍 ) FILTERS")
        all_depts = sorted(full_df['dept'].unique().tolist())
        sel_dept = st.sidebar.selectbox("Department", [" "] + all_depts, key="dept_query")
        c_q = st.sidebar.text_input("Course #", key="course_query").strip().upper()
        p_q = st.sidebar.text_input("Professor", key="prof_query").strip().upper()

        results = full_df.copy()
        if sel_dept != " ": results = results[results['dept'] == sel_dept]
        if c_q: results = results[results['course'].str.contains(c_q, na=False)]
        if p_q: results = results[results['instructor'].str.contains(p_q, na=False)]

        for idx, row in results.head(15).iterrows():
            with st.container(border=True):
                cA, cB = st.columns([2, 1])
                with cA:
                    st.markdown(f"### {row['course']} | {row['quarter']} {row['year']}")
                    if st.button(f"👤 {row['instructor']}", key=f"btn_{idx}"):
                        st.session_state.selected_prof = row['instructor']
                        st.rerun()
                    st.write(f"**GPA:** {row[gpa_col]:.2f}")
                with cB:
                    # Small Distribution Chart
                    fig = px.bar(x=['A','B','C','D','F'], y=[row.get('a',0), row.get('b',0), row.get('c',0), row.get('d',0), row.get('f',0)], height=120, template="plotly_dark")
                    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True, key=f"f_{idx}", config={'displayModeBar': False})

if __name__ == "__main__":
    main()
