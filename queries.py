# queries.py

# --- QUERY 1: THE MAIN TABLE ---
# Chronological sort: Newest years and Fall quarters at the top.
GET_RECENT_LECTURES = """
SELECT * FROM courses 
WHERE course_num < 198 
ORDER BY q_year DESC, q_rank DESC;
"""

# --- QUERY 2: ALL UNDERGRAD HALL OF FAME ---
# Filters out 4.0s and requires at least 4 instances (COUNT > 3).
GET_EASIEST_CLASSES = """
SELECT 
    course, 
    ROUND(AVG(avgGPA), 2) as mean_gpa
FROM courses
WHERE course_num < 198 
  AND avgGPA < 4.0
GROUP BY course
HAVING COUNT(*) > 3
ORDER BY mean_gpa DESC
LIMIT 10;
"""

# --- QUERY 3: LOWER DIV HALL OF FAME (< 98) ---
# Specifically targets classes under 98 (Introductory/GE level).
GET_EASIEST_LOWER_DIV = """
SELECT 
    course, 
    ROUND(AVG(avgGPA), 2) as mean_gpa
FROM courses
WHERE course_num < 98 
  AND avgGPA < 4.0
GROUP BY course
HAVING COUNT(*) > 3
ORDER BY mean_gpa DESC
LIMIT 10;
"""

GET_EASIEST_DEPTS = """
SELECT 
    dept, 
    ROUND(AVG(avgGPA), 2) as dept_avg_gpa,
    COUNT(*) as total_records
FROM courses
WHERE course_num < 198 
  AND avgGPA < 4.0
GROUP BY dept
HAVING total_records > 20  -- Ensures we only show departments with enough data
ORDER BY dept_avg_gpa DESC
LIMIT 5;
"""
