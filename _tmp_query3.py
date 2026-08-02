import sqlite3
import json

conn = sqlite3.connect(r'C:\Users\16257\.local\share\mimocode\mimocode.db')
cur = conn.cursor()

# Check message table schema
cur.execute("PRAGMA table_info(message)")
print("=== MESSAGE TABLE SCHEMA ===")
for r in cur.fetchall():
    print(f"  {r}")

# Check part table schema  
cur.execute("PRAGMA table_info(part)")
print("\n=== PART TABLE SCHEMA ===")
for r in cur.fetchall():
    print(f"  {r}")

# Get the Tetris session - check parts instead of messages
tetris_sid = 'ses_077ded624ffeBvSArV9S2PjBW1'
print(f"\n=== TETRIS SESSION PARTS (sample) ===")
cur.execute("""
    SELECT p.id, p.message_id, json_extract(p.data, '$.type'), substr(p.data, 1, 500)
    FROM part p
    WHERE p.session_id = ?
    ORDER BY p.time_created
    LIMIT 20
""", (tetris_sid,))
for r in cur.fetchall():
    ptype = r[2]
    data = r[3]
    print(f"  part {r[0]} | msg {r[1]} | type={ptype}")
    if data:
        try:
            d = json.loads(data)
            if ptype == 'text':
                text = d.get('text', '')[:200]
                print(f"    text: {text}")
            elif ptype == 'tool':
                tool = d.get('tool', '')
                state = d.get('state', {})
                inp = str(state.get('input', ''))[:200]
                out = str(state.get('output', ''))[:200]
                print(f"    tool={tool} | input={inp} | output={out}")
        except:
            print(f"    raw: {data[:200]}")

conn.close()
