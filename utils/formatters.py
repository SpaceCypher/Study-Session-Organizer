"""Data formatting utilities"""
from datetime import datetime


def format_date(date_obj):
    """Format date object to string (YYYY-MM-DD)"""
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime('%Y-%m-%d') if date_obj else None


def format_time(time_obj):
    """Format time object to string (HH:MM:SS)"""
    if isinstance(time_obj, str):
        return time_obj
    return time_obj.strftime('%H:%M:%S') if time_obj else None


def format_datetime(dt_obj):
    """Format datetime object to readable string"""
    if isinstance(dt_obj, str):
        return dt_obj
    return dt_obj.strftime('%Y-%m-%d %H:%M:%S') if dt_obj else None


def format_gpa(gpa):
    """Format GPA to 2 decimal places"""
    try:
        return f"{float(gpa):.2f}"
    except (ValueError, TypeError):
        return "0.00"


def format_compatibility_score(score):
    """Format compatibility score to 2 decimal places"""
    try:
        return f"{float(score):.2f}"
    except (ValueError, TypeError):
        return "0.00"
