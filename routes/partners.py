"""Partner finder routes"""
from flask import Blueprint, render_template, jsonify, session, request
from database.db_manager import DatabaseManager
from database import procedures
from config import Config
from utils.auth_helpers import login_required
from utils import validators

partners_bp = Blueprint('partners', __name__)


@partners_bp.route('/partners/find')
@login_required
def find():
    """Display find partners page"""
    return render_template('partners/find.html')


@partners_bp.route('/api/partners/find', methods=['POST'])
@login_required
def find_partners():
    """Find compatible study partners"""
    user_id = session.get('user_id')
    data = request.get_json()
    
    subject_id = data.get('subject_id')
    date = data.get('date')
    start_time = data.get('start_time')
    duration = data.get('duration', 2)  # Default 2 hours
    
    # Validation
    errors = []
    if not subject_id:
        errors.append('Subject is required')
    if not date or not validators.validate_date(date):
        errors.append('Valid date is required')
    if not start_time or not validators.validate_time(start_time):
        errors.append('Valid start time is required')
    
    if errors:
        return jsonify({'success': False, 'message': '; '.join(errors)}), 400
    
    # Call FindStudyPartners stored procedure
    with DatabaseManager(Config.DB_CONFIG) as db:
        try:
            partners = procedures.find_study_partners(
                db, user_id, subject_id, date, start_time, duration
            )
            
            return jsonify({
                'success': True,
                'data': partners
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500


@partners_bp.route('/api/partners/invite', methods=['POST'])
@login_required
def invite_partner():
    """Send invitation to a partner to create a study session together"""
    user_id = session.get('user_id')
    data = request.get_json()
    
    partner_id = data.get('partner_id')
    subject_id = data.get('subject_id')
    session_date = data.get('date')
    start_time = data.get('start_time')
    message = data.get('message', '')
    
    # Validation
    if not partner_id or not subject_id or not session_date or not start_time:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        try:
            # Get sender and receiver info
            sender = db.execute_query(
                "SELECT name, email FROM STUDENT WHERE student_id = %s",
                (user_id,)
            )
            
            partner = db.execute_query(
                "SELECT name, email FROM STUDENT WHERE student_id = %s",
                (partner_id,)
            )
            
            subject = db.execute_query(
                "SELECT subject_name FROM SUBJECT WHERE subject_id = %s",
                (subject_id,)
            )
            
            if not sender or not partner or not subject:
                return jsonify({'success': False, 'message': 'Invalid user or subject'}), 400
            
            # Calculate end time (add 1 hour by default)
            from datetime import datetime, timedelta
            start_dt = datetime.strptime(start_time, '%H:%M')
            end_dt = start_dt + timedelta(hours=1)
            end_time = end_dt.strftime('%H:%M:%S')
            
            # Create the study session first
            session_query = """
                INSERT INTO STUDY_SESSION 
                (created_by, location_id, session_date, start_time, end_time, max_participants, status, description, created_date)
                VALUES (%s, NULL, %s, %s, %s, 6, 'Planned', %s, NOW())
            """
            
            description = f"Study session organized by {sender[0]['name']}"
            if message:
                description += f". {message}"
            
            db.execute_update(session_query, (user_id, session_date, start_time, end_time, description))
            
            # Get the newly created session ID
            session_id_result = db.execute_query("SELECT LAST_INSERT_ID() as session_id")
            new_session_id = session_id_result[0]['session_id']
            
            # Link the subject to the session
            db.execute_update(
                "INSERT INTO SESSION_SUBJECT (session_id, subject_id) VALUES (%s, %s)",
                (new_session_id, subject_id)
            )
            
            # Add the creator as a participant
            db.execute_update(
                "INSERT INTO SESSION_PARTICIPANT (session_id, student_id, role, join_date, attendance_status) VALUES (%s, %s, 'Organizer', NOW(), 'Registered')",
                (new_session_id, user_id)
            )
            
            # Create notification message with link to the session
            notification_message = f"{sender[0]['name']} invited you to study {subject[0]['subject_name']} on {session_date} at {start_time}"
            if message:
                notification_message += f". Message: {message}"
            
            # Insert notification with the session ID
            insert_query = """
                INSERT INTO NOTIFICATION 
                (student_id, notification_type, message, sent_date, read_status, related_session_id)
                VALUES (%s, 'Session Invite', %s, NOW(), 0, %s)
            """
            
            db.execute_update(insert_query, (partner_id, notification_message, new_session_id))
            
            return jsonify({
                'success': True,
                'message': f'Study session created and invitation sent to {partner[0]["name"]}!',
                'session_id': new_session_id
            })
            
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
