# ⬡ Gaucho Insights
**UCSB Grade Analytics Dashboard**

A deployed Streamlit dashboard for UC Santa Barbara students to explore historical grade distributions, professor ratings, GE requirements, and ML-powered course insights — all in one place.

🔗 **Live App:** *(add your Streamlit Cloud URL here)*  
📁 **Repo:** [github.com/josh11100](https://github.com/josh11100)

---

## Features

### Search Tool
- Filter courses by **department**, **course number**, **professor name**, and **GE area**
- Each result card shows:
  - Course name, quarter, and year
  - Bar chart of grade distribution (A/B/C/D/F) with **real student counts** including +/− grades
  - Total enrolled (`n=X`) per section
  - Avg GPA badge (EASY / CHILL / STRESSFUL)
  - GE area pills (cyan) for any GE requirements the course satisfies
  - RMP badge if RateMyProfessors data is available
- Click **STATS** to open a full course stats card with historical GPA trends and detailed distributions
- Click a professor name (with RMP badge) to open their full RMP profile + GPA history across all courses

### My Quarter
- Upload a screenshot of your UCSB GOLD schedule
- Instantly see GPA breakdowns and insights for your enrolled courses

### ML Insights
- **GPA Forecast** — Linear regression on historical GPA per course, forecasting the next 3 quarters
- **Prof-Course Fit** — Rates how a professor grades a specific course relative to their own overall average
- **Grade Anomalies** — KL-divergence anomaly detection to flag unusual grade distributions
- **Teaching Style Clusters** — KMeans clustering of professors by their RMP student tags
- **Similar Courses** — Cosine similarity across grade distributions to find courses with comparable workload/difficulty

---

## Data Files

Place all data files in the **root directory** or a `data/` subfolder.

| File | Required | Description |
|---|---|---|
| `courseGrades.csv` |  Yes | Historical UCSB grade data by course/instructor/quarter |
| `rmp_final_data.csv` | Optional | RateMyProfessors scraped data for prof ratings |
| `ges_long_form.csv` | Optional | GE area mappings (long form: `Category`, `Course` columns) |
| `ges.csv` | Optional | GE area mappings (wide form: `Course` + one column per GE area) |

### courseGrades.csv columns

| Column | Description |
|---|---|
| `course` | Course identifier (e.g. `CMPSC 24`) |
| `instructor` | Instructor last name, first initial |
| `quarter` | Quarter (Fall / Winter / Spring / Summer) |
| `year` | Academic year |
| `A`, `B`, `C`, `D`, `F` | Count of students receiving each exact letter grade |
| `Ap`, `Am`, `Bp`, `Bm`, `Cp`, `Cm`, `Dp`, `Dm` | Plus/minus sub-grade counts |
| `nLetterStudents` | Total students graded on a letter scale (authoritative enrollment count) |
| `avgGPA` | Average GPA for the section |
| `dept` | Department code |

> **Note on grade counts:** The `A`–`F` columns only include *exact* letter grades (no +/−). The bar charts use the full letter-tier totals (e.g. A = A + A+ + A−) so the counts match `nLetterStudents`. Small class sizes on some cards (especially summer sections) are accurate — summer sections genuinely run with 10–30 students.

---

## Setup & Running Locally

### Prerequisites
- Python 3.10+
- pip

### Install dependencies

```bash
pip install streamlit pandas plotly scikit-learn scipy
```

### Run

```bash
streamlit run main_app.py
```

Then open `http://localhost:8501` in your browser.

### File structure

```
gaucho-insights/
├── main_app.py
├── courseGrades.csv        # or data/courseGrades.csv
├── rmp_final_data.csv      # optional
├── ges_long_form.csv       # optional
├── ges.csv                 # optional
└── README.md
```

---

## Deploying to Streamlit Cloud

1. Push your repo to GitHub (keep data files in the repo or use `st.secrets` for private data)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Select your repo, branch, and `main_app.py` as the entry point
4. Deploy — no extra config needed

---

## Tech Stack

| Layer | Tools |
|---|---|
| Frontend | Streamlit, custom CSS (Orbitron + Rajdhani fonts), SVG charts |
| Visualization | Plotly (interactive charts), inline SVG (bar chart cards) |
| ML | scikit-learn (LinearRegression, KMeans, cosine_similarity), scipy (KL divergence) |
| Data | pandas, UCSB grade data (public records) |
| Hosting | Streamlit Community Cloud |

---

## ML Methods

| Feature | Method | Input | Output |
|---|---|---|---|
| GPA Forecast | Linear Regression (sklearn) | Historical avg GPA per quarter | Next 3 quarter forecast + R² |
| Prof-Course Fit | Z-score vs prof baseline | Per-section GPA | Fit score in σ units |
| Grade Anomalies | KL Divergence | Grade distribution vector | Anomaly score per section |
| Teaching Clusters | KMeans on TF-IDF of RMP tags | Tag text per professor | Cluster label + top terms |
| Similar Courses | Cosine Similarity | Grade distribution vector | Top-N similar courses |

---

## Known Limitations

- Grade data is sourced from public UCSB records — some older quarters may have incomplete +/− breakdowns
- RMP matching is fuzzy (last name + first initial) — a small number of professors may be mismatched
- GE data covers courses that have been formally approved; newly approved GEs may not appear until the data file is updated
- ML features require sufficient historical data (≥4 data points for forecasting, ≥3 sections for anomaly detection)

---

## About

Built by **Josh Chung** — Statistics & Data Science, UCSB Class of 2027.

-  joshuachung@ucsb.edu
-  [linkedin.com/in/joshua-chung858](https://linkedin.com/in/joshua-chung858)
-  [github.com/josh11100](https://github.com/josh11100)