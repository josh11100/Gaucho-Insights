import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Page Config
st.set_page_config(page_title="Gaucho Insights", layout="wide", page_icon="🎓")

def load_all_data():
    """Loads and cleans the raw data from the data folder"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    grades_path = os.path.join(current_dir, 'data', 'courseGrades.csv')
    rmp_path = os.path.join(current_dir, 'data', 'rmp_ratings.csv')

    try:
        df = pd.read_csv(grades_path)
        df.columns = [str(c).strip() for c in df.columns]
    except FileNotFoundError:
        st.error(f"❌ Could not find 'courseGrades.csv' in the 'data' folder.")
        return pd.DataFrame(), pd.DataFrame()

    try:
        rmp_df = pd.read_csv(rmp_path)
        rmp_df['match_name'] = rmp_df['instructor'].str.split().str[-1].str.upper()
        rmp_df['rmp_rating'] = pd.to_numeric(rmp_df['rmp_rating'], errors='coerce')
        rmp_df = rmp_df.sort_values('rmp_rating', ascending=False).drop_duplicates('match_name')
    except Exception:
        rmp_df = pd.DataFrame(columns=['match_name', 'rmp_rating'])

    return df, rmp_df

# --- DATA INITIALIZATION ---
df, rmp_df = load_all_data()

# --- SIDEBAR SEARCH ---
with st.sidebar:
    st.title("🔍 Search Filters")
    search_mode = st.radio("Search by:", ["Department", "Course Code"])
    user_input = st.text_input(f"Enter {search_mode}:", "PSTAT")
    st.divider()
    st.info("Searching across UCSB Grade History & RateMyProfessors data.")

# --- PROCESSING SEARCH ---
if not df.empty:
    # Filter for search
    if search_mode == "Department":
        filtered = df[df['dept'].str.contains(user_input, case=False, na=False)].copy()
    else:
        filtered = df[df['course'].str.contains(user_input, case=False, na=False)].copy()

    # Merge RMP
    if not filtered.empty:
        filtered['match_name'] = filtered['instructor'].str.split().str[0].str.upper()
        if not rmp_df.empty:
            filtered = filtered.merge(rmp_df[['match_name', 'rmp_rating']], on='match_name', how='left')
            filtered['rmp_rating_display'] = filtered['rmp_rating'].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "N/A")
        else:
            filtered['rmp_rating_display'] = "N/A"

    # --- MAIN UI ---
    st.title("🎓 Gaucho Insights")

    # TOP SECTION: Global Insights (The "Top 3" you wanted)
    st.subheader("🏆 Course Highlights")
    
    # Calculate the easiest classes (highest average GPA) for the current search
    if not filtered.empty:
        top_3 = filtered.groupby('course')['avgGPA'].mean().sort_values(ascending=False).head(3)
        cols = st.columns(3)
        for i, (course_name, gpa_val) in enumerate(top_3.items()):
            cols[i].metric(label=f"#{i+1} Easiest Class", value=course_name, delta=f"{gpa_val:.2f} Avg GPA")
    
    st.divider()

    if not filtered.empty:
        # Metrics Row
        m1, m2, m3 = st.columns(3)
        m1.metric("Avg GPA", f"{filtered['avgGPA'].mean():.2f}")
        
        # Calculate numeric RMP avg
        valid_rmp = pd.to_numeric(filtered['rmp_rating'], errors='coerce').dropna()
        avg_rmp = valid_rmp.mean() if not valid_rmp.empty else 0
        m2.metric("Avg RMP Score", f"{avg_rmp:.1f}/5.0" if avg_rmp > 0 else "N/A")
        m3.metric("Total Sections", len(filtered))

        # Visualization
        st.subheader("GPA Distribution")
        fig = px.box(filtered, x="course", y="avgGPA", color="course", points="all",
                     hover_data=["instructor", "rmp_rating_display"],
                     labels={"avgGPA": "Avg GPA", "course": "Course"})
        st.plotly_chart(fig, use_container_width=True)

        # Data Table
        st.subheader("Detailed Data Explorer")
        st.dataframe(
            filtered[['instructor', 'course', 'avgGPA', 'rmp_rating_display', 'quarter']].sort_values("avgGPA", ascending=False),
            use_container_width=True
        )
    else:
        st.warning(f"No results found for {user_input}.")
