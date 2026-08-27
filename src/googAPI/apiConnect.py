import datetime
import os.path
from dateutil import parser
import sqlite3
import logging
import json
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

from src.functions import dateParse
from src.local_dir import TascalApp
from src.db_schema import update_check, get_sync_token, save_sync_token, insert_event, delete_event, insert_task, insert_calendar, insert_task_list, delete_calendar, delete_task


SCOPES = ["https://www.googleapis.com/auth/calendar","https://www.googleapis.com/auth/tasks" ]

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
    return creds


def full_update(creds):
    app= TascalApp()
    conn = sqlite3.connect(app.db_path)
    cursor = conn.cursor()
#Attach the incoming calendar apis to their respective tables

    #Build services and transfer to the database
    try:
        calendarService = build("calendar", "v3", credentials=creds)
        calendarEvents =get_calendar_events(calendarService, cursor)
        calendarList = get_calendars(calendarService, cursor)

        taskService = build("tasks", "v1", credentials=creds)
        taskEvents = get_tasks(taskService, cursor)
        taskLists = get_task_lists(taskService)

    except HttpError as error:
        print(f"An error occurred: {error}")

    try:
        #print(f"Calendar Events: {calendarEvents}")
        #print(f"Tasks: {taskEvents}")
        if calendarEvents != None:
            for event in calendarEvents:
                if event.get('status') == 'cancelled':
                    delete_event(cursor, event['id'])
                else:    
                    if update_check(cursor, event):
                        #print(f"inserting event")
                        insert_event(cursor, event)

        if calendarList != None:
            for calendar in calendarList:
                if calendar.get('deleted') == True:
                    delete_calendar(cursor, calendar['id'])
                else:
                    if update_check (cursor, calendar):
                        insert_calendar(cursor, calendar)
        
        if taskEvents != None:

            for task in taskEvents:
                if task.get('deleted') == True:
                    delete_task(cursor, task['id'])
                else:
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



def get_calendars(service, cursor):

    sync_token = get_sync_token(cursor, 'calendar_list', None)
    all_calendars = []
    page_token = None

    try:
        while True:
            params = {  
                        'pageToken': page_token
                        }

            if sync_token:
                params['syncToken'] = sync_token

            calendars_result = service.calendarList().list(**params).execute()

            calendars = calendars_result.get("items", [])
            all_calendars.extend(calendars)

            page_token = calendars_result.get("nextPageToken")

            if page_token:
                continue

            new_sync_token = calendars_result.get('nextSyncToken')
            if new_sync_token:
                save_sync_token(cursor, 'calendar_list', None, new_sync_token)
                print(f"Saved new syncToken")

            break

    except HttpError as e:
        if e.resp.status == 410:
            print("Sync token expired, performing full sync")
            cursor.execute('DELETE FROM sync_state WHERE resource_type=? AND resource_id=?', ('calendar_list', None ))
            return get_calendars(service, cursor)
        else:
            raise

    print(f"\nTotal calendars: {len(all_calendars)}")
    return all_calendars


def get_calendar_events(service, cursor, calendar_id="primary"):

    sync_token = get_sync_token(cursor, 'calendar_events', calendar_id)
    all_events = []
    page_token = None

    try:
        while True:

            params = {
                'calendarId': calendar_id,
                'singleEvents':True,
                'pageToken': page_token
            }

            if sync_token:
                params['syncToken'] = sync_token
                print(f"Using synctoken from incremental sync")
            else:
                now = datetime.datetime.now(tz=datetime.timezone.utc)
                now_iso = now.isoformat()
                year_end = datetime.datetime(now.year,12,31,23,59,59, tzinfo=datetime.timezone.utc).isoformat()

                params['timeMax'] = year_end
                print(f"Full sync - fetching all events for {now.year}")

            events_results = service.events().list(**params).execute()
            events = events_results.get('items',[])
            all_events.extend(events)

            page_token = events_results.get('nextPageToken')
            if page_token:
                continue

            new_sync_token = events_results.get('nextSyncToken')
            if new_sync_token:
                save_sync_token(cursor,'calendar_events', calendar_id, new_sync_token)
                print(f"Saved new syncToken")

            break


    except HttpError as e:
        if e.resp.status == 410:
            print("Sync token expired, performing full sync")
            cursor.execute('DELETE FROM sync_state WHERE resource_type=? AND resource_id=?', ('calendar_events', calendar_id))
            return get_calendar_events(service, cursor, calendar_id)
        else:
            raise

    json_size = len(json.dumps(all_events))
    print(f"JSON size: {json_size / 1024:.2f} KB")
    print(f"Total events pulled: {len(all_events)}")
    
    return all_events 


def get_tasks(service, cursor):

    all_tasks = []

    try: 
        results = service.tasklists().list().execute()
        task_lists= results.get("items", [])

        if not task_lists:
            print("No tasks found.")
            return 

    except Exception as e:
        print(f"Error {e}")
    

    try:
        for task_list in task_lists:
            task_list_id = task_list['id']
            page_token = None 

            while True:
                params = {'tasklist': task_list_id}
                sync_token = get_sync_token(cursor, 'tasks', task_list_id)

                if sync_token:
                    params['syncToken'] = sync_token
                    print("Using synctoken for incremental sync")
                else:
                    params['pageToken'] = page_token

                task_results = service.tasks().list(**params).execute()
                tasks = task_results.get("items", [])

                for task in tasks:
                    task['taskListID'] = task_list_id

                all_tasks.extend(tasks)

                page_token = task_results.get('nextPageToken')
                if page_token:
                    continue

                new_sync_token = task_results.get('nextSyncToken')
                if new_sync_token:
                    save_sync_token(cursor, 'tasks', task_list_id, new_sync_token)
                    print(f"Saved new sync token {new_sync_token}")

                break

    except HttpError as e:
        if e.resp.status == 410:
            print("Sync token expired, performing full sync")
            cursor.execute('DELETE FROM sync_state WHERE resource_type=? AND resource_id=?', ('tasks', task_list_id))
            return get_tasks(service, cursor)
        else:
            raise

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
