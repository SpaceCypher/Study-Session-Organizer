"""Session management routes"""
from flask import Blueprint, render_template, jsonify, session, request
from database.db_manager import DatabaseManager
from database import procedures
from config import Config
from utils.auth_helpers import login_required
from utils import validators

sessions_bp = Blueprint('sessions', __name__)


@sessions_bp.route('/sessions/browse')
@login_required
def browse():
    """Display browse sessions page"""
    return render_template('sessions/browse.html')


@sessions_bp.route('/sessions/create')
@login_required
def create():
    """Display create session page"""
    return render_template('sessions/create.html')


@sessions_bp.route('/sessions/<int:session_id>')
@login_required
def detail(session_id):
    """Display session detail page"""
    return render_template('sessions/detail.html', session_id=session_id)


@sessions_bp.route('/sessions/my-sessions')
@login_required
def my_sessions():
    """Display user's sessions page"""
    return render_template('sessions/my_sessions.html')


@sessions_bp.route('/api/sessions/my-sessions')
@login_required
def get_my_sessions():
    """Get current user's sessions with optional status filter"""
    user_id = session.get('user_id')
    status_filter = request.args.get('status', '')
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        query = """
            SELECT 
                ss.session_id,
                ss.session_date,
                ss.start_time,
                ss.end_time,
                ss.status,
                ss.description,
                ss.max_participants,
                ss.created_by,
                sub.subject_name,
                sub.subject_code,
                l.building,
                l.room_number,
                sp.role,
                COUNT(DISTINCT sp2.student_id) as participant_count,
                (SELECT COUNT(*) FROM SESSION_OUTCOME so 
                 WHERE so.session_id = ss.session_id AND so.student_id = %s) as has_feedback
            FROM SESSION_PARTICIPANT sp
            JOIN STUDY_SESSION ss ON sp.session_id = ss.session_id
            JOIN SESSION_SUBJECT ssub ON ss.session_id = ssub.session_id
            JOIN SUBJECT sub ON ssub.subject_id = sub.subject_id
            LEFT JOIN LOCATION l ON ss.location_id = l.location_id
            LEFT JOIN SESSION_PARTICIPANT sp2 ON ss.session_id = sp2.session_id
            WHERE sp.student_id = %s
        """
        
        params = [user_id, user_id]
        
        if status_filter:
            statuses = status_filter.split(',')
            placeholders = ','.join(['%s'] * len(statuses))
            query += f" AND ss.status IN ({placeholders})"
            params.extend(statuses)
        
        query += """
            GROUP BY ss.session_id, ss.session_date, ss.start_time, ss.end_time, 
                     ss.status, ss.description, ss.max_participants, ss.created_by,
                     sub.subject_name, sub.subject_code, l.building, l.room_number, sp.role
            ORDER BY ss.session_date DESC, ss.start_time DESC
        """
        
        sessions = db.execute_query(query, tuple(params))
        
        return jsonify({'success': True, 'data': sessions})


# API Routes

@sessions_bp.route('/api/sessions')
@login_required
def get_sessions():
    """Get all sessions with optional filters"""
    subject_id = request.args.get('subject_id')
    status = request.args.get('status')
    date = request.args.get('date')
    search = request.args.get('search', '')
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        query = """
            SELECT 
                ss.session_id,
                ss.session_date,
                ss.start_time,
                ss.end_time,
                ss.status,
                ss.description,
                ss.max_participants,
                sub.subject_name,
                sub.subject_code,
                l.building,
                l.room_number,
                s.name as creator_name,
                COUNT(sp.student_id) as participant_count
            FROM STUDY_SESSION ss
            JOIN SESSION_SUBJECT ssub ON ss.session_id = ssub.session_id
            JOIN SUBJECT sub ON ssub.subject_id = sub.subject_id
            LEFT JOIN LOCATION l ON ss.location_id = l.location_id
            JOIN STUDENT s ON ss.created_by = s.student_id
            LEFT JOIN SESSION_PARTICIPANT sp ON ss.session_id = sp.session_id
            WHERE ss.status != 'Cancelled'
        """
        params = []
        
        if subject_id:
            query += " AND sub.subject_id = %s"
            params.append(subject_id)
        
        if status:
            query += " AND ss.status = %s"
            params.append(status)
        
        if date:
            query += " AND ss.session_date = %s"
            params.append(date)
        
        if search:
            query += " AND (ss.description LIKE %s OR sub.subject_name LIKE %s OR s.name LIKE %s)"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        
        query += """
            GROUP BY ss.session_id, ss.session_date, ss.start_time, ss.end_time, 
                     ss.status, ss.description, ss.max_participants, sub.subject_name, 
                     sub.subject_code, l.building, l.room_number, s.name
            ORDER BY ss.session_date ASC, ss.start_time ASC
            LIMIT 50
        """
        
        sessions = db.execute_query(query, tuple(params))
        
        return jsonify({'success': True, 'data': sessions})


