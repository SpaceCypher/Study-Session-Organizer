"""Main Flask application"""
from flask import Flask, render_template, redirect, url_for
from flask.json.provider import DefaultJSONProvider
from flask_session import Session
from config import Config
from datetime import datetime, date, time, timedelta

# Custom JSON encoder for database types
class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, time):
            return obj.strftime('%H:%M:%S')
        if isinstance(obj, timedelta):
            # Convert timedelta to total seconds or HH:MM:SS format
            total_seconds = int(obj.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return super().default(obj)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
app.json = CustomJSONProvider(app)

# Initialize session
Session(app)

# Import and register blueprints
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.sessions import sessions_bp
from routes.partners import partners_bp
from routes.notifications import notifications_bp
from routes.analytics import analytics_bp
from routes.profile import profile_bp
from routes.subjects import subjects_bp

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(sessions_bp)
app.register_blueprint(partners_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(subjects_bp)


@app.route('/')
def index():
    """Redirect to login or dashboard"""
    from flask import session
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
