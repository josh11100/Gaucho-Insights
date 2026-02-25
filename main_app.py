import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Set page config for a professional look
st.set_page_config(page_title="Gaucho Insights", layout="wide", page_icon="🎓")

def load_and_query_data(search_term, mode="Department"):
    # --- PATH SETUP ---
    # This finds the exact folder where THIS script (main_app.py) is sitting
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct full paths to your files
    grades_path = os.path.join(current_dir, 'courseGrades.csv')
    rmp_path = os.path.join(current_dir, 'data', 'rmp_ratings.csv')

    # 1. Load Grades Data
    try:
        df = pd.read_csv(grades_path)
        # Clean up column names (remove hidden spaces)
        df.columns = [str(c).strip() for c in df.columns]
    except FileNotFoundError:
        st.error(f"❌ Could not find 'courseGrades.csv' at: {grades_path}")
        return pd.DataFrame()

    # 2. Load RMP Data
    try:
        rmp_df = pd.read_csv(rmp_path)
        # Match by last name: Split "FIRST LAST" and take the last part
        rmp_df['match_name'] = rmp_df['instructor'].str.split().str[-1].str.upper()
        rmp_df['rmp_rating'] = pd.to_numeric(rmp_df['rmp_rating'], errors='coerce')
        # Keep highest rating for duplicate names
        rmp_df = rmp_df.sort_values('rmp_rating', ascending=False).drop_duplicates('match_name')
    except Exception:
        # If no RMP data, create an empty frame so the merge doesn't crash
        rmp_df = pd.DataFrame(columns=['match_name', 'rmp_rating'])

    # 3. Filter Grade Data based on Search
    if mode == "Department":
        data = df[df['dept'].str.contains(search_term, case=False, na=False)].copy()
    else:
        data = df[df['course'].str.contains(search_term, case=False, na=False)].copy()

    # 4. Merge Grades with RMP
    if not data.empty:
        # Match by last name: "LASTNAME FIRSTINIT" -> Take the first part
        data['match_name'] = data['instructor'].str.split().str[0].str.upper()
        
        if not rmp_df.empty:
            data = data.merge(rmp_df[['match_name', 'rmp_rating']], on='match_name', how='left')
            data['rmp_rating'] = data['rmp_rating'].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "N/A")
        else:
            data['rmp_rating'] = "N/A"
            
        data = data.drop(columns=['match_name'])

    return data

# --- UI SETUP ---
st.title("🎓 Gaucho Insights")
st.markdown("### UCSB Grade Distribution & RateMyProfessors")

col1, col2 = st.columns([1, 2])
with col1:
    search_mode = st.radio("Search by:", ["Department", "Course Code"])
    user_input = st.text_input(f"Enter {search_mode}:", "PSTAT")

# Fetch Data
filtered_data = load_and_query_data(user_input, search_mode)

if not filtered_data.empty:
    # --- METRICS ---
    avg_gpa = filtered_data['avgGPA'].mean()
    valid_rmp = pd.to_numeric(filtered_data['rmp_rating'], errors='coerce').dropna()
    avg_rmp = valid_rmp.mean() if not valid_rmp.empty else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Average GPA", f"{avg_gpa:.2f}")
    m2.metric("Avg RMP Score", f"{avg_rmp:.1f} / 5.0" if avg_rmp > 0 else "N/A")
    m3.metric("Sections Analyzed", len(filtered_data))

    st.divider()

    # --- VISUALIZATION ---
    st.subheader(f"GPA Spread for {user_input}")
    # Box plots show the range of difficulty better than bars
    fig = px.box(filtered_data, x="course", y="avgGPA", 
                 color="course", points="all",
                 hover_data=["instructor", "rmp_rating"],
                 labels={"avgGPA": "Average GPA", "course": "Course Code"})
    
    st.plotly_chart(fig, use_container_width=True)

    # --- DATA TABLE ---
    st.subheader("Details Table")
    # Define columns to show (and check if they exist)
    cols_to_show = ['instructor', 'course', 'avgGPA', 'rmp_rating', 'quarter']
    existing_cols = [c for c in cols_to_show if c in filtered_data.columns]
    
    st.dataframe(
        filtered_data[existing_cols].sort_values(by="avgGPA", ascending=False),
        use_container_width=True
    )
else:
    st.warning(f"No results found for '{user_input}'. Try 'PSTAT' or 'ECON'.")

st.sidebar.info("💡 **Pro Tip:**\nSearch by **Department** (e.g., PSTAT) to compare all classes in that major.")
