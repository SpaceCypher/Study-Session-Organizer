"""
Database Schema Reference - Actual table and column names
Use this for reference when writing queries
"""

# TABLE NAMES (all uppercase with underscores)
TABLES = {
    'student': 'STUDENT',
    'study_session': 'STUDY_SESSION',
    'session_participant': 'SESSION_PARTICIPANT',
    'subject': 'SUBJECT',
    'location': 'LOCATION',
    'notification': 'NOTIFICATION',
    'session_outcome': 'SESSION_OUTCOME',
    'compatibility_score': 'COMPATIBILITY_SCORE',
    'availability': 'AVAILABILITY',
    'student_subject': 'STUDENT_SUBJECT',
    'session_subject': 'SESSION_SUBJECT',
    'location_facilities': 'LOCATION_FACILITIES'
}

# COLUMN NAMES (all lowercase with underscores)
COLUMNS = {
    'STUDENT': ['student_id', 'name', 'email', 'phone', 'major', 'year', 'gpa', 
                'learning_style', 'personality_type', 'enrollment_id', 'needs_help', 
                'can_teach', 'created_date', 'last_active', 'password'],
    
    'STUDY_SESSION': ['session_id', 'created_by', 'location_id', 'session_date', 
                      'start_time', 'end_time', 'max_participants', 'status', 
                      'description', 'created_date'],
    
    'SESSION_SUBJECT': ['session_id', 'subject_id', 'coverage_id', 'time_allocated', 
                        'focus_level', 'topics_covered'],
    
    'SESSION_PARTICIPANT': ['participant_id', 'session_id', 'student_id', 'role', 'joined_date'],
    
    'SUBJECT': ['subject_id', 'subject_name', 'subject_code', 'department', 'credit_hours', 'difficulty_level', 'description'],
    
    'LOCATION': ['location_id', 'building', 'room_number', 'capacity', 'accessibility', 'available_hours'],
    
    'NOTIFICATION': ['notification_id', 'student_id', 'notification_type', 'message', 
                     'sent_date', 'read_status', 'read_date', 'delivered_date', 'related_session_id']
}

# STORED PROCEDURES
PROCEDURES = [
    'CreateStudySession',
    'FindStudyPartners',
    'GenerateSessionAnalytics',
    'JoinStudySession',
    'UpdateCompatibilityScores'
]

# FUNCTIONS (actual database names - case-sensitive)
FUNCTIONS = [
    'CALCULATE_COMPATIBILITY',  # Used in profile compatibility calculations
    'CheckAvailability',
    'OptimizeGroupSize',
    'PredictSuccessRate',
    'FindOptimalLocation'
]
