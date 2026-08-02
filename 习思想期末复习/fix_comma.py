import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('习思想期末复习/刷题题库.html', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
# Line 133 (0-indexed: 132) is missing trailing comma
line133 = lines[132]
if not line133.rstrip().endswith(','):
    lines[132] = line133.rstrip() + ','
    with open('习思想期末复习/刷题题库.html', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('Fixed line 133 - added trailing comma')
else:
    print('Line 133 already has comma')

# Also check for any other missing commas between question objects
fix_count = 0
for i in range(len(lines)):
    stripped = lines[i].rstrip()
    if stripped.endswith('}') and i + 1 < len(lines):
        next_stripped = lines[i+1].lstrip()
        if next_stripped.startswith('{id:') and not stripped.endswith(','):
            lines[i] = stripped + ','
            fix_count += 1
            print(f'Fixed line {i+2} - added trailing comma')

if fix_count > 0:
    with open('习思想期末复习/刷题题库.html', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'Total fixes: {fix_count}')
