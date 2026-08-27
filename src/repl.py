import cmd
import sqlite3
import logging
from src.local_dir import TascalApp
from src.googAPI.apiConnect import (
    google_api_connect,
    get_calendar_events,
    get_calendars,
    get_tasks,
    get_task_lists
)
from src.db_schema import (
    update_check, 
    insert_event, 
    insert_calendar, 
    insert_task, 
    insert_task_list, 
    delete_task,
    delete_calendar,
    delete_event
)
from src.functions import simplifyTime, dateCheck, dateParse
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from datetime import date, time, timedelta
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

class TascalREPL(cmd.Cmd):
    intro = "\n--Welcome to Tascal--\n"

    prompt = "tascal> "

    def __init__(self):
        super().__init__()
        self.app = TascalApp()
        self.creds = None
        self.cursor = None
        self.conn = None
        self.calendar_service = None
        self.task_service = None


        self.initialize()

    def initialize(self):
        try:
            self.conn = sqlite3.connect(self.app.db_path)
            self.cursor = self.conn.cursor()
            print("DATABASE CONNECTED")
            self.creds = google_api_connect()
            print("GOOGLE SERVER CONNECTED")
            self.do_sync("")
        except Exception as e:
            print(f"Initialization error: {e}")


    def do_sync(self, arg):
        if not self.creds or not self.cursor:
            print("Not connected to servers, please restart")

        try:
                calendarService = build("calendar", "v3", credentials=self.creds)
                calendarEvents =get_calendar_events(calendarService, self.cursor)
                calendarList = get_calendars(calendarService, self.cursor)
        
                taskService = build("tasks", "v1", credentials=self.creds)
                taskEvents = get_tasks(taskService, self.cursor)
                taskLists = get_task_lists(taskService)
        
        except HttpError as error:
            print(f"An error occurred: {error}")
        
        try:
            #print(f"Calendar Events: {calendarEvents}")
            #print(f"Tasks: {taskEvents}")
            if calendarEvents != None:
                for event in calendarEvents:
                    if event.get('status') == 'cancelled':
                        delete_event(self.cursor, event['id'])
                    if update_check(self.cursor, event):
                        #print(f"inserting event")
                        insert_event(self.cursor, event)
    
            if calendarList != None:
                for calendar in calendarList:
                    if calendar.get('deleted') == True:
                        delete_calendar(self.cursor, calendar['id'])
                    if update_check (self.cursor, calendar):
                        insert_calendar(self.cursor, calendar)
            
            if taskEvents != None:
                for task in taskEvents:
                    if task.get('deleted') == True:
                        delete_task(self.cursor, task['id'])
                    if update_check(self.cursor, task):
                        insert_task(self.cursor, task)
    
            if taskLists != None:
                for list in taskLists:
                    if update_check(self.cursor, list):
                        insert_task_list(self.cursor, list)
    
    
        except (KeyError, sqlite3.DatabaseError, TypeError) as e:
            print(f"ERROR: {e}")
            logging.error(f"Error syncing events: {e}")
    
        self.conn.commit()
        print("Successful connection and update")

    def do_today(self, arg):
        try:
            today = date.today().isoformat()

            self.cursor.execute("""
            SELECT title, start_time, end_time
            FROM events
            WHERE DATE(start_time) = DATE(?)
            ORDER BY start_time                      
            """, (today,))

            events = self.cursor.fetchall()
            if events:
                print("\nToday's schedule currently looks like:\n")
                for title, start, end in events:
                    print(f" - {title}: {simplifyTime(start)} -> {simplifyTime(end)}")
                print("\n")
            else:
                print(f"No events scheduled for {today}")

            self.cursor.execute("""
            SELECT title, due_date, status
            FROM tasks
            WHERE DATE(due_date) = DATE(?)
            """, (today,))

            tasks = self.cursor.fetchall()

            if tasks:
                print("\n Today's Tasks:\n")
                for title, due_date, status in tasks:
                    print(f" - {title}: {simplifyTime(due_date)} : {status}")
            else:
                print(f"No tasks schedule for {today}")

        except Exception as e:
            print(f"Errors {e}")


    def do_upcoming(self, arg):
        

        if len(arg.split()) > 1:
            print("Usage: upcoming <[week, month, year]> --> no argument returns upcoming week")
            return

        timeframe = arg.strip().lower() if arg else "week"

        try:
            today = date.today()
            if timeframe == "week":
                enddate = (date.today() + timedelta(days = 7))
            elif timeframe == "month":
                print("month selected")
                enddate = (date.today() + timedelta(days = 30))
            elif timeframe == "year":
                print("year selected")
                enddate = date(today.year, 12, 31)
            else:
                print("Usage: upcoming <[week, month, year]> --> no argument returns upcoming week")
                return


            self.cursor.execute("""
            SELECT title, start_time, end_time FROM events
            WHERE DATE(start_time) BETWEEN DATE(?) AND DATE(?)
            ORDER BY start_time
            """, (today.isoformat(), enddate.isoformat()))

            events = self.cursor.fetchall()

            self.cursor.execute("""
            SELECT title, due_date, status FROM tasks
            WHERE DATE(due_date) BETWEEN DATE(?) AND DATE(?)
            ORDER BY due_date
            """, (today.isoformat(), enddate.isoformat()))

            tasks = self.cursor.fetchall()
            current_date=date.today().strftime("%B %d, %Y")

            if events:
                print(f"\nUpcoming: {timeframe} \n")
                print(f"---Today ({current_date})---\n")
                for title, start, end in events:
                    current_date = dateCheck(start, current_date)
                    print(f"- {title}: {simplifyTime(start)} -> {simplifyTime(end)}")
                print()

            if tasks:
                for title, due_date, status in tasks:
                    print("Upcoming Tasks:")
                    print(f"- {title}: {simplifyTime(due_date)} : {status}")

                print()

        except Exception as e:
            print(f"Error {e}")

    def do_create(self, arg):
        try:
            self.cursor.execute("SELECT id, summary, timeZone FROM calendars ORDER BY summary")
            calendars = self.cursor.fetchall()
    
            if not calendars:
                print("no calendars found in database, returning")
                return
    
            calendar_names = [cal[1] for cal in calendars]
            calendar_lookup = {cal[1]: [cal[0],cal[2]] for cal in calendars}
    
            completer = WordCompleter(calendar_names, ignore_case=True)
    
            calendar_name = prompt("Calendar: ", completer=completer)
            if calendar_name not in calendar_lookup:
                print(f"Calendar :{calendar_name} not found, available calendar names are: {', '.join(calendar_names)}")
                return
    
            calendar_id, timezone = calendar_lookup[calendar_name]

    
            summary = prompt("Summary: ")
            start_time =  dateParse("start")
            end_time = dateParse("end")
            description = prompt("Description: ")
    
        except (sqlite3.Error, ValueError) as e:
            print(f"Error retrieving calendar or parsing dates{e}")
    
        try:
            event = {
                'summary': summary,
                'start': {'dateTime': start_time, 'timeZone':timezone},
                'end': {'dateTime': end_time, 'timeZone': timezone},
                'description': description
            }
            service = build("calendar","v3", credentials=self.creds)
            result = service.events().insert(calendarId=calendar_id, body=event).execute()
            insert_event(self.cursor, result)
            self.conn.commit()
        except HttpError as error:
            print(f"Http Error: {error}")
    

    def do_exit(self, arg):
        print("Exiting the program....\nThanks for using Tascal!")
        if self.conn:
            self.conn.close()
        return True

    def do_quit(self, arg):
        return self.do_exit(arg)

    
    