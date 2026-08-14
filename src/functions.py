from datetime import date, datetime


def simplifyTime(time):
    dt_converted = datetime.fromisoformat(time)
    formatted_time = dt_converted.strftime("%I:%M %p")
    return formatted_time
