import sqlite3
import json

conn = sqlite3.connect(r'C:\Users\16257\.local\share\mimocode\mimocode.db')
cur = conn.cursor()

# Proxy session - get text parts to understand what was discussed
proxy_sid = 'ses_077e68622ffeHIsidFfLc1hglE'
print(f"=== PROXY SESSION - TEXT PARTS ===")
cur.execute("""
    SELECT p.id, json_extract(p.data, '$.type'), substr(json_extract(p.data, '$.text'), 1, 500)
    FROM part p
    WHERE p.session_id = ? AND json_extract(p.data, '$.type') = 'text'
    ORDER BY p.time_created
""", (proxy_sid,))
for r in cur.fetchall():
    ptype = r[1]
    text = r[2] or ''
    print(f"  [{ptype}] {text[:300]}")
    print()

# Proxy session - tool calls
print(f"\n=== PROXY SESSION - TOOL CALLS ===")
cur.execute("""
    SELECT p.id, json_extract(p.data, '$.tool'), substr(p.data, 1, 1000)
    FROM part p
    WHERE p.session_id = ? AND json_extract(p.data, '$.type') = 'tool'
    ORDER BY p.time_created
""", (proxy_sid,))
for r in cur.fetchall():
    tool = r[1]
    data = r[2]
    try:
        d = json.loads(data)
        state = d.get('state', {})
        inp = state.get('input', {})
        out = str(state.get('output', ''))[:200]
        if tool == 'bash':
            cmd = inp.get('command', '')[:200]
            print(f"  BASH: {cmd}")
            if out:
                print(f"    out: {out[:150]}")
        elif tool == 'read':
            print(f"  READ: {inp.get('file_path', 'N/A')}")
        elif tool == 'edit':
            print(f"  EDIT: {inp.get('file_path', 'N/A')}")
        elif tool == 'write':
            print(f"  WRITE: {inp.get('file_path', 'N/A')}")
        else:
            print(f"  {tool}: {str(inp)[:150]}")
    except:
        print(f"  {tool}: parse error")

# TikTok session
tiktok_sid = 'ses_087ad70fbffeqF4ZmJL6QI1EJ9'
print(f"\n=== TIKTOK SESSION - TEXT PARTS ===")
cur.execute("""
    SELECT p.id, json_extract(p.data, '$.type'), substr(json_extract(p.data, '$.text'), 1, 500)
    FROM part p
    WHERE p.session_id = ? AND json_extract(p.data, '$.type') = 'text'
    ORDER BY p.time_created
""", (tiktok_sid,))
for r in cur.fetchall():
    ptype = r[1]
    text = r[2] or ''
    print(f"  [{ptype}] {text[:300]}")
    print()

conn.close()
