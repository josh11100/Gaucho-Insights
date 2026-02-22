import pandas as pd
import os

# --- CONFIG ---
FILE_PATH = 'data/courseGrades.csv'

def load_data():
    if not os.path.exists(FILE_PATH):
        print(f"Error: {FILE_PATH} not found.")
        return None
    df = pd.read_csv(FILE_PATH)
    df['instructor'] = df['instructor'].str.strip()
    df['course'] = df['course'].str.strip()
    return df

def search():
    df = load_data()
    if df is None: return

    while True:
        print("\n" + "="*30)
        print("UCSB STATS LOOKUP")
        print("1. Search by COURSE (e.g., 120A)")
        print("2. Search by PROFESSOR (e.g., DUNCAN)")
        print("3. Exit")
        choice = input("Select an option (1-3): ")

        if choice == '1':
            c_num = input("Enter course number (e.g., 120A): ").upper()
            # Search for courses containing that string
            results = df[df['course'].str.contains(c_num, na=False)]
            if not results.empty:
                # Group by instructor to see who grades best for this specific course
                summary = results.groupby('instructor')['avgGPA'].mean().sort_values(ascending=False)
                print(f"\nAverage GPAs for PSTAT {c_num}:")
                print(summary)
            else:
                print("No records found for that course.")

        elif choice == '2':
            name = input("Enter Professor Last Name: ").upper()
            results = df[df['instructor'].str.contains(name, na=False)]
            if not results.empty:
                summary = results.groupby('course')['avgGPA'].mean().sort_values(ascending=False)
                print(f"\nHistorical Grades for Prof. {name}:")
                print(summary)
            else:
                print("No records found for that name.")

        elif choice == '3':
            break

if __name__ == "__main__":
    search()