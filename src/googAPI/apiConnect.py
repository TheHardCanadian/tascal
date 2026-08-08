import datetime
print("Datetime imported")
import os.path
print("OS path imported")
import sqlite3
print("sqlite imported")
import logging
print("logging imported")
import json
from google.auth.transport.requests import Request
print("google request imported")
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
print("google credentials imported")
from google_auth_oauthlib.flow import InstalledAppFlow
print("google flow imported")
from googleapiclient.discovery import build
print("google build imported")
from googleapiclient.errors import HttpError
print("google httperror imported")

from src.local_dir import TascalApp
print("src local directory imported")
from src.db_schema import update_check, insert_event, insert_task, insert_calendar, insert_task_list
print("src loca dir imported")


SCOPES = ["https://www.googleapis.com/auth/calendar.readonly","https://www.googleapis.com/auth/tasks" ]

def google_api_connect():    # rename to "Connect"
    print("Starting main")
    app = TascalApp()
    print("Tascal app created")
    creds = None
    print("About to check tokens path")


    # load existing tokens if availabl

    if app.tokens_path.exists():
        print("Path exists, retrieving credentials")
        creds = Credentials.from_authorized_user_file(str(app.tokens_path), SCOPES) #review Credentials class

    # if no valid credentials available, run OauthFlow
    if not creds or not creds.valid:
        print("No creds or Not Valid")
        if creds and creds.expired and creds.refresh_token:
            print("Entering cred refresh")
            try:
                creds.refresh(Request())
            except RefreshError as e:
                logging.warning(f"Token refresh failed: {e}. Deleting tokens and re-authenticating...")
                app.tokens_path.unlink(missing_ok=True)
                creds=None
            except Exception as e:
                logging.error(f"Unexpected error during refresh: {e}")
                raise
        if not creds:
            print("Flow time")
            flow = InstalledAppFlow.from_client_secrets_file(str(app.credentials_path), SCOPES) #Review installed app flow docs
            creds = flow.run_local_server(port=0)

        app.save_tokens(creds.to_json())

    print("Connection Successful")

    conn = sqlite3.connect(app.db_path)
    cursor = conn.cursor()
#Attach the incoming calendar apis to their respective tables

    #Build services and transfer to the database
    try:


        
        calendarService = build("calendar", "v3", credentials=creds)
        calendarEvents =get_calendar_events(calendarService)
        calendarList = get_calendars(calendarService)

        taskService = build("tasks", "v1", credentials=creds)
        taskEvents = get_tasks(taskService)
        taskLists = get_task_lists(taskService)

    except HttpError as error:
        print(f"An error occurred: {error}")

    try:
        #print(f"Calendar Events: {calendarEvents}")
        #print(f"Tasks: {taskEvents}")
        if calendarEvents != None:
            for event in calendarEvents:
                if update_check(cursor, event):
                    #print(f"inserting event")
                    insert_event(cursor, event)

        if calendarList != None:
            for calendar in calendarList:
                if update_check (cursor, calendar):
                    insert_calendar(cursor, calendar)
        
        if taskEvents != None:
            for task in taskEvents:
                #print(f"inserting task {task}")
                if update_check(cursor, task):
                    insert_task(cursor, task)

        if taskLists != None:
            for list in taskLists:
                if update_check(cursor, list):
                    insert_task_list(cursor, list)


    except (KeyError, sqlite3.DatabaseError, TypeError) as e:
        print(f"ERROR: {e}")
        logging.error(f"Error syncing events: {e}")

    conn.commit()
    conn.close()
    print("Successful connection and update")



def get_calendars(service):
    all_calendars = []
    page_token = None

    while True:
        calendars_result = service.calendarList().list(pageToken = page_token).execute()

        calendars = calendars_result.get("items", [])
        all_calendars.extend(calendars)

        page_token = calendars_result.get("nextPageToken")

        if not page_token:
            break

    print(f"\nTotal calendars: {len(all_calendars)}")
    return all_calendars


def get_calendar_events(service):
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    now_iso = now.isoformat()
    year_datetime = datetime.datetime(now.year,12,31,23,59,59, tzinfo=datetime.timezone.utc).isoformat()

    all_events = []
    page_token = None

    while True:
        events_results = service.events().list(
            calendarId="primary",
            singleEvents=True,
            orderBy="startTime",
            timeMax=year_datetime,
            pageToken=page_token
        ).execute()


        events = events_results.get('items',[])
        all_events.extend(events)

        page_token = events_results.get('nextPageToken')

        if not page_token:
            break

    json_size = len(json.dumps(all_events))
    print(f"JSON size: {json_size / 1024:.2f} KB")
    print(f"Total events pulled: {len(all_events)}")
    if not events:
        print("No upcoming events found,")
        return []

    return all_events 


def get_tasks(service):
    print("\n---TASKS---\n")

    results = service.tasklists().list().execute()
    task_lists= results.get("items", [])
    no_lists = len(task_lists)

    if not task_lists:
        print("No tasks found.")
        return

    #task_list_id = task_lists[0]["id"]

    #task_results = service.tasks().list(tasklist=task_list_id).execute()
    all_tasks = []

    for i in range(no_lists):
        task_results = service.tasks().list(tasklist=task_lists[i]["id"]).execute()
        tasks = task_results.get("items", [])

        for task in tasks:
            task['taskListID'] = i
            print(f"- {task['title']}")

        all_tasks.extend(tasks)
    return all_tasks

def get_task_lists(service):
    all_tasklists = []
    page_token = None

    while True:
        tasklist_results = service.tasklists().list(pageToken=page_token).execute()
        tasklists = tasklist_results.get("items", [])

        all_tasklists.extend(tasklists)


        page_token = tasklist_results.get('nextPageToken')
        if not page_token:
            break

    print(f"Total task lists: {len(all_tasklists)}")
    return all_tasklists



if __name__ == "__main__":
    google_api_connect()
"""
Potential commands


"""