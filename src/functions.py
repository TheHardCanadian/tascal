from datetime import date, datetime
from dateutil import parser
from prompt_toolkit import prompt


def simplifyTime(time):
    dt_converted = datetime.fromisoformat(time)
    formatted_time = dt_converted.strftime("%I:%M %p")
    return formatted_time

def simplifyDate(time):
    dt_converted = datetime.fromisoformat(time)
    formatted_time = dt_converted.strftime("%B %d, %Y")
    return formatted_time

def dateCheck(date, current_date):
    dt_converted = datetime.fromisoformat(date)
    dt = dt_converted.strftime("%B %d, %Y")

    if current_date != dt:
        current_date = dt
        print(f"\n---{current_date}---\n")

    return current_date
    
def dateParse(timeperiod_str):
    time_str = prompt(f"Enter {timeperiod_str} date / time: ")
    try:
        time = parser.parse(time_str).isoformat()
        return time
    except (ValueError, TypeError):
        print("invalid date/Time, try a valid date/time such as:\n- 08/24/2026 3:30pm\n- Aug 25, 2026 10:30am\n -2026-08-25 10:30:45\n etc")
        return
    