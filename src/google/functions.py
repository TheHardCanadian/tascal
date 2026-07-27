import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.local_dir import TascalApp

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly","https://www.googleapis.com/auth/tasks" ]

def google_api_connect():    # rename to "Connect"
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
"""
    try:
        #Build Cal service
        calendar_service = build("calendar", "v3", credentials=creds)
        get_calendar_events(calendar_service)

        tasks_service = build("tasks", "v1", credentials=creds)
        get_tasks(tasks_service)

    except HttpError as error:
        print(f"An error occurred: {error}")
"""



def get_calendar_events(service):
    now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    print("\n---Calendar Events---\n")
    events_results = service.events().list(
        timeMin=now,
        maxResults=10,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = events_results.get("items",[])

    if not events:
        print("No upcoming events found,")
        return


    for event in events:
        start=event["start"].get("dateTime", event["start"].get("date"))
        start_datetime = datetime.datetime.fromisoformat(start)
        start_date=start_datetime.date()

    
        print(f"{start_date} - {event['summary']}")

def get_tasks(service):
    print("\n---TASKS---\n")

    results = service.tasklists().list().execute()
    task_lists= results.get("items", [])

    if not task_lists:
        print("No tasks found.")
        return

    task_list_id = task_lists[0]["id"]

    task_results = service.tasks().list(tasklist=task_list_id).execute()
    tasks = task_results.get("items", [])

    for task in tasks:
        print(f"- {task['title']}")


"""
Potential commands


"""