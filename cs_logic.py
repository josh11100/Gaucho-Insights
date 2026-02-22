import pandas as pd

def process_cs(df):
    # Filter for CS and clean data
    data = df[df['dept'] == 'CMPSC'].copy() # Use 'CS' if that's what's in your CSV
    return data
