from flask import Flask, jsonify, request, render_template, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from helpers import login_required, admin_required, parse_email_input

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

# The homepage route which dispalys the calendar
@app.route("/")
def calendar_page():
    if "user_id" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user_id"])
    if user.role == "admin":
        return redirect("/admin/dashboard")
    else:
        return redirect("/student/dashboard")

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

class User(db.Model):
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
    status = db.Column(db.String(20), default="pending")  # pending/accepted/denied
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
    session.clear()

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

        if user is None or not check_password_hash(user.password_hash, password):
            flash("Invalid email/username or password", "error")
            return render_template("login.html"), 403

        session["user_id"] = user.id
        session["user_role"] = user.role

        if user.role == "student" and user.status != "approved":
            flash("Your account is pending approval. Please wait for admin approval.", "error")
            return redirect("/login")

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
    session.clear()

    if request.method == "POST":
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
        return redirect("/signup")

    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/admin/dashboard")
def admin_dashboard():
    if "user_id" not in session:
        flash("Please log in to continue.", "error")
        return redirect("/login")
    
    user = User.query.get(session["user_id"])
    if user is None or user.role != "admin":
        flash("Access denied. Admin login required.", "error")
        return redirect("/login")
    
    return render_template("admin/dashboard.html")

@app.route("/student/dashboard")
def student_dashboard():
    if "user_id" not in session:
        flash("Please log in to continue.", "error")
        return redirect("/login")
    
    user = User.query.get(session["user_id"])
    
    # Check if student is approved
    if user.status != "approved":
        return render_template("student/pending.html")
    
    return render_template("student/dashboard.html")

@app.route("/admin/home")
@admin_required
def admin_home():
    return render_template("home.html")

@app.route("/student/home")
@login_required
def student_home():
    user = User.query.get(session["user_id"])
    if user.status != "approved":
        return redirect("/student/dashboard")
    return render_template("home.html")

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
    user = User.query.get(session["user_id"])
    if user.status != "approved":
        return redirect("/student/dashboard")
    return render_template("student/calendar.html")

if __name__ == "__main__":
    app.run(debug=True)