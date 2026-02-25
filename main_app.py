import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Set page config
st.set_page_config(page_title="Gaucho Insights", layout="wide", page_icon="🎓")

def load_and_query_data(search_term, mode="Department"):
    # --- PATH SETUP ---
    # Points to the 'data' folder relative to this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Both files are now in the 'data' subfolder
    grades_path = os.path.join(current_dir, 'data', 'courseGrades.csv')
    rmp_path = os.path.join(current_dir, 'data', 'rmp_ratings.csv')

    # 1. Load Grades Data
    try:
        df = pd.read_csv(grades_path)
        df.columns = [str(c).strip() for c in df.columns]
    except FileNotFoundError:
        st.error(f"❌ Could not find 'courseGrades.csv' in the 'data' folder.")
        return pd.DataFrame()

    # 2. Load RMP Data
    try:
        rmp_df = pd.read_csv(rmp_path)
        rmp_df['match_name'] = rmp_df['instructor'].str.split().str[-1].str.upper()
        rmp_df['rmp_rating'] = pd.to_numeric(rmp_df['rmp_rating'], errors='coerce')
        rmp_df = rmp_df.sort_values('rmp_rating', ascending=False).drop_duplicates('match_name')
    except Exception:
        rmp_df = pd.DataFrame(columns=['match_name', 'rmp_rating'])

    # 3. Filter Grade Data
    if mode == "Department":
        data = df[df['dept'].str.contains(search_term, case=False, na=False)].copy()
    else:
        data = df[df['course'].str.contains(search_term, case=False, na=False)].copy()

    # 4. Merge
    if not data.empty:
        data['match_name'] = data['instructor'].str.split().str[0].str.upper()
        if not rmp_df.empty:
            data = data.merge(rmp_df[['match_name', 'rmp_rating']], on='match_name', how='left')
            data['rmp_rating'] = data['rmp_rating'].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "N/A")
        else:
            data['rmp_rating'] = "N/A"
        data = data.drop(columns=['match_name'])

    return data

# --- REST OF UI CODE (Metrics, Plotly, etc.) stays the same ---
st.title("🎓 Gaucho Insights")
search_mode = st.radio("Search by:", ["Department", "Course Code"])
user_input = st.text_input(f"Enter {search_mode}:", "PSTAT")

filtered_data = load_and_query_data(user_input, search_mode)

if not filtered_data.empty:
    m1, m2, m3 = st.columns(3)
    m1.metric("Average GPA", f"{filtered_data['avgGPA'].mean():.2f}")
    
    # Calculate RMP avg
    valid_rmp = pd.to_numeric(filtered_data['rmp_rating'], errors='coerce').dropna()
    avg_rmp = valid_rmp.mean() if not valid_rmp.empty else 0
    m2.metric("Avg RMP Score", f"{avg_rmp:.1f} / 5.0" if avg_rmp > 0 else "N/A")
    m3.metric("Sections", len(filtered_data))

    fig = px.box(filtered_data, x="course", y="avgGPA", color="course", points="all",
                 hover_data=["instructor", "rmp_rating"])
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(filtered_data.sort_values(by="avgGPA", ascending=False), use_container_width=True)
