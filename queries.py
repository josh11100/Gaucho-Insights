# queries.py

# --- QUERY 1: THE MAIN TABLE ---
# This query handles the chronological sorting.
# DESC (Descending) ensures 2024 comes before 2023.
GET_RECENT_LECTURES = """
SELECT * FROM courses 
WHERE course_num < 198 
ORDER BY q_year DESC, q_rank DESC;
"""

# --- QUERY 2: THE HALL OF FAME ---
# This query calculates the average GPA for every unique course.
# It filters out 198+ classes to keep the results realistic.
# queries.py

GET_EASIEST_CLASSES = """
SELECT 
    course, 
    ROUND(AVG(avgGPA), 2) as mean_gpa
FROM courses
WHERE course_num < 198 
  AND avgGPA < 4.0        -- <--- Filter out the unrealistic 4.0s
GROUP BY course
HAVING COUNT(*) > 3      -- Must have been taught at least 3 times
ORDER BY mean_gpa DESC
LIMIT 10;
"""

# --- OPTIONAL QUERY 3: TOP PROFESSORS ---
# You can use this later if you want to add a 'Best Professors' section
GET_TOP_PROFS = """
SELECT 
    instructor, 
    ROUND(AVG(avgGPA), 2) as avg_gpa,
    COUNT(*) as total_quarters
FROM courses
WHERE course_num < 198
GROUP BY instructor
HAVING total_quarters > 5
ORDER BY avg_gpa DESC
LIMIT 10;
"""
