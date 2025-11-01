"""Test user registration"""
from database.db_manager import DatabaseManager
from config import Config

# Insert a test student
db = DatabaseManager(Config.DB_CONFIG)
db.connect()

# Check if student exists
check = db.execute_query('SELECT * FROM STUDENT WHERE email = %s', ('test@example.com',))
if check:
    print('✅ Test student already exists')
    print(f"   ID: {check[0]['student_id']}")
    print(f"   Name: {check[0]['name']}")
    print(f"   Email: {check[0]['email']}")
else:
    # Insert test student
    result = db.execute_update('''
        INSERT INTO STUDENT (name, email, phone, password, major, year, gpa, learning_style, personality_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', ('Test User', 'test@example.com', '1234567890', 'password123', 'Computer Science', 2, 3.5, 'Visual', 'Ambivert'))
    print(f'✅ Test student created with ID: {result["last_id"]}')
    print(f'   Email: test@example.com')
    print(f'   Password: password123')

db.close()
