from flask import redirect, session, current_app
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        
        from app import db, User
        with current_app.app_context():
            user = User.query.get(session.get("user_id"))
            if user is None or user.role != "admin":
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