@sessions_bp.route('/api/sessions/<int:session_id>')
@login_required
def get_session_detail(session_id):
    """Get detailed session information"""
    user_id = session.get('user_id')
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        # Get session details
        query_session = """
            SELECT 
                ss.session_id,
                ss.created_by,
                ss.location_id,
                ss.session_date,
                ss.start_time,
                ss.end_time,
                ss.max_participants,
                ss.status,
                ss.description,
                ss.created_date,
                sub.subject_name,
                sub.subject_code,
                l.building,
                l.room_number,
                l.capacity,
                s.student_id as creator_id,
                s.name as creator_name,
                s.major as creator_major,
                s.year as creator_year,
                s.gpa as creator_gpa,
                COUNT(sp.student_id) as participant_count
            FROM STUDY_SESSION ss
            JOIN SESSION_SUBJECT ssub ON ss.session_id = ssub.session_id
            JOIN SUBJECT sub ON ssub.subject_id = sub.subject_id
            LEFT JOIN LOCATION l ON ss.location_id = l.location_id
            JOIN STUDENT s ON ss.created_by = s.student_id
            LEFT JOIN SESSION_PARTICIPANT sp ON ss.session_id = sp.session_id
            WHERE ss.session_id = %s
            GROUP BY ss.session_id, ss.created_by, ss.location_id, ss.session_date, 
                     ss.start_time, ss.end_time, ss.max_participants, ss.status, 
                     ss.description, ss.created_date, sub.subject_name, sub.subject_code, 
                     l.building, l.room_number, l.capacity, s.student_id, s.name, 
                     s.major, s.year, s.gpa
        """
        session_result = db.execute_query(query_session, (session_id,))
        
        if not session_result:
            return jsonify({'success': False, 'message': 'Session not found'}), 404
        
        session_data = session_result[0]
        
        # Get participants with compatibility scores
        query_participants = """
            SELECT 
                s.student_id,
                s.name,
                s.major,
                s.year,
                s.gpa,
                sp.role
            FROM SESSION_PARTICIPANT sp
            JOIN STUDENT s ON sp.student_id = s.student_id
            WHERE sp.session_id = %s
        """
        participants = db.execute_query(query_participants, (session_id,))
        
        # Check if current user is participant
        is_participant = any(p['student_id'] == user_id for p in participants)
        is_creator = session_data['creator_id'] == user_id
        
        session_data['participants'] = participants
        session_data['is_participant'] = is_participant
        session_data['is_creator'] = is_creator
        
        return jsonify({'success': True, 'data': session_data})


