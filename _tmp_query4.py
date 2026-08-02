import sqlite3
import json

conn = sqlite3.connect(r'C:\Users\16257\.local\share\mimocode\mimocode.db')
cur = conn.cursor()

# Tetris session - get more tool calls
tetris_sid = 'ses_077ded624ffeBvSArV9S2PjBW1'
print(f"=== TETRIS SESSION - ALL TOOL CALLS ===")
cur.execute("""
    SELECT p.id, json_extract(p.data, '$.tool'), substr(p.data, 1, 1000)
    FROM part p
    WHERE p.session_id = ? AND json_extract(p.data, '$.type') = 'tool'
    ORDER BY p.time_created
""", (tetris_sid,))
for r in cur.fetchall():
    tool = r[1]
    data = r[2]
    try:
        d = json.loads(data)
        state = d.get('state', {})
        inp = state.get('input', {})
        out = str(state.get('output', ''))[:300]
        if tool == 'write':
            print(f"  WRITE: {inp.get('file_path', 'N/A')}")
        elif tool == 'read':
            print(f"  READ: {inp.get('file_path', 'N/A')}")
        elif tool == 'edit':
            print(f"  EDIT: {inp.get('file_path', 'N/A')}")
        elif tool == 'bash':
            cmd = inp.get('command', '')[:150]
            print(f"  BASH: {cmd}")
        elif tool == 'glob':
            print(f"  GLOB: {inp.get('pattern', 'N/A')}")
        else:
            print(f"  {tool}: {str(inp)[:150]}")
    except:
        print(f"  {tool}: parse error")

# Check what files exist in 游戏 directory
print(f"\n=== FILES IN 游戏 DIRECTORY ===")

conn.close()
