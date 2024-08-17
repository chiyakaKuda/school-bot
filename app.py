import re
import sqlite3
import json
import datetime
import requests
from flask import Flask, request, session, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from twilio.rest import Client
from bs4 import BeautifulSoup



app = Flask(__name__)
app.secret_key = 'KDCHIYAKA'

# Load the schedules data file
with open('schedules.json') as f:
    schedules = json.load(f)
#Load Events data
with open('events.json') as f:
    events = json.load(f)
#Load Exams data
with open('exams.json') as f:
    exams = json.load(f)

# Email configuration to send feedback to EMAIL_ADDRESS
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_ADDRESS = 'centurygothic22@gmail.com'
EMAIL_PASSWORD = 'lhei vosk aqcc vjby'
MY_EMAIL = 'rootlocalhost04@gmail.com'

#whatsapp configuration to send feedback to my whatsapp No.
TWILIO_ACCOUNT_SID = 'AC67c639c49106574238009309b44a3c31'
TWILIO_AUTH_TOKEN = '50703cac7b225ffda81df269155d5244'
TWILIO_WHATSAPP_NUMBER = 'whatsapp:+14155238886'
MY_WHATSAPP_NUMBER = 'whatsapp:+263718083975'


#creating database if the user was't registered
def init_db(phone_number):
    db_name = f"{phone_number}.db"
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS student   
                 (phonenumber TEXT PRIMARY KEY, RegNo TEXT, Program TEXT, Year INTEGER)''')
    conn.commit()
    conn.close()


#Function to fetch the events from HIT Website:
def scrape_school_events():
    url = "https://www.hit.ac.zw/" 
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    events = []
    event_sections = soup.find_all('div', class_='ectbe-inner-wrapper ectbe-simple-event')
    
    for event in event_sections:
        day = event.find('span', class_='ectbe-ev-day').text
        month = event.find('span', class_='ectbe-ev-mo').text
        year = event.find('span', class_='ectbe-ev-yr').text
        title = event.find('div', class_='ectbe-evt-title').text.strip()
        link = event.find('a', class_='ectbe-evt-url')['href']
        
        events.append(f"{title} - {day} {month} {year}\nMore Info: {link}")
        print(f"Event: {title} on {day}, Link: {link}")
    
    return events
#end of scraped data............
#------------------------------------#
# Check if user exists has already registered
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

# Saving user details 
def save_user(phone_number, reg_no, program, year):
    db_name = f"{phone_number}.db"
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("INSERT INTO student (phonenumber, RegNo, Program, Year) VALUES (?, ?, ?, ?)",
              (phone_number, reg_no, program, year))
    conn.commit()
    conn.close()
#------------------------------------------------------FUNCTIONS------------------------------------------------------#
#------------------------------------------------------FUNCTIONS------------------------------------------------------#
#Sending Feedback:Email Version
def send_feedback_via_email(feedback):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = MY_EMAIL
    msg['Subject'] = "New Feedback Received"

    msg.attach(MIMEText(feedback, 'plain'))

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    text = msg.as_string()
    server.sendmail(EMAIL_ADDRESS, MY_EMAIL, text)
    server.quit()

#Sending by Feedback:WhatsApp:
def send_feedback_via_whatsapp(feedback):
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"Feedback received:\n{feedback}",
            from_=TWILIO_WHATSAPP_NUMBER,
            to=MY_WHATSAPP_NUMBER
        )
        return message.sid
    except Exception as e:
        print(f"Failed to send WhatsApp message: {e}")
        return None
    
# Convert word numbers to digits if user uses words instead of numbers
def word_to_number(word):
    word_dict = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
    }
    return word_dict.get(word.lower(), word)


#Scrap News From HIT Website
# Getting class-names of tags
def scrape_news():
    url = "https://www.hit.ac.zw/"  
    response = requests.get(url)   
    soup = BeautifulSoup(response.text, 'html.parser')
    news_container = soup.find('div', class_='elementor-posts-container')  
    articles = news_container.find_all('article', class_='elementor-post')
    output = "Our News:\n"
    for article in articles:
        title = article.find('h2', class_='elementor-post__title').get_text(strip=True)
        excerpt = article.find('div', class_='elementor-post__excerpt').get_text(strip=True)
        link = article.find('a', class_='elementor-post__read-more')['href']
        output += f"{title}\n{excerpt} More News: {link}\n\n"
    return output.strip()

# Get User Registered Details Function
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
    
# Get Upcoming Events _ Removed 
def get_upcoming_events():
    today = datetime.date.today()
    upcoming_events = []
    
    for event in events:
        event_date = datetime.datetime.strptime(event['date'], "%Y-%m-%d").date()
        if event_date >= today:
            formatted_date = event_date.strftime('%A %d %B %Y')  # Format: DayOfWeek Day Month Year
            upcoming_events.append(f"{event['event_name']} on {formatted_date}")
    
    if upcoming_events:
        return "Upcoming Events:\n" + "\n".join(upcoming_events)
    else:
        return "No upcoming events."
    
#Function to Get Exam Schedule 
def get_exam_schedule(phone_number):
    user_details = get_user_details(phone_number)
    _, program, year = user_details.split(', ')
    program = program.split(': ')[1].lower()
    year = int(year.split(': ')[1])
    
    today = datetime.date.today()
    upcoming_exams = []

    for entry in exams:
        if entry['program'] == program and entry['year'] == year:
            for exam in entry['exams']:
                exam_date = datetime.datetime.strptime(exam['date'], "%Y-%m-%d").date()
                if exam_date >= today:
                    formatted_date = exam_date.strftime('%A %d %B %Y')
                    upcoming_exams.append(f"Course: {exam['course_name']} on {formatted_date} at {exam['time']} in {exam['venue']}")

    if upcoming_exams:
        return "Upcoming Exams:\n" + "\n".join(upcoming_exams)
    else:
        return "No upcoming exams."

## Function to get notices

def scrape_notices():
    url = 'https://www.hit.ac.zw/'  #
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    notices = []
    
    
    notice_container = soup.find('div', class_='elementor-posts-container')
    articles = notice_container.find_all('article', class_='elementor-post')
    for article in articles[:3]:  
        title_tag = article.find('h3', class_='elementor-post__title')
        link_tag = title_tag.find('a')
        title = link_tag.text.strip()
        link = link_tag['href']
        
        notices.append({'title': title, 'link': link})
    
    return notices

# Function to get the schedule our schedules
def get_schedule(program, year, day):
    try:
        program = program.lower()
        schedule_for_day = schedules[program][str(year)][day]
        # Format the schedule into a readable string
        formatted_schedule = f"" + "\n".join(
            [f"{entry['time']}\n{entry['subject']}\n{entry['instructor']}\n{entry['room']}\n" for entry in schedule_for_day]
        )
        return formatted_schedule
    except KeyError:
        return "Schedule not found."
    
#Updating User Details
def update_user_details(phone_number, field, value):
    db_name = f"{phone_number}.db"
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    
    if field == 'reg_no':
        c.execute("UPDATE student SET RegNo = ? WHERE phonenumber = ?", (value, phone_number))
    elif field == 'program':
        c.execute("UPDATE student SET Program = ? WHERE phonenumber = ?", (value, phone_number))
    elif field == 'year':
        c.execute("UPDATE student SET Year = ? WHERE phonenumber = ?", (value, phone_number))
    
    conn.commit()
    conn.close()

#Facilities Dtata
facilities = {
    "classrooms": ["S101", "S102", "S103", "S104", "S105", "S106"]
}
rooms = ['s101', 's102', 's103', 's104', 's105', 's106', 'n109', 'room 12', 'room 15', 'room 20', 'room 22', 'engineering hall']

# function to convert time current time to 24 hr NOTATION
def convert_to_24hr(time):
    return datetime.datetime.strptime(time.strip(), "%I:%M %p").strftime("%H:%M")

#Converting provided time to readable format by functions.
def convert_time_format(time_str):
    start_time, end_time = time_str.split(" - ")
    return convert_to_24hr(start_time), convert_to_24hr(end_time)

# Checking the availability of a Facility based on timetable
def check_availability(facility_name):
    try:
        current_time = datetime.datetime.now().strftime("%H:%M")
        current_day = datetime.datetime.now().strftime("%A")

        facility_name = facility_name.lower()
        availability_info = []

        for program in schedules:
            for year in schedules[program]:
                day_schedule = schedules[program][year].get(current_day, [])

                for entry in day_schedule:
                    start_time, end_time = convert_time_format(entry['time'])
                    if entry['room'].lower() == facility_name:
                        print(
                            f"Checking {entry['room']} for {entry['subject']} from {start_time} to {end_time} against current time {current_time}")
                        if start_time <= current_time <= end_time:
                            availability_info.append(
                                f"{facility_name.upper()} is currently occupied by {entry['subject']} with {entry['instructor']} for {program} Year {year}.")

        if availability_info:
            return "\n".join(availability_info)
        else:
            return f"{facility_name.upper()} is currently not occupied."

    except Exception as e:
        print(f"An error occurred in check_availability: {e}")
        return "An error occurred. Please try again later."
    

# Main Function app.py is initiated by sending Hi to the ChatBot
#THE CHATBOT MAIN CODE-/\-
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
                msg.body("Welcome back! Please choose an option:\n1. Today's Schedule\n2. Tomorrow's Schedule\n3. My Details\n4. School Facilities\n5. Exam Schedule\n6. Upcoming Events\n7. Our News\n8. Feedback")
            elif incoming_msg in ['3', "my details"]:
                user_details = get_user_details(sender) + "\nChange something? Type 'update details' to get started!"
                msg.body(user_details)

            elif incoming_msg == 'update details':
                msg.body("Which detail would you like to update?\n1. Registration Number\n2. Program\n3. University\n4. Year\nChoose which detail to update by typing its number!Up")
                session['update_step'] = 'choose_update'

            elif session.get('update_step') == 'choose_update':
                if incoming_msg == '1':
                    msg.body("Enter your new Registration Number. eg. H230186N")
                    session['update_step'] = 'update_reg_no'
                elif incoming_msg == '2':
                    msg.body("Enter your new Program.e.g Computer Science")
                    session['update_step'] = 'update_program'
                elif incoming_msg == '3':
                    msg.body("Enter your new Year.eg 1, 2, 4")
                    session['update_step'] = 'update_year'
                elif incoming_msg == '4':
                    msg.body("Enter your new Year.")
                    session['update_step'] = 'update_year'
                
                else:
                    msg.body("Looks like your option is on a coffee break. Type 'update details' to find what you can change!.")

            elif session.get('update_step') == 'update_reg_no':
                if re.match(r'^H\d{6}[A-Z]$', incoming_msg.upper()):
                    update_user_details(sender, 'reg_no', incoming_msg.upper())
                    msg.body("our Registration Number is now updated! 🚀 Type 'hi' to explore your refreshed menu!")
                    session.pop('update_step', None)
                else:
                    msg.body("Whoa, that Reg No is a bit off the beaten path. Try entering it as H230186N for the correct format!")

            elif session.get('update_step') == 'update_program':
                if re.match(r'^[A-Za-z\s]+$', incoming_msg):
                    update_user_details(sender, 'program', incoming_msg.lower())
                    msg.body("Your program has been updated! 🎓 Type 'hi' to check out what’s new on your list!")
                    session.pop('update_step', None)
                else:
                    msg.body("Hmm, looks like your program name is in code. Use only letters—no numbers or symbols allowed!")

            elif session.get('update_step') == 'update_year':
                year = word_to_number(incoming_msg)
                if str(year).isdigit() and 1 <= int(year) <= 5:
                    update_user_details(sender, 'year', int(year))
                    msg.body("You’re now in the right year! 🎓 Type 'hi' to explore your new options!")
                    session.pop('update_step', None)
                else:
                    msg.body("⚠It looks like your year is a bit out of range. Please stick to a number between 1 and 5!")
            elif incoming_msg in ['1', "today's schedule"]:
                day =datetime.datetime.now().strftime("%A")  
                user_details = get_user_details(sender)
                _, program, year = user_details.split(', ')
                program = program.split(': ')[1]
                year = int(year.split(': ')[1])
                schedule = get_schedule(program, year, day)
                msg.body(f"Today's Schedule:\n{schedule}")
            elif incoming_msg in ['2', "tomorrow's schedule"]:
                
                tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
                day = tomorrow.strftime("%A") 
                user_details = get_user_details(sender)
                _, program, year = user_details.split(', ')                                                                                                                                             
                program = program.split(': ')[1]
                year = int(year.split(': ')[1])  
                schedule = get_schedule(program, year, day)
                msg.body(f"Tomorrow's Schedule:\n {schedule}")
            elif incoming_msg == '4':
                rooms_list = '\n'.join([f"{i + 1}. {room}" for i, room in enumerate(rooms)])
                msg.body(f"Here is a list of the Classrooms at HIT:\n{rooms_list}\nType the name of the Classroom to check its occupancy status.")
            elif incoming_msg in rooms:
                availability = check_availability(incoming_msg)
                msg.body(availability)
            elif incoming_msg in ['5', "exam schedule"]:
                msg.body(get_exam_schedule(sender))
            elif incoming_msg in ['6', "upcoming events"]:
               # msg.body(get_upcoming_events()) --->removed function
                events = scrape_school_events()
                if events:
                    events_message = "\n\n".join(events)
                    msg.body(f"Here are the upcoming events:\n\n{events_message}")
                else:
                    msg.body("Sorry, no events found at the moment.")
                    msg.body("Send 'Events' to get the latest events from the school website.")
            elif incoming_msg == '7':
                news = scrape_news()
                msg.body(news)
            elif incoming_msg == '8':
                msg.body("Please type your feedback.")
                session['step'] = 'feedback'
            elif session.get('step') == 'feedback':
                feedback = incoming_msg
                #send_feedback_via_whatsapp(feedback)  ---> function not working
                send_feedback_via_email(feedback)  
                msg.body("Thanks for the feedback! 💕Our team is now assembling a highly secret committee to review it.🕵️‍♂️")
                session.pop('step', None)
            else:
                msg.body("Oops! We didn’t catch that. Type 'hi' and let’s get you back on the right track!")
            
        else:
#----- -----------------------------------------------New user registration flow--------------------------------------------------------
            if 'step' not in session:
                session['step'] = 'start'

            if session['step'] == 'start':
                if incoming_msg == 'register':
                    msg.body("Enter your Reg No.e.g H230186N")
                    session['step'] = 'reg_no' 
                else:
                    msg.body("Greetings, future HIT graduate! 🌟 Type 'register' To continue and view your class schedules")
            
            elif session['step'] == 'reg_no':
                if re.match(r'^H\d{6}[A-Z]$', incoming_msg.upper()):
                    session['reg_no'] = incoming_msg.upper()
                    msg.body("Enter Your Program.e.g Computer Science/Software Engineering")
                    session['step'] = 'program'
                else:
                    msg.body("Whoa, that Reg No is a bit off the beaten path. Try entering it as H230186N for the correct format!")
            
            elif session['step'] == 'program':
                if re.match(r'^[A-Za-z\s]+$', incoming_msg):
                    session['program'] = incoming_msg.lower()
                    msg.body("Enter your Academic Year.e.g 1,2,3")
                    session['step'] = 'year'
                else:
                    msg.body("Looks like your program name is trying too hard to be unique! Stick to letters only and skip the numbers and special characters.")
            
            elif session['step'] == 'year':
                year = word_to_number(incoming_msg)
                if str(year).isdigit() and 1 <= int(year) <= 5:
                    # Save user details
                    init_db(sender)
                    save_user(sender, session['reg_no'], session['program'], int(year))
                    msg.body("You’re officially registered! Type 'hi' to start your journey of endless possibilities!")
                    session.pop('step', None)
                else:
                    msg.body("⚠It looks like your year is a bit out of range. Please stick to a number between 1 and 5!.")
    except Exception as e: 
        print(f"An error occurred: {e}")
        msg.body("We hit a snag! Looks like our servers took a coffee break. Try again in a bit.")

    return str(response)


if __name__ == '__main__':
    app.run(debug=True)