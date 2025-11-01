"""Analytics routes"""
from flask import Blueprint, render_template, jsonify, session
from database.db_manager import DatabaseManager
from database import procedures
from config import Config
from utils.auth_helpers import login_required

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/analytics')
@login_required
def dashboard():
    """Display analytics dashboard page"""
    return render_template('analytics/dashboard.html')


@analytics_bp.route('/api/analytics/<int:student_id>')
@login_required
def get_analytics(student_id):
    """Get analytics for a student (calls GenerateSessionAnalytics procedure)"""
    user_id = session.get('user_id')
    
    # Users can only view their own analytics for now
    if student_id != user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    with DatabaseManager(Config.DB_CONFIG) as db:
        try:
            overall_stats, subject_performance, frequent_partners = procedures.generate_session_analytics(db, student_id)
            
            # Format the data for frontend
            overall = overall_stats[0] if overall_stats else {}
            subjects = subject_performance if subject_performance else []
            partners = frequent_partners if frequent_partners else []
            
            return jsonify({
                'success': True,
                'overall': overall,
                'subjects': subjects,
                'partners': partners
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
