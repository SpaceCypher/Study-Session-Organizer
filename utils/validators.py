"""Input validation functions"""
import re
from datetime import datetime


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone):
    """Validate phone number (10 digits)"""
    pattern = r'^\d{10}$'
    return re.match(pattern, phone) is not None


def validate_gpa(gpa):
    """Validate GPA (0.0 to 10.0)"""
    try:
        gpa_float = float(gpa)
        return 0.0 <= gpa_float <= 10.0
    except (ValueError, TypeError):
        return False


def validate_year(year):
    """Validate year (1-6)"""
    try:
        year_int = int(year)
        return 1 <= year_int <= 6
    except (ValueError, TypeError):
        return False


def validate_date(date_str):
    """Validate date format (YYYY-MM-DD)"""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except (ValueError, TypeError):
        return False


def validate_time(time_str):
    """Validate time format (HH:MM:SS or HH:MM)"""
    try:
        # Try both formats
        try:
            datetime.strptime(time_str, '%H:%M:%S')
        except ValueError:
            datetime.strptime(time_str, '%H:%M')
        return True
    except (ValueError, TypeError):
        return False


def validate_learning_style(style):
    """Validate learning style"""
    valid_styles = ['Visual', 'Auditory', 'Reading/Writing', 'Kinesthetic', 'Mixed']
    return style in valid_styles


def validate_personality_type(personality):
    """Validate personality type (MBTI)"""
    valid_types = ['INTJ', 'INTP', 'ENTJ', 'ENTP', 'INFJ', 'INFP', 'ENFJ', 'ENFP',
                   'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ', 'ISTP', 'ISFP', 'ESTP', 'ESFP']
    return personality in valid_types


def validate_future_date(date_str):
    """Validate that date is not in the past"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        return date_obj >= today
    except (ValueError, TypeError):
        return False


def validate_time_range(start_time, end_time):
    """Validate that end time is after start time"""
    try:
        start = datetime.strptime(start_time, '%H:%M:%S').time()
        end = datetime.strptime(end_time, '%H:%M:%S').time()
        return end > start
    except (ValueError, TypeError):
        return False


def validate_datetime_not_past(date_str, time_str):
    """Validate that datetime is not in the past"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        time_obj = datetime.strptime(time_str, '%H:%M:%S').time()
        datetime_obj = datetime.combine(date_obj, time_obj)
        now = datetime.now()
        return datetime_obj >= now
    except (ValueError, TypeError):
        return False


def sanitize_input(text, max_length=None):
    """Sanitize text input to prevent XSS"""
    if not text:
        return ''
    
    # Remove any HTML tags
    text = re.sub(r'<[^>]+>', '', str(text))
    
    # Trim whitespace
    text = text.strip()
    
    # Limit length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text


def validate_rating(rating):
    """Validate rating (1.0 to 5.0)"""
    try:
        rating_float = float(rating)
        return 1.0 <= rating_float <= 5.0
    except (ValueError, TypeError):
        return False
