# queries.py

# --- QUERY 1: THE MAIN TABLE ---
GET_RECENT_LECTURES = """
SELECT * FROM courses 
WHERE course_num < 198 
ORDER BY q_year DESC, q_rank DESC;
"""

# --- QUERY 2: LOWER DIV HALL OF FAME (< 100) ---
# Focuses on GEs and introductory courses.
GET_EASIEST_LOWER_DIV = """
SELECT 
    course, 
    ROUND(AVG(avgGPA), 2) as mean_gpa
FROM courses
WHERE course_num < 100 
  AND avgGPA < 4.0
GROUP BY course
HAVING COUNT(*) > 3
ORDER BY mean_gpa DESC
LIMIT 10;
"""

# --- QUERY 3: UPPER DIV HALL OF FAME (100 - 197) ---
# Focuses on major-specific requirements.
GET_EASIEST_UPPER_DIV = """
SELECT 
    course, 
    ROUND(AVG(avgGPA), 2) as mean_gpa
FROM courses
WHERE course_num >= 100 AND course_num < 198
  AND avgGPA < 4.0
GROUP BY course
HAVING COUNT(*) > 3
ORDER BY mean_gpa DESC
LIMIT 10;
"""

# --- QUERY 4: EASIEST DEPARTMENTS ---
GET_EASIEST_DEPTS = """
SELECT 
    dept, 
    ROUND(AVG(avgGPA), 2) as dept_avg_gpa,
    COUNT(*) as total_records
FROM courses
WHERE course_num < 198 
  AND avgGPA < 4.0
GROUP BY dept
HAVING total_records > 20
ORDER BY dept_avg_gpa DESC
LIMIT 5;
"""
