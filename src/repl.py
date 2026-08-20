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
from src.functions import simplifyTime, dateCheck
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from datetime import date, time, timedelta

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
            if events:
                current_date=date.today().strftime("%B %d, %Y")
                print(f"\nUpcoming: {timeframe} \n")
                print(f"---Today ({current_date})---\n")
                for title, start, end in events:
                    current_date = dateCheck(start, current_date)
                    print(f"- {title}: {simplifyTime(start)} -> {simplifyTime(end)}")
                print()
        except Exception as e:
            print(f"Error {e}")
        

    def do_exit(self, arg):
        print("Exiting the program....\nThanks for using Tascal!")
        if self.conn:
            self.conn.close()
        return True

    def do_quit(self, arg):
        return self.do_exit(arg)

    
    