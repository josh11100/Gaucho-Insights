@st.cache_data
def load_data():
    csv_path = os.path.join('data', 'courseGrades.csv')
    
    if not os.path.exists(csv_path):
        st.error(f"File not found at {csv_path}.")
        st.stop()
        
    df_raw = pd.read_csv(csv_path)
    
    # --- PRE-PROCESSING ---
    df_raw['dept'] = df_raw['dept'].str.strip()
    df_raw['course'] = df_raw['course'].str.replace(r'\s+', ' ', regex=True).str.strip()
    df_raw['course_num'] = df_raw['course'].str.extract(r'(\d+)').astype(float)
    
    q_order = {'FALL': 4, 'SUMMER': 3, 'SPRING': 2, 'WINTER': 1}
    # Create the temp split to extract year/rank
    temp_split = df_raw['quarter'].str.upper().str.split(' ')
    df_raw['q_year'] = pd.to_numeric(temp_split.str[1])
    df_raw['q_rank'] = temp_split.str[0].map(q_order)

    # --- THE CRITICAL FIX ---
    # SQLite hates Python lists. We must NOT include the split list in to_sql.
    # We also ensure no empty/NaN values crash the insert.
    df_for_sql = df_raw.copy()
    
    # --- SQLITE WORKFLOW ---
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    
    # We only send columns that SQLite understands (Strings and Numbers)
    df_for_sql.to_sql('courses', conn, index=False, if_exists='replace')
    
    df_final = pd.read_sql_query(GET_RECENT_LECTURES, conn)
    conn.close()
    
    # Drop the helper columns from the final result so the user doesn't see them
    return df_final.drop(columns=['course_num', 'q_year', 'q_rank'], errors='ignore')
