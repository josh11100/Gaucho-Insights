#
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Page Config
st.set_page_config(page_title="Gaucho Grade Insight", layout="wide")

st.title("📊 Gaucho Grade Insight Engine")
st.markdown("Detailed historical breakdown by Year and Quarter.")

@st.cache_data
def load_data():
    df = pd.read_csv('data/courseGrades.csv')
    df['dept'] = df['dept'].str.strip()
    df['instructor'] = df['instructor'].str.strip()
    df['course'] = df['course'].str.strip()
    # Ensure 'quarter' is treated as a string for searching
    df['quarter'] = df['quarter'].astype(str)
    return df

df = load_data()

# Sidebar
all_depts = sorted(df['dept'].unique())
selected_dept = st.sidebar.selectbox("Select Department", all_depts, index=all_depts.index("PSTAT"))
dept_df = df[(df['dept'] == selected_dept) & (df['avgGPA'] > 0)]

# SEARCH SECTION
st.subheader(f"Search {selected_dept} Records")
search_query = st.text_input("Search Course or Professor").upper()

if search_query:
    # Filter for exact matches or contains
    results = dept_df[(dept_df['course'].str.contains(search_query)) | 
                      (dept_df['instructor'].str.contains(search_query))]
    
    if not results.empty:
        # Display the table including the Quarter/Year
        st.write(f"Showing {len(results)} records found:")
        st.dataframe(results[['quarter', 'course', 'instructor', 'avgGPA', 'nLetterStudents']].sort_values(by='quarter', ascending=False))
        
        # TREND ANALYSIS
        st.divider()
        st.subheader(f"GPA Trend for '{search_query}'")
        
        # Create a line chart to see if grades are changing over time
        # Note: Quarters aren't perfectly chronological by string sort, 
        # but it gives a good visual spread.
        trend_data = results.groupby('quarter')['avgGPA'].mean().reset_index()
        
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        sns.lineplot(data=trend_data, x='quarter', y='avgGPA', marker='o', ax=ax2)
        plt.xticks(rotation=45)
        ax2.set_title("GPA Fluctuations by Quarter")
        st.pyplot(fig2)
    else:
        st.warning("No records found for that search.")
