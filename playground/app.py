from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

# Configuration for SQLAlchemy
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

#Run the app
if __name__ == "__main__":
    app.run(debug=True)