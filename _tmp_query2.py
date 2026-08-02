import sqlite3
import json

conn = sqlite3.connect(r'C:\Users\16257\.local\share\mimocode\mimocode.db')
cur = conn.cursor()

# Get sessions for this project, last 14 days, non-checkpoint-writer, non-ask
project_id = '6c97ec37-76a8-400a-9aba-5b99df030cc2'
cur.execute("""
    SELECT id, title, time_created 
    FROM session 
    WHERE project_id = ? 
    ORDER BY time_created DESC
""", (project_id,))
all_sessions = cur.fetchall()
print(f"=== ALL SESSIONS FOR THIS PROJECT ({len(all_sessions)}) ===")
for s in all_sessions:
    print(f"  {s[0]} | {s[1][:80]} | {s[2]}")

# Get the Tetris session details
tetris_sid = 'ses_077ded624ffeBvSArV9S2PjBW1'
print(f"\n=== TETRIS SESSION MESSAGES ===")
cur.execute("""
    SELECT m.id, json_extract(m.data, '$.role'), m.agent_id, m.time_created, substr(json_extract(m.data, '$.content'), 1, 200)
    FROM message m
    WHERE m.session_id = ?
    ORDER BY m.time_created
""", (tetris_sid,))
for r in cur.fetchall():
    role = r[1]
    agent = r[2] or 'main'
    content = r[4] or ''
    print(f"  [{agent}] {role}: {content[:150]}")

# Get the proxy session details
proxy_sid = 'ses_077e68622ffeHIsidFfLc1hglE'
print(f"\n=== PROXY SESSION MESSAGES ===")
cur.execute("""
    SELECT m.id, json_extract(m.data, '$.role'), m.agent_id, m.time_created, substr(json_extract(m.data, '$.content'), 1, 200)
    FROM message m
    WHERE m.session_id = ?
    ORDER BY m.time_created
""", (proxy_sid,))
for r in cur.fetchall():
    role = r[1]
    agent = r[2] or 'main'
    content = r[4] or ''
    print(f"  [{agent}] {role}: {content[:150]}")

# Check TikTok session
tiktok_sid = 'ses_087ad70fbffeqF4ZmJL6QI1EJ9'
print(f"\n=== TIKTOK SESSION MESSAGES ===")
cur.execute("""
    SELECT m.id, json_extract(m.data, '$.role'), m.agent_id, m.time_created, substr(json_extract(m.data, '$.content'), 1, 200)
    FROM message m
    WHERE m.session_id = ?
    ORDER BY m.time_created
""", (tiktok_sid,))
for r in cur.fetchall():
    role = r[1]
    agent = r[2] or 'main'
    content = r[4] or ''
    print(f"  [{agent}] {role}: {content[:150]}")

conn.close()
