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
  AND avgGPA < 3.9          -- Filter out individual 4.0 entries
GROUP BY course
HAVING COUNT(*) > 3         -- Must have been taught at least 3 times
   AND mean_gpa < 4.0       -- Double check the final average isn't 4.0
ORDER BY mean_gpa DESC
LIMIT 10;
"""


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
