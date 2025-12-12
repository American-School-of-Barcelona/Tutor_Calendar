from flask import Flask, jsonify, request, render_template, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash

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

# Function to provide data for the calendar html template
def get_calendar_data():
    week_days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    months = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]
    return render_template("calendar.html", week_days=week_days, months=months)

# The homepage route which dispalys the calendar
@app.route("/")
def calendar_page():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("calendar.html")

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
    if request.method == "POST":
        email_or_username = request.form.get("email")  # Keep name as "email" for HTML
        password = request.form.get("password")
        
        # Try to find user by email first, then by username
        user = User.query.filter_by(email=email_or_username).first()
        if not user:
            user = User.query.filter_by(username=email_or_username).first()
        
        if not user:
            flash("Invalid email/username or password", "error")
            return redirect("/login")
        
        password_match = check_password_hash(user.password_hash, password)
        
        if password_match:
            # Check if user is approved
            if user.role == "student" and user.status != "approved":
                flash("Your account is pending approval. Please wait for admin approval.", "error")
                return redirect("/login")
            
            session["user_id"] = user.id
            session["user_role"] = user.role

            # Redirect based on role
            if user.role == "admin":
                return redirect("/admin/dashboard")
            else:
                return redirect("/student/dashboard")

        flash("Invalid email/username or password", "error")
        return redirect("/login")
    
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
    """Create test users for development - REMOVE IN PRODUCTION"""
    
    try:
        # Delete ALL existing test users (by any method)
        User.query.filter_by(username="admin").delete()
        User.query.filter_by(username="student").delete()
        User.query.filter_by(email="admin@tutomatics.com").delete()
        User.query.filter_by(email="student@tutomatics.com").delete()
        User.query.filter_by(email="admin@gmail.com").delete()
        User.query.filter_by(email="student@gmail.com").delete()
        db.session.commit()
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@tutomatics.com",
            password_hash=hash_password("A12345"),
            role="admin",
            status="approved"
        )
        
        # Create student user
        student_user = User(
            username="student",
            email="student@tutomatics.com",
            password_hash=hash_password("S12345"),
            role="student",
            status="approved"
        )
        
        db.session.add(admin_user)
        db.session.add(student_user)
        db.session.commit()
        
        # Verify they were created
        admin_check = User.query.filter_by(username="admin").first()
        student_check = User.query.filter_by(username="student").first()
        
        result = "Test users created!<br><br>"
        result += f"Admin: username 'admin' or email 'admin@tutomatics.com' / password: A12345<br>"
        result += f"Student: username 'student' or email 'student@tutomatics.com' / password: S12345<br><br>"
        
        if admin_check:
            result += f"✓ Admin user verified in database<br>"
        else:
            result += f"✗ Admin user NOT found in database<br>"
            
        if student_check:
            result += f"✓ Student user verified in database<br>"
        else:
            result += f"✗ Student user NOT found in database<br>"
        
        result += "<br><a href='/check-users'>Check users</a>"
        return result
    except Exception as e:
        return f"Error creating users: {str(e)}"

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        lastname = request.form.get("lastname")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        repeat_password = request.form.get("repeat_password")
        
        # Validation
        if not all([name, lastname, username, email, password, repeat_password]):
            flash("All fields are required", "error")
            return redirect("/signup")
        
        if password != repeat_password:
            flash("Passwords do not match", "error")
            return redirect("/signup")
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered", "error")
            return redirect("/signup")
        
        # Check if username already exists
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            flash("Username already taken", "error")
            return redirect("/signup")
        
        # Create new user with pending status
        new_user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role="student",
            status="pending"
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Show success message
        flash("Sign up request submitted! Check your email for an approval notification", "success")
        return redirect("/signup")
    return render_template("signup.html")

@app.route("/init-db")
def init_db():
    """Create database tables - REMOVE IN PRODUCTION"""
    try:
        db.create_all()
        return "Database tables created successfully!<br><a href='/create-test-users'>Create test users</a>"
    except Exception as e:
        return f"Error: {str(e)}"

@app.route("/check-db")
def check_db():
    """Check database status"""
    try:
        # Try to query users
        user_count = User.query.count()
        admin = User.query.filter_by(email="admin@gmail.com").first()
        
        result = f"Database Status:<br>"
        result += f"Total users: {user_count}<br>"
        result += f"Admin user exists: {admin is not None}<br>"
        
        if admin:
            result += f"Admin email: {admin.email}<br>"
            result += f"Admin role: {admin.role}<br>"
            result += f"Admin status: {admin.status}<br>"
        
        return result
    except Exception as e:
        return f"Database Error: {str(e)}<br><a href='/init-db'>Create tables first</a>"

@app.route("/logout")

def logout():
    session.clear()
    return redirect(url_for("login"))
#Run the app
if __name__ == "__main__":
    app.run(debug=True)

@app.route("/admin/dashboard")
def admin_dashboard():
    if "user_id" not in session or session.get("user_role") != "admin":
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