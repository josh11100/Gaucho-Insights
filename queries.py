# queries.py

# Query to get standard undergraduate classes sorted by newest year first
GET_RECENT_LECTURES = """
SELECT * FROM df 
WHERE course_num < 198 
ORDER BY q_year DESC, q_rank DESC
"""

# Example for later
GET_TOP_PROFS = """
SELECT instructor, AVG(avgGPA) as mean_gpa
FROM df
GROUP BY instructor
HAVING COUNT(*) > 5
ORDER BY mean_gpa DESC
LIMIT 10
"""
