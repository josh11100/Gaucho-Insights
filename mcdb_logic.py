import pandas as pd
def process_mcdb(df):
    return df[df['dept'] == 'MCDB'].copy()
