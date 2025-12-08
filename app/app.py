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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
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
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'admin' or 'student'
    status = db.Column(db.String(20), default="pending") # pending/approved/rejected
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
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["user_role"] = user.role
            return redirect("/")
        
        flash("Invalid email or password", "error")
        return redirect("/login")
    
   
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
     if request.method == "POST":
        name = request.form.get("name")
        lastname = request.form.get("lastname")
        email = request.form.get("email")
        password = request.form.get("password")
        repeat_password = request.form.get("repeat_password")
        
        # Validation
        if not all([name, lastname, email, password, repeat_password]):
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
        
        # Create new user with pending status
        new_user = User(
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

@app.route("/logout")

def logout():
    session.clear()
    return redirect(url_for("login"))
#Run the app
if __name__ == "__main__":
    app.run(debug=True)