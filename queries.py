# queries.py

# Query using actual SQLite syntax
GET_RECENT_LECTURES = """
SELECT * FROM courses 
WHERE course_num < 198 
ORDER BY q_year DESC, q_rank DESC;
"""
