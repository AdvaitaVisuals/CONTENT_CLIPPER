import sqlite3

def init_db():
    conn = sqlite3.connect('biru_factory.db')
    cursor = conn.cursor()
    # Task table to track status and details
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT, -- 'whatsapp' or 'web'
            sender TEXT,
            url TEXT,
            project_id TEXT,
            status TEXT DEFAULT 'pending',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            clips_json TEXT
        )
    ''')
    # System logs for general monitoring
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sys_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def log_task(source, sender, url, project_id, status='pending'):
    try:
        conn = sqlite3.connect('biru_factory.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO tasks (source, sender, url, project_id, status) VALUES (?, ?, ?, ?, ?)',
                       (source, sender, url, project_id, status))
        conn.commit()
        conn.close()
        print(f"DEBUG: Task Logged -> {source} | {sender} | {project_id}")
    except Exception as e:
        print(f"DB Error (log_task): {e}")

def update_task_status(project_id, status, clips=None):
    try:
        conn = sqlite3.connect('biru_factory.db')
        cursor = conn.cursor()
        if clips:
            cursor.execute('UPDATE tasks SET status = ?, clips_json = ? WHERE project_id = ?', 
                           (status, json.dumps(clips), project_id))
        else:
            cursor.execute('UPDATE tasks SET status = ? WHERE project_id = ?', (status, project_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error (update_status): {e}")

def get_recent_tasks(limit=10):
    try:
        conn = sqlite3.connect('biru_factory.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks ORDER BY timestamp DESC LIMIT ?', (limit,))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows
    except:
        return []

if __name__ == "__main__":
    init_db()
    print("Database Initialized: biru_factory.db")
