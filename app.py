import re
import sqlite3
from flask import Flask, request, session
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)
app.secret_key = 'H230186N'  # Set a secret key for session management

# Database initialization (only needs to be done once)
def init_db():
    # Initialize database for each phone number on the first registration
    pass

# Initialize database for a specific user
def init_user_db(phone_number):
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

# Main chatbot logic
@app.route('/webhook', methods=['POST'])
def webhook():
    incoming_msg = request.values.get('Body', '').lower().strip()
    sender = request.values.get('From')
    response = MessagingResponse()
    msg = response.message()

    # Initialize user database if necessary
    if not user_exists(sender):
        init_user_db(sender)

    # Check if user exists
    if user_exists(sender):
        if incoming_msg == 'hi':
            msg.body("Welcome back! Please choose an option:\n[Todays Schedule], [Tomorrows Schedule], [My Details]")
        elif incoming_msg == 'todays schedule':
            # Logic to fetch and send today's schedule
            msg.body("Here is today's schedule...")
        elif incoming_msg == 'tomorrows schedule':
            # Logic to fetch and send tomorrow's schedule
            msg.body("Here is tomorrow's schedule...")
        elif incoming_msg == 'my details':
            # Logic to fetch and send user details
            msg.body("Here are your details...")
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
                msg.body("Welcome to HIT chatbot. Type 'register' to start registration.")
        
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
                save_user(sender, session['reg_no'], session['program'], int(year))
                msg.body("Registration successful! Type 'hi' to see options.")
                session.pop('step', None)  # Clear the session step
            else:
                msg.body("Invalid Year. Please enter a number between 1 and 5.")

    return str(response)

if __name__ == '__main__':
    app.run(debug=True)
