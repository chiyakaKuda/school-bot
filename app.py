import re
import sqlite3
import json
from flask import Flask, request, session
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)
app.secret_key = 'KDCHIYAKA'

# Load the schedule from the JSON file
with open('schedules.json') as f:
    schedules = json.load(f)

# Database initialization
def init_db(phone_number):
    db_name = f"{phone_number}.db"
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS student
                 (phonenumber TEXT PRIMARY KEY, RegNo TEXT, Program TEXT, Year INTEGER)''')
    conn.commit()
    conn.close()

# Check if user exists
def user_exists(phone_number):
    db_name = f"{phone_number}.db"
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("SELECT * FROM student WHERE phonenumber = ?", (phone_number,))
        user = c.fetchone()
        conn.close()
        return user is not None
    except sqlite3.OperationalError:
        return False

# Save user details
def save_user(phone_number, reg_no, program, year):
    db_name = f"{phone_number}.db"
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("INSERT INTO student (phonenumber, RegNo, Program, Year) VALUES (?, ?, ?, ?)",
              (phone_number, reg_no, program, year))
    conn.commit()
    conn.close()

# Convert word numbers to digits
def word_to_number(word):
    word_dict = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
    }
    return word_dict.get(word.lower(), word)

# Function to get user details
def get_user_details(phone_number):
    db_name = f"{phone_number}.db"
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT * FROM student WHERE phonenumber = ?", (phone_number,))
    user = c.fetchone()
    conn.close()
    if user:
        reg_no, program, year = user[1], user[2], user[3]
        return f"Reg No: {reg_no}, Program: {program}, Year: {year}"
    else:
        return "User details not found."

# Function to get the schedule
def get_schedule(program, year, day):
    try:
        schedule_for_day = schedules[program][str(year)][day]
        # Format the schedule into a readable string
        formatted_schedule = f"Today's Schedule:\n" + "\n".join(
            [f"{entry['time']}\n{entry['subject']}\n{entry['instructor']}\n{entry['room']}\n" for entry in schedule_for_day]
        )
        return formatted_schedule
    except KeyError:
        return "Schedule not found."
# Main chatbot logic
@app.route('/webhook', methods=['POST'])
def webhook():
    incoming_msg = request.values.get('Body', '').lower().strip()
    sender = request.values.get('From')
    response = MessagingResponse()
    msg = response.message()

    try:
        # Check if user exists
        if user_exists(sender):
            if incoming_msg == 'hi':
                msg.body("Welcome back! Please choose an option:\n1. Today's Schedule\n2. Tomorrow's Schedule\n3. My Details")
            elif incoming_msg in ['1', "today's schedule"]:
                day = "Monday"  # Replace with logic to determine the current day
                user_details = get_user_details(sender)
                _, program, year = user_details.split(', ')
                program = program.split(': ')[1]
                year = int(year.split(': ')[1])
                schedule = get_schedule(program, year, day)
                msg.body(f"Today's Schedule: {schedule}")
            elif incoming_msg in ['2', "tomorrow's schedule"]:
                day = "Tuesday"  # Replace with logic to determine the next day
                user_details = get_user_details(sender)
                _, program, year = user_details.split(', ')
                program = program.split(': ')[1]
                year = int(year.split(': ')[1])
                schedule = get_schedule(program, year, day)
                msg.body(f"Tomorrow's Schedule: {schedule}")
            elif incoming_msg in ['3', 'my details']:
                user_details = get_user_details(sender)
                msg.body(user_details)
            else:
                msg.body("Invalid input. Type 'hi' to see options.")
        else:
            # New user registration flow
            if 'step' not in session:
                session['step'] = 'start'

            if session['step'] == 'start':
                if incoming_msg == 'register':
                    msg.body("Enter your Reg No.")
                    session['step'] = 'reg_no'
                else:
                    msg.body("Welcome to HIT chatbot. Type register to start by registration.")
            
            elif session['step'] == 'reg_no':
                if re.match(r'^H\d{6}[A-Z]$', incoming_msg.upper()):
                    session['reg_no'] = incoming_msg.upper()
                    msg.body("Enter Your Program.")
                    session['step'] = 'program'
                else:
                    msg.body("Invalid Reg No format. Please enter in the format H230186N.")
            
            elif session['step'] == 'program':
                if re.match(r'^[A-Za-z\s]+$', incoming_msg):
                    session['program'] = incoming_msg
                    msg.body("Enter your Year.")
                    session['step'] = 'year'
                else:
                    msg.body("Invalid Program. Please enter a valid program name without numbers or special characters.")
            
            elif session['step'] == 'year':
                year = word_to_number(incoming_msg)
                if str(year).isdigit() and 1 <= int(year) <= 5:
                    # Save user details
                    init_db(sender)
                    save_user(sender, session['reg_no'], session['program'], int(year))
                    msg.body("Registration successful! Type 'hi' to see options.")
                    session.pop('step', None)
                else:
                    msg.body("Invalid Year. Please enter a number between 1 and 5.")
    except Exception as e:
        print(f"An error occurred: {e}")
        msg.body("An error occurred. Please try again later.")

    return str(response)

if __name__ == '__main__':
    app.run(debug=True)
