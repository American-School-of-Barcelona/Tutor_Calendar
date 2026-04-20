from flask import redirect, flash
from flask_login import current_user
from functools import wraps
from datetime import datetime, timedelta, time


def parse_time_hhmm(s: str) -> time:
    """Parse HTML time input values: 'HH:MM' or 'HH:MM:SS'."""
    s = (s or "").strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(s, fmt).time()
        except ValueError:
            continue
    raise ValueError(f"Invalid time: {s!r}")


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
    Check if a booking time slot does NOT conflict with any tutor unavailability blocks.
    Each Availability row is treated as a blocked interval where the tutor is not available.
    
    Returns:
        True if booking does NOT overlap any unavailability block (so it is allowed),
        False if it overlaps at least one unavailability block.
    """
    
    from app.app import Availability
    
    booking_start_time = start.time()
    booking_end_time = end.time()
    
    blocks = db_session.query(Availability).filter_by(user_id=tutor_id).all()
    
    if not blocks:
        return True
    
    booking_date = start.date()

    for block in blocks:
        if block.repeat_until and booking_date > block.repeat_until.date():
            continue
        if booking_start_time < block.end_time and booking_end_time > block.start_time:
            return False

    return True

def is_within_24h_of_booking(start_time) -> bool:
    now = datetime.utcnow()
    delta = (start_time - now).total_seconds()
    return 0 < delta <= 24 * 3600

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