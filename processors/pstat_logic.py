import pandas as pd
import re

def process_pstat(df):
    # Filter for PSTAT, remove P/NP (avgGPA > 0), and Undergrad (< 199)
    pstat_df = df[df['dept'] == 'PSTAT'].copy()
    pstat_df = pstat_df[(pstat_df['avgGPA'] > 0) & (pstat_df['nLetterStudents'] > 0)]
    
    def get_num(s):
        match = re.search(r'\d+', str(s))
        return int(match.group()) if match else 0
    
    pstat_df['course_num'] = pstat_df['course'].apply(get_num)
    return pstat_df[pstat_df['course_num'] < 199]