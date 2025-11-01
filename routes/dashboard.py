"""Dashboard routes"""
from flask import Blueprint, render_template, jsonify, session
from database.db_manager import DatabaseManager
from config import Config
from utils.auth_helpers import login_required

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Display main dashboard"""
    return render_template('dashboard.html')


@dashboard_bp.route('/api/dashboard/upcoming')
@login_required
def get_upcoming_sessions():
    """Get upcoming sessions for logged-in user"""
    user_id = session.get('user_id')
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        query = """
            SELECT 
                ss.session_id,
                ss.session_date,
                ss.start_time,
                ss.end_time,
                ss.status,
                ss.max_participants,
                sub.subject_name,
                sub.subject_code,
                l.building,
                l.room_number,
                COUNT(sp.student_id) as participant_count
            FROM STUDY_SESSION ss
            JOIN SESSION_SUBJECT ssub ON ss.session_id = ssub.session_id
            JOIN SUBJECT sub ON ssub.subject_id = sub.subject_id
            LEFT JOIN LOCATION l ON ss.location_id = l.location_id
            LEFT JOIN SESSION_PARTICIPANT sp ON ss.session_id = sp.session_id
            WHERE ss.session_id IN (
                SELECT session_id FROM SESSION_PARTICIPANT WHERE student_id = %s
            )
            AND ss.session_date >= CURDATE()
            AND ss.status IN ('Planned', 'Active')
            GROUP BY ss.session_id, ss.session_date, ss.start_time, ss.end_time, 
                     ss.status, ss.max_participants, sub.subject_name, sub.subject_code, 
                     l.building, l.room_number
            ORDER BY ss.session_date, ss.start_time
            LIMIT 3
        """
        sessions = db.execute_query(query, (user_id,))
        
        return jsonify({'success': True, 'data': sessions})


@dashboard_bp.route('/api/dashboard/stats')
@login_required
def get_stats():
    """Get quick stats for dashboard"""
    user_id = session.get('user_id')
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        # Total sessions attended
        query_total = """
            SELECT COUNT(*) as total
            FROM SESSION_PARTICIPANT sp
            JOIN STUDY_SESSION ss ON sp.session_id = ss.session_id
            WHERE sp.student_id = %s AND ss.status = 'Completed'
        """
        total_result = db.execute_query(query_total, (user_id,))
        total_sessions = total_result[0]['total'] if total_result else 0
        
        # Average effectiveness rating
        query_effectiveness = """
            SELECT AVG(so.effectiveness_rating) as avg_effectiveness
            FROM SESSION_OUTCOME so
            JOIN STUDY_SESSION ss ON so.session_id = ss.session_id
            JOIN SESSION_PARTICIPANT sp ON ss.session_id = sp.session_id
            WHERE sp.student_id = %s
        """
        effectiveness_result = db.execute_query(query_effectiveness, (user_id,))
        avg_effectiveness = effectiveness_result[0]['avg_effectiveness'] if effectiveness_result and effectiveness_result[0]['avg_effectiveness'] else 0
        
        # Upcoming sessions count
        query_upcoming = """
            SELECT COUNT(*) as upcoming
            FROM SESSION_PARTICIPANT sp
            JOIN STUDY_SESSION ss ON sp.session_id = ss.session_id
            WHERE sp.student_id = %s 
            AND ss.session_date >= CURDATE()
            AND ss.status IN ('Planned', 'Active')
        """
        upcoming_result = db.execute_query(query_upcoming, (user_id,))
        upcoming_sessions = upcoming_result[0]['upcoming'] if upcoming_result else 0
        
        return jsonify({
            'success': True,
            'data': {
                'total_sessions': total_sessions,
                'avg_effectiveness': round(float(avg_effectiveness), 2) if avg_effectiveness else 0,
                'upcoming_sessions': upcoming_sessions
            }
        })


@dashboard_bp.route('/api/dashboard/notifications')
@login_required
def get_recent_notifications():
    """Get recent notifications"""
    user_id = session.get('user_id')
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        query = """
            SELECT 
                n.notification_id,
                n.notification_type,
                n.message,
                n.read_status,
                n.sent_date
            FROM NOTIFICATION n
            WHERE n.student_id = %s
            ORDER BY n.sent_date DESC
            LIMIT 5
        """
        notifications = db.execute_query(query, (user_id,))
        
        return jsonify({'success': True, 'data': notifications})


@dashboard_bp.route('/api/dashboard/invitations')
@login_required
def get_pending_invitations():
    """Get pending session invitations (sessions user hasn't joined yet)"""
    user_id = session.get('user_id')
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        # Get notifications about session invites that user hasn't responded to
        query = """
            SELECT 
                n.notification_id,
                n.related_session_id as session_id,
                n.message,
                n.sent_date,
                ss.session_date,
                ss.start_time,
                ss.end_time,
                sub.subject_name,
                sub.subject_code,
                l.building,
                l.room_number,
                COUNT(sp.student_id) as participant_count,
                ss.max_participants
            FROM NOTIFICATION n
            JOIN STUDY_SESSION ss ON n.related_session_id = ss.session_id
            JOIN SESSION_SUBJECT ssub ON ss.session_id = ssub.session_id
            JOIN SUBJECT sub ON ssub.subject_id = sub.subject_id
            LEFT JOIN LOCATION l ON ss.location_id = l.location_id
            LEFT JOIN SESSION_PARTICIPANT sp ON ss.session_id = sp.session_id
            WHERE n.student_id = %s
            AND n.notification_type = 'Session Invite'
            AND n.read_status = 0
            AND ss.session_date >= CURDATE()
            AND ss.status = 'Planned'
            AND NOT EXISTS (
                SELECT 1 FROM SESSION_PARTICIPANT 
                WHERE session_id = ss.session_id AND student_id = %s
            )
            GROUP BY n.notification_id, n.related_session_id, n.message, n.sent_date,
                     ss.session_date, ss.start_time, ss.end_time, sub.subject_name,
                     sub.subject_code, l.building, l.room_number, ss.max_participants
            ORDER BY n.sent_date DESC
            LIMIT 5
        """
        invitations = db.execute_query(query, (user_id, user_id))
        
        return jsonify({'success': True, 'data': invitations or []})
