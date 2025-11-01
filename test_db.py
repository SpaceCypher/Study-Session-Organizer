"""Test database connectivity"""
from database.db_manager import DatabaseManager
from config import Config

def test_connection():
    """Test MySQL database connection"""
    print("Testing database connection...")
    print(f"Host: {Config.DB_CONFIG['host']}")
    print(f"User: {Config.DB_CONFIG['user']}")
    print(f"Database: {Config.DB_CONFIG['database']}")
    print("-" * 50)
    
    try:
        with DatabaseManager(Config.DB_CONFIG) as db:
            # Test basic query
            result = db.execute_query("SELECT 1 as test")
            print("✅ Connection successful!")
            print(f"Test query result: {result}")
            
            # Check if STUDENT table exists
            tables = db.execute_query("SHOW TABLES")
            print(f"\n✅ Found {len(tables)} tables in database:")
            for table in tables:
                print(f"  - {list(table.values())[0]}")
            
            # Try to count students
            student_count = db.execute_query("SELECT COUNT(*) as count FROM STUDENT")
            print(f"\n✅ Current student count: {student_count[0]['count']}")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Connection failed!")
        print(f"Error: {str(e)}")
        print("\nPlease check:")
        print("1. MySQL server is running")
        print("2. Database 'study_session_organizer' exists")
        print("3. Username and password are correct in .env file")
        print("4. All tables from schema are created")
        return False

if __name__ == '__main__':
    test_connection()
