import datetime

def convert_to_24hr(time):
    return datetime.datetime.strptime(time.strip(), "%I:%M %p").strftime("%H:%M")

def convert_time_format(time_str):
    start_time, end_time = time_str.split(" - ")
    return convert_to_24hr(start_time), convert_to_24hr(end_time)

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
                        print(f"Checking {entry['room']} for {entry['subject']} from {start_time} to {end_time} against current time {current_time}")
                        if start_time <= current_time <= end_time:
                            availability_info.append(f"{facility_name.upper()} is currently occupied by {entry['subject']} with {entry['instructor']} for {program} year {year}.")
        
        if availability_info:
            return "\n".join(availability_info)
        else:
            return f"{facility_name.upper()} is currently not occupied."

    except Exception as e:
        print(f"An error occurred in check_availability: {e}")
        return "An error occurred. Please try again later."

# Example schedules.json
schedules = {
    "computer science": {
        "1": {
            "Monday": [
                {
                    "time": "08:00 AM - 10:00 AM",
                    "subject": "Object Oriented in Java",
                    "instructor": "Mr. Mkonzvi",
                    "room": "Room 12"
                },
                {
                    "time": "10:00 AM - 12:00 PM",
                    "subject": "Data Structures",
                    "instructor": "Ms. Smith",
                    "room": "Room 15"
                }
            ],
            "Tuesday": [
                {
                    "time": "08:00 AM - 10:00 AM",
                    "subject": "Algorithms",
                    "instructor": "Dr. Johnson",
                    "room": "Room 22"
                },
                {
                    "time": "10:00 AM - 12:00 PM",
                    "subject": "Data Structures",
                    "instructor": "Ms. Smith",
                    "room": "Room 15"
                }
            ]
        },
        "2": {
            "Friday": [
                {
                    "time": "08:00 AM - 12:00 PM",
                    "subject": "Computer Networks",
                    "instructor": "Mr. Brown",
                    "room": "s101"
                },
                {
                    "time": "10:00 AM - 12:00 PM",
                    "subject": "Algorithms",
                    "instructor": "Dr. Johnson",
                    "room": "s101"
                },
                {
                    "time": "10:00 AM - 12:00 PM",
                    "subject": "Data Structures",
                    "instructor": "Ms. Smith",
                    "room": "s101"
                }
            ],
            "Tuesday": [
                {
                    "time": "08:00 AM - 10:00 AM",
                    "subject": "Technopreneurship",
                    "instructor": "Mr. Obert Chahele",
                    "room": "Engineering Hall"
                },
                {
                    "time": "10:00 AM - 12:00 PM",
                    "subject": "Software Engineering",
                    "instructor": "Mrs. Chibhabha",
                    "room": "N109"
                },
                {
                    "time": "02:00 PM - 06:00 PM",
                    "subject": "Ethics and Professionalism",
                    "instructor": "Ms. Muteveni",
                    "room": "N109"
                }
            ]
        }
    },
    "information technology": {
        "1": {
            "Monday": [
                {
                    "time": "08:00 AM - 10:00 AM",
                    "subject": "Introduction to IT",
                    "instructor": "Ms. Lee",
                    "room": "Room 20"
                }
            ]
        }
    }
}

# Test the function
print(check_availability("s101"))
print("Hello World")