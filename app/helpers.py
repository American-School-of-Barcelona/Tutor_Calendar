from flask import redirect, flash
from flask_login import current_user
from functools import wraps

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