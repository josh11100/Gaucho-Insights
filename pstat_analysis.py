import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re

# --- CONFIGURATION ---
# If your files are in a folder called 'data', use 'data/courseGrades.csv'
# Otherwise, just use 'courseGrades.csv'
FILE_PATH = 'data/courseGrades.csv' 
DEPT_CODE = 'PSTAT'

def get_course_number(course_str):
    """Extracts the number from a course string like '120A' -> 120"""
    match = re.search(r'\d+', str(course_str))
    return int(match.group()) if match else 0

def run_analysis():
    # 1. Safety Check: File Existence
    if not os.path.exists(FILE_PATH):
        print(f"ERROR: File not found at {FILE_PATH}")
        print(f"Current Directory: {os.getcwd()}")
        return

    print(f"--- Processing {DEPT_CODE} Analysis (Cleaned Data) ---")
    df = pd.read_csv(FILE_PATH)
    
    # 2. Basic Cleaning
    df['dept'] = df['dept'].str.strip()
    df['course'] = df['course'].str.strip()
    df['instructor'] = df['instructor'].str.strip()

    # 3. Apply Filters for Reality
    # - Must be PSTAT
    # - Must have > 0 GPA (removes P/NP ghost zeros)
    # - Must have at least 1 letter student (verifies it's not a seminar)
    cleaned_df = df[
        (df['dept'] == DEPT_CODE) & 
        (df['avgGPA'] > 0) & 
        (df['nLetterStudents'] > 0)
    ].copy()

    # 4. Filter for Undergraduate Courses (< 199)
    cleaned_df['course_num'] = cleaned_df['course'].apply(get_course_number)
    undergrad_df = cleaned_df[(cleaned_df['course_num'] < 199) & (cleaned_df['course_num'] > 0)]

    if undergrad_df.empty:
        print("No valid undergraduate data found. Check your filters!")
        return

    # 5. Get Course Stats (Hardest/Easiest)
    course_stats = undergrad_df.groupby('course')['avgGPA'].mean().sort_values()

    print("\n--- THE REAL HARDEST PSTAT CLASSES (Actual Letter Grades) ---")
    print(course_stats.head(10))

    print("\n--- THE REAL EASIEST PSTAT CLASSES ---")
    print(course_stats.tail(10))

    # 6. Identifying "Tough Graders" (Professors)
    # Only looking at those who have taught at least 3 times for a fair average
    prof_stats = undergrad_df.groupby('instructor').agg({
        'avgGPA': 'mean',
        'course': 'count'
    })
    tough_profs = prof_stats[prof_stats['course'] >= 3].sort_values(by='avgGPA')
    
    print("\n--- TOP 5 TOUGHEST GRADERS (min. 3 quarters) ---")
    print(tough_profs.head(5))

    # 7. VISUALIZATION 1: The Histogram (The Distribution)
    plt.figure(figsize=(10, 5))
    sns.histplot(undergrad_df['avgGPA'], bins=20, kde=True, color='purple')
    plt.axvline(undergrad_df['avgGPA'].mean(), color='red', linestyle='--', label='Dept Avg')
    plt.title(f'{DEPT_CODE} Grade Distribution (Undergrad Only)')
    plt.xlabel('Average GPA')
    plt.legend()
    plt.savefig('pstat_distribution.png')

    # 8. VISUALIZATION 2: The Bar Chart (The Labels)
    plt.figure(figsize=(12, 8))
    # Combine bottom 7 and top 7 for a clear comparison
    compare_df = pd.concat([course_stats.head(7), course_stats.tail(7)])
    colors = ['firebrick'] * 7 + ['seagreen'] * 7
    compare_df.plot(kind='barh', color=colors)
    plt.title('PSTAT: Most Difficult vs. Easiest Courses')
    plt.xlabel('Historical Average GPA')
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig('pstat_course_labels.png')

    print(f"\nSUCCESS: Created 'pstat_distribution.png' and 'pstat_course_labels.png'")

if __name__ == "__main__":
    run_analysis()