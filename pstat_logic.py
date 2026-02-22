import pandas as pd

def process_pstat(df):
    # Filter for PSTAT and clean data
    data = df[df['dept'] == 'PSTAT'].copy()
    return data
