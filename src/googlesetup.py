import time
start = time.time()
print("Starting imports")


import datetime
print(f"Datetime import: {time.time() - start:.2f}s")
import os.path
print(f"OS path import: {time.time() - start:.2f}s")
from google.auth.transport.requests import Request
print(f"Requests import: {time.time() - start:.2f}s")
from google.oauth2.credentials import Credentials
print(f"Google creds import import: {time.time() - start:.2f}s")
from google_auth_oauthlib.flow import InstalledAppFlow
print(f"Flow import: {time.time() - start:.2f}s")
from googleapiclient.discovery import build
print(f"Discovery import: {time.time() - start:.2f}s")
from googleapiclient.errors import HttpError
print(f"HttpError import: {time.time() - start:.2f}s")

from local_dir import TascalApp
print(f"Tascal local import: {time.time() - start:.2f}s")

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly","https://www.googleapis.com/auth/tasks" ]

def main ():
    print("Starting main")
    app = TascalApp()
    print("Tascal app created")
    creds = None
    print("About to check tokens path")


    # load existing tokens if available
    
    if app.tokens_path.exists():
        print("Path exists, retrieving credentials")
        creds = Credentials.from_authorized_user_file(str(app.tokens_path), SCOPES) #review Credentials class

    # if no valid credentials available, run OauthFlow
    if not creds or not creds.valid:
        print("No creds or Not Valid")
        if creds and creds.expired and creds.refresh_token:
            print("Entering cred refresh")
            creds.refresh(Request())
        else:
            print("Flow time")
            flow = InstalledAppFlow.from_client_secrets_file(str(app.credentials_path), SCOPES) #Review installed app flow docs
            creds = flow.run_local_server(port=0)

        app.save_tokens(creds.to_json())

    print("Connection Successful")

    try:
        #Build Cal service
        calendar_service = build("calendar", "v3", credentials=creds)
        get_calendar_events(calendar_service)

        tasks_service = build("tasks", "v1", credentials=creds)
        get_tasks(tasks_service)

    except HttpError as error:
        print(f"An error occurred: {error}")


def get_calendar_events(service):
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    now_iso = now.isoformat()
    year_datetime = datetime.datetime(now.year,12,31,23,59,59, tzinfo=datetime.timezone.utc).isoformat()

    
    print("\n---Calendar Events---\n")
    events_results = service.events().list(
        calendarId="primary",
        timeMin=now_iso,
        singleEvents=True,
        orderBy="startTime",
        timeMax=year_datetime,
    ).execute()

    events = events_results.get("items",[])

    if not events:
        print("No upcoming events found,")
        return

    for event in events:

        start = event["start"].get("dateTime", event["start"].get("date"))
        start_datetime = datetime.datetime.fromisoformat(start)
        start_date = start_datetime.date()
        start_time = start_datetime.strftime("%I:%M %p")
        print(f"{start_date} - {start_time} - {event['summary']}")

def get_tasks(service):
    print("\n---TASKS---\n")

    results = service.tasklists().list().execute()
    task_lists= results.get("items", [])

    if not task_lists:
        print("No tasks found.")
        return

    for list in task_lists:
        print(list['title'])
        print("----------")
        task_list_id = list["id"]
        task_results = service.tasks().list(tasklist=task_list_id).execute()
        tasks = task_results.get("items", [])
        
        for task in tasks:
            print(f"- {task['title']}")


if __name__ == "__main__":
    main()
