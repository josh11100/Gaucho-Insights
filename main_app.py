import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px
import streamlit.components.v1 as components 

# Keep your original page config
st.set_page_config(page_title="Gaucho Insights", layout="wide", page_icon="🎓")

# --- INITIALIZE SESSION STATE FOR DRILL-DOWN ---
if 'selected_prof' not in st.session_state:
    st.session_state.selected_prof = None

# --- YOUR ORIGINAL CSS INJECTION ---
st.markdown("""
    <style>
        .stTabs [data-baseweb="tab-list"] {
            gap: 50px; justify-content: center; background-color: rgba(0, 0, 0, 0.2);
            padding: 10px; border-radius: 15px; margin-bottom: 20px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 60px; white-space: pre-wrap; background-color: transparent;
            border-radius: 10px; color: #888; font-size: 22px !important;
            font-weight: 700; font-family: 'Orbitron', sans-serif; transition: all 0.3s ease;
        }
        .stTabs [data-baseweb="tab"]:hover { color: #FFD700; background-color: rgba(255, 215, 0, 0.1); }
        .stTabs [aria-selected="true"] { color: #FFD700 !important; border-bottom: 3px solid #FFD700 !important; text-shadow: 0 0 10px rgba(255, 215, 0, 0.5); }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_and_clean_data():
    # --- YOUR ORIGINAL LOADING LOGIC ---
    def find_file(name):
        paths_to_check = [name, os.path.join('data', name)]
        for p in paths_to_check:
            if os.path.exists(p): return p
        return None

    csv_path = find_file('courseGrades.csv')
    rmp_path = find_file('rmp_final_data.csv')
    if not csv_path: st.error("Missing 'courseGrades.csv'."); st.stop()
        
    df = pd.read_csv(csv_path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # Cleaning
    def get_course_num(course_str):
        match = re.search(r'(\d+)', str(course_str))
        return int(match.group(1)) if match else None

    df['course_num_val'] = df['course'].apply(get_course_num)
    df = df[(df['course_num_val'].notna()) & (df['course_num_val'] <= 198) & (df['course_num_val'] != 99)]

    # Registrar Join Key
    def get_registrar_key(name):
        if pd.isna(name): return "UNKNOWN"
        parts = str(name).upper().split()
        return f"{parts[0]}{parts[1][0] if len(parts) > 1 else ''}"

    df['join_key'] = df['instructor'].apply(get_registrar_key)
    
    if rmp_path:
        rmp_df = pd.read_csv(rmp_path)
        rmp_df.columns = [c.strip().lower() for c in rmp_df.columns]
        # Rename so columns match your search logic
        rmp_df = rmp_df.rename(columns={'instructor': 'instructor_rmp', 'rating': 'rmp_rating', 'difficulty': 'rmp_difficulty', 'take_again': 'rmp_take_again', 'tags': 'rmp_tags', 'url': 'rmp_url'})
        df = pd.merge(df, rmp_df, left_on='join_key', right_on='instructor_rmp', how='left')
    
    for col in ['instructor', 'quarter', 'course', 'dept']:
        if col in df.columns: df[col] = df[col].astype(str).str.upper().str.strip()

    gpa_col = next((c for c in ['avggpa', 'avg_gpa', 'avg gpa'] if c in df.columns), 'avggpa')
    return df, gpa_col

def main():
    full_df, gpa_col = load_and_clean_data()
    # (Hero Header and 3D logic remains same as your original...)
    # ... [Insert your original Hero HTML and Tabs logic here] ...

    with tab2:
        # Search Filters
        # ... [Your filter code] ...

        # --- NEW PROFILE DRILL-DOWN LOGIC ---
        if st.session_state.selected_prof:
            st.button("⬅ Back to Results", on_click=lambda: st.session_state.update({'selected_prof': None}))
            prof_data = full_df[full_df['instructor'] == st.session_state.selected_prof].iloc[0]
            st.subheader(f"👤 {st.session_state.selected_prof}")
            st.metric("Rating", prof_data.get('rmp_rating', 'N/A'))
            st.write(f"**Tags:** {prof_data.get('rmp_tags', 'None')}")
            st.dataframe(full_df[full_df['instructor'] == st.session_state.selected_prof])
        else:
            # --- YOUR ORIGINAL SEARCH RESULTS LOOP ---
            for idx, row in data.head(20).iterrows():
                # ... Original row display ...
                if st.button(f"👨‍🏫 {row['instructor']}", key=f"btn_{idx}"):
                    st.session_state.selected_prof = row['instructor']
                    st.rerun()

if __name__ == "__main__":
    main()
