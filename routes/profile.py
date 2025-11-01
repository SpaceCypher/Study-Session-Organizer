"""Profile routes - View and edit user profiles"""
from flask import Blueprint, render_template, request, jsonify, session
from database.db_manager import DatabaseManager
from config import Config
from utils import validators
from utils.auth_helpers import login_required

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/profile')
@login_required
def view_own_profile():
    """View own profile"""
    return render_template('profile/view.html', user_id=session.get('user_id'), is_own=True)


@profile_bp.route('/profile/<int:user_id>')
@login_required
def view_profile(user_id):
    """View another user's profile"""
    current_user_id = session.get('user_id')
    is_own = (user_id == current_user_id)
    return render_template('profile/view.html', user_id=user_id, is_own=is_own)


@profile_bp.route('/profile/edit')
@login_required
def edit_profile_page():
    """Display edit profile page"""
    return render_template('profile/edit.html')


@profile_bp.route('/api/profile/current')
@login_required
def get_current_profile():
    """Get current user's profile for editing"""
    user_id = session.get('user_id')
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        query = """
            SELECT 
                student_id,
                name,
                email,
                phone,
                major,
                year,
                gpa,
                learning_style,
                personality_type,
                needs_help,
                can_teach
            FROM STUDENT
            WHERE student_id = %s
        """
        result = db.execute_query(query, (user_id,))
        
        if not result:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        return jsonify({'success': True, 'data': result[0]})


@profile_bp.route('/api/profile/<int:user_id>')
@login_required
def get_profile(user_id):
    """Get user profile data"""
    current_user_id = session.get('user_id')
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        query = """
            SELECT 
                student_id,
                name,
                email,
                phone,
                major,
                year,
                gpa,
                learning_style,
                personality_type,
                needs_help,
                can_teach,
                created_date,
                last_active
            FROM STUDENT
            WHERE student_id = %s
        """
        result = db.execute_query(query, (user_id,))
        
        if not result:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        user_data = result[0]
        
        # Get subjects the user is enrolled in
        subjects_query = """
            SELECT 
                s.subject_id,
                s.subject_name,
                s.subject_code,
                ss.proficiency_level,
                ss.needs_help,
                ss.can_teach
            FROM STUDENT_SUBJECT ss
            JOIN SUBJECT s ON ss.subject_id = s.subject_id
            WHERE ss.student_id = %s
        """
        user_data['subjects'] = db.execute_query(subjects_query, (user_id,))
        
        # Get session statistics
        stats_query = """
            SELECT 
                COUNT(*) as total_sessions,
                SUM(CASE WHEN ss.status = 'Completed' THEN 1 ELSE 0 END) as completed_sessions,
                SUM(CASE WHEN sp.role = 'Organizer' THEN 1 ELSE 0 END) as organized_sessions
            FROM SESSION_PARTICIPANT sp
            JOIN STUDY_SESSION ss ON sp.session_id = ss.session_id
            WHERE sp.student_id = %s
        """
        stats = db.execute_query(stats_query, (user_id,))
        user_data['stats'] = stats[0] if stats else {'total_sessions': 0, 'completed_sessions': 0, 'organized_sessions': 0}
        
        # Calculate compatibility score if viewing another user
        if user_id != current_user_id:
            try:
                compatibility_query = "SELECT CALCULATE_COMPATIBILITY(%s, %s) as compatibility"
                comp_result = db.execute_query(compatibility_query, (current_user_id, user_id))
                user_data['compatibility_score'] = comp_result[0]['compatibility'] if comp_result else 0
            except Exception as e:
                print(f'Compatibility calculation error: {e}')
                user_data['compatibility_score'] = 0
        
        return jsonify({'success': True, 'data': user_data})


