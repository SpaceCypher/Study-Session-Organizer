"""Wrappers for stored procedures"""
from database.db_manager import DatabaseManager


def find_study_partners(db: DatabaseManager, student_id, subject_id, session_date, start_time, duration):
    """
    Find compatible study partners
    Calls: FindStudyPartners(studentid, subjectid, sessiondate, starttime, duration)
    Returns: List of compatible partners with scores > 0.60
    """
    results, _ = db.call_procedure('FindStudyPartners', [student_id, subject_id, session_date, start_time, duration])
    return results[0] if results else []


def create_study_session(db: DatabaseManager, student_id, subject_id, date, start_time, end_time, max_participants, description):
    """
    Create new study session
    Calls: CreateStudySession(studentid, subjectid, date, start, end, maxparticipants, description, OUT sessionid)
    Returns: New session ID
    """
    # OUT parameter needs to be passed as 0 initially
    args = [student_id, subject_id, date, start_time, end_time, max_participants, description, 0]
    results, out_params = db.call_procedure('CreateStudySession', args)
    
    # The last parameter is the OUT parameter (session_id)
    new_session_id = out_params[-1]
    return new_session_id


def join_study_session(db: DatabaseManager, session_id, student_id):
    """
    Join a study session
    Calls: JoinStudySession(sessionid, studentid)
    """
    results, _ = db.call_procedure('JoinStudySession', [session_id, student_id])
    return True


def update_compatibility_scores(db: DatabaseManager):
    """
    Recalculate all compatibility scores
    Calls: UpdateCompatibilityScores()
    """
    results, _ = db.call_procedure('UpdateCompatibilityScores', [])
    return True


def generate_session_analytics(db: DatabaseManager, student_id):
    """
    Generate analytics for a student
    Calls: GenerateSessionAnalytics(studentid)
    Returns: Tuple of (overall_stats, subject_performance, frequent_partners)
    """
    results, _ = db.call_procedure('GenerateSessionAnalytics', [student_id])
    
    # Returns 3 result sets
    overall_stats = results[0] if len(results) > 0 else []
    subject_performance = results[1] if len(results) > 1 else []
    frequent_partners = results[2] if len(results) > 2 else []
    
    return overall_stats, subject_performance, frequent_partners
