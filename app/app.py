from flask import Flask, jsonify, request, render_template, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from .helpers import admin_required, parse_email_input, calculate_price, slots_overlap, is_within_availability, get_booking_color

import os

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
            static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'))

# Configuration for SQLAlchemy
app.config['SECRET_KEY'] = 'your-secret-key-here-change-this-later'
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(base_dir, 'instance', 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # Redirect to login if not authenticated
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "error"

# User loader function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# The homepage route which dispalys the calendar
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/availability")
def availability():
    return render_template("availability.html")

# The route to handle date selection
@app.route("/select_date", methods=["POST"])
def select_date():
    data = request.get_json() # Get JSON data from the request
    if not data:
        return jsonify({"error": "No data provided"}), 400
    # Extract date information from the received data
    time = data.get("time")
    day = data.get("day")
    month = data.get("month")
    year = data.get("year")
    selected_date = data.get("selected_date")
    print(f"Date selected: {selected_date} (Time: {time}, Day: {day}, Month: {month}, Year: {year})")
    # Return a success response
    return jsonify({"status": "success", "selected_date": selected_date,
                    "time": time, "day": day, "month": month, "year": year})

from datetime import datetime
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = "user"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class Availability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    repeat_rule = db.Column(db.String(50)) # daily/weekly/monthly/until date/etc.
    repeat_until = db.Column(db.DateTime, nullable=True)
    user = db.relationship('User', backref=db.backref('availabilities', lazy=True))

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    lesson_minutes = db.Column(db.Integer, nullable=False)  # Duration in minutes
    price_eur = db.Column(db.Integer, nullable=False)  # Price in euros
    status = db.Column(db.String(20), default="pending")  # pending/accepted/denied/cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship("User", foreign_keys=[student_id], backref="student_bookings")
    tutor = db.relationship("User", foreign_keys=[tutor_id], backref="tutor_bookings")

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref=db.backref("notifications", lazy=True))

def hash_password(password: str) -> str:
    return generate_password_hash(password)

@app.route("/login", methods=["GET", "POST"])
def login():
    # If user is already logged in, redirect to their dashboard
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect("/admin/dashboard")
        else:
            return redirect("/student/dashboard")

    if request.method == "POST":
        raw_email = request.form.get("email")
        password = request.form.get("password")

        if not raw_email or not password:
            flash("You must complete all fields.", "error")
            return render_template("login.html"), 400

        try:
            _, email = parse_email_input(raw_email)
        except ValueError as e:
            flash(str(e), "error")
            return render_template("login.html"), 400

        user = User.query.filter_by(email=email).first()
        
        # If not found by email, try username
        if not user:
            username, _ = parse_email_input(raw_email)
            user = User.query.filter_by(username=username).first()

        if user is None or not check_password_hash(user.password_hash, password):
            flash("Invalid email/username or password", "error")
            return render_template("login.html"), 403

        # Check if student is approved
        if user.role == "student" and user.status != "approved":
            flash("Your account is pending approval. Please wait for admin approval.", "error")
            return render_template("login.html")

        # Log the user in using Flask-Login
        login_user(user)
        
        if user.role == "admin":
            return redirect("/admin/dashboard")
        else:
            return redirect("/student/dashboard")

    return render_template("login.html")

@app.route("/debug-login")
def debug_login():
    """Debug login - check if users exist and test password"""
    try:
        admin = User.query.filter_by(email="admin@gmail.com").first()
        
        if not admin:
            return "Admin user does NOT exist!<br><a href='/create-test-users'>Create test users</a>"
        
        # Test password
        test_password = "admin"
        password_match = check_password_hash(admin.password_hash, test_password)
        
        result = f"Admin user found!<br>"
        result += f"Email: {admin.email}<br>"
        result += f"Role: {admin.role}<br>"
        result += f"Status: {admin.status}<br>"
        result += f"Password hash: {admin.password_hash[:50]}...<br>"
        result += f"Password 'admin' matches: {password_match}<br>"
        
        # Test with wrong password
        wrong_match = check_password_hash(admin.password_hash, "wrong")
        result += f"Password 'wrong' matches: {wrong_match}<br>"
        
        return result
    except Exception as e:
        return f"Error: {str(e)}<br><a href='/init-db'>Create tables first</a>"
    
