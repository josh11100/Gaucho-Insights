import streamlit as st
import pandas as pd
import plotly.express as px

# Set page config for a wider layout
st.set_page_config(page_title="Gaucho Insights", layout="wide")

def load_and_query_data(search_term, mode="Department"):
    # 1. Load Grades Data
    try:
        df = pd.read_csv('courseGrades.csv')
        df.columns = [str(c).strip() for c in df.columns]
    except FileNotFoundError:
        st.error("❌ 'courseGrades.csv' not found. Please ensure it's in the project folder.")
        return pd.DataFrame()

    # 2. Load RMP Data
    try:
        rmp_df = pd.read_csv('data/rmp_ratings.csv')
        # Create a matching key: "LASTNAME" from RMP's "FIRST LAST"
        rmp_df['match_name'] = rmp_df['instructor'].str.split().str[-1].str.upper()
        # Clean duplicates
        rmp_df = rmp_df.sort_values('rmp_rating', ascending=False).drop_duplicates('match_name')
    except Exception:
        rmp_df = pd.DataFrame()

    # 3. Filter Grade Data based on Search
    if mode == "Department":
        data = df[df['dept'].str.contains(search_term, case=False, na=False)].copy()
    else:
        data = df[df['course'].str.contains(search_term, case=False, na=False)].copy()

    # 4. Perform the Merge logic
    if not rmp_df.empty and not data.empty:
        # Create matching key: "LASTNAME" from Grade Data's "LASTNAME FIRSTINITIAL"
        data['match_name'] = data['instructor'].str.split().str[0].str.upper()
        
        # Convert rmp_rating to numeric for calculations
        rmp_df['rmp_rating'] = pd.to_numeric(rmp_df['rmp_rating'], errors='coerce')
        
        data = data.merge(rmp_df[['match_name', 'rmp_rating']], on='match_name', how='left')
        data['rmp_rating'] = data['rmp_rating'].fillna("N/A")
        data = data.drop(columns=['match_name'])

    return data

# --- UI SETUP ---
st.title("🎓 Gaucho Insights: UCSB Grade & Professor Explorer")

col1, col2 = st.columns([1, 2])

with col1:
    search_mode = st.radio("Search by:", ["Department", "Course Code"])
    user_input = st.text_input(f"Enter {search_mode} (e.g., PSTAT or PSTAT 120A)", "PSTAT")

# Fetch Data
filtered_data = load_and_query_data(user_input, search_mode)

if not filtered_data.empty:
    # --- METRICS SECTION ---
    avg_gpa = filtered_data['avgGPA'].mean()
    
    # Calculate average RMP rating (excluding N/As)
    valid_rmp = pd.to_numeric(filtered_data['rmp_rating'], errors='coerce').dropna()
    avg_rmp = valid_rmp.mean() if not valid_rmp.empty else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Average GPA", f"{avg_gpa:.2f}")
    m2.metric("RMP Score", f"{avg_rmp:.1f} / 5.0" if avg_rmp > 0 else "N/A")
    m3.metric("Total Sections", len(filtered_data))

    # --- VISUALIZATION ---
    st.subheader(f"GPA Distribution for {user_input}")
    fig = px.histogram(filtered_data, x="avgGPA", color="instructor", 
                       hover_data=["course", "rmp_rating"],
                       title="Average GPA by Instructor")
    st.plotly_chart(fig, use_container_width=True)

    # --- DATA TABLE ---
    st.subheader("Detailed Course Data")
    # Clean up display columns
    display_df = filtered_data[['instructor', 'course', 'avgGPA', 'rmp_rating', 'quarter']].sort_values(by="avgGPA", ascending=False)
    st.dataframe(display_df, use_container_width=True)

else:
    st.warning("No data found for that search. Try something like 'PSTAT' or 'ECON'.")

st.markdown("---")
st.caption("Data sources: UCSB Office of the Registrar & RateMyProfessors")
