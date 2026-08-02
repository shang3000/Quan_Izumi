import sqlite3
conn = sqlite3.connect(r'C:\Users\16257\.local\share\mimocode\mimocode.db')
cur = conn.cursor()

# List tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print("=== TABLES ===")
for t in tables:
    print(t)

# Get project ID hash for this project
print("\n=== PROJECTS ===")
try:
    cur.execute("SELECT * FROM project LIMIT 10")
    for r in cur.fetchall():
        print(r)
except Exception as e:
    print(f"  Error: {e}")

# Get recent sessions (last 14 days)
print("\n=== RECENT SESSIONS (last 14 days) ===")
try:
    cur.execute("SELECT id, project_id, title, time_created FROM session ORDER BY time_created DESC LIMIT 20")
    for r in cur.fetchall():
        print(r)
except Exception as e:
    print(f"  Error: {e}")

conn.close()
