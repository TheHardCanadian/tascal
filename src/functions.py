from datetime import date, datetime


def simplifyTime(time):
    dt_converted = datetime.fromisoformat(time)
    formatted_time = dt_converted.strftime("%I:%M %p")
    return formatted_time

def dateCheck(date, current_date):
    dt_converted = datetime.fromisoformat(date)
    dt = dt_converted.strftime("%B %d, %Y")

    if current_date != dt:
        current_date = dt
        print(f"\n---{current_date}---\n")

    return current_date
    
    