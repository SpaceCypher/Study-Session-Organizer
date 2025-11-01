"""Notification routes"""
from flask import Blueprint, render_template, jsonify, session, request
from database.db_manager import DatabaseManager
from config import Config
from utils.auth_helpers import login_required

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/notifications')
@login_required
def list():
    """Display notifications list page"""
    return render_template('notifications/list.html')


@notifications_bp.route('/api/notifications')
@login_required
def get_notifications():
    """Get all notifications with optional filter"""
    user_id = session.get('user_id')
    filter_type = request.args.get('filter', 'all')  # all, read, unread
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        query = """
            SELECT 
                notification_id,
                notification_type,
                message,
                read_status,
                sent_date
            FROM NOTIFICATION
            WHERE student_id = %s
        """
        params = [user_id]
        
        if filter_type == 'read':
            query += " AND read_status = TRUE"
        elif filter_type == 'unread':
            query += " AND read_status = FALSE"
        
        query += " ORDER BY sent_date DESC LIMIT 50"
        
        notifications = db.execute_query(query, tuple(params))
        
        return jsonify({'success': True, 'data': notifications})


@notifications_bp.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
@login_required
def mark_as_read(notification_id):
    """Mark notification as read"""
    user_id = session.get('user_id')
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        query = """
            UPDATE NOTIFICATION 
            SET read_status = TRUE, read_date = CURRENT_TIMESTAMP
            WHERE notification_id = %s AND student_id = %s
        """
        db.execute_update(query, (notification_id, user_id,))
        
        return jsonify({'success': True, 'message': 'Notification marked as read'})


@notifications_bp.route('/api/notifications/unread-count')
@login_required
def get_unread_count():
    """Get unread notification count"""
    user_id = session.get('user_id')
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        query = """
            SELECT COUNT(*) as count 
            FROM NOTIFICATION 
            WHERE student_id = %s AND read_status = FALSE
        """
        result = db.execute_query(query, (user_id,))
        count = result[0]['count'] if result else 0
        
        return jsonify({'success': True, 'count': count})
