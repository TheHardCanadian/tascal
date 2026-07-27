import sqlite3
from pathlib import Path
from local_dir import TascalApp

def setup_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            kind TEXT
            etag TEXT
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
            etag TEXT,
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
            title TEXT NOT NULL,
            notes TEXT,
            status TEXT,
            due_date TEXT,
            completed TIMESTAMP,
            updated TIMESTAMP,
            parent_id TEXT,
            raw_data TEXT,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialized at {db_path}")

def insert_event(event, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    


def insert_task
if __name__ == "__main__":
    app = TascalApp()
    setup_database(app.db_path)