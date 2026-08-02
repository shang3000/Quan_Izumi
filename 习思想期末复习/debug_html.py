import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('习思想期末复习/刷题题库.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Check for JS syntax issues
# 1. Check renderNav function
idx = content.find('function renderNav')
if idx >= 0:
    print("renderNav found at char:", idx)
    print(content[idx:idx+200])
    print("---")

# 2. Check chapters array
idx = content.find('const chapters')
if idx >= 0:
    print("chapters found at char:", idx)
    print(content[idx:idx+500])
    print("---")

# 3. Check variables
idx = content.find('let currentChapter')
if idx >= 0:
    print("currentChapter found at char:", idx)
    print(content[idx:idx+100])
    print("---")

idx = content.find('let currentFilter')
if idx >= 0:
    print("currentFilter found at char:", idx)
    print(content[idx:idx+100])
    print("---")

# 4. Check userAnswers
idx = content.find('let userAnswers')
if idx >= 0:
    print("userAnswers found at char:", idx)
    print(content[idx:idx+100])
    print("---")

# 5. Check total questions count
import re
q_count = len(re.findall(r'\{id:\d+,chapter:', content))
print("Total questions in data:", q_count)

# 6. Check chapters count
ch_count = len(re.findall(r'\{id:\d+,name:', content))
print("Total chapters in nav:", ch_count)

# 7. Check for the renderQuestions call at init
idx = content.find('renderQuestions();')
calls = [m.start() for m in re.finditer(r'renderQuestions\(\)', content)]
print("renderQuestions() calls at:", calls)
