import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Set page config for a professional look
st.set_page_config(page_title="Gaucho Insights", layout="wide", page_icon="🎓")

def load_and_query_data(search_term, mode="Department"):
    # --- PATH SETUP ---
    # This ensures the app finds your CSVs regardless of where you launch from
    base_path = os.path.dirname(os.path.abspath(__file__))
    grades_path = os.path.join(base_path, 'courseGrades.csv')
    rmp_path = os.path.join(base_path, 'data', 'rmp_ratings.csv')

    # 1. Load Grades Data
    try:
        df = pd.read_csv(grades_path)
        df.columns = [str(c).strip() for c in df.columns]
    except FileNotFoundError:
        st.error(f"❌ 'courseGrades.csv' not found at: {grades_path}")
        return pd.DataFrame()

    # 2. Load RMP Data
    try:
        rmp_df = pd.read_csv(rmp_path)
        # Create a matching key: Last name from RMP's "FIRST LAST"
        rmp_df['match_name'] = rmp_df['instructor'].str.split().str[-1].str.upper()
        # Ensure ratings are numbers and take the highest if duplicates exist
        rmp_df['rmp_rating'] = pd.to_numeric(rmp_df['rmp_rating'], errors='coerce')
        rmp_df = rmp_df.sort_values('rmp_rating', ascending=False).drop_duplicates('match_name')
    except Exception:
        # If RMP data is missing, we just continue without it
        rmp_df = pd.DataFrame()

    # 3. Filter Grade Data based on Search
    if mode == "Department":
        data = df[df['dept'].str.contains(search_term, case=False, na=False)].copy()
    else:
        data = df[df['course'].str.contains(search_term, case=False, na=False)].copy()

    # 4. Perform the Merge logic
    if not rmp_df.empty and not data.empty:
        # Create matching key: Last name from Grade Data's "LASTNAME FIRSTINITIAL"
        data['match_name'] = data['instructor'].str.split().str[0].str.upper()
        
        # Join the datasets
        data = data.merge(rmp_df[['match_name', 'rmp_rating']], on='match_name', how='left')
        
        # Clean up column for display
        data['rmp_rating'] = data['rmp_rating'].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "N/A")
        data = data.drop(columns=['match_name'])
    else:
        data['rmp_rating'] = "N/A"

    return data

# --- UI SETUP ---
st.title("🎓 Gaucho Insights")
st.markdown("### UCSB Grade Distribution & Professor Ratings")

# Sidebar / Header Controls
col1, col2 = st.columns([1, 2])
with col1:
    search_mode = st.radio("Search by:", ["Department", "Course Code"])
    user_input = st.text_input(f"Enter {search_mode}:", "PSTAT")

# Fetch Data
filtered_data = load_and_query_data(user_input, search_mode)

if not filtered_data.empty:
    # --- METRICS SECTION ---
    avg_gpa = filtered_data['avgGPA'].mean()
    
    # Calculate average RMP rating for the valid numbers we found
    valid_rmp = pd.to_numeric(filtered_data['rmp_rating'], errors='coerce').dropna()
    avg_rmp = valid_rmp.mean() if not valid_rmp.empty else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Average GPA", f"{avg_gpa:.2f}")
    m2.metric("Avg RMP Score", f"{avg_rmp:.1f} / 5.0" if avg_rmp > 0 else "N/A")
    m3.metric("Sections Analyzed", len(filtered_data))

    st.divider()

    # --- VISUALIZATION ---
    st.subheader(f"GPA Analysis: {user_input}")
    
    # Create a nice Plotly chart
    fig = px.box(filtered_data, x="course", y="avgGPA", 
                 color="course", points="all",
                 hover_data=["instructor", "rmp_rating"],
                 title="GPA Spread by Course (Hover for Professor Details)")
    
    st.plotly_chart(fig, use_container_width=True)

    # --- DATA TABLE ---
    st.subheader("Raw Data Explorer")
    # Clean up the view for the user
    display_cols = ['instructor', 'course', 'avgGPA', 'rmp_rating', 'quarter', 'nLetterStudents']
    # Filter only columns that exist (to avoid errors)
    existing_cols = [c for c in display_cols if c in filtered_data.columns]
    
    st.dataframe(
        filtered_data[existing_cols].sort_values(by="avgGPA", ascending=False),
        use_container_width=True
    )

else:
    st.warning(f"No results found for '{user_input}'. Check your spelling or search mode!")

st.sidebar.info("Tips:\n- Use 'PSTAT' for the whole department.\n- Use 'PSTAT 120A' for a specific class.")