@profile_bp.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update user profile"""
    user_id = session.get('user_id')
    data = request.get_json()
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        # Extract and validate data
        name = data.get('name')
        phone = data.get('phone')
        major = data.get('major')
        year = data.get('year')
        gpa = data.get('gpa')
        learning_style = data.get('learning_style')
        personality_type = data.get('personality_type')
        needs_help = data.get('needs_help')
        can_teach = data.get('can_teach')
        
        # Validation
        errors = []
        if name and len(validators.sanitize_input(name)) == 0:
            errors.append('Name is required')
        if phone and not validators.validate_phone(phone):
            errors.append('Valid 10-digit phone number is required')
        if year is not None and not validators.validate_year(year):
            errors.append('Year must be between 1 and 6')
        if gpa is not None and not validators.validate_gpa(gpa):
            errors.append('GPA must be between 0.0 and 10.0')
        if learning_style and not validators.validate_learning_style(learning_style):
            errors.append('Invalid learning style')
        if personality_type and not validators.validate_personality_type(personality_type):
            errors.append('Invalid personality type')
        
        if errors:
            return jsonify({'success': False, 'message': '; '.join(errors)}), 400
        
        # Build update query
        update_fields = []
        params = []
        
        if name:
            update_fields.append("name = %s")
            params.append(validators.sanitize_input(name, max_length=100))
        if phone:
            update_fields.append("phone = %s")
            params.append(phone)
        if major:
            update_fields.append("major = %s")
            params.append(validators.sanitize_input(major, max_length=100))
        if year is not None:
            update_fields.append("year = %s")
            params.append(year)
        if gpa is not None:
            update_fields.append("gpa = %s")
            params.append(gpa)
        if learning_style:
            update_fields.append("learning_style = %s")
            params.append(learning_style)
        if personality_type:
            update_fields.append("personality_type = %s")
            params.append(personality_type)
        if needs_help is not None:
            update_fields.append("needs_help = %s")
            params.append(needs_help)
        if can_teach is not None:
            update_fields.append("can_teach = %s")
            params.append(can_teach)
        
        if update_fields:
            params.append(user_id)
            update_query = f"UPDATE STUDENT SET {', '.join(update_fields)} WHERE student_id = %s"
            db.execute_update(update_query, tuple(params))
            
            # Update session name if name changed
            if name:
                session['user_name'] = validators.sanitize_input(name, max_length=100)
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})


@profile_bp.route('/profile/availability')
@login_required
def availability_page():
    """Display availability management page"""
    return render_template('profile/availability.html')


@profile_bp.route('/api/profile/availability')
@login_required
def get_availability():
    """Get user's availability schedule"""
    user_id = session.get('user_id')
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        query = """
            SELECT 
                day_of_week,
                start_time,
                end_time,
                location_preference,
                is_recurring
            FROM AVAILABILITY
            WHERE student_id = %s
            ORDER BY 
                FIELD(day_of_week, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'),
                start_time
        """
        availability = db.execute_query(query, (user_id,))
        return jsonify({'success': True, 'data': availability or []})


@profile_bp.route('/api/profile/availability', methods=['POST'])
@login_required
def add_availability():
    """Add availability slot"""
    user_id = session.get('user_id')
    data = request.get_json()
    
    day_of_week = data.get('day_of_week')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    location_preference = data.get('location_preference', '')
    
    # Validation
    valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    if not day_of_week or day_of_week not in valid_days:
        return jsonify({'success': False, 'message': 'Invalid day of week'}), 400
    
    if not start_time or not end_time:
        return jsonify({'success': False, 'message': 'Start time and end time are required'}), 400
    
    if not validators.validate_time_range(start_time, end_time):
        return jsonify({'success': False, 'message': 'End time must be after start time'}), 400
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        # Check for overlapping slots
        overlap_query = """
            SELECT COUNT(*) as count
            FROM AVAILABILITY
            WHERE student_id = %s 
            AND day_of_week = %s
            AND (
                (start_time <= %s AND end_time > %s) OR
                (start_time < %s AND end_time >= %s) OR
                (start_time >= %s AND end_time <= %s)
            )
        """
        overlap = db.execute_query(overlap_query, (user_id, day_of_week, start_time, start_time, end_time, end_time, start_time, end_time))
        
        if overlap and overlap[0]['count'] > 0:
            return jsonify({'success': False, 'message': 'This time slot overlaps with existing availability'}), 400
        
        # Insert new availability
        insert_query = """
            INSERT INTO AVAILABILITY (student_id, day_of_week, start_time, end_time, location_preference, is_recurring)
            VALUES (%s, %s, %s, %s, %s, 1)
        """
        db.execute_update(insert_query, (user_id, day_of_week, start_time, end_time, location_preference))
        
        return jsonify({'success': True, 'message': 'Availability added successfully'})


@profile_bp.route('/api/profile/availability', methods=['DELETE'])
@login_required
def delete_availability():
    """Delete availability slot"""
    user_id = session.get('user_id')
    data = request.get_json()
    
    day_of_week = data.get('day_of_week')
    start_time = data.get('start_time')
    
    if not day_of_week or not start_time:
        return jsonify({'success': False, 'message': 'Day and start time are required'}), 400
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        delete_query = """
            DELETE FROM AVAILABILITY
            WHERE student_id = %s AND day_of_week = %s AND start_time = %s
        """
        db.execute_update(delete_query, (user_id, day_of_week, start_time))
        
        return jsonify({'success': True, 'message': 'Availability deleted successfully'})
