import pandas as pd
def process_chem(df):
    # This captures both CHEM and CHEM (Lab/etc) if needed
    return df[df['dept'].str.contains('CHEM', na=False)].copy()
