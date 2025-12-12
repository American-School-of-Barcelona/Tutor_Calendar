from flask import redirect, session
from functools import wraps
from models import User

def login_required(f):
    """
    Decorate routes to require login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorate routes to require admin login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        
        user = User.query.get(session.get("user_id"))
        if user is None or user.role != "admin":
            return redirect("/")
        
        return f(*args, **kwargs)
    return decorated_function

def parse_email_input(raw: str):
    """
    Parse email input - accepts username or full email
    Returns username, email
    For your system, we'll allow any email domain
    """
    if raw is None:
        raise ValueError("Email is required")

    value = raw.strip()
    if not value:
        raise ValueError("Email is required")

    # If it contains @, it's a full email
    if "@" in value:
        parts = value.split("@")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError("Invalid email format")
        username = parts[0]
        email = value
        return username, email

    return value, None