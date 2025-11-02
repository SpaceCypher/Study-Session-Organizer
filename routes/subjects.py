"""Subject management routes"""
from flask import Blueprint, render_template, jsonify, session, request
from database.db_manager import DatabaseManager
from config import Config
from utils.auth_helpers import login_required

subjects_bp = Blueprint('subjects', __name__)


@subjects_bp.route('/profile/subjects')
@login_required
def manage_subjects():
    """Display subject management page"""
    return render_template('profile/subjects.html')


@subjects_bp.route('/api/profile/subjects')
@login_required
def get_user_subjects():
    """Get all subjects for current user"""
    user_id = session.get('user_id')
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        query = """
            SELECT 
                ss.subject_id,
                s.subject_name,
                s.subject_code,
                s.credit_hours,
                ss.proficiency_level,
                ss.can_teach,
                ss.needs_help,
                ss.current_grade,
                ss.enrolled_date
            FROM STUDENT_SUBJECT ss
            JOIN SUBJECT s ON ss.subject_id = s.subject_id
            WHERE ss.student_id = %s
            ORDER BY s.subject_name
        """
        subjects = db.execute_query(query, (user_id,))
        
        return jsonify({'success': True, 'data': subjects or []})


@subjects_bp.route('/api/subjects/available')
@login_required
def get_available_subjects():
    """Get subjects not yet enrolled by user"""
    user_id = session.get('user_id')
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        query = """
            SELECT 
                s.subject_id,
                s.subject_name,
                s.subject_code,
                s.credit_hours,
                s.difficulty_level
            FROM SUBJECT s
            WHERE s.subject_id NOT IN (
                SELECT subject_id 
                FROM STUDENT_SUBJECT 
                WHERE student_id = %s
            )
            ORDER BY s.subject_name
        """
        subjects = db.execute_query(query, (user_id,))
        
        return jsonify({'success': True, 'data': subjects or []})


@subjects_bp.route('/api/profile/subjects', methods=['POST'])
@login_required
def add_subject():
    """Add a subject for the user"""
    user_id = session.get('user_id')
    data = request.get_json()
    
    subject_id = data.get('subject_id')
    proficiency_level = data.get('proficiency_level', 'Beginner')
    can_teach = data.get('can_teach', False)
    needs_help = data.get('needs_help', True)
    current_grade = data.get('current_grade')
    
    # Validation
    if not subject_id:
        return jsonify({'success': False, 'message': 'Subject is required'}), 400
    
    if proficiency_level not in ['Beginner', 'Intermediate', 'Advanced', 'Expert']:
        return jsonify({'success': False, 'message': 'Invalid proficiency level'}), 400
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        try:
            # Check if already enrolled
            check_query = "SELECT 1 FROM STUDENT_SUBJECT WHERE student_id = %s AND subject_id = %s"
            existing = db.execute_query(check_query, (user_id, subject_id))
            
            if existing:
                return jsonify({'success': False, 'message': 'Already enrolled in this subject'}), 400
            
            # Insert new subject
            insert_query = """
                INSERT INTO STUDENT_SUBJECT 
                (student_id, subject_id, proficiency_level, can_teach, needs_help, current_grade, enrolled_date)
                VALUES (%s, %s, %s, %s, %s, %s, CURDATE())
            """
            db.execute_update(insert_query, (user_id, subject_id, proficiency_level, can_teach, needs_help, current_grade))
            
            return jsonify({'success': True, 'message': 'Subject added successfully'})
            
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500


@subjects_bp.route('/api/profile/subjects/<int:subject_id>', methods=['PUT'])
@login_required
def update_subject(subject_id):
    """Update subject proficiency and preferences"""
    user_id = session.get('user_id')
    data = request.get_json()
    
    proficiency_level = data.get('proficiency_level')
    can_teach = data.get('can_teach')
    needs_help = data.get('needs_help')
    current_grade = data.get('current_grade')
    
    # Validation
    if proficiency_level and proficiency_level not in ['Beginner', 'Intermediate', 'Advanced', 'Expert']:
        return jsonify({'success': False, 'message': 'Invalid proficiency level'}), 400
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        try:
            # Build update query dynamically
            updates = []
            params = []
            
            if proficiency_level is not None:
                updates.append("proficiency_level = %s")
                params.append(proficiency_level)
            
            if can_teach is not None:
                updates.append("can_teach = %s")
                params.append(can_teach)
            
            if needs_help is not None:
                updates.append("needs_help = %s")
                params.append(needs_help)
            
            if current_grade is not None:
                updates.append("current_grade = %s")
                params.append(current_grade)
            
            if not updates:
                return jsonify({'success': False, 'message': 'No updates provided'}), 400
            
            # Add WHERE conditions to params
            params.extend([user_id, subject_id])
            
            update_query = f"""
                UPDATE STUDENT_SUBJECT 
                SET {', '.join(updates)}
                WHERE student_id = %s AND subject_id = %s
            """
            
            db.execute_update(update_query, tuple(params))
            
            return jsonify({'success': True, 'message': 'Subject updated successfully'})
            
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500


@subjects_bp.route('/api/profile/subjects/<int:subject_id>', methods=['DELETE'])
@login_required
def remove_subject(subject_id):
    """Remove a subject from user's enrollment"""
    user_id = session.get('user_id')
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        try:
            delete_query = """
                DELETE FROM STUDENT_SUBJECT 
                WHERE student_id = %s AND subject_id = %s
            """
            db.execute_update(delete_query, (user_id, subject_id))
            
            return jsonify({'success': True, 'message': 'Subject removed successfully'})
            
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
