# queries.py

GET_RECENT_LECTURES = """
SELECT * FROM courses 
WHERE course_num < 198 
ORDER BY q_year DESC, q_rank DESC;
"""

GET_EASIEST_LOWER_DIV = """
SELECT course, ROUND(AVG(avgGPA), 2) as mean_gpa
FROM courses WHERE course_num < 100 AND avgGPA < 4.0
GROUP BY course HAVING COUNT(*) > 3
ORDER BY mean_gpa DESC LIMIT 10;
"""

GET_EASIEST_UPPER_DIV = """
SELECT course, ROUND(AVG(avgGPA), 2) as mean_gpa
FROM courses WHERE course_num >= 100 AND course_num < 198 AND avgGPA < 4.0
GROUP BY course HAVING COUNT(*) > 3
ORDER BY mean_gpa DESC LIMIT 10;
"""

GET_EASIEST_DEPTS = """
SELECT dept, ROUND(AVG(avgGPA), 2) as dept_avg_gpa, COUNT(*) as total_records
FROM courses WHERE course_num < 198 AND avgGPA < 4.0
GROUP BY dept HAVING total_records > 20
ORDER BY dept_avg_gpa DESC LIMIT 5;
"""

GET_BEST_GE_PROFS = """
SELECT instructor, ROUND(AVG(avgGPA), 2) as avg_instructor_gpa, COUNT(*) as classes_taught
FROM courses WHERE course_num < 100 AND avgGPA < 4.0
GROUP BY instructor HAVING classes_taught >= 3
ORDER BY avg_instructor_gpa DESC LIMIT 10;
"""
