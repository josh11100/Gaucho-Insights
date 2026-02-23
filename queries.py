GET_RECENT_LECTURES = """
SELECT * FROM courses 
WHERE course_num < 198 
ORDER BY q_year DESC, q_rank DESC;
"""

# You can add more queries here as you learn!
GET_EASIEST_CLASSES = """
SELECT course, AVG(avgGPA) as mean_gpa
FROM courses
GROUP BY course
ORDER BY mean_gpa DESC
LIMIT 10;
"""