@sessions_bp.route('/api/sessions/create', methods=['POST'])
@login_required
def create_session():
    """Create new study session"""
    user_id = session.get('user_id')
    data = request.get_json()
    
    # Extract and validate data
    subject_id = data.get('subject_id')
    date = data.get('date')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    max_participants = data.get('max_participants')
    description = data.get('description', '')
    location_id = data.get('location_id')
    
    # Validation
    errors = []
    if not subject_id:
        errors.append('Subject is required')
    if not date or not validators.validate_date(date):
        errors.append('Valid date is required')
    elif not validators.validate_future_date(date):
        errors.append('Session date cannot be in the past')
    if not start_time or not validators.validate_time(start_time):
        errors.append('Valid start time is required')
    if not end_time or not validators.validate_time(end_time):
        errors.append('Valid end time is required')
    elif validators.validate_time(start_time) and not validators.validate_time_range(start_time, end_time):
        errors.append('End time must be after start time')
    if not validators.validate_datetime_not_past(date, start_time) if (date and start_time) else False:
        errors.append('Session cannot be scheduled in the past')
    if not max_participants or not (2 <= int(max_participants) <= 15):
        errors.append('Max participants must be between 2 and 15')
    
    # Sanitize description
    description = validators.sanitize_input(description, max_length=1000)
    
    if errors:
        return jsonify({'success': False, 'message': '; '.join(errors)}), 400
    
    # Call CreateStudySession stored procedure
    with DatabaseManager(Config.DB_CONFIG) as db:
        try:
            new_session_id = procedures.create_study_session(
                db, user_id, subject_id, date, start_time, end_time, 
                max_participants, description
            )
            
            # Update location if provided
            if location_id:
                update_query = "UPDATE STUDY_SESSION SET location_id = %s WHERE session_id = %s"
                db.execute_update(update_query, (location_id, new_session_id))
            
            return jsonify({
                'success': True, 
                'message': 'Session created successfully',
                'data': {'session_id': new_session_id}
            })
        except Exception as e:
            print(f"ERROR creating session: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': f'Failed to create session: {str(e)}'}), 500


@sessions_bp.route('/sessions/<int:session_id>/edit', methods=['GET'])
@login_required
def edit_session_page(session_id):
    """Display edit session page"""
    return render_template('sessions/edit.html', session_id=session_id)


@sessions_bp.route('/api/sessions/<int:session_id>', methods=['PUT'])
@login_required
def update_session(session_id):
    """Update an existing study session"""
    user_id = session.get('user_id')
    data = request.get_json()
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        # Check if user is the creator
        check_query = "SELECT created_by, session_date, start_time, status FROM STUDY_SESSION WHERE session_id = %s"
        result = db.execute_query(check_query, (session_id,))
        
        if not result:
            return jsonify({'success': False, 'message': 'Session not found'}), 404
        
        if result[0]['created_by'] != user_id:
            return jsonify({'success': False, 'message': 'Only the organizer can edit this session'}), 403
        
        if result[0]['status'] not in ['Planned', 'Active']:
            return jsonify({'success': False, 'message': 'Cannot edit completed or cancelled sessions'}), 400
        
        # Extract and validate data
        subject_id = data.get('subject_id')
        date = data.get('date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        max_participants = data.get('max_participants')
        description = data.get('description', '')
        location_id = data.get('location_id')
        
        # Validation
        errors = []
        if subject_id is not None and not subject_id:
            errors.append('Subject is required')
        if date and not validators.validate_date(date):
            errors.append('Valid date is required')
        elif date and not validators.validate_future_date(date):
            errors.append('Session date cannot be in the past')
        if start_time and not validators.validate_time(start_time):
            errors.append('Valid start time is required')
        if end_time and not validators.validate_time(end_time):
            errors.append('Valid end time is required')
        elif start_time and end_time and not validators.validate_time_range(start_time, end_time):
            errors.append('End time must be after start time')
        if max_participants is not None and not (2 <= int(max_participants) <= 15):
            errors.append('Max participants must be between 2 and 15')
        
        if errors:
            return jsonify({'success': False, 'message': '; '.join(errors)}), 400
        
        # Sanitize description
        description = validators.sanitize_input(description, max_length=1000)
        
        # Update session
        try:
            update_fields = []
            params = []
            
            if date:
                update_fields.append("session_date = %s")
                params.append(date)
            if start_time:
                update_fields.append("start_time = %s")
                params.append(start_time)
            if end_time:
                update_fields.append("end_time = %s")
                params.append(end_time)
            if max_participants is not None:
                update_fields.append("max_participants = %s")
                params.append(max_participants)
            if description is not None:
                update_fields.append("description = %s")
                params.append(description)
            if location_id is not None:
                update_fields.append("location_id = %s")
                params.append(location_id if location_id else None)
            
            if update_fields:
                params.append(session_id)
                update_query = f"UPDATE STUDY_SESSION SET {', '.join(update_fields)} WHERE session_id = %s"
                db.execute_update(update_query, tuple(params))
            
            # Update subject if provided
            if subject_id:
                update_subject_query = "UPDATE SESSION_SUBJECT SET subject_id = %s WHERE session_id = %s"
                db.execute_update(update_subject_query, (subject_id, session_id))
            
            return jsonify({
                'success': True,
                'message': 'Session updated successfully'
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500


@sessions_bp.route('/api/sessions/<int:session_id>/join', methods=['POST'])
@login_required
def join_session(session_id):
    """Join a study session"""
    user_id = session.get('user_id')
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        try:
            # Call JoinStudySession stored procedure
            procedures.join_study_session(db, session_id, user_id)
            
            return jsonify({
                'success': True, 
                'message': 'Successfully joined session'
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500


@sessions_bp.route('/api/sessions/<int:session_id>/leave', methods=['POST', 'DELETE'])
@login_required
def leave_session(session_id):
    """Leave a study session"""
    user_id = session.get('user_id')
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        # Check if user is creator
        query_check = "SELECT created_by FROM STUDY_SESSION WHERE session_id = %s"
        result = db.execute_query(query_check, (session_id,))
        
        if result and result[0]['created_by'] == user_id:
            return jsonify({'success': False, 'message': 'Creator cannot leave session. Cancel it instead.'}), 400
        
        # Remove from session
        query_delete = """
            DELETE FROM SESSION_PARTICIPANT 
            WHERE session_id = %s AND student_id = %s
        """
        db.execute_update(query_delete, (session_id, user_id))
        
        return jsonify({'success': True, 'message': 'Successfully left session'})


@sessions_bp.route('/api/sessions/<int:session_id>/feedback', methods=['POST'])
@login_required
def submit_feedback(session_id):
    """Submit feedback for a completed session"""
    user_id = session.get('user_id')
    data = request.get_json()
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        # Check if user was a participant
        check_participant = """
            SELECT sp.student_id FROM SESSION_PARTICIPANT sp
            JOIN STUDY_SESSION ss ON sp.session_id = ss.session_id
            WHERE sp.session_id = %s AND sp.student_id = %s AND ss.status = 'Completed'
        """
        participant = db.execute_query(check_participant, (session_id, user_id))
        
        if not participant:
            return jsonify({'success': False, 'message': 'You can only submit feedback for completed sessions you attended'}), 403
        
        # Check if feedback already exists
        check_feedback = "SELECT outcome_id FROM SESSION_OUTCOME WHERE session_id = %s AND student_id = %s"
        existing = db.execute_query(check_feedback, (session_id, user_id))
        
        if existing:
            return jsonify({'success': False, 'message': 'You have already submitted feedback for this session'}), 400
        
        # Extract and validate feedback data
        effectiveness_rating = data.get('effectiveness_rating')
        learning_improvement = data.get('learning_improvement')
        would_repeat = data.get('would_repeat', True)
        outcome_type = data.get('outcome_type', 'Positive')
        comments = validators.sanitize_input(data.get('comments', ''), max_length=500)
        
        errors = []
        if not effectiveness_rating or not validators.validate_rating(effectiveness_rating):
            errors.append('Effectiveness rating (1.0-5.0) is required')
        if not learning_improvement or not validators.validate_rating(learning_improvement):
            errors.append('Learning improvement rating (1.0-5.0) is required')
        if outcome_type not in ['Positive', 'Neutral', 'Negative']:
            errors.append('Invalid outcome type')
        
        if errors:
            return jsonify({'success': False, 'message': '; '.join(errors)}), 400
        
        # Insert feedback
        try:
            insert_query = """
                INSERT INTO SESSION_OUTCOME 
                (session_id, student_id, effectiveness_rating, learning_improvement, would_repeat, outcome_type, comments)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            db.execute_update(insert_query, (session_id, user_id, effectiveness_rating, learning_improvement, would_repeat, outcome_type, comments))
            
            return jsonify({
                'success': True,
                'message': 'Feedback submitted successfully'
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500


@sessions_bp.route('/api/sessions/<int:session_id>/cancel', methods=['POST'])
@login_required
def cancel_session(session_id):
    """Cancel a study session (creator only)"""
    user_id = session.get('user_id')
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        # Check if user is creator
        query_check = "SELECT created_by FROM STUDY_SESSION WHERE session_id = %s"
        result = db.execute_query(query_check, (session_id,))
        
        if not result or result[0]['created_by'] != user_id:
            return jsonify({'success': False, 'message': 'Only creator can cancel session'}), 403
        
        # Update status to Cancelled
        query_update = "UPDATE STUDY_SESSION SET status = 'Cancelled' WHERE session_id = %s"
        db.execute_update(query_update, (session_id,))
        
        return jsonify({'success': True, 'message': 'Session cancelled successfully'})


@sessions_bp.route('/api/sessions/<int:session_id>/participants/<int:student_id>', methods=['DELETE'])
@login_required
def remove_participant(session_id, student_id):
    """Remove a participant from a session (organizer only)"""
    user_id = session.get('user_id')
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        # Check if current user is the session creator/organizer
        query_check = "SELECT created_by FROM STUDY_SESSION WHERE session_id = %s"
        result = db.execute_query(query_check, (session_id,))
        
        if not result or result[0]['created_by'] != user_id:
            return jsonify({'success': False, 'message': 'Only session organizer can remove participants'}), 403
        
        # Cannot remove the organizer themselves
        if student_id == user_id:
            return jsonify({'success': False, 'message': 'Organizer cannot be removed from session'}), 400
        
        # Check if participant exists in session
        query_participant = """
            SELECT role FROM SESSION_PARTICIPANT 
            WHERE session_id = %s AND student_id = %s
        """
        participant = db.execute_query(query_participant, (session_id, student_id))
        
        if not participant:
            return jsonify({'success': False, 'message': 'Participant not found in session'}), 404
        
        # Cannot remove another organizer
        if participant[0]['role'] == 'Organizer':
            return jsonify({'success': False, 'message': 'Cannot remove organizer'}), 400
        
        # Remove participant
        query_delete = """
            DELETE FROM SESSION_PARTICIPANT 
            WHERE session_id = %s AND student_id = %s
        """
        db.execute_update(query_delete, (session_id, student_id))
        
        return jsonify({'success': True, 'message': 'Participant removed successfully'})


@sessions_bp.route('/api/subjects')
@login_required
def get_subjects():
    """Get all subjects for dropdown"""
    with DatabaseManager(Config.DB_CONFIG) as db:
        query = "SELECT subject_id, subject_name, subject_code FROM SUBJECT ORDER BY subject_name"
        subjects = db.execute_query(query)
        
        return jsonify({'success': True, 'data': subjects})


@sessions_bp.route('/api/locations')
@login_required
def get_locations():
    """Get all locations for dropdown"""
    with DatabaseManager(Config.DB_CONFIG) as db:
        query = "SELECT location_id, building, room_number, capacity FROM LOCATION ORDER BY building, room_number"
        locations = db.execute_query(query)
        
        return jsonify({'success': True, 'data': locations})


@sessions_bp.route('/api/locations/recommend')
@login_required
def recommend_location():
    """Recommend optimal location based on parameters"""
    max_participants = request.args.get('max_participants', type=int, default=10)
    session_date = request.args.get('session_date')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        # Find available locations with sufficient capacity
        query = """
            SELECT 
                l.location_id,
                l.building,
                l.room_number,
                l.capacity,
                COUNT(ss.session_id) as usage_count
            FROM LOCATION l
            LEFT JOIN STUDY_SESSION ss ON l.location_id = ss.location_id
                AND ss.session_date = %s
                AND ss.status IN ('Planned', 'Active')
                AND (
                    (ss.start_time < %s AND ss.end_time > %s) OR
                    (ss.start_time < %s AND ss.end_time > %s) OR
                    (ss.start_time >= %s AND ss.end_time <= %s)
                )
            WHERE l.capacity >= %s
            GROUP BY l.location_id, l.building, l.room_number, l.capacity
            HAVING COUNT(ss.session_id) = 0
            ORDER BY l.capacity ASC
            LIMIT 5
        """
        
        params = (session_date, end_time, start_time, end_time, end_time, start_time, end_time, max_participants)
        recommended = db.execute_query(query, params)
        
        if not recommended:
            # If no location available, return all locations with sufficient capacity
            fallback_query = """
                SELECT location_id, building, room_number, capacity
                FROM LOCATION
                WHERE capacity >= %s
                ORDER BY capacity ASC
                LIMIT 5
            """
            recommended = db.execute_query(fallback_query, (max_participants,))
        
        return jsonify({
            'success': True,
            'data': recommended,
            'message': 'Recommended locations based on capacity and availability' if recommended else 'No suitable locations found'
        })
