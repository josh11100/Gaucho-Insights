import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px

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
    rmp_path = find_file(['rmp_final_data (1).csv', 'rmp_final_data.csv'])
    
    if not csv_path:
        st.error("Missing 'courseGrades.csv'. Please upload your grade data.")
        st.stop()
        
    df = pd.read_csv(csv_path)
    df.columns = [str(c).strip().lower() for c in df.columns]

    # IMPROVED JOIN KEY: Removes (KEN) and sorts words for perfect matching
    def get_join_key(name):
        if pd.isna(name): return "UNKNOWN"
        # Clean: Remove (KEN), commas, periods, and extra spaces
        name = re.sub(r'\(.*?\)', '', str(name)).upper()
        name = name.replace(',', ' ').replace('.', '').replace('-', ' ')
        parts = sorted(list(set(name.split()))) # Sorting makes "John Smith" == "Smith John"
        if len(parts) >= 2:
            return f"{parts[0]} {parts[1][0]}"
        return parts[0] if parts else "UNKNOWN"

    df['join_key'] = df['instructor'].apply(get_join_key)
    
    # Identify GPA and Grade Columns
    gpa_col = next((c for c in ['avggpa', 'avg_gpa', 'avg gpa'] if c in df.columns), 'avggpa')
    grade_cols = [c for c in ['a', 'b', 'c', 'd', 'f', 'p', 'np'] if c in df.columns]

    # --- NEW FILTERS ---
    # 1. Filter out 0.0 or 4.0 GPAs
    if gpa_col in df.columns:
        df = df[(df[gpa_col] > 0.0) & (df[gpa_col] < 4.0)]
    
    # 2. Filter out classes with < 5 people
    if grade_cols:
        df['student_count'] = df[grade_cols].sum(axis=1)
        df = df[df['student_count'] >= 5]

    # Merge RMP Data
    if rmp_path:
        rmp_df = pd.read_csv(rmp_path)
        rmp_df.columns = [c.strip().lower() for c in rmp_df.columns]
        rmp_df['join_key'] = rmp_df['instructor'].apply(get_join_key)
        rmp_df = rmp_df.drop_duplicates(subset=['join_key'])

        # Keep relevant RMP columns
        rmp_cols = [c for c in rmp_df.columns if c.startswith('rmp_') or c == 'join_key']
        df = pd.merge(df, rmp_df[rmp_cols], on='join_key', how='left')

    # General Cleaning
    df['course_num'] = df['course'].apply(lambda x: int(re.search(r'(\d+)', str(x)).group(1)) if re.search(r'(\d+)', str(x)) else None)
    df = df[(df['course_num'].notna()) & (df['course_num'] <= 198)]

    for col in ['instructor', 'quarter', 'course', 'dept']:
        if col in df.columns: df[col] = df[col].astype(str).str.upper().str.strip()

    return df, gpa_col

# --- 3. UI LOGIC ---
if 'selected_prof' not in st.session_state: st.session_state.selected_prof = None

