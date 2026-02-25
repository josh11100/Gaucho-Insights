import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px

# 1. Logic File Imports
try:
    import pstat_logic, cs_logic, mcdb_logic, chem_logic
except ImportError:
    st.error("┐(~ー~;)┌ Logic files missing.")
    st.stop()

st.set_page_config(page_title="Gaucho Insights", layout="wide")

def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

@st.cache_data
def load_and_clean_data():
    csv_path = os.path.join('data', 'courseGrades.csv')
    if not os.path.exists(csv_path):
        st.error("¯\_(ツ)_/¯ Data file missing.")
        st.stop()
        
    df = pd.read_csv(csv_path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    text_cols = ['instructor', 'quarter', 'course', 'dept']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()

    gpa_col = next((c for c in ['avggpa', 'avg_gpa', 'avg gpa'] if c in df.columns), 'avggpa')
    
    for col in [gpa_col, 'a', 'b', 'c', 'd', 'f']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Aggregation to combine sections
    group_cols = ['instructor', 'quarter', 'course', 'dept']
    df = df.groupby(group_cols).agg({
        gpa_col: 'mean',
        'a': 'sum', 'b': 'sum', 'c': 'sum', 'd': 'sum', 'f': 'sum'
    }).reset_index()

    df = df[(df['a'] + df['b'] + df['c'] + df['d'] + df['f']) >= 15]

    def get_time_score(row):
        year_val = 0
        q_weight = 0
        q_str = str(row.get('quarter', '')).upper().strip()
        
        if len(q_str) == 5 and q_str.isdigit():
            year_val = int(q_str[:4])
            q_code = q_str[4]
            q_weight = int(q_code) if q_code in '1234' else 0
        else:
            four_digit = re.findall(r'\b(202[1-9]|2030)\b', q_str)
            if four_digit:
                year_val = int(four_digit[0])
            else:
                two_digit = re.findall(r'(\d{2})', q_str)
                if two_digit:
                    year_nums = [int(n) for n in two_digit if 21 <= int(n) <= 35]
                    year_val = 2000 + year_nums[-1] if year_nums else 2000 + int(two_digit[-1])
            
            if "FALL" in q_str or " F" in q_str: q_weight = 4
            elif "SUMMER" in q_str or " M" in q_str: q_weight = 3
            elif "SPRING" in q_str or " S" in q_str: q_weight = 2
            elif "WINTER" in q_str or " W" in q_str: q_weight = 1
            
        return year_val, q_weight

    time_results = df.apply(lambda r: pd.Series(get_time_score(r)), axis=1)
    df['year_val'] = time_results[0].astype(int)
    df['q_weight'] = time_results[1].astype(int)
            
    return df, gpa_col

def main():
    st.title("(つ▀¯▀ )つ GAUCHO INSIGHTS ⊂(▀¯▀⊂ )")
    full_df, gpa_col = load_and_clean_data()

    st.sidebar.header("🔍 FILTERS")
    mode = st.sidebar.selectbox("DEPARTMENT", ["All Departments", "PSTAT", "CS", "MCDB", "CHEM"])
    course_q = st.sidebar.text_input("COURSE #").strip().upper()
    prof_q = st.sidebar.text_input("PROFESSOR").strip().upper()
    
    data = full_df.copy()
    if mode == "PSTAT": data = pstat_logic.process_pstat(data)
    elif mode == "CS": data = cs_logic.process_cs(data)
    elif mode == "MCDB": data = mcdb_logic.process_mcdb(data)
    elif mode == "CHEM": data = chem_logic.process_chem(data)

    if course_q: data = data[data['course'].str.contains(course_q, na=False)]
    if prof_q: data = data[data['instructor'].str.contains(prof_q, na=False)]

    if not data.empty:
        data = data.sort_values(by=['year_val', 'q_weight', gpa_col], ascending=[False, False, False])

        st.markdown("### (◕‿◕✿) Top Rated in Selection")
        top_cols = st.columns(3)
        valid_profs = data[data[gpa_col] > 0]
        if not valid_profs.empty:
            top_profs = valid_profs.groupby('instructor')[gpa_col].mean().sort_values(ascending=False).head(3)
            for i, (prof, gpa) in enumerate(top_profs.items()):
                top_cols[i].metric(prof, f"{gpa:.2f} GPA")

        st.markdown("---")

        rows = data.head(30)
        for i in range(0, len(rows), 2):
            grid_cols = st.columns(2)
            for j in range(2):
                idx = i + j
                if idx < len(rows):
                    row = rows.iloc[idx]
                    with grid_cols[j]:
                        with st.container(border=True):
                            # --- YEAR AND COURSE HEADER ---
                            y_val = int(row['year_val'])
                            q_label = row['quarter']
                            
                            # This replaces the emoji with the Year/Quarter text
                            st.markdown(f"#### {q_label} | {row['course']}")
                            st.caption(f"Instructor: **{row['instructor']}**")
                            
                            c1, c2 = st.columns([1, 1.2])
                            with c1:
                                # Logic for label text (moved emoji here)
                                if row[gpa_col] >= 3.5: label = "✨ EASY A"
                                elif row[gpa_col] <= 2.8: label = "💀 WEED-OUT"
                                else: label = "⚖️ BALANCED"
                                
                                total_s = int(row['a'] + row['b'] + row['c'] + row['d'] + row['f'])
                                st.write(f"**{label}**")
                                st.write(f"**Avg GPA:** {row[gpa_col]:.2f}")
                                st.write(f"**Students:** {total_s}")
                            
                            with c2:
                                grade_counts = pd.DataFrame({
                                    'Grade': ['A', 'B', 'C', 'D', 'F'],
                                    'Count': [row['a'], row['b'], row['c'], row['d'], row['f']]
                                })
                                fig = px.bar(grade_counts, x='Grade', y='Count', color='Grade',
                                             color_discrete_map={'A':'#00CCFF','B':'#3498db','C':'#FFD700','D':'#e67e22','F':'#e74c3c'},
                                             template="plotly_dark", height=140)
                                fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), showlegend=False,
                                                  paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                                  yaxis_title=None, xaxis_title=None)
                                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"grid_{idx}")
    else:
        st.info("┐(~ー~;)┌ No courses found.")

if __name__ == "__main__":
    main()
