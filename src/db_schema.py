import sqlite3
import json
from pathlib import Path
from src.local_dir import TascalApp
from datetime import datetime


def setup_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            kind TEXT,
            etag TEXT,
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            time_zone TEXT,
            description TEXT,
            location TEXT,
            status TEXT,
            transparency TEXT,
            visibility TEXT,
            created TIMESTAMP,
            updated TIMESTAMP,
            raw_data TEXT,  -- ← Store full JSON as backup
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    '''
    )

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            etag TEXT,
            task_list_id TEXT,
            title TEXT,
            notes TEXT,
            status TEXT,
            due_date TEXT,
            completed TIMESTAMP,
            updated TIMESTAMP,
            parent_id TEXT,
            raw_data TEXT,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    '''
    )

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calendars (
            id TEXT PRIMARY KEY,
            etag TEXT,
            summary TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT,
            timeZone TEXT,
            colorId TEXT,
            backgroundColor TEXT,
            foregroundColor TEXT,
            is_selected INTEGER DEFAULT 1,
            accessRole TEXT,
            is_primary INTEGER DEFAULT 0,
            raw_data TEXT,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    '''
    )

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_lists (
            id TEXT PRIMARY KEY,
            etag TEXT,
            title TEXT NOT NULL,
            updated TIMESTAMP,
            raw_data TEXT,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    '''
    )

    conn.commit()
    conn.close()
    print(f"Database initialized at {db_path}")


def update_check(cursor, api_event):

    cursor.execute('SELECT etag FROM events WHERE id = ?', (api_event['id'],))
    row=cursor.fetchone()

    return row is None or row[0] != api_event.get('etag')

def insert_event(cursor, event):
    cursor.execute('''
        INSERT OR REPLACE INTO events (kind, etag, id, title, start_time, end_time, time_zone, description, location, status, transparency, visibility, created, updated, raw_data, synced_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        event.get('kind', ''),
        event.get('etag', ''),
        event.get('id', ''),
        event.get('summary', ''),
        event['start'].get('dateTime', event['start'].get('date')),
        event['end'].get('dateTime', event['end'].get('date')),    
        event['start'].get('timeZone', ''),
        event.get('description', ''),
        event.get('location', ''),
        event.get('status', ''),
        event.get('transparency', ''),
        event.get('visibility', ''),
        event.get('created', ''),
        event.get('updated', ''),
        json.dumps(event),
        datetime.now(),
    ))


def insert_calendar(cursor, calendar):
    cursor.execute('''
    INSERT OR REPLACE INTO calendars (id, etag, summary, description, location, timeZone, colorId, backgroundColor, foregroundColor, is_selected, accessRole, is_primary, raw_data, synced_at)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
''', (
    calendar.get('id', ''),
    calendar.get('etag', ''), 
    calendar.get('summary', ''), 
    calendar.get('description', 'No description'),
    calendar.get('location', ''),
    calendar.get('timeZone', ''),
    calendar.get('colorId', ''),
    calendar.get('backgroundColor', ''),
    calendar.get('foregroundColor', ''),
    calendar.get('selected', True),
    calendar.get('accessRole', ''),
    calendar.get('primary', False),
    json.dumps(calendar),
    datetime.now()
))


    #if api_event.etag is in databasee, do not update
def insert_task(cursor, event):
    cursor.execute('''
        INSERT OR REPLACE INTO tasks (id, etag, task_list_id, title, notes, status, due_date, completed, updated, parent_id, raw_data, synced_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        event.get('id', ''),
        event.get('etag', ''),
        event.get('taskListID', ''),
        event.get('title', ''),
        event.get('notes', ''),
        event.get('status', ''),
        event.get('due', ''),
        event.get('completed', ''),
        event.get('updated', ''),
        event.get('parent', ''),
        json.dumps(event),
        datetime.now(),
    ))
def insert_task_list(cursor, list):
    cursor.execute('''
    INSERT OR REPLACE INTO task_lists (id, etag, title, updated, raw_data, synced_at)
    VALUES(?,?,?,?,?,?)
''', (
    list.get('id', ''),
    list.get('etag', ''),
    list.get('title', ''),
    list.get('updated', ''),
    json.dumps(list),
    datetime.now()
))

if __name__ == "__main__":
    app = TascalApp()   
    setup_database(app.db_path)