def main():
    full_df, gpa_col = load_and_clean_data()

    st.markdown('<div style="text-align:center; padding:10px;"><h1 style="color:#FFD700; font-family:\'Orbitron\'; font-size:clamp(1.5rem, 5vw, 3rem);">(つ▀¯▀ )つ GAUCHO INSIGHTS ⊂(▀¯▀⊂ )</h1></div>', unsafe_allow_html=True)

    # --- VIEW: PROFESSOR PROFILE ---
    if st.session_state.selected_prof:
        prof_name = st.session_state.selected_prof
        prof_rows = full_df[full_df['instructor'] == prof_name]
        
        if st.button("⬅ BACK TO SEARCH"):
            st.session_state.selected_prof = None
            st.rerun()

        st.title(f"👤 {prof_name}")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Career GPA", f"{prof_rows[gpa_col].mean():.2f}")
        
        # Check for RMP data
        has_rmp = 'rmp_rating' in prof_rows.columns and pd.notna(prof_rows.iloc[0]['rmp_rating'])
        if has_rmp:
            data = prof_rows.iloc[0]
            m2.metric("RMP Quality", f"{data['rmp_rating']}/5.0")
            m3.metric("Difficulty", f"{data.get('rmp_difficulty', data.get('rmp_diff', 'N/A'))}/5.0")
            m4.metric("Take Again", f"{data.get('rmp_take_again', 'N/A')}")
            
            if 'rmp_tags' in data and pd.notna(data['rmp_tags']):
                st.subheader("Professor Tags")
                tags = str(data['rmp_tags']).replace('"', '').replace('[', '').replace(']', '').split(',')
                tag_html = "".join([f"<span class='tag-pill'>{t.strip()}</span>" for t in tags if t.strip().lower() != "none" and t.strip() != ""])
                st.markdown(tag_html, unsafe_allow_html=True)
            
            if 'rmp_url' in data and pd.notna(data['rmp_url']):
                st.markdown(f"🔗 [Full RateMyProfessors Profile]({data['rmp_url']})")
        else:
            st.info("No RMP data matched for this instructor.")

        st.subheader("Teaching History")
        st.dataframe(prof_rows[['course', 'quarter', 'year', gpa_col]].sort_values('year', ascending=False), use_container_width=True)
        st.stop()

    # --- VIEW: MAIN SEARCH ---
    tab1, tab2 = st.tabs(["🏠 HOME", "🔍 SEARCH TOOL"])

    with tab1:
        st.markdown("""<div style="background:rgba(0,31,63,0.7); border:2px solid #FFD700; border-radius:20px; padding:30px;">
            <h2 style="color:#FFD700; font-family:'Orbitron';">WELCOME GAUCHOS!</h2>
            <p>Search results now filter out 0.0/4.0 GPAs and small classes (<5 students).</p>
        </div>""", unsafe_allow_html=True)

    with tab2:
        st.sidebar.header("( 🔍 ) FILTERS")
        all_depts = sorted(full_df['dept'].unique().tolist())
        sel_dept = st.sidebar.selectbox("Department", [" "] + all_depts, key="dept_query")
        
        # Tag Filter
        all_tags = set()
        if 'rmp_tags' in full_df.columns:
            for t_str in full_df['rmp_tags'].dropna():
                for t in t_str.replace('"', '').split(','):
                    if t.strip().lower() != "none" and t.strip() != "": all_tags.add(t.strip())
        sel_tags = st.sidebar.multiselect("Filter by RMP Tags", options=sorted(list(all_tags)))

        c_q = st.sidebar.text_input("Course #", key="course_query").strip().upper()
        p_q = st.sidebar.text_input("Professor Name", key="prof_query").strip().upper()

        results = full_df.copy()
        if sel_dept != " ": results = results[results['dept'] == sel_dept]
        if c_q: results = results[results['course'].str.contains(c_q, na=False)]
        if p_q: results = results[results['instructor'].str.contains(p_q, na=False)]
        if sel_tags:
            results = results[results['rmp_tags'].apply(lambda x: any(tag in str(x) for tag in sel_tags) if pd.notna(x) else False)]

        for idx, row in results.head(15).iterrows():
            with st.container(border=True):
                cA, cB = st.columns([2, 1])
                with cA:
                    st.markdown(f"### {row['course']} | {row['quarter']} {row['year']}")
                    if st.button(f"👤 {row['instructor']}", key=f"btn_{idx}"):
                        st.session_state.selected_prof = row['instructor']
                        st.rerun()
                    
                    # SHOW RMP DATA IN SEARCH RESULTS
                    if 'rmp_rating' in row and pd.notna(row['rmp_rating']):
                        st.markdown(f"⭐ **RMP:** {row['rmp_rating']}/5.0 | **GPA:** {row[gpa_col]:.2f}")
                        if pd.notna(row['rmp_tags']):
                            # Show first 3 tags
                            preview_tags = str(row['rmp_tags']).replace('"', '').split(',')[:3]
                            tag_line = " ".join([f"`{t.strip()}`" for t in preview_tags])
                            st.markdown(tag_line)
                    else:
                        st.write(f"**GPA:** {row[gpa_col]:.2f} (No RMP data)")
                        
                with cB:
                    fig = px.bar(x=['A','B','C','D','F'], 
                                 y=[row.get('a',0), row.get('b',0), row.get('c',0), row.get('d',0), row.get('f',0)], 
                                 height=120, template="plotly_dark")
                    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True, key=f"f_{idx}", config={'displayModeBar': False})

if __name__ == "__main__":
    main()
