from flask import redirect, flash
from flask_login import current_user
from functools import wraps
from datetime import datetime, timedelta

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "error")
            return redirect("/login")
        
        if current_user.role != "admin":
            flash("Access denied. Admin login required.", "error")
            return redirect("/")
        
        return f(*args, **kwargs)
    return decorated_function

def parse_email_input(raw: str):
    if raw is None:
        raise ValueError("email is required")

    value = raw.strip()
    if not value:
        raise ValueError("email is required")

    if "@" in value:
        parts = value.split("@")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError("Invalid email format")
        username = parts[0]
        email = value.lower()
        return username, email

    if "@" in value or " " in value:
        raise ValueError("Invalid email format")

    username = value
    email = f"{value}@tutomatics.com"
    return username, email

# Booking helper functions

def calculate_price(lesson_minutes: int) -> int:
    """
    Calculate lesson price based on duration.
    Business rules:
    - Base price: 100€ for 2 hours (120 minutes)
    - Additional: 50€ per extra hour (60 minutes)
    - Formula: 100 + 50 * ((minutes - 120) / 60)
    
    Args:
        lesson_minutes: Duration in minutes (must be >= 120)
    
    Returns:
        Price in euros (integer)
    
    Raises:
        ValueError: If lesson_minutes < 120
    """
    if lesson_minutes < 120:
        raise ValueError("Minimum lesson duration is 2 hours (120 minutes)")
    
    # Calculate extra hours beyond the base 2 hours
    extra_hours = (lesson_minutes - 120) / 60
    price = 100 + int(50 * extra_hours)
    return price

def slots_overlap(start1: datetime, end1: datetime, start2: datetime, end2: datetime) -> bool:
    """
    Check if two time slots overlap.
    
    Args:
        start1, end1: First slot start and end times
        start2, end2: Second slot start and end times
    
    Returns:
        True if slots overlap, False otherwise
    """
    # Two slots overlap if one starts before the other ends
    return start1 < end2 and start2 < end1

def is_within_availability(tutor_id: int, start: datetime, end: datetime, db_session) -> bool:
    """
    Check if a booking time slot falls within tutor's availability blocks.
    Note: This is a simplified check. For now, we'll check if the booking
    time falls within any availability block for the given day.
    
    Args:
        tutor_id: ID of the tutor/admin
        start: Booking start time
        end: Booking end time
        db_session: Database session object
    
    Returns:
        True if booking is within availability, False otherwise
    """
    from app import Availability
    
    # Get the day of the week (0=Monday, 6=Sunday)
    booking_day = start.weekday()
    booking_start_time = start.time()
    booking_end_time = end.time()
    
    # Query availability blocks for this tutor
    availabilities = db_session.query(Availability).filter_by(user_id=tutor_id).all()
    
    if not availabilities:
        # No availability set = tutor is available all day (for now)
        return True
    
    # Check if booking time falls within any availability block
    for avail in availabilities:
        if avail.start_time <= booking_start_time and booking_end_time <= avail.end_time:
            return True
    
    return False

def get_booking_color(status: str) -> str:
    """
    Get CSS color class name for booking status.
    Used for styling calendar slots and booking lists.
    
    Args:
        status: Booking status ('pending', 'accepted', 'denied', 'cancelled')
    
    Returns:
        CSS class name string
    """
    color_map = {
        'pending': 'booking-pending',
        'accepted': 'booking-accepted',
        'denied': 'booking-denied',
        'cancelled': 'booking-cancelled'
    }
    return color_map.get(status, 'booking-unknown')