@app.route("/check-users")
def check_users():
    """Check if test users exist and verify their credentials"""
    try:
        result = "<h2>User Database Check</h2>"
        
        # Check admin user by username
        admin_by_username = User.query.filter_by(username="admin").first()
        result += f"<h3>Admin by username 'admin':</h3>"
        if admin_by_username:
            result += f"✓ Found!<br>"
            result += f"  - ID: {admin_by_username.id}<br>"
            result += f"  - Username: {admin_by_username.username}<br>"
            result += f"  - Email: {admin_by_username.email}<br>"
            result += f"  - Role: {admin_by_username.role}<br>"
            result += f"  - Status: {admin_by_username.status}<br>"
            
            # Test password
            test_pass = "A12345"
            password_match = check_password_hash(admin_by_username.password_hash, test_pass)
            result += f"  - Password 'A12345' matches: {password_match}<br>"
            if not password_match:
                result += f"  - Password hash: {admin_by_username.password_hash[:50]}...<br>"
        else:
            result += "✗ NOT FOUND<br>"
        
        # Check admin user by email
        admin_by_email = User.query.filter_by(email="admin@tutomatics.com").first()
        result += f"<h3>Admin by email 'admin@tutomatics.com':</h3>"
        if admin_by_email:
            result += f"✓ Found!<br>"
            result += f"  - Username: {admin_by_email.username}<br>"
        else:
            result += "✗ NOT FOUND<br>"
        
        # Check student user
        student_by_username = User.query.filter_by(username="student").first()
        result += f"<h3>Student by username 'student':</h3>"
        if student_by_username:
            result += f"✓ Found!<br>"
            result += f"  - Username: {student_by_username.username}<br>"
            result += f"  - Email: {student_by_username.email}<br>"
            
            # Test password
            test_pass = "S12345"
            password_match = check_password_hash(student_by_username.password_hash, test_pass)
            result += f"  - Password 'S12345' matches: {password_match}<br>"
        else:
            result += "✗ NOT FOUND<br>"
        
        # List all users
        all_users = User.query.all()
        result += f"<h3>All users in database ({len(all_users)}):</h3>"
        for u in all_users:
            result += f"  - ID: {u.id}, Username: {u.username}, Email: {u.email}, Role: {u.role}<br>"
        
        result += "<br><a href='/create-test-users'>Create test users</a>"
        return result
    except Exception as e:
        return f"Error: {str(e)}<br><a href='/init-db'>Initialize database</a>"

@app.route("/create-test-users")
def create_test_users():
    try:
        User.query.filter_by(username="admin").delete()
        User.query.filter_by(username="student").delete()
        User.query.filter_by(email="admin@tutomatics.com").delete()
        User.query.filter_by(email="student@tutomatics.com").delete()
        db.session.commit()
        
        admin_user = User(
            username="admin",
            email="admin@tutomatics.com",
            password_hash=generate_password_hash("A12345"),
            role="admin",
            status="approved"
        )
        
        student_user = User(
            username="student",
            email="student@tutomatics.com",
            password_hash=generate_password_hash("S12345"),
            role="student",
            status="approved"
        )
        
        db.session.add(admin_user)
        db.session.add(student_user)
        db.session.commit()
        
        admin_check = User.query.filter_by(username="admin").first()
        student_check = User.query.filter_by(username="student").first()
        
        result = "Test users created!<br><br>"
        result += "Admin: username 'admin' or email 'admin@tutomatics.com' / password: A12345<br>"
        result += "Student: username 'student' or email 'student@tutomatics.com' / password: S12345<br><br>"
        
        if admin_check:
            result += "✓ Admin user verified<br>"
        else:
            result += "✗ Admin user NOT found<br>"
            
        if student_check:
            result += "✓ Student user verified<br>"
        else:
            result += "✗ Student user NOT found<br>"
        
        result += "<br><a href='/check-users'>Check users</a>"
        return result
    except Exception as e:
        return f"Error: {str(e)}"

@app.route("/signup", methods=["GET", "POST"])
def signup():
    # If user is already logged in, redirect to their dashboard
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect("/admin/dashboard")
        else:
            return redirect("/student/dashboard")
    
    if request.method == "POST":
        # ... rest of signup logic
        name = request.form.get("name")
        lastname = request.form.get("lastname")
        username = request.form.get("username")
        raw_email = request.form.get("email")
        password = request.form.get("password")
        repeat_password = request.form.get("repeat_password")

        if not all([name, lastname, username, raw_email, password, repeat_password]):
            flash("All fields are required", "error")
            return render_template("signup.html"), 400

        try:
            parsed_username, email = parse_email_input(raw_email)
        except ValueError as e:
            flash(str(e), "error")
            return render_template("signup.html"), 400

        if password != repeat_password:
            flash("Passwords do not match", "error")
            return render_template("signup.html"), 400

        existing_email = User.query.filter_by(email=email).first()
        if existing_email is not None:
            flash("That email is already registered", "error")
            return render_template("signup.html"), 400

        existing_username = User.query.filter_by(username=username).first()
        if existing_username is not None:
            flash("That username is already taken", "error")
            return render_template("signup.html"), 400

        hashed = generate_password_hash(password)

        new_user = User(
            username=username,
            email=email,
            password_hash=hashed,
            role="student",
            status="pending"
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Sign up request submitted! Check your email for an approval notification", "success")
        return redirect("/")

    return render_template("signup.html")

@app.route("/admin/approve-user/<int:user_id>", methods=["POST"])
@admin_required
def approve_user(user_id):
    user = User.query.get(user_id)
    if user and user.status == "pending":
        user.status = "approved"
        db.session.commit()
        flash(f"User {user.username} has been approved.", "success")
    return redirect("/admin/signup-approvals")

@app.route("/admin/deny-user/<int:user_id>", methods=["POST"])
@admin_required
def deny_user(user_id):
    user = User.query.get(user_id)
    if user and user.status == "pending":
        db.session.delete(user)
        db.session.commit()
        flash(f"User {user.username} has been denied and removed.", "info")
    return redirect("/admin/signup-approvals")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect("/")

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        flash("Access denied. Admin login required.", "error")
        return redirect("/login")
    
    return render_template("admin/dashboard.html")

@app.route("/student/dashboard")
@login_required
def student_dashboard():
    # Check if student is approved
    if current_user.status != "approved":
        return render_template("student/pending.html")
    
    return render_template("student/dashboard.html")

@app.route("/admin/home")
@admin_required
def admin_home():
    return render_template("index.html")

@app.route("/student/home")
@login_required
def student_home():
    if current_user.status != "approved":
        return redirect("/student/dashboard")
    return render_template("index.html")

@app.route("/debug-login-step-by-step", methods=["GET", "POST"])
def debug_login_step_by_step():
    """Debug route to see exactly what happens at each login step"""
    result = "<h2>Login Debug - Step by Step</h2>"
    
    if request.method == "POST":
        raw_input = request.form.get("email")
        password = request.form.get("password")
        
        result += f"<h3>Step 1: Raw Input</h3>"
        result += f"Raw input received: '{raw_input}'<br>"
        result += f"Password received: '{password}'<br><br>"
        
        result += f"<h3>Step 2: Parse Email Input</h3>"
        try:
            username, email = parse_email_input(raw_input)
            result += f"✓ Parsed successfully<br>"
            result += f"  Username returned: '{username}'<br>"
            result += f"  Email returned: '{email}'<br><br>"
        except ValueError as e:
            result += f"✗ Parse failed: {str(e)}<br>"
            return result
        
        result += f"<h3>Step 3: Database Query</h3>"
        user_by_email = User.query.filter_by(email=email).first()
        if user_by_email:
            result += f"✓ User found by email '{email}'<br>"
            result += f"  User ID: {user_by_email.id}<br>"
            result += f"  Username: {user_by_email.username}<br>"
            result += f"  Email: {user_by_email.email}<br>"
            result += f"  Password hash: {user_by_email.password_hash[:50]}...<br><br>"
        else:
            result += f"✗ No user found with email '{email}'<br>"
            result += f"<br>Trying username query...<br>"
            user_by_username = User.query.filter_by(username=username).first()
            if user_by_username:
                result += f"✓ User found by username '{username}'<br>"
                result += f"  User email in DB: '{user_by_username.email}'<br>"
                result += f"  Expected email: '{email}'<br>"
                result += f"  Match? {user_by_username.email.lower() == email.lower()}<br>"
            else:
                result += f"✗ No user found with username '{username}'<br>"
            return result
        
        result += f"<h3>Step 4: Password Verification</h3>"
        password_match = check_password_hash(user_by_email.password_hash, password)
        result += f"Password match result: {password_match}<br>"
        
        if password_match:
            result += f"<h3>✓ SUCCESS - Login should work!</h3>"
        else:
            result += f"<h3>✗ FAILED - Password doesn't match</h3>"
            result += f"Testing with different passwords:<br>"
            test_passwords = ["A12345", "admin", "S12345", "student"]
            for test_pwd in test_passwords:
                test_match = check_password_hash(user_by_email.password_hash, test_pwd)
                result += f"  '{test_pwd}': {test_match}<br>"
    
    else:
        result += """
        <form method="POST">
            <input type="text" name="email" placeholder="Email or Username" required><br><br>
            <input type="password" name="password" placeholder="Password" required><br><br>
            <button type="submit">Debug Login</button>
        </form>
        """
    
    result += "<br><br><a href='/check-users'>Check all users</a>"
    return result

@app.route("/admin/calendar")
@admin_required
def admin_calendar():
    return render_template("admin/calendar.html")

@app.route("/student/calendar")
@login_required
def student_calendar():
    if current_user.status != "approved":
        return redirect("/student/dashboard")
    return render_template("student/calendar.html")

@app.route("/admin/booking-approvals")
@admin_required
def admin_booking_approvals():
    return render_template("admin/booking-approvals.html")

@app.route("/admin/signup-approvals")
@admin_required
def admin_signup_approvals():
    pending_users = User.query.filter_by(status="pending").all()
    return render_template("admin/signup-approvals.html", pending_users=pending_users)

if __name__ == "__main__":
    app.run(debug=True)

@app.route("/api/book-slot", methods=["POST"])
@login_required
def book_slot():
    """
    Create a booking request for a student.
    Requires: student must be logged in and approved.
    """
    if current_user.role != "student" or current_user.status != "approved":
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400
    
    start_time_str = data.get("start_time")
    lesson_minutes = data.get("lesson_minutes")
    
    if not start_time_str or not lesson_minutes:
        return jsonify({"success": False, "error": "Missing required fields"}), 400
    
    try:
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        if start_time.tzinfo:
            start_time = start_time.replace(tzinfo=None)
    except ValueError:
        return jsonify({"success": False, "error": "Invalid date format"}), 400
    
    # Validate duration
    if lesson_minutes < 120 or lesson_minutes > 240:
        return jsonify({"success": False, "error": "Duration must be between 2 and 4 hours"}), 400
    
    if lesson_minutes % 60 != 0:
        return jsonify({"success": False, "error": "Duration must be in 1-hour increments"}), 400
    
    # Check if booking is in the future
    if start_time < datetime.utcnow():
        return jsonify({"success": False, "error": "Cannot book past time slots"}), 400
    
    # Calculate end time
    end_time = start_time.replace(minute=start_time.minute + lesson_minutes)
    
    # Calculate price
    try:
        price_eur = calculate_price(lesson_minutes)
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    
    # Get tutor/admin (for now, assume there's one admin/tutor)
    tutor = User.query.filter_by(role="admin").first()
    if not tutor:
        return jsonify({"success": False, "error": "No tutor available"}), 500
    
    # Check for conflicts with accepted bookings
    conflicting_bookings = Booking.query.filter(
        Booking.tutor_id == tutor.id,
        Booking.status == "accepted",
        Booking.start_time < end_time,
        Booking.end_time > start_time
    ).first()
    
    if conflicting_bookings:
        return jsonify({"success": False, "error": "This time slot is already booked"}), 400
    
    # Create booking
    new_booking = Booking(
        student_id=current_user.id,
        tutor_id=tutor.id,
        start_time=start_time,
        end_time=end_time,
        lesson_minutes=lesson_minutes,
        price_eur=price_eur,
        status="pending"
    )
    
    db.session.add(new_booking)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "booking_id": new_booking.id,
        "message": "Booking request submitted successfully"
    }